"""Animated story Short: one emotional Muslim family story -> YouTube Short.

Format (since 05.11.2026, modelled on viral "deen tales" Shorts):
  3D-animation stills (Z-Image-Turbo, LOCAL on the Mac, free) with Ken-Burns
  motion; the characters TALK themselves (own edge-tts voice + local Wav2Lip
  lip-sync on every speaking scene, since 05.11. evening), bold
  word-by-word captions, and a closing card with one verified reminder.

Runs on the Mac (launchd), not on GitHub - the image model needs Apple Silicon.

    venv/bin/python src/story_short.py            # scheduled: throttled, uploads
    venv/bin/python src/story_short.py --dry-run  # render only
    venv/bin/python src/story_short.py --id rent-tawakkul --dry-run
"""
import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import edge_tts

import history
from story_bank import all_stories

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("story")

OUTPUT_DIR = ROOT / "src" / "output"
REMOTION_DIR = ROOT / "remotion"
REMOTION_BIN = REMOTION_DIR / "node_modules" / ".bin" / "remotion"
MFLUX_PY = Path.home() / ".local/share/uv/tools/mflux/bin/python"
IMG_SCRIPT = ROOT / "scripts" / "story_images.py"

STYLE = ("3D Pixar Disney animated movie still, stylized cartoon characters with big expressive "
         "eyes, soft cinematic lighting, rich warm colors, shallow depth of field, highly detailed, "
         "emotional, vertical 9:16 composition, modest clothing")
NEGATIVE_HINT = "no text, no letters, no watermark, no logo"

# voice role -> (edge-tts voice, rate, pitch)
VOICES = {
    "narrator":    ("en-US-ChristopherNeural", "-4%", "-2Hz"),
    "woman":       ("en-US-AvaNeural", "-2%", "+0Hz"),
    "young_man":   ("en-US-AndrewNeural", "+0%", "+0Hz"),
    "man":         ("en-US-BrianNeural", "-3%", "-2Hz"),
    "elder_man":   ("en-GB-RyanNeural", "-10%", "-8Hz"),
    "elder_woman": ("en-GB-SoniaNeural", "-10%", "-6Hz"),
    "child":       ("en-US-AnaNeural", "+0%", "+0Hz"),
    "girl":        ("en-US-AnaNeural", "-4%", "-4Hz"),
}
GAP_LINE = 0.22    # silence between lines inside a scene (s)
GAP_SCENE = 0.30   # extra silence when the picture changes


# ---------------------------------------------------------------- audio
async def _tts(text: str, path: str, voice: str, rate: str, pitch: str) -> list[dict]:
    com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7
                words.append({"text": ch["text"], "start": s, "end": s + ch["duration"] / 1e7})
    return words


def _dur(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def scene_speaker(sc: dict) -> str | None:
    """The character whose mouth moves in this scene (first non-narrator line)."""
    if sc.get("speaker"):
        return sc["speaker"]
    return next((spk for spk, _ in sc.get("lines", []) if spk != "narrator"), None)


def build_audio(story: dict, out_mp3: str, work: Path | None = None
                ) -> tuple[list[dict], list[dict], float]:
    """Synthesises every line with its speaker's voice. Returns (words, scenes, total).
    words carry the speaker; scenes = [{start, end, lines:[{speaker, wav, start}]}]
    aligned with story['scenes'] + ending. The per-line wavs stay in `work` for lip-sync."""
    work = Path(work or tempfile.mkdtemp(prefix="story_tts_"))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    chars = story["characters"]
    silence = str(work / "sil.wav")
    pieces, words, scenes = [], [], []
    t = 0.0

    def add_silence(sec: float):
        nonlocal t
        p = str(work / f"sil_{len(pieces)}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=24000:cl=mono", "-t", f"{sec:.3f}", p], check=True)
        pieces.append(p)
        t += sec

    ending = story["ending"]
    all_scenes = story["scenes"] + [{"lines": [["narrator", ending["reminder"]]], "ending": True}]
    for si, sc in enumerate(all_scenes):
        start = t
        placed = []
        for li, (spk, text) in enumerate(sc["lines"]):
            role = "narrator" if spk == "narrator" else chars.get(spk, {}).get("voice", "narrator")
            voice, rate, pitch = VOICES.get(role, VOICES["narrator"])
            p = str(work / f"l_{si}_{li}.mp3")
            ws = asyncio.run(_tts(text, p, voice, rate, pitch))
            wav = p[:-4] + ".wav"  # concat demuxer needs one codec: mp3 -> wav
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ar", "24000",
                            "-ac", "1", wav], check=True)
            p = wav
            d = _dur(p) or (ws[-1]["end"] + 0.2 if ws else 1.0)
            for w in ws:
                words.append({"text": w["text"], "start": w["start"] + t, "end": w["end"] + t,
                              "speaker": spk})
            pieces.append(p)
            placed.append({"speaker": spk, "wav": p, "start": t})
            t += d
            add_silence(GAP_LINE)
        if si < len(all_scenes) - 1:
            add_silence(GAP_SCENE)
        scenes.append({"start": start, "end": t, "lines": placed})
    add_silence(1.2)  # let the ending card breathe
    scenes[-1]["end"] = t
    for i in range(len(scenes) - 1):  # no gaps between pictures
        scenes[i]["end"] = scenes[i + 1]["start"]
    scenes[0]["start"] = 0.0

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    voice_wav = str(work / "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-ar", "24000", "-ac", "1", voice_wav], check=True)
    # soft synthesised night ambience under the voices (halal: no instruments)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", voice_wav,
        "-f", "lavfi", "-t", f"{t:.2f}", "-i", "anoisesrc=color=brown:r=24000:a=0.5",
        "-filter_complex",
        "[1:a]lowpass=f=520,volume=0.07[bg];[0:a]loudnorm=I=-15:TP=-1.5[v];"
        "[v][bg]amix=inputs=2:duration=first:normalize=0[a]",
        "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", out_mp3], check=True)
    return words, scenes, t


# ---------------------------------------------------------------- images
def scene_prompt(story: dict, shot: str, speaker: str | None = None) -> str:
    low = shot.lower()
    looks = [c["look"] for k, c in story["characters"].items()
             if f"{k} " in f"{low} " or f"{k}'" in low or k == speaker]
    cast = (" Characters: " + "; ".join(looks) + ".") if looks else ""
    talk = ""
    if speaker and speaker in story["characters"]:
        talk = (f" {speaker} is talking, mouth slightly open, face fully visible and turned towards "
                f"the camera, {speaker}'s face is the biggest and closest face in the picture.")
    return f"{STYLE}. Setting: {story.get('setting', '')}. Scene: {shot}.{talk}{cast} {NEGATIVE_HINT}."


def build_images(story: dict, out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    seed0 = sum(ord(c) for c in story["id"]) * 97
    jobs, paths = [], []
    for i, sc in enumerate(story["scenes"]):
        p = out_dir / f"img_{i:02d}.png"
        jobs.append({"prompt": scene_prompt(story, sc["shot"], scene_speaker(sc)), "out": str(p),
                     "seed": seed0 + i})
        paths.append(str(p))
    spec = out_dir / "jobs.json"
    spec.write_text(json.dumps({"width": 768, "height": 1344, "steps": 9, "jobs": jobs}, indent=1))
    # one image per process, one after another (a single batch once froze the Mac)
    for i, p in enumerate(paths):
        if Path(p).exists():
            continue
        r = subprocess.run([str(MFLUX_PY), str(IMG_SCRIPT), str(spec), str(i)])
        if r.returncode != 0:
            raise RuntimeError(f"image {i} failed")
        log.info(f"image {i + 1}/{len(paths)} done")
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        raise RuntimeError(f"{len(missing)} images missing")
    return paths


# ---------------------------------------------------------------- lip-sync
LIP_PY = Path.home() / ".local/share/wav2lip/venv/bin/python"
LIP_SCRIPT = ROOT / "scripts" / "lipsync.py"
FADE = 0.35   # must match FADE in remotion/src/MuslimStory.tsx
FPS = 30


def _read_wav(path: str):
    import array
    import wave
    with wave.open(path) as w:
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
        return a, w.getframerate()


def build_talking(story: dict, scenes: list, images: list[str], out_dir: Path) -> list:
    """One lip-synced clip per scene with a speaking character (None = still image).
    Each clip starts at max(0, scene.start - FADE) and covers the whole visible span;
    its audio contains ONLY that speaker's lines, so the mouth rests otherwise."""
    import array
    import wave
    if not LIP_PY.exists():
        log.warning("Wav2Lip not installed - stills only")
        return [None] * len(images)
    if out_dir.exists():  # clips belong to THIS audio take - never reuse old ones
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    jobs, clips = [], []
    n = len(images)
    for i, sc in enumerate(story["scenes"]):
        spk = scene_speaker(sc)
        if not spk or spk not in story["characters"]:
            clips.append(None)
            continue
        t0 = max(0.0, scenes[i]["start"] - FADE)
        t1 = (scenes[n]["start"] if i == n - 1 else scenes[i]["end"]) + FADE + 0.3
        sr = 24000
        track = array.array("h", bytes(2 * (int((t1 - t0) * sr) + 1)))
        for ln in scenes[i]["lines"]:
            if ln["speaker"] != spk:
                continue
            a, _ = _read_wav(ln["wav"])
            o = int((ln["start"] - t0) * sr)
            a = a[: max(0, len(track) - o)]
            track[o:o + len(a)] = a  # same length slice -> in-place overwrite
        wav = out_dir / f"lip_{i:02d}.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(track.tobytes())
        out = out_dir / f"talk_{i:02d}.mp4"
        jobs.append({"image": images[i], "audio": str(wav), "out": str(out), "speaker": spk})
        clips.append({"path": str(out), "start": t0})
    if not jobs:
        return clips
    spec = out_dir / "lip_jobs.json"
    res = out_dir / "lip_result.json"
    spec.write_text(json.dumps({"fps": FPS, "jobs": jobs, "result": str(res)}, indent=1))
    r = subprocess.run([str(LIP_PY), str(LIP_SCRIPT), str(spec)])
    ok = json.loads(res.read_text()) if res.exists() and r.returncode == 0 else {}
    clips = [c if c and ok.get(c["path"]) and Path(c["path"]).exists() else None for c in clips]
    log.info(f"Lip-sync: {sum(1 for c in clips if c)}/{len(jobs)} speaking scenes animated")
    return clips


# ---------------------------------------------------------------- render
def render(story: dict, audio: str, images: list[str], words: list, scenes: list,
           total: float, out_mp4: str, clips: list | None = None) -> str:
    pub = REMOTION_DIR / "public" / "story"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    shutil.copy(audio, pub / "audio.mp3")
    names = []
    for i, p in enumerate(images):
        n = f"img_{i:02d}.png"
        shutil.copy(p, pub / n)
        names.append(f"story/{n}")
    videos = []
    for i, c in enumerate(clips or [None] * len(images)):
        if c:
            n = f"talk_{i:02d}.mp4"
            shutil.copy(c["path"], pub / n)
            videos.append({"src": f"story/{n}", "start": c["start"]})
        else:
            videos.append(None)
    props = {
        "audio": "story/audio.mp3",
        "images": names,
        "videos": videos,
        "scenes": [{"start": x["start"], "end": x["end"]} for x in scenes],
        "words": words,
        "durationSeconds": total,
        "ending": story["ending"],
        "handle": "@MuslimWorld-info",
    }
    pp = REMOTION_DIR / "props_story.json"
    pp.write_text(json.dumps(props, ensure_ascii=False))
    r = subprocess.run([str(REMOTION_BIN), "render", "MuslimStory", str(Path(out_mp4).resolve()),
                        f"--props={pp}", "--log=error", "--concurrency=3"],
                       cwd=str(REMOTION_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Remotion story render failed:\n{r.stderr[-2000:]}")
    return out_mp4


# ---------------------------------------------------------------- pipeline
def pick_story(story_id: str | None) -> dict | None:
    stories = all_stories()
    if story_id:
        return next(s for s in stories if s["id"] == story_id)
    done = history.all_titles()
    fresh = [s for s in stories if s["title"] not in done]
    return fresh[0] if fresh else None


def description(story: dict) -> str:
    e = story["ending"]
    tags = " ".join("#" + t.replace(" ", "") for t in story.get("tags", [])[:4])
    return (f"{story['hook']}\n\n"
            f"“{e['reminder']}”\n\U0001F4D6 {e['source']}\n\n"
            f"{e['arabic']} — {e['word']}\n\n"
            f"A short animated reminder story. The characters are fictional; the reminder is real.\n"
            f"Follow for a new Islamic story every day.\n\n"
            f"#shorts #islamicstory #muslim {tags}")


def run(story_id: str | None = None, dry_run: bool = False, privacy: str = "public"):
    if not dry_run and not story_id:
        from main import _should_skip_for_quota
        skip, reason = _should_skip_for_quota()
        if skip:
            log.info(f"Skipping - {reason}.")
            return None
    story = pick_story(story_id)
    if not story:
        log.warning("Story bank used up - skipping (no repeats). Refill src/story_bank.py.")
        return None
    log.info(f"Story: {story['title']}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = OUTPUT_DIR / f"story_{story['id']}"
    work.mkdir(parents=True, exist_ok=True)

    log.info("Voices...")
    audio = str(work / "audio.mp3")
    words, scenes, total = build_audio(story, audio, work / "lines")
    log.info(f"Audio {total:.1f}s, {len(words)} words, {len(scenes)} scenes")

    log.info("Images (local Z-Image-Turbo)...")
    images = build_images(story, work / "images")

    log.info("Lip-sync (local Wav2Lip)...")
    clips = build_talking(story, scenes, images, work / "talk")

    log.info("Rendering...")
    out = str(OUTPUT_DIR / f"story_{ts}.mp4")
    render(story, audio, images, words, scenes, total, out, clips)
    log.info(f"Video: {out}")
    if dry_run:
        return out

    from upload_youtube import upload_short
    vid = upload_short(video_path=out, title=story["title"][:100], description=description(story),
                       tags=story.get("tags", []) + ["islamic story", "muslim", "islam"],
                       privacy=privacy)
    history.add_entry("short", story["title"], "story")
    log.info(f"Done! https://youtube.com/shorts/{vid}")
    shutil.rmtree(work, ignore_errors=True)
    return vid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", dest="story_id")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--privacy", default=os.environ.get("UPLOAD_PRIVACY", "public"),
                    choices=["public", "private", "unlisted"])
    a = ap.parse_args()
    run(a.story_id, a.dry_run, a.privacy)
