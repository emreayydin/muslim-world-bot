"""Entry point for long-form Islamic educational videos (16:9).

generate script -> narrate all sections (intro/10 points/outro) into one audio
track with timing -> render 1920x1080 video -> upload as a normal video.
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

from generate_compilation import generate_compilation
from text_to_speech import build_narration
from render_long import render_long, make_thumbnail
from upload_youtube import upload_short, set_thumbnail

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")


def run(topic: str = None, dry_run: bool = False, privacy: str = "public"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(exist_ok=True)

    log.info("Generating long-form script...")
    import history
    comp = generate_compilation(topic, avoid=history.recent_titles(30, kind="long"))
    log.info(f"Title: {comp['title']} ({len(comp['facts'])} points)")
    (OUTPUT_DIR / f"comp_{ts}.json").write_text(json.dumps(comp, ensure_ascii=False, indent=2))

    # Build narration segments: intro, each point (headline + body), outro
    segments = [("intro", comp["intro"])]
    for i, f in enumerate(comp["facts"], 1):
        segments.append((f"point_{i}", f"{f['headline']}. {f['text']}"))
    segments.append(("outro", comp["outro"]))

    log.info("Generating narration (all sections)...")
    audio_path = str(OUTPUT_DIR / f"long_audio_{ts}.mp3")
    words, sections = build_narration(segments, audio_path)
    dur = max(s["end"] for s in sections)
    log.info(f"Audio: {audio_path} ({dur/60:.1f} min)")

    # AI images per section (halal: no people/faces) — falls FAL_KEY; sonst Pexels
    visuals = None
    if os.environ.get("FAL_KEY"):
        try:
            from generate_visuals import visuals_for_sections
            log.info("Generating AI images (Flux) per section...")
            visuals = visuals_for_sections(
                comp, sections, str(OUTPUT_DIR / f"visuals_{ts}"), orientation="landscape",
                style="reverent, cinematic, peaceful, soft divine light, no people, no faces, Islamic art aesthetic")
        except Exception as e:
            log.warning(f"AI images failed ({e}) — using Pexels.")

    log.info("Rendering video (16:9)...")
    video_path = str(OUTPUT_DIR / f"long_{ts}.mp4")
    render_long(comp, audio_path, sections, video_path, visuals=visuals)
    log.info(f"Video: {video_path}")

    thumb_path = str(OUTPUT_DIR / f"long_thumb_{ts}.png")
    make_thumbnail(comp, thumb_path)

    desc = _build_description(comp, sections)

    if dry_run:
        log.info(f"[DRY RUN] Not uploaded: {video_path}")
        log.info(f"[DRY RUN] Thumbnail: {thumb_path}")
        return video_path

    log.info(f"Uploading (privacy={privacy})...")
    video_id = upload_short(
        video_path=video_path, title=comp["title"], description=desc,
        tags=comp.get("tags", []), privacy=privacy, is_short=False,
    )
    set_thumbnail(video_id, thumb_path)
    history.add_entry("long", comp["title"], comp.get("category", ""))
    log.info(f"Done! https://youtu.be/{video_id}")
    return video_id


def _fmt_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _build_description(comp: dict, sections: list[dict]) -> str:
    """Description with YouTube chapter timestamps (must start at 0:00) + sources."""
    point_sections = [s for s in sections if s["label"].startswith("point_")]
    lines = [comp["intro"], "", "⏱️ Chapters:", "0:00 Intro"]
    for i, s in enumerate(point_sections):
        headline = comp["facts"][i]["headline"]
        lines.append(f"{_fmt_ts(s['start'])} {i + 1}. {headline}")
    outro = next((s for s in sections if s["label"] == "outro"), None)
    if outro:
        lines.append(f"{_fmt_ts(outro['start'])} Reflection")
    # Sources block (channel policy: always cite)
    lines += ["", "📖 Sources:"]
    for i, f in enumerate(comp["facts"], 1):
        if f.get("source"):
            lines.append(f"{i}. {f['source']}")
    return "\n".join(lines)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Muslim World — Long-form Bot")
    p.add_argument("--topic", type=str, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--privacy", type=str, default=os.environ.get("UPLOAD_PRIVACY", "public"),
                   choices=["public", "private", "unlisted"])
    args = p.parse_args()
    run(topic=args.topic, dry_run=args.dry_run, privacy=args.privacy)
