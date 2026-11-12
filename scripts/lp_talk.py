"""Audio-driven talking cartoon faces with LivePortrait (local, Apple Silicon).

Replaces Wav2Lip (13.11.2026: user found the mouths out of sync / smeared on the
Pixar-style faces). Instead of painting a new mouth, LivePortrait's own lip
retargeting opens and closes the character's mouth; the opening per frame comes
from the loudness of the speaker's voice, so the timing is exact. Eyes blink
naturally every few seconds.

Runs in its own venv, model loaded once for all jobs:

    ~/.local/share/liveportrait/venv/bin/python scripts/lp_talk.py jobs.json

jobs.json = {"fps": 30, "result": "/abs/result.json",
             "jobs": [{"image": "/abs/img.png", "audio": "/abs/line.wav", "out": "/abs/talk.mp4"}]}
Same job format as scripts/lipsync.py. A job without a detectable face is
reported as False and the scene stays a still image.
"""
import os
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")  # before torch import
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import cv2
import numpy as np
import torch

LP = Path(os.path.expanduser("~/.local/share/liveportrait/LivePortrait"))
sys.path.insert(0, str(LP))
os.chdir(LP)  # config uses relative weight paths

from src.config.crop_config import CropConfig  # noqa: E402
from src.config.inference_config import InferenceConfig  # noqa: E402
from src.live_portrait_pipeline import LivePortraitPipeline  # noqa: E402
from src.utils.crop import paste_back, prepare_paste_back  # noqa: E402
from src.utils.retargeting_utils import calc_eye_close_ratio, calc_lip_close_ratio  # noqa: E402

LIP_OPEN_MAX = 0.42   # lip ratio at the loudest syllables
LIP_CLOSED = 0.0


def read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    return a / 32768.0, sr


def mouth_curve(audio: np.ndarray, sr: int, fps: int) -> np.ndarray:
    """Per-frame mouth opening 0..1 from loudness (attack fast, release a bit slower)."""
    n = max(1, int(round(len(audio) / sr * fps)))
    hop = sr / fps
    win = int(sr * 0.04)
    rms = np.zeros(n)
    for i in range(n):
        c = int((i + 0.5) * hop)
        seg = audio[max(0, c - win // 2): c + win // 2]
        rms[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0.0
    ref = np.percentile(rms[rms > 0], 92) if np.any(rms > 0) else 1.0
    env = np.clip(rms / (ref + 1e-6), 0, 1)
    env[env < 0.12] = 0.0                      # silence -> closed
    env = env ** 0.7
    out = np.zeros(n)
    for i in range(n):                          # asymmetric smoothing
        prev = out[i - 1] if i else 0.0
        k = 0.75 if env[i] > prev else 0.45
        out[i] = prev + k * (env[i] - prev)
    return np.concatenate([out[1:], out[-1:]])  # mouth leads the sound by one frame


def blink_curve(n: int, fps: int, seed: int) -> np.ndarray:
    """1 = open, dips to ~0 for ~5 frames every 2.5-5 s."""
    rng = np.random.default_rng(seed)
    e = np.ones(n)
    t = int(rng.uniform(0.8, 2.0) * fps)
    shape = np.array([0.6, 0.15, 0.0, 0.15, 0.6])
    while t < n - len(shape):
        e[t:t + len(shape)] = shape
        t += int(rng.uniform(2.5, 5.0) * fps)
    return e


class Talker:
    def __init__(self):
        inf = InferenceConfig()
        inf.flag_do_torch_compile = False
        self.inf = inf
        self.crop_cfg = CropConfig()
        self.pipe = LivePortraitPipeline(inference_cfg=inf, crop_cfg=self.crop_cfg)
        self.w = self.pipe.live_portrait_wrapper
        self.dev = self.w.device

    def run(self, job: dict, fps: int) -> bool:
        bgr = cv2.imread(job["image"])
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        crop = self.pipe.cropper.crop_source_image(rgb, self.crop_cfg)
        if crop is None:
            print(f"no face -> skip {Path(job['out']).name}", flush=True)
            return False
        lmk = crop["lmk_crop"]
        I_s = self.w.prepare_source(crop["img_crop_256x256"])
        x_info = self.w.get_kp_info(I_s)
        f_s = self.w.extract_feature_3d(I_s)
        x_s = self.w.transform_keypoint(x_info)
        mask = prepare_paste_back(self.inf.mask_crop, crop["M_c2o"], dsize=(rgb.shape[1], rgb.shape[0]))

        c_s_lip = torch.from_numpy(calc_lip_close_ratio(lmk[None])).float().to(self.dev)
        c_s_eye = torch.from_numpy(calc_eye_close_ratio(lmk[None])).float().to(self.dev)
        eye_open = float(c_s_eye.mean())

        audio, sr = read_wav(job["audio"])
        mouth = mouth_curve(audio, sr, fps)
        blink = blink_curve(len(mouth), fps, abs(hash(job["out"])) % 10_000)

        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps, (rgb.shape[1], rgb.shape[0]))
        cache = {}
        with torch.no_grad():
            for m, b in zip(mouth, blink):
                key = (round(float(m), 2), round(float(b), 2))
                if key not in cache:
                    lip_t = torch.tensor([[LIP_CLOSED + key[0] * LIP_OPEN_MAX]], device=self.dev)
                    d_lip = self.w.retarget_lip(x_s, torch.cat([c_s_lip, lip_t], dim=1))
                    eye_t = torch.tensor([[eye_open * key[1]]], device=self.dev)
                    d_eye = self.w.retarget_eye(x_s, torch.cat([c_s_eye, eye_t], dim=1))
                    x_d = self.w.stitching(x_s, x_s + d_lip + d_eye)
                    out = self.w.parse_output(self.w.warp_decode(f_s, x_s, x_d)["out"])[0]
                    frame = paste_back(out, crop["M_c2o"], rgb, mask)
                    cache[key] = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                vw.write(cache[key])
        vw.release()
        out = Path(job["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", str(out)], check=True)
        os.unlink(tmp)
        print(f"talk {out.name} {len(mouth)}f ({len(cache)} unique)", flush=True)
        return True


def main(path: str) -> None:
    spec = json.loads(Path(path).read_text())
    fps = spec.get("fps", 30)
    t = Talker()
    done = {}
    for job in spec["jobs"]:
        try:
            done[job["out"]] = t.run(job, fps)
        except Exception as e:  # one bad clip must not kill the short
            print(f"error {job['out']}: {e}", flush=True)
            done[job["out"]] = False
    Path(spec.get("result", str(Path(path).with_suffix(".result.json")))).write_text(json.dumps(done))


if __name__ == "__main__":
    main(sys.argv[1])
