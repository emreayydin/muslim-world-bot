"""POV Short: "POV: you wake up in Madinah" - first-person day with clock + fact chips.

Format since 15.11.2026 (reference: @wander_frame_ POV city days). Reuses the
story pipeline pieces: edge-tts voice, local Z-Image-Turbo images (one image per
process), Remotion render (composition MuslimPOV), YouTube upload, TikTok post.

    venv/bin/python src/pov_short.py --id pov-madinah-day --dry-run
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import history  # noqa: E402
import story_short as ss  # noqa: E402
from pov_bank import all_povs  # noqa: E402

log = ss.log
VOICE = ("en-US-AndrewNeural", "-8%", "-2Hz")   # calm inner monologue
STYLE = ("soft stylized 3D miniature diorama render, cozy toy-like low-poly look, warm cinematic light, "
         "shallow depth of field, first-person POV shot from the eyes of the viewer, no faces visible, "
         "people only as small distant figures seen from behind, vertical 9:16")
# 15.11.: Z-Image draws hands whenever the prompt mentions them -> only scenes
# that hold/touch something get the hand description, all others "no hands".
HANDS = ("the viewer's own two hands (light brown skin, sleeves of a white thobe) come in from the "
         "bottom edge")
HAND_WORDS = ("your hand", "your hands", "holding", "phone", "cup", "quran", "wudu", "your open hands")
# never mention hands/arms in the other scenes - even "no hands" makes the
# model draw hands (15.11.); describe a plain eye-level view instead
NO_HANDS_STYLE = STYLE.replace("first-person POV shot from the eyes of the viewer",
                               "eye-level view straight ahead as seen by a visitor, wide scenery, "
                               "clear empty foreground")


def shot_prompt(pov: dict, shot: str) -> str:
    low = shot.lower()
    if any(w in low for w in HAND_WORDS):
        return f"{STYLE}, {HANDS}. Place: {pov['place']}. Scene: {shot}. {ss.NEGATIVE_HINT}."
    shot = shot.replace("first-person view", "eye-level view").replace(", no hands visible", "")
    return f"{NO_HANDS_STYLE}. Place: {pov['place']}. Scene: {shot}. {ss.NEGATIVE_HINT}."


GAP = 0.45


def build_audio(pov: dict, out_mp3: str, work: Path):
    work.mkdir(parents=True, exist_ok=True)
    pieces, words, scenes, t = [], [], [], 0.0

    def sil(sec):
        nonlocal t
        p = str(work / f"sil_{len(pieces)}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=24000:cl=mono", "-t", f"{sec:.3f}", p], check=True)
        pieces.append(p)
        t += sec

    lines = [s["line"] for s in pov["scenes"]] + [pov["ending"]["reminder"]]
    sil(0.6)  # let the first picture + POV hook land
    for i, text in enumerate(lines):
        start = t if i else 0.0
        mp3 = str(work / f"l_{i}.mp3")
        ws = asyncio.run(ss._tts(text, mp3, *VOICE))
        wav = mp3[:-4] + ".wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "24000", "-ac", "1", wav],
                       check=True)
        d = ss._dur(wav)
        for w in ws:
            words.append({"text": w["text"], "start": w["start"] + t, "end": w["end"] + t})
        pieces.append(wav)
        t += d
        sil(GAP + (0.6 if i == len(lines) - 2 else 0))
        scenes.append({"start": start, "end": t})
    sil(1.4)
    scenes[-1]["end"] = t
    for i in range(len(scenes) - 1):
        scenes[i]["end"] = scenes[i + 1]["start"]
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    voice = str(work / "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-ar", "24000", "-ac", "1", voice], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-f", "lavfi", "-t", f"{t:.2f}",
                    "-i", "anoisesrc=color=pink:r=24000:a=0.4", "-filter_complex",
                    "[1:a]lowpass=f=900,volume=0.05[bg];[0:a]loudnorm=I=-15:TP=-1.5[v];"
                    "[v][bg]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", out_mp3], check=True)
    return words, scenes, t


def build_images(pov: dict, out_dir: Path, limit: int | None = None) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    seed0 = sum(ord(c) for c in pov["id"]) * 31
    jobs = [{"prompt": shot_prompt(pov, s["shot"]),
             "out": str(out_dir / f"img_{i:02d}.png"), "seed": seed0 + i} for i, s in enumerate(pov["scenes"])]
    spec = out_dir / "jobs.json"
    spec.write_text(json.dumps({"width": 768, "height": 1344, "steps": 9, "jobs": jobs}, indent=1))
    made = 0
    for i, j in enumerate(jobs):
        if Path(j["out"]).exists():
            continue
        if limit is not None and made >= limit:
            return []
        ss._run_one(spec, i, f"image {i}")
        made += 1
        log.info(f"image {i + 1}/{len(jobs)} done")
    return [j["out"] for j in jobs]


def render(pov: dict, audio: str, images: list[str], words, scenes, total, out_mp4: str) -> str:
    pub = ss.REMOTION_DIR / "public" / "pov"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    shutil.copy(audio, pub / "audio.mp3")
    names = []
    for i, p in enumerate(images):
        shutil.copy(p, pub / f"img_{i:02d}.png")
        names.append(f"pov/img_{i:02d}.png")
    sc = []
    for i, s in enumerate(scenes):
        src = pov["scenes"][i] if i < len(pov["scenes"]) else {}
        sc.append({"start": s["start"], "end": s["end"], "time": src.get("time", ""), "chip": src.get("chip")})
    props = {"audio": "pov/audio.mp3", "images": names, "scenes": sc, "words": words,
             "durationSeconds": total, "date": pov["date"], "place": pov["place"], "hook": pov["hook"],
             "ending": pov["ending"], "handle": "Muslim World"}
    pp = ss.REMOTION_DIR / "props_pov.json"
    pp.write_text(json.dumps(props, ensure_ascii=False))
    r = subprocess.run([str(ss.REMOTION_BIN), "render", "MuslimPOV", str(Path(out_mp4).resolve()),
                        f"--props={pp}", "--log=error", "--concurrency=3"],
                       cwd=str(ss.REMOTION_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Remotion POV render failed:\n{r.stderr[-2000:]}")
    return out_mp4


# ---------------------------------------------------------------- 3D look (19.11.)
# Built with the reanimate skill against .reanimate/pov/spec.md: every AI still
# gets a depth map (Depth Pro via mflux, bright = near) and becomes a displaced
# 3D plane the camera moves into (composition MuslimPOV3D in remotion/src/pov3d).
DEPTH_BIN = Path.home() / ".local/share/uv/tools/mflux/bin/mflux-save-depth"


def build_depths(images: list[str]) -> list[str]:
    out = []
    for i, img in enumerate(images):
        d = img[:-4] + "_depth.png"
        if not Path(d).exists():  # one process per image, like the stills
            r = subprocess.run([str(DEPTH_BIN), "--image-path", img, "--quantize", "8"],
                               cwd=str(Path(img).parent), capture_output=True, text=True)
            if r.returncode != 0 or not Path(d).exists():
                raise RuntimeError(f"depth map {i} failed: {r.stderr[-300:]}")
            log.info(f"depth {i + 1}/{len(images)} done")
        out.append(d)
    return out


def cam_for(scene: dict, i: int) -> str:
    if scene.get("cam"):
        return scene["cam"]
    low = scene["shot"].lower()
    if i == 0:
        return "settle"
    if "walking" in low or "walk " in low:
        return "walk"
    if any(w in low for w in ("looking up", "window", "out of", "view of")):
        return "tilt"
    return "pan" if i % 2 else "walk"


def render3d(pov: dict, audio: str, images: list[str], depths: list[str], words, scenes, total,
             out_mp4: str, clips: list | None = None) -> str:
    pub = ss.REMOTION_DIR / "public" / "pov3d"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    shutil.copy(audio, pub / "audio.mp3")
    n = len(images)
    shots = []
    for i, (img, dep) in enumerate(zip(images, depths)):
        shutil.copy(img, pub / f"img_{i:02d}.png")
        shutil.copy(dep, pub / f"img_{i:02d}_depth.png")
        sc = pov["scenes"][i]
        shot = {"start": scenes[i]["start"], "end": scenes[n]["start"] if i == n - 1 else scenes[i]["end"],
                "time": sc["time"], "cam": cam_for(sc, i), "chip": sc.get("chip"),
                "image": f"pov3d/img_{i:02d}.png", "depth": f"pov3d/img_{i:02d}_depth.png"}
        c = (clips or [None] * n)[i]
        if c:
            shutil.copy(c["path"], pub / f"clip_{i:02d}.mp4")
            shot["video"] = f"pov3d/clip_{i:02d}.mp4"
            shot["videoSeconds"] = c["seconds"]
        shots.append(shot)
    props = {"audio": "pov3d/audio.mp3", "shots": shots, "words": words, "durationSeconds": total,
             "date": pov["date"], "place": pov["place"], "hook": pov["hook"],
             "ending": pov["ending"], "endStart": scenes[n]["start"], "handle": "Muslim World"}
    pp = ss.REMOTION_DIR / "props_pov3d.json"
    pp.write_text(json.dumps(props, ensure_ascii=False))
    r = subprocess.run([str(ss.REMOTION_BIN), "render", "MuslimPOV3D", str(Path(out_mp4).resolve()),
                        f"--props={pp}", "--gl=angle", "--log=error", "--concurrency=2"],
                       cwd=str(ss.REMOTION_DIR), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Remotion POV3D render failed:\n{r.stderr[-2000:]}")
    return out_mp4


# ---------------------------------------------------------------- real motion (19.11.)
# User: "more movement and sounds of people, not still-image-like". Every scene
# becomes a 4-6 s clip from the local LTX-2.3 video model (q4, --low-ram, one
# process per clip, ~145 s each, >=30 % RAM free in tests): people walk, the
# camera moves, and LTX adds matching ambient sound (footsteps, voices, water).
LTX_BIN = Path.home() / ".local/share/ltx/ltx-2-mlx/.venv/bin/ltx-2-mlx"
LTX_MODEL = "dgrauet/ltx-2.3-mlx-q4"
MOVE = {"settle": "the view slowly settles as if just waking up",
        "tilt": "the camera tilts up slowly and leans forward",
        "walk": "gentle handheld camera walking forward",
        "pan": "the camera slowly turns to look around"}


def motion_prompt(pov: dict, sc: dict, i: int) -> str:
    if sc.get("motion"):
        return sc["motion"]
    shot = sc["shot"].replace("first-person view", "first-person POV")
    return (f"{shot}, in {pov['place']}. Soft stylized 3D miniature animation, warm light. "
            f"Small people move naturally in the background, seen from behind, cloth and leaves move "
            f"gently; {MOVE[cam_for(sc, i)]}. No text. Sound: realistic ambient sound of this place - "
            f"footsteps, distant voices, birds or water where visible, no music.")


def build_clips(pov: dict, images: list[str], scenes: list) -> list:
    """One LTX clip per scene, sized to the scene length (frames = 8k+1 at 24 fps)."""
    clips = []
    for i, (img, sc) in enumerate(zip(images, pov["scenes"])):
        dur = max(2.0, scenes[i]["end"] - scenes[i]["start"])
        frames = min(145, int((dur * 24 + 7) // 8) * 8 + 1)
        out = img[:-4] + "_clip.mp4"
        if not Path(out).exists():
            r = subprocess.run([str(LTX_BIN), "generate", "--distilled", "--low-ram", "-m", LTX_MODEL,
                                "--image", img, "0", "1.0", "-p", motion_prompt(pov, sc, i),
                                "-H", "832", "-W", "480", "-f", str(frames), "--frame-rate", "24",
                                "-s", str(sum(ord(c) for c in pov["id"]) + i), "-o", out],
                               capture_output=True, text=True)
            if r.returncode != 0 or not Path(out).exists():
                log.warning(f"clip {i} failed - depth fallback\n{r.stderr[-300:]}")
                clips.append(None)
                continue
            log.info(f"clip {i + 1}/{len(images)} done ({frames} frames)")
        clips.append({"path": out, "seconds": frames / 24})
    return clips


def description(pov: dict) -> str:
    e = pov["ending"]
    facts = "\n".join(f"• {s['chip']['title']} – {s['chip']['sub']}" for s in pov["scenes"] if s.get("chip"))
    tags = " ".join("#" + t.replace(" ", "") for t in pov.get("tags", [])[:4])
    return (f"{pov['hook']}\n\n{facts}\n\n“{e['reminder']}”\n📖 {e['source']}\n\n"
            f"A first-person animated day. Follow for more.\n\n#shorts #pov #islam {tags}")


def pick(pov_id: str | None):
    povs = all_povs()
    if pov_id:
        return next(p for p in povs if p["id"] == pov_id)
    done = history.all_titles()
    return next((p for p in povs if p["title"].strip().lower() not in done), None)


def run(pov_id=None, dry_run=False, privacy="public"):
    pov = pick(pov_id)
    if not pov:
        log.warning("POV bank used up - refill src/pov_bank.py")
        return None
    log.info(f"POV: {pov['title']}")
    work = ss.OUTPUT_DIR / f"pov_{pov['id']}"
    audio = str(work / "audio.mp3")
    words, scenes, total = build_audio(pov, audio, work / "lines")
    log.info(f"Audio {total:.1f}s")
    images = build_images(pov, work / "images")
    out = str(ss.OUTPUT_DIR / f"pov_{datetime.now():%Y%m%d_%H%M%S}.mp4")
    if os.environ.get("POV_STYLE", "3d") == "3d":
        depths = build_depths(images)
        clips = build_clips(pov, images, scenes) if os.environ.get("POV_MOTION", "1") == "1" else None
        render3d(pov, audio, images, depths, words, scenes, total, out, clips)
    else:
        render(pov, audio, images, words, scenes, total, out)
    log.info(f"Video: {out}")
    if dry_run:
        return out
    from upload_youtube import upload_short
    vid = upload_short(video_path=out, title=pov["title"][:100], description=description(pov),
                       tags=pov.get("tags", []) + ["pov", "islam", "muslim"], privacy=privacy)
    history.add_entry("short", pov["title"], "pov")
    log.info(f"Done! https://youtube.com/shorts/{vid}")
    ss.post_tiktok(pov, out)
    shutil.rmtree(work, ignore_errors=True)
    return vid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--privacy", default=os.environ.get("UPLOAD_PRIVACY", "public"))
    a = ap.parse_args()
    run(a.id, a.dry_run, a.privacy)
