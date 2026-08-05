"""AI video via fal.ai — animate a still (halal) image into a short clip with
real, gentle motion (image-to-video), instead of the fake Ken-Burns zoom.

Cheapest-but-good default: LTX Video image-to-video (~$0.02 per 5s clip). Swap
via AI_VIDEO_MODEL for WAN / Kling etc. (better but pricier). Degrades
gracefully: if FAL_KEY is missing or a call fails, the caller keeps the still +
Ken-Burns, so the bot never breaks.

Env:
  FAL_KEY          – fal.ai API key
  AI_VIDEO_MODEL   – default fal-ai/ltx-video/image-to-video
"""
import os
import urllib.request
import requests

FAL_RUN = "https://fal.run"
I2V_MODEL = os.environ.get("AI_VIDEO_MODEL", "fal-ai/ltx-video/image-to-video")

# Calm, reverent motion — subtle drift only (no people, no fast action)
DEFAULT_MOTION = ("gentle slow cinematic camera push-in, subtle drifting clouds "
                  "and soft moving light, calm and peaceful, no people")


def _download(url: str, path: str) -> str:
    with urllib.request.urlopen(url, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())
    return path


def _video_url(data: dict) -> str:
    """Pulls the clip URL out of fal's response (shape varies by model)."""
    if isinstance(data.get("video"), dict) and data["video"].get("url"):
        return data["video"]["url"]
    if data.get("videos"):
        return data["videos"][0]["url"]
    if isinstance(data.get("video"), str):
        return data["video"]
    raise RuntimeError(f"no video url in response: {str(data)[:300]}")


def animate_image_url(image_url: str, out_path: str, motion: str = DEFAULT_MOTION,
                      model: str = I2V_MODEL) -> str:
    """Animates a (publicly reachable) image URL into a short clip. Returns local path."""
    key = os.environ["FAL_KEY"]
    body = {"image_url": image_url, "prompt": motion}
    r = requests.post(f"{FAL_RUN}/{model}", headers={
        "Authorization": f"Key {key}", "Content-Type": "application/json",
    }, json=body, timeout=600)
    if r.status_code != 200:
        raise RuntimeError(f"fal {model} {r.status_code}: {r.text[:300]}")
    return _download(_video_url(r.json()), out_path)


if __name__ == "__main__":
    # End-to-end test: halal hero image -> LTX video clip. Prints timing.
    import time
    from generate_visuals import FAL_RUN as _R, FACT_MODEL  # reuse config

    key = os.environ["FAL_KEY"]
    prompt = ("serene grand mosque courtyard at dawn, soft golden light rays through "
              "mist, calm sky, reverent, cinematic, highly detailed, no people")
    print("1/2 generating hero image (flux/dev)...")
    t0 = time.time()
    ir = requests.post(f"{FAL_RUN}/{FACT_MODEL}", headers={
        "Authorization": f"Key {key}", "Content-Type": "application/json"},
        json={"prompt": prompt, "image_size": "portrait_16_9", "num_images": 1,
              "enable_safety_checker": True}, timeout=180)
    ir.raise_for_status()
    img_url = ir.json()["images"][0]["url"]
    print(f"   image ok ({time.time()-t0:.0f}s): {img_url[:70]}...")

    print("2/2 animating with LTX (image-to-video)...")
    t1 = time.time()
    out = animate_image_url(img_url, "/tmp/ai_video_test.mp4")
    print(f"   video ok ({time.time()-t1:.0f}s): {out}")
