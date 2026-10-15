"""Render an existing source-marked reminder locally; never publish it."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from local_content import ENTRIES
from text_to_speech import generate_audio
from render_remotion import render_remotion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="The Dua Ibrahim Made for His Future Children")
    parser.add_argument("--name", default="ibrahim-dua")
    args = parser.parse_args()
    item = next((dict(entry) for entry in ENTRIES if entry["title"] == args.title), None)
    if not item or not item.get("source"):
        raise SystemExit("Choose an existing source-marked bank title.")
    item["cta"] = "Follow Muslim World for a daily reminder with its source."
    out = ROOT / "src" / "output" / "quality-2026-10-15" / args.name
    out.mkdir(parents=True, exist_ok=True)
    text = f"{item['hook']}. {item['body']} {item['cta']}"
    cache = out / "narration.json"
    audio = out / "voice.mp3"
    data = json.loads(cache.read_text()) if cache.exists() else {}
    if data.get("text") == text and audio.exists():
        words = data["words"]
    else:
        words = generate_audio(text, str(audio), rate="-6%")
        cache.write_text(json.dumps({"text": text, "words": words}, ensure_ascii=False, indent=2))
    (out / "content.json").write_text(json.dumps(item, ensure_ascii=False, indent=2))
    render_remotion(item, str(audio), str(out / "preview.mp4"), words)
    print(out / "preview.mp4")


if __name__ == "__main__":
    main()
