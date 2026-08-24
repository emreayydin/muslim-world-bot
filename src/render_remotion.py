"""Render a Muslim World Short via the Remotion animated composition.

Free + halal: animated Islamic geometry, drifting stars, glow, self-glowing
Arabic, and kinetic word-highlight captions — no stock/AI images. The caller
falls back to the ffmpeg renderer (render_video) on any failure, so the bot
never breaks.
"""
import json
import shutil
import subprocess
from pathlib import Path

from render_video import _group_captions, TYPE_BADGES, _probe_duration

REMOTION_DIR = Path(__file__).resolve().parent.parent / "remotion"
PUBLIC = REMOTION_DIR / "public"
REMOTION_BIN = REMOTION_DIR / "node_modules" / ".bin" / "remotion"

# (top = rich edge colour, bottom = dark centre) per content type
PALETTE = {
    "quran":         ([8, 60, 48],  [4, 20, 26]),
    "hadith":        ([8, 46, 56],  [4, 16, 24]),
    "dua":           ([26, 20, 58], [8, 8, 26]),
    "akhlaq":        ([12, 56, 26], [4, 20, 12]),
    "prophet_story": ([14, 18, 56], [4, 8, 24]),
    "islamic_story": ([44, 30, 14], [16, 10, 6]),
    "did_you_know":  ([40, 30, 10], [14, 10, 4]),
}
DEFAULT_PAL = ([8, 40, 34], [4, 18, 22])


def render_remotion(item: dict, audio_path: str, output_path: str, words: list) -> str:
    if not REMOTION_BIN.exists():
        raise RuntimeError("Remotion not installed (run `npm ci` in remotion/)")

    total = (max(w["end"] for w in words) + 0.8) if words else _probe_duration(audio_path)
    if total <= 0:
        total = 40.0
    captions = _group_captions(words or [], total=total) if words else []
    top, bottom = PALETTE.get(item.get("content_type", ""), DEFAULT_PAL)

    PUBLIC.mkdir(exist_ok=True)
    shutil.copy(audio_path, PUBLIC / "audio.mp3")

    props = {
        "badge": TYPE_BADGES.get(item.get("content_type", ""), "REMINDER"),
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "arabic": item.get("arabic", "") or "",
        "captions": captions,
        "audio": "audio.mp3",
        "top": top,
        "bottom": bottom,
    }
    props_path = REMOTION_DIR / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False))

    out = str(Path(output_path).resolve())
    cmd = [str(REMOTION_BIN), "render", "MuslimShort", out,
           f"--props={props_path}", "--log=error"]
    r = subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Remotion render failed:\n{r.stderr[-1800:]}")
    return output_path


LONG_TOP, LONG_BOTTOM = [8, 46, 38], [4, 20, 26]   # calm emerald for long videos


def render_remotion_long(comp: dict, audio_path: str, output_path: str,
                         words: list, sections: list) -> str:
    """Renders a long-form 16:9 video via the animated MuslimLong composition."""
    if not REMOTION_BIN.exists():
        raise RuntimeError("Remotion not installed (run `npm ci` in remotion/)")

    facts = comp.get("facts", [])
    comp_sections = []
    for s in sections:
        label = s["label"]
        if label == "intro":
            comp_sections.append({"label": "intro", "start": s["start"], "end": s["end"]})
        elif label == "outro":
            comp_sections.append({"label": "outro", "start": s["start"], "end": s["end"]})
        elif label.startswith("point_"):
            idx = int(label.split("_")[1])
            f = facts[idx - 1] if 0 < idx <= len(facts) else {}
            comp_sections.append({
                "label": "point", "start": s["start"], "end": s["end"], "index": idx,
                "headline": f.get("headline", ""), "source": f.get("source", ""),
            })

    total = max(s["end"] for s in sections) + 0.6
    captions = _group_captions(words or [], total=total) if words else []

    PUBLIC.mkdir(exist_ok=True)
    shutil.copy(audio_path, PUBLIC / "audio.mp3")

    props = {
        "title": comp.get("title", ""),
        "count": len(facts),
        "sections": comp_sections,
        "captions": captions,
        "audio": "audio.mp3",
        "top": LONG_TOP,
        "bottom": LONG_BOTTOM,
    }
    props_path = REMOTION_DIR / "props_long.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False))

    out = str(Path(output_path).resolve())
    cmd = [str(REMOTION_BIN), "render", "MuslimLong", out,
           f"--props={props_path}", "--log=error"]
    r = subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Remotion long render failed:\n{r.stderr[-1800:]}")
    return output_path


if __name__ == "__main__":
    from text_to_speech import generate_audio
    item = {
        "content_type": "dua",
        "title": "The Dua That Gives You Strength",
        "source": "Qur'an 3:173",
        "arabic": "حَسْبُنَا ٱللَّهُ وَنِعْمَ ٱلْوَكِيلُ",
        "hook": "Say this when you feel weak.",
        "body": "When the weight of the world presses on your chest, turn to Allah "
                "with these words. Allah is enough for us, and He is the best guardian. "
                "Say it, and feel the burden lift.",
        "cta": "Follow for a daily reminder.",
    }
    text = f"{item['hook']} {item['body']} {item['cta']}"
    w = generate_audio(text, "/tmp/rr_audio.mp3", rate="-6%")
    render_remotion(item, "/tmp/rr_audio.mp3", "/tmp/rr_out.mp4", w)
    print("Rendered /tmp/rr_out.mp4")
