"""Main entry point: generate one Islamic Short, render it, upload to YouTube.

There are 7 content types but 6 daily slots (cron 0,4,8,12,16,20 UTC), so the
type rotates by an absolute slot counter (day * 6 + slot % 7). Over a week every
type — Qur'an, Hadith, Dua, Character, Prophets, Islamic story, Did-you-know —
gets aired evenly; pass --type to force a specific one.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from generate_content import generate_content, CONTENT_TYPES
from text_to_speech import generate_audio
from audio_fx import add_ambience
from render_video import render_video
from upload_youtube import upload_short

# Calmer, more reflective narration than the trivia bot (slightly slower voice)
NARRATION_RATE = "-6%"
# Ambience bed per content type (all synthesised, halal, no instruments)
AMBIENCE_KIND = {
    "quran": "wind", "hadith": "wind", "dua": "night",
    "akhlaq": "wind", "prophet_story": "night", "islamic_story": "night",
    "did_you_know": "wind",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")

# Long-form videos publish on these UTC weekdays (Mon=0 … Sun=6): Tue, Thu, Sun.
LONG_VIDEO_WEEKDAYS = {1, 3, 6}

# Self-throttle so the bot paces itself even though GitHub's free cron fires
# unreliably. The shorts workflow is scheduled far more often than needed (every
# 2h); these caps decide whether a given run actually uploads. YouTube's free
# quota = 10,000 units/day, videos.insert = 1,600 → 6 uploads/day max.
DAILY_UPLOAD_CAP = 6          # total videos (shorts + long) per quota day
MIN_HOURS_BETWEEN = 2.0       # min spacing so 6 uploads fit the active window (08-20 UTC)


def _should_skip_for_quota() -> tuple[bool, str]:
    """Returns (skip, reason) based on the day's upload count and spacing, so
    dropped cron triggers get 'caught up' by later ones without exceeding quota."""
    import history
    total = history.uploads_in_current_window()
    shorts = history.uploads_in_current_window(kind="short")
    gap = history.hours_since_last_upload()

    # Reserve one slot for the long-form video on its days (Tue/Thu/Sun).
    is_long_day = datetime.utcnow().weekday() in LONG_VIDEO_WEEKDAYS
    short_cap = DAILY_UPLOAD_CAP - 1 if is_long_day else DAILY_UPLOAD_CAP

    if total >= DAILY_UPLOAD_CAP:
        return True, f"daily upload cap reached ({total}/{DAILY_UPLOAD_CAP})"
    if shorts >= short_cap:
        return True, f"short cap for today reached ({shorts}/{short_cap})"
    if gap is not None and gap < MIN_HOURS_BETWEEN:
        return True, f"only {gap:.1f}h since last upload (min {MIN_HOURS_BETWEEN}h)"
    return False, ""


# Weighted rotation — analytics (Aug 2026) show Dua is by far the top performer
# (4 of the top videos are duas), so it airs ~2x as often as the other types.
WEIGHTED_ROTATION = [
    "dua", "quran", "hadith", "akhlaq", "prophet_story", "islamic_story",
    "did_you_know", "dua",
]


def _type_for_now() -> str:
    """Picks the next content type from the weighted rotation, advancing once per
    real upload (indexed by total history length) so the cycle stays even
    regardless of when GitHub's cron actually fires."""
    import history
    n = history.count()
    return WEIGHTED_ROTATION[n % len(WEIGHTED_ROTATION)]


def _build_description(item: dict) -> str:
    """Description leads with the source + Arabic (channel policy: always cite)."""
    parts = []
    if item.get("translation"):
        parts.append(item["translation"])
    else:
        parts.append(item.get("body", ""))
    parts.append("")
    parts.append(f"📖 Source: {item.get('source', '')}")
    if item.get("arabic"):
        parts.append("")
        parts.append(item["arabic"])
    if item.get("transliteration"):
        parts.append(item["transliteration"])
    return "\n".join(parts).strip()


def run(content_type: str = None, dry_run: bool = False, privacy: str = "public"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(exist_ok=True)

    auto = content_type is None  # scheduled run (no explicit --type)

    # Respect the daily upload quota only for scheduled, real uploads; a manual
    # run (explicit --type) or a dry run is never skipped.
    if auto and not dry_run:
        skip, reason = _should_skip_for_quota()
        if skip:
            log.info(f"Skipping this run — {reason}.")
            return None

    if content_type is None:
        content_type = _type_for_now()

    # 1. Generate content (avoiding recent titles)
    log.info(f"Generating content (type={content_type})...")
    import history
    item = generate_content(content_type, avoid=history.recent_titles(40, kind="short"))
    log.info(f"Title: {item['title']}  |  Source: {item.get('source')}")

    (OUTPUT_DIR / f"content_{timestamp}.json").write_text(
        json.dumps(item, ensure_ascii=False, indent=2))

    # 2. Text to speech (returns word-level timing for captions)
    log.info("Generating audio...")
    tts_text = f"{item['hook']} {item['body']} {item.get('cta', '')}".strip()
    voice_path = str(OUTPUT_DIR / f"voice_{timestamp}.mp3")
    words = generate_audio(tts_text, voice_path, rate=NARRATION_RATE)
    log.info(f"Voice: {voice_path} ({len(words)} words)")

    # 2b. Mix a calm halal ambience bed under the voice (word timing unaffected)
    audio_path = str(OUTPUT_DIR / f"audio_{timestamp}.mp3")
    add_ambience(voice_path, audio_path, kind=AMBIENCE_KIND.get(content_type, "wind"))

    # 2c. AI images (halal: no people/faces) — falls FAL_KEY gesetzt; sonst Pexels.
    #     Mit AI_VIDEO=1 wird zusätzlich das ERSTE Bild per LTX zum echten
    #     Video-Hook animiert (günstigster Qualitäts-Hebel: ~$0.02/Short).
    ai_images = None
    hook_video = None
    # RENDER_ENGINE=remotion → free animated Remotion visuals; skip paid fal.ai.
    use_remotion = os.environ.get("RENDER_ENGINE", "").lower() == "remotion"
    IMG_STYLE = ("reverent, cinematic, peaceful, soft divine light, no people, "
                 "no faces, Islamic art aesthetic")
    if not use_remotion and os.environ.get("FAL_KEY") and item.get("image_prompts"):
        prompts = item["image_prompts"]
        vis_dir = str(OUTPUT_DIR / f"visuals_{timestamp}")
        try:
            from generate_visuals import images_for_prompts, flux_image_and_url
            if os.environ.get("AI_VIDEO") == "1" and prompts:
                from generate_video import animate_image_url
                os.makedirs(vis_dir, exist_ok=True)
                # AI_IMAGE_MAX = number of AI still-images (Ken-Burns). 0 = budget
                # mode: only the animated hook + free Pexels for the rest.
                img_max = int(os.environ.get("AI_IMAGE_MAX", str(len(prompts))))
                log.info(f"Generating AI hook image + animating (LTX)... [img_max={img_max}]")
                img0, url0 = flux_image_and_url(
                    prompts[0], os.path.join(vis_dir, "img_0.png"),
                    orientation="portrait", style=IMG_STYLE)
                try:
                    hook_video = animate_image_url(url0, os.path.join(vis_dir, "hook.mp4"))
                except Exception as e:
                    log.warning(f"AI hook video failed ({e}) — using Ken-Burns.")
                if img_max >= 1:
                    rest = images_for_prompts(prompts[1:img_max], vis_dir, orientation="portrait",
                                              style=IMG_STYLE) if img_max > 1 else []
                    ai_images = [img0] + rest
                else:
                    ai_images = None  # budget: hook video + Pexels body
            else:
                log.info("Generating AI images (Flux)...")
                ai_images = images_for_prompts(prompts, vis_dir, orientation="portrait",
                                               style=IMG_STYLE)
        except Exception as e:
            log.warning(f"AI images failed ({e}) — using Pexels.")

    # 3. Render video (halal montage + animated captions + source line)
    log.info("Rendering video...")
    video_path = str(OUTPUT_DIR / f"short_{timestamp}.mp4")
    background = os.environ.get("BACKGROUND_VIDEO_PATH")
    if use_remotion:
        try:
            from render_remotion import render_remotion
            render_remotion(item, audio_path, video_path, words)
        except Exception as e:
            log.warning(f"Remotion render failed ({e}) — falling back to ffmpeg.")
            render_video(item, audio_path, video_path, words=words, background_video=background)
    else:
        render_video(item, audio_path, video_path, words=words, background_video=background,
                     ai_images=ai_images, hook_video=hook_video)
    log.info(f"Video: {video_path}")

    if dry_run:
        log.info(f"[DRY RUN] Not uploaded. Saved at: {video_path}")
        return video_path

    # 4. Upload to YouTube
    log.info(f"Uploading (privacy={privacy})...")
    video_id = upload_short(
        video_path=video_path,
        title=item["title"],
        description=_build_description(item),
        tags=item.get("tags", []),
        privacy=privacy,
    )
    history.add_entry("short", item["title"], item.get("content_type", ""))
    log.info(f"Done! https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Muslim World — Shorts Bot")
    parser.add_argument("--type", dest="content_type", type=str, default=None,
                        choices=CONTENT_TYPES, help="Content type (default: by hour)")
    parser.add_argument("--dry-run", action="store_true", help="No upload, local render only")
    parser.add_argument("--privacy", type=str, default=os.environ.get("UPLOAD_PRIVACY", "public"),
                        choices=["public", "private", "unlisted"])
    args = parser.parse_args()

    run(content_type=args.content_type, dry_run=args.dry_run, privacy=args.privacy)
