"""Local lip-sync for the story Shorts (Wav2Lip-GAN, Apple Silicon / MPS).

Runs inside its own venv (~/.local/share/wav2lip/venv), model loaded once:

    ~/.local/share/wav2lip/venv/bin/python scripts/lipsync.py jobs.json

jobs.json = {"fps": 30, "jobs": [{"image": "/abs/img_01.png", "audio": "/abs/line_01.wav",
                                  "out": "/abs/talk_01.mp4"}, ...]}
Each job: still image + one spoken line -> silent mp4 whose mouth moves with the
audio (audio is muxed later by Remotion). Only the lower face is replaced, with a
feathered mask, so the rest of the picture stays sharp. If no face is found the
job is reported as skipped and the scene falls back to the plain still image.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import torch

W2L = Path(os.path.expanduser("~/.local/share/wav2lip"))
sys.path.insert(0, str(W2L / "Wav2Lip"))
import audio as w2l_audio  # noqa: E402
from face_detection.detection.sfd.sfd_detector import SFDDetector  # noqa: E402
from models import Wav2Lip  # noqa: E402

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
IMG = 96
MEL_STEP = 16


def load_model() -> torch.nn.Module:
    ckpt = torch.load(W2L / "ckpt" / "wav2lip_gan.pth", map_location="cpu", weights_only=True)
    state = {k.replace("module.", ""): v for k, v in ckpt["state_dict"].items()}
    m = Wav2Lip()
    m.load_state_dict(state)
    return m.to(DEVICE).eval()


def find_face(det: SFDDetector, img: np.ndarray, speaker_hint: str | None):
    """Largest confident face (the speaker is framed as the main face)."""
    # detect on a downscaled copy for speed, map back
    # stylised 3D faces score lower than real ones (0.5-0.75), so accept >= 0.5;
    # second pass at full size when the small pass finds nothing
    boxes, s = [], 1.0
    for target in (640, 1344):
        s = min(1.0, target / max(img.shape[:2]))
        small = cv2.resize(img, None, fx=s, fy=s) if s < 1 else img
        boxes = [b for b in det.detect_from_image(small[..., ::-1].copy()) if b[-1] >= 0.5]
        if boxes:
            break
    if not boxes:
        return None
    x1, y1, x2, y2, _ = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    x1, y1, x2, y2 = [int(v / s) for v in (x1, y1, x2, y2)]
    w = x2 - x1
    if w < img.shape[1] * 0.12:  # face too small to read lips -> keep still
        return None
    pad = int(0.06 * (y2 - y1))
    return max(0, x1), max(0, y1), min(img.shape[1], x2), min(img.shape[0], y2 + pad)


def mouth_mask(h: int, w: int) -> np.ndarray:
    """Feathered ellipse over the lower half of the face box."""
    m = np.zeros((h, w), np.float32)
    cv2.ellipse(m, (w // 2, int(h * 0.74)), (int(w * 0.36), int(h * 0.27)), 0, 0, 360, 1.0, -1)
    k = max(3, (min(h, w) // 6) | 1)
    return cv2.GaussianBlur(m, (k, k), 0)[..., None]


def run_job(model, det, job: dict, fps: int) -> bool:
    img = cv2.imread(job["image"])
    box = find_face(det, img, job.get("speaker"))
    if box is None:
        print(f"no face -> skip {Path(job['out']).name}", flush=True)
        return False
    x1, y1, x2, y2 = box
    face = img[y1:y2, x1:x2]
    fh, fw = face.shape[:2]

    wav = w2l_audio.load_wav(job["audio"], 16000)
    mel = w2l_audio.melspectrogram(wav)
    n_frames = max(1, int(round(len(wav) / 16000 * fps)))
    mult = 80.0 / fps
    chunks = []
    for i in range(n_frames):
        st = int(i * mult)
        chunks.append(mel[:, st:st + MEL_STEP] if st + MEL_STEP <= mel.shape[1]
                      else mel[:, -MEL_STEP:])

    f96 = cv2.resize(face, (IMG, IMG))
    masked = f96.copy()
    masked[IMG // 2:] = 0
    base = np.concatenate([masked, f96], axis=2) / 255.0
    mask = mouth_mask(fh, fw)

    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    h, w = img.shape[:2]
    vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    bs = 64
    with torch.no_grad():
        for i in range(0, n_frames, bs):
            mb = np.asarray(chunks[i:i + bs])[:, None]  # B,1,80,16
            ib = np.repeat(base[None], len(mb), 0).transpose(0, 3, 1, 2)
            pred = model(torch.FloatTensor(mb).to(DEVICE), torch.FloatTensor(ib).to(DEVICE))
            pred = (pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.0)
            for p in pred:
                p = cv2.resize(p.astype(np.uint8), (fw, fh), interpolation=cv2.INTER_CUBIC)
                # gentle unsharp to hide the 96px upscale
                p = cv2.addWeighted(p, 1.5, cv2.GaussianBlur(p, (0, 0), 2), -0.5, 0)
                frame = img.copy()
                frame[y1:y2, x1:x2] = (p * mask + face * (1 - mask)).astype(np.uint8)
                vw.write(frame)
    vw.release()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast", str(out)], check=True)
    os.unlink(tmp)
    print(f"talk {out.name} {n_frames}f face={fw}px", flush=True)
    return True


def main(path: str) -> None:
    spec = json.loads(Path(path).read_text())
    fps = spec.get("fps", 30)
    model = load_model()
    det = SFDDetector(device="cpu")
    done = {}
    for job in spec["jobs"]:
        if Path(job["out"]).exists():
            done[job["out"]] = True
            continue
        try:
            done[job["out"]] = run_job(model, det, job, fps)
        except Exception as e:  # one bad clip must not kill the short
            print(f"error {job['out']}: {e}", flush=True)
            done[job["out"]] = False
    Path(spec.get("result", Path(path).with_suffix(".result.json"))).write_text(json.dumps(done))


if __name__ == "__main__":
    main(sys.argv[1])
