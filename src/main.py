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
from render_video import render_video
from upload_youtube import upload_short

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


def _type_for_now() -> str:
    """Rotates through all content types using an absolute slot counter.

    6 slots/day but 7 types, so a fixed hour->type map would never reach the 7th.
    Using (ordinal_day * 6 + slot) % len(types) cycles every type evenly over days.
    """
    now = datetime.utcnow()
    slot = now.hour // 4                        # 0..5
    counter = now.date().toordinal() * 6 + slot
    return CONTENT_TYPES[counter % len(CONTENT_TYPES)]


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
    audio_path = str(OUTPUT_DIR / f"audio_{timestamp}.mp3")
    words = generate_audio(tts_text, audio_path)
    log.info(f"Audio: {audio_path} ({len(words)} words)")

    # 3. Render video (halal montage + animated captions + source line)
    log.info("Rendering video...")
    video_path = str(OUTPUT_DIR / f"short_{timestamp}.mp4")
    background = os.environ.get("BACKGROUND_VIDEO_PATH")
    render_video(item, audio_path, video_path, words=words, background_video=background)
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
