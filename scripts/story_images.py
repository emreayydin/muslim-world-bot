"""Batch image generator for the story Shorts, run LOCALLY on Apple Silicon.

Runs inside the mflux tool environment (uv tool install mflux), NOT the bot's
venv, so the model is loaded exactly once per story:

    ~/.local/share/uv/tools/mflux/bin/python scripts/story_images.py jobs.json [index]
    (with index: only that one image - the pipeline renders one image per process)

jobs.json = {"width": 768, "height": 1344, "steps": 9,
             "jobs": [{"prompt": "...", "out": "/abs/img_00.png", "seed": 123}, ...]}
Free: Z-Image-Turbo (Apache-2.0) via MLX, no API, no key.
"""
import json
import sys
import time
from pathlib import Path

from mflux.models.common.config.model_config import ModelConfig
from mflux.models.z_image.variants.z_image import ZImage


def main(path: str, only: int | None = None) -> None:
    spec = json.loads(Path(path).read_text())
    if only is not None:  # one image per process: lighter on the Mac (06.11.)
        spec["jobs"] = [spec["jobs"][only]]
        if Path(spec["jobs"][0]["out"]).exists():
            return
    w, h, steps = spec.get("width", 768), spec.get("height", 1344), spec.get("steps", 9)
    t0 = time.time()
    # Pre-quantised 8-bit MLX weights (11 GB) - downloaded once into the HF cache.
    model = ZImage(model_path=spec.get("model_path", "mflux-community/z-image-turbo-mflux-q8"),
                   model_config=ModelConfig.z_image_turbo())
    print(f"model loaded in {time.time() - t0:.0f}s", flush=True)
    for i, job in enumerate(spec["jobs"]):
        out = Path(job["out"])
        if out.exists():
            continue
        t = time.time()
        img = model.generate_image(seed=int(job["seed"]), prompt=job["prompt"],
                                   num_inference_steps=steps, width=w, height=h)
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(path=str(out))
        print(f"[{i + 1}/{len(spec['jobs'])}] {out.name} {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
