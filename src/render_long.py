"""Renders a long-form 16:9 (1920x1080) Islamic educational video.

Background = looped montage of landscape halal Pexels clips (hard cuts). On top,
each section (intro / point 1-10 / outro) gets its own overlay card shown for its
time window: an intro title, a "n/10 + headline + source" banner per point, and
an outro card.

Uses only overlay/scale/crop/concat so it runs on the limited local ffmpeg and
on Ubuntu CI alike.
"""
import subprocess
import math
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from fetch_background import fetch_background_clips
from render_video import _find_font, _strip_emoji, _wrap, _probe_duration, TYPE_COLORS, DEFAULT_COLORS, GOLD

LW, LH = 1920, 1080
SEG = 3.0           # seconds per clip before a cut
BASE_TARGET = 78.0  # length of the base montage before it loops
ZOOM_PER_SEG = 0.14

# Long videos use a fixed calm emerald palette
LONG_TOP, LONG_BOTTOM = (6, 40, 32), (13, 92, 74)


def _gradient(top, bottom, path):
    base = Image.new("RGB", (LW, LH), top)
    layer = Image.new("RGB", (LW, LH), bottom)
    mask = Image.new("L", (LW, LH))
    mask.putdata([int(255 * (y / LH)) for y in range(LH) for _ in range(LW)])
    base.paste(layer, (0, 0), mask)
    base.save(path)
    return path


def _new_scrim_img():
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, LW, LH], fill=(0, 0, 0, 90))
    d.rectangle([0, 0, LW, 250], fill=(0, 0, 0, 90))          # top band for banner
    d.rectangle([0, LH - 160, LW, LH], fill=(0, 0, 0, 80))    # bottom band for source
    return img, d


def _intro_card(comp, path):
    img, d = _new_scrim_img()
    badge_f = _find_font(54)
    title_f = _find_font(104)

    badge = f"{len(comp['facts'])} REMINDERS"
    bw = d.textlength(badge, font=badge_f)
    d.rounded_rectangle([(LW - bw) / 2 - 34, 300, (LW + bw) / 2 + 34, 384],
                        radius=22, fill=GOLD)
    d.text(((LW - bw) / 2, 312), badge, font=badge_f, fill=(11, 20, 55))

    lines = _wrap(d, _strip_emoji(comp["title"]), title_f, LW - 320)
    y = 440
    for line in lines:
        w = d.textlength(line, font=title_f)
        d.text(((LW - w) / 2, y), line, font=title_f, fill=(255, 255, 255),
               stroke_width=6, stroke_fill=(0, 0, 0))
        y += 120
    img.save(path)
    return path


def _fact_card(idx, total, headline, source, path):
    img, d = _new_scrim_img()
    num_f = _find_font(60)
    head_f = _find_font(76)
    src_f = _find_font(46)

    # big watermark number
    big_f = _find_font(420)
    d.text((70, LH - 470), str(idx), font=big_f, fill=(255, 255, 255, 26))

    # top banner: "idx/total"
    pill = f"{idx}/{total}"
    pw = d.textlength(pill, font=num_f)
    d.rounded_rectangle([80, 70, 80 + pw + 52, 156], radius=20, fill=GOLD)
    d.text((106, 82), pill, font=num_f, fill=(11, 20, 55))

    head = _strip_emoji(headline)
    lines = _wrap(d, head, head_f, LW - 200)
    y = 176
    for line in lines[:2]:
        d.text((84, y), line, font=head_f, fill=(255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0))
        y += 90

    # source at bottom (channel policy: always cite)
    if source:
        text = f"— {source}"
        w = d.textlength(text, font=src_f)
        d.text(((LW - w) / 2, LH - 118), text, font=src_f, fill=GOLD,
               stroke_width=4, stroke_fill=(0, 0, 0))
    img.save(path)
    return path


def _outro_card(comp, path):
    img, d = _new_scrim_img()
    q_f = _find_font(80)
    sub_f = _find_font(56)

    q = "Which reminder touched your heart the most?"
    lines = _wrap(d, q, q_f, LW - 360)
    y = 360
    for line in lines:
        w = d.textlength(line, font=q_f)
        d.text(((LW - w) / 2, y), line, font=q_f, fill=(255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0))
        y += 94

    cta = "SUBSCRIBE FOR A DAILY REMINDER"
    cw = d.textlength(cta, font=sub_f)
    d.rounded_rectangle([(LW - cw) / 2 - 40, y + 40, (LW + cw) / 2 + 40, y + 128],
                        radius=24, fill=GOLD)
    d.text(((LW - cw) / 2, y + 56), cta, font=sub_f, fill=(11, 20, 55))
    img.save(path)
    return path


def make_thumbnail(comp: dict, path: str) -> str:
    """Generates a 1280x720 YouTube thumbnail."""
    TW, TH = 1280, 720
    img = Image.new("RGB", (TW, TH), LONG_TOP)
    layer = Image.new("RGB", (TW, TH), LONG_BOTTOM)
    mask = Image.new("L", (TW, TH))
    mask.putdata([int(255 * (y / TH)) for y in range(TH) for _ in range(TW)])
    img.paste(layer, (0, 0), mask)
    d = ImageDraw.Draw(img)

    n = len(comp["facts"])
    big = _find_font(380)
    num = str(n)
    nw = d.textlength(num, font=big)
    nx = TW - nw - 60
    ny = (TH - 380) / 2 + 20
    d.text((nx, ny), num, font=big, fill=GOLD, stroke_width=12, stroke_fill=(0, 0, 0))

    brand_f = _find_font(46)
    brand = "MUSLIM WORLD"
    bw = d.textlength(brand, font=brand_f)
    d.rounded_rectangle([60, 70, 60 + bw + 48, 150], radius=18, fill=GOLD)
    d.text((84, 84), brand, font=brand_f, fill=(11, 20, 55))

    title_f = _find_font(86)
    lines = _wrap(d, _strip_emoji(comp["title"]), title_f, 700)
    y = 210
    for line in lines[:4]:
        d.text((64, y), line, font=title_f, fill=(255, 255, 255),
               stroke_width=6, stroke_fill=(0, 0, 0))
        y += 102
    img.save(path)
    return path


def _build_montage(clips, out_path):
    """Builds a varied base montage (~BASE_TARGET s) with fast cuts + zoom-push."""
    durations = {c: _probe_duration(c) for c in clips}
    clips = [c for c in clips if durations[c] >= 1.0] or clips

    n_segments = max(len(clips), math.ceil(BASE_TARGET / SEG))
    seg_frames = max(1, int(SEG * 30))
    zin = ZOOM_PER_SEG / seg_frames
    usage = {c: 0 for c in clips}

    inputs, filters, labels = [], [], []
    for i in range(n_segments):
        clip = clips[i % len(clips)]
        dur = durations.get(clip, 0) or SEG
        max_start = max(0.0, dur - SEG)
        start = (usage[clip] * SEG) % (max_start + 0.001) if max_start > 0 else 0.0
        usage[clip] += 1

        inputs += ["-ss", f"{start:.2f}", "-t", f"{SEG:.2f}", "-i", clip]
        if i % 2 == 0:
            zexpr = f"min(zoom+{zin:.5f},{1 + ZOOM_PER_SEG:.3f})"
        else:
            zexpr = f"if(eq(on,0),{1 + ZOOM_PER_SEG:.3f},max(zoom-{zin:.5f},1.0))"
        filters.append(
            f"[{i}:v]fps=30,"
            f"scale={int(LW*1.25)}:{int(LH*1.25)}:force_original_aspect_ratio=increase,"
            f"crop={int(LW*1.25)}:{int(LH*1.25)},"
            f"zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={LW}x{LH}:fps=30,setsar=1,format=yuv420p[v{i}]")
        labels.append(f"[v{i}]")

    concat = "".join(labels) + f"concat=n={n_segments}:v=1:a=0[bg]"
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", ";".join(filters + [concat]), "-map", "[bg]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30", "-an", "-threads", "0", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Montage failed:\n{r.stderr[-2000:]}")
    return out_path


def _img_segment(img, dur, out, zoom_in=True):
    frames = max(1, int(dur * 30))
    inc = 0.12 / frames
    z = (f"min(zoom+{inc:.6f},1.12)" if zoom_in
         else f"if(eq(on,0),1.12,max(zoom-{inc:.6f},1.0))")
    vf = (f"scale={int(LW*1.25)}:{int(LH*1.25)}:force_original_aspect_ratio=increase,"
          f"crop={int(LW*1.25)}:{int(LH*1.25)},"
          f"zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={LW}x{LH}:fps=30,setsar=1,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}",
                    "-i", img, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30", "-t", f"{dur:.2f}", out],
                   capture_output=True, text=True, check=True)


def _build_sectioned_bg(visuals, sections, work, out_path):
    parts, last_img = [], None
    for idx, s in enumerate(sections):
        dur = max(0.5, s["end"] - s["start"])
        img = visuals.get(s["label"]) or last_img
        seg = str(work / f"bg_{idx}.mp4")
        if img is None:
            img = _gradient(LONG_TOP, LONG_BOTTOM, str(work / "bgfallback.png"))
        _img_segment(img, dur, seg, zoom_in=(idx % 2 == 0))
        if visuals.get(s["label"]):
            last_img = visuals[s["label"]]
        parts.append(seg)
    lst = work / "bgsegs.txt"
    lst.write_text("\n".join(f"file '{p}'" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", out_path], capture_output=True, text=True, check=True)
    return out_path


def render_long(comp: dict, audio_path: str, sections: list[dict], output_path: str,
                visuals: dict = None) -> str:
    """sections: [{label, start, end}] from build_narration (intro/point_i/outro)."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="long_"))
    total = max(s["end"] for s in sections) + 0.5

    # ---- background: AI images per section (preferred) -> Pexels -> gradient ----
    ai_bg = None
    if visuals:
        try:
            ai_bg = _build_sectioned_bg(visuals, sections, work, str(work / "aibg.mp4"))
        except Exception as e:
            print(f"AI background failed ({e}) — using Pexels.")

    clips = [] if ai_bg else fetch_background_clips(
        comp.get("category", ""), str(work / "clips"), count=14,
        tags=comp.get("visual_tags"), orientation="landscape")
    if ai_bg:
        bg_input = ["-i", ai_bg]
        bg_filter = f"[0:v]scale={LW}:{LH},setsar=1[bg]"
    elif clips:
        base = _build_montage(clips, str(work / "base.mp4"))
        bg_input = ["-stream_loop", "-1", "-i", base]
        bg_filter = f"[0:v]scale={LW}:{LH},setsar=1[bg]"
    else:
        grad = _gradient(LONG_TOP, LONG_BOTTOM, str(work / "grad.png"))
        bg_input = ["-loop", "1", "-t", f"{total:.2f}", "-i", grad]
        bg_filter = (f"[0:v]scale={int(LW*1.15)}:{int(LH*1.15)},"
                     f"crop={LW}:{LH}:x='(in_w-{LW})/2+sin(t/6)*50':"
                     f"y='(in_h-{LH})/2+cos(t/7)*40',setsar=1[bg]")

    # ---- one card per section ----
    total_points = len(comp["facts"])
    cards, point_i = [], 0
    for i, s in enumerate(sections):
        p = str(work / f"card_{i}.png")
        if s["label"] == "intro":
            _intro_card(comp, p)
        elif s["label"] == "outro":
            _outro_card(comp, p)
        else:
            point_i += 1
            f = comp["facts"][point_i - 1]
            _fact_card(point_i, total_points, f["headline"], f.get("source", ""), p)
        cards.append({"path": p, "dur": max(0.1, s["end"] - s["start"])})

    list_path = work / "cards.txt"
    lines = []
    for c in cards:
        lines.append(f"file '{c['path']}'")
        lines.append(f"duration {c['dur']:.3f}")
    lines.append(f"file '{cards[-1]['path']}'")
    list_path.write_text("\n".join(lines))

    # ---- compose: background + ONE overlay track + audio (3 inputs) ----
    cmd = ["ffmpeg", "-y"] + bg_input
    cmd += ["-f", "concat", "-safe", "0", "-i", str(list_path)]
    cmd += ["-i", audio_path]

    filter_complex = (
        bg_filter
        + ";[1:v]fps=30,format=rgba,setsar=1[ov]"
        + ";[bg][ov]overlay=eof_action=pass:format=auto[v]"
    )
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-r", "30",
        "-threads", "0", "-t", f"{total:.2f}", "-shortest", output_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr[-2500:]}")
    return output_path
