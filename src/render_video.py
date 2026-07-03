"""Renders a vertical Short (9:16, 1080x1920) with fast cuts + animated captions.

Pipeline:
  1. Background = montage of several halal Pexels clips, hard-cut every ~1.7s
     with an alternating Ken-Burns push. Falls back to an animated gradient in
     the channel's colours if no Pexels key / no clips.
  2. Pillow renders one full-frame RGBA overlay per spoken phrase: a dark scrim,
     the type badge + title, the current caption, and a persistent source line.
  3. ffmpeg composites background + ONE timed overlay track + audio (3 inputs).

Uses only ffmpeg filters available without freetype/libass (overlay/scale/crop/
concat/zoompan) so it runs on the limited local build and Ubuntu CI alike.
"""
import subprocess
import re
import os
import math
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from fetch_background import fetch_background_clips

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
SEGMENT = 1.7          # seconds per clip before a hard cut (faster = more dynamic)
ZOOM_PER_SEG = 0.16    # Ken-Burns push per segment

# Channel palette per content type (deep greens / teal / gold / midnight)
TYPE_COLORS = {
    "quran":         ((6, 40, 32),   (13, 92, 74)),    # emerald
    "hadith":        ((8, 30, 40),   (16, 74, 92)),    # teal
    "dua":           ((20, 16, 44),  (52, 40, 104)),   # indigo night
    "akhlaq":        ((10, 40, 18),  (26, 92, 46)),    # green
    "prophet_story": ((10, 12, 40),  (20, 26, 80)),    # midnight blue
    "islamic_story": ((32, 22, 12),  (104, 68, 30)),   # warm sepia / amber
    "did_you_know":  ((30, 22, 8),   (110, 78, 20)),   # warm gold
}
DEFAULT_COLORS = ((8, 34, 28), (16, 82, 66))
GOLD = (212, 175, 55)   # accent used for badges + source line

# On-screen badge per content type
TYPE_BADGES = {
    "quran": "QUR'AN", "hadith": "HADITH", "dua": "DUA",
    "akhlaq": "CHARACTER", "prophet_story": "PROPHETS", "islamic_story": "STORY",
    "did_you_know": "DID YOU KNOW",
}

BOLD_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
]

EMOJI_PATTERN = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+",
    flags=re.UNICODE,
)


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    for path in BOLD_FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _strip_emoji(text: str) -> str:
    return EMOJI_PATTERN.sub("", text).strip()


def _probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ---------- caption grouping ----------

def _group_captions(words: list[dict], max_words: int = 3, total: float = None) -> list[dict]:
    groups, cur = [], []
    for w in words:
        cur.append(w)
        ends = w["text"] and w["text"][-1] in ".!?,;:"
        if len(cur) >= max_words or ends:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    captions = []
    for g in groups:
        text = " ".join(x["text"] for x in g).strip().rstrip(",;:")
        captions.append({"text": text, "start": g[0]["start"], "end": g[-1]["end"]})

    for i in range(len(captions)):
        if i == 0:
            captions[i]["start"] = 0.0
        if i < len(captions) - 1:
            captions[i]["end"] = captions[i + 1]["start"]
        elif total:
            captions[i]["end"] = total
    return captions


# ---------- PNG layers (Pillow) ----------

def _gradient_png(top_rgb, bottom_rgb, path):
    base = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), top_rgb)
    top = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), bottom_rgb)
    mask = Image.new("L", (VIDEO_WIDTH, VIDEO_HEIGHT))
    mask.putdata([int(255 * (y / VIDEO_HEIGHT)) for y in range(VIDEO_HEIGHT) for _ in range(VIDEO_WIDTH)])
    base.paste(top, (0, 0), mask)
    base.save(path)
    return path


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_scrim(d):
    d.rectangle([0, 0, VIDEO_WIDTH, VIDEO_HEIGHT], fill=(0, 0, 0, 100))
    d.rectangle([0, 0, VIDEO_WIDTH, 340], fill=(0, 0, 0, 80))
    d.rectangle([0, VIDEO_HEIGHT - 360, VIDEO_WIDTH, VIDEO_HEIGHT], fill=(0, 0, 0, 90))


def _draw_title(d, item):
    badge_font = _find_font(40)
    title_font = _find_font(58)
    badge = TYPE_BADGES.get(item.get("content_type", ""), "REMINDER")
    bw = d.textlength(badge, font=badge_font)
    bx = (VIDEO_WIDTH - bw) / 2
    d.rounded_rectangle([bx - 28, 120, bx + bw + 28, 188], radius=20, fill=GOLD)
    d.text((bx, 130), badge, font=badge_font, fill=(0, 0, 0))
    title = _strip_emoji(item.get("title", ""))
    y = 220
    for line in _wrap(d, title, title_font, VIDEO_WIDTH - 140):
        w = d.textlength(line, font=title_font)
        d.text(((VIDEO_WIDTH - w) / 2, y), line, font=title_font, fill=(255, 255, 255),
               stroke_width=4, stroke_fill=(0, 0, 0))
        y += 72


def _draw_source(d, source):
    """Persistent source citation at the bottom (channel policy: always cite)."""
    if not source:
        return
    f = _find_font(44)
    text = f"— {source}"
    w = d.textlength(text, font=f)
    d.text(((VIDEO_WIDTH - w) / 2, VIDEO_HEIGHT - 180), text, font=f, fill=GOLD,
           stroke_width=4, stroke_fill=(0, 0, 0))


def _overlay_frame(item, caption_text, path):
    """One full-frame RGBA overlay: scrim + badge/title + caption + source."""
    img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_scrim(d)
    _draw_title(d, item)
    if caption_text:
        font = _find_font(84)
        lines = _wrap(d, caption_text.upper(), font, VIDEO_WIDTH - 160)
        line_h = 102
        y = (VIDEO_HEIGHT - len(lines) * line_h) / 2 + 100
        for line in lines:
            w = d.textlength(line, font=font)
            d.text(((VIDEO_WIDTH - w) / 2, y), line, font=font, fill=(255, 255, 255),
                   stroke_width=9, stroke_fill=(0, 0, 0))
            y += line_h
    _draw_source(d, item.get("source", ""))
    img.save(path)
    return path


# ---------- background montage ----------

def _build_montage(clips: list[str], total: float, out_path: str) -> str:
    """Concatenates clips with hard cuts every SEGMENT seconds to fill `total`."""
    durations = {c: _probe_duration(c) for c in clips}
    clips = [c for c in clips if durations[c] >= 1.0] or clips

    n_segments = max(1, math.ceil(total / SEGMENT))
    usage = {c: 0 for c in clips}

    seg_frames = max(1, int(SEGMENT * 30))
    zin = ZOOM_PER_SEG / seg_frames

    inputs, filters, labels = [], [], []
    for i in range(n_segments):
        clip = clips[i % len(clips)]
        dur = durations.get(clip, 0) or SEGMENT
        max_start = max(0.0, dur - SEGMENT)
        start = (usage[clip] * SEGMENT) % (max_start + 0.001) if max_start > 0 else 0.0
        usage[clip] += 1

        inputs += ["-ss", f"{start:.2f}", "-t", f"{SEGMENT:.2f}", "-i", clip]
        lbl = f"v{i}"
        if i % 2 == 0:
            zexpr = f"min(zoom+{zin:.5f},{1 + ZOOM_PER_SEG:.3f})"
        else:
            zexpr = f"if(eq(on,0),{1 + ZOOM_PER_SEG:.3f},max(zoom-{zin:.5f},1.0))"
        filters.append(
            f"[{i}:v]fps=30,"
            f"scale={int(VIDEO_WIDTH*1.3)}:{int(VIDEO_HEIGHT*1.3)}:force_original_aspect_ratio=increase,"
            f"crop={int(VIDEO_WIDTH*1.3)}:{int(VIDEO_HEIGHT*1.3)},"
            f"zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps=30,"
            f"setsar=1,format=yuv420p[{lbl}]"
        )
        labels.append(f"[{lbl}]")

    concat = "".join(labels) + f"concat=n={n_segments}:v=1:a=0[bg]"
    filter_complex = ";".join(filters + [concat])

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[bg]",
        "-t", f"{total:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30", "-an",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Montage failed:\n{r.stderr[-2000:]}")
    return out_path


# ---------- compose ----------

def render_video(item: dict, audio_path: str, output_path: str,
                 words: list[dict] = None, background_video: str = None) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="short_"))

    total = (max(w["end"] for w in words) + 0.8) if words else _probe_duration(audio_path)
    if total <= 0:
        total = 50.0

    # ----- background -----
    clips = [background_video] if background_video else \
        fetch_background_clips(item.get("content_type", ""), str(work / "clips"),
                               count=6, tags=item.get("visual_tags"))

    t_arg = ["-t", f"{total:.2f}"]
    if clips:
        bg = _build_montage(clips, total, str(work / "montage.mp4"))
        bg_input = ["-i", bg]
        bg_filter = f"[0:v]setsar=1[bg]"
    else:
        top, bottom = TYPE_COLORS.get(item.get("content_type", ""), DEFAULT_COLORS)
        grad = _gradient_png(top, bottom, str(work / "grad.png"))
        bg_input = ["-loop", "1"] + t_arg + ["-i", grad]
        bg_filter = (
            f"[0:v]scale={int(VIDEO_WIDTH*1.2)}:{int(VIDEO_HEIGHT*1.2)},"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
            f"x='(in_w-{VIDEO_WIDTH})/2+sin(t/5)*60':"
            f"y='(in_h-{VIDEO_HEIGHT})/2+cos(t/6)*60',setsar=1[bg]"
        )

    # ----- overlay track (scrim + badge/title + captions + source) -----
    captions = _group_captions(words or [], total=total) if words else []
    if not captions:
        captions = [{"text": "", "start": 0.0, "end": total}]

    frames = []
    for i, c in enumerate(captions):
        p = _overlay_frame(item, c["text"], str(work / f"ov_{i}.png"))
        dur = max(0.1, c["end"] - c["start"])
        frames.append((p, dur))

    list_path = work / "frames.txt"
    lines = []
    for p, dur in frames:
        lines.append(f"file '{p}'")
        lines.append(f"duration {dur:.3f}")
    lines.append(f"file '{frames[-1][0]}'")  # required final repeat
    list_path.write_text("\n".join(lines))

    # ----- final compose: background + overlay track + audio (3 inputs) -----
    cmd = ["ffmpeg", "-y"] + bg_input
    cmd += ["-f", "concat", "-safe", "0", "-i", str(list_path)]   # 1: overlay frames
    cmd += ["-i", audio_path]                                     # 2: audio

    filter_complex = (
        bg_filter
        + ";[1:v]fps=30,format=rgba,setsar=1[ov]"
        + ";[bg][ov]overlay=eof_action=pass:format=auto[v]"
    )

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-t", f"{total:.2f}", "-shortest",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr[-2500:]}")
    return output_path


if __name__ == "__main__":
    from text_to_speech import generate_audio
    sample = {
        "content_type": "quran",
        "title": "The Verse That Calms Every Heart",
        "hook": "Allah never burdens a soul beyond its capacity.",
        "body": "In Surah Al-Baqarah, Allah reminds us that He never places on any "
                "soul a burden greater than it can bear. Whatever you are facing today, "
                "it was measured for you, and you were made able to carry it.",
        "source": "Qur'an 2:286",
        "cta": "Follow for a daily reminder.",
        "visual_tags": ["light rays sky", "calm ocean", "sunrise clouds"],
    }
    text = f"{sample['hook']} {sample['body']} {sample['cta']}"
    w = generate_audio(text, "/tmp/test_audio.mp3")
    render_video(sample, "/tmp/test_audio.mp3", "/tmp/test_video.mp4", words=w)
    print("Video: /tmp/test_video.mp4")
