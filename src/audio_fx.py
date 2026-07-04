"""Adds a calm, halal ambience bed under the narration.

The bed is SYNTHESISED by ffmpeg (filtered brown noise) — no audio files, no
licensing, and no musical instruments (channel policy). It just adds a soft
'hush' of wind/air under the voice so the video feels produced, not dry.
"""
import subprocess
from pathlib import Path


def _probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# Filter shaping per ambience kind (all just shaped brown noise)
AMBIENCE = {
    "wind":  "lowpass=f=850,highpass=f=90",     # soft airy hush
    "night": "lowpass=f=500",                   # deep, calm
    "rain":  "highpass=f=400,lowpass=f=6000",   # gentle rain-like
}


def add_ambience(voice_path: str, out_path: str, kind: str = "wind",
                 volume: float = 0.09) -> str:
    """Mixes a quiet synthesised ambience bed under the voice track.

    Returns out_path. Falls back to copying the voice if ffmpeg fails, so the
    pipeline never breaks because of the ambience step.
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    dur = _probe_duration(voice_path)
    if dur <= 0:
        dur = 50.0
    shape = AMBIENCE.get(kind, AMBIENCE["wind"])
    fade = min(1.5, dur / 4)

    bed = (f"[1:a]{shape},volume={volume},"
           f"afade=t=in:d={fade:.2f},afade=t=out:st={max(0.0, dur - fade):.2f}:d={fade:.2f}[bed]")
    mix = "[0:a][bed]amix=inputs=2:duration=first:normalize=0[a]"

    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anoisesrc=color=brown:amplitude=0.4",
        "-filter_complex", f"{bed};{mix}",
        "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Ambience mix failed, using dry voice: {r.stderr[-400:]}")
        import shutil
        shutil.copy(voice_path, out_path)
    return out_path


if __name__ == "__main__":
    from text_to_speech import generate_audio
    generate_audio("Peace be upon you. This is a calm reminder.", "/tmp/v.mp3")
    add_ambience("/tmp/v.mp3", "/tmp/v_amb.mp3", kind="wind")
    print("Wrote /tmp/v_amb.mp3")
