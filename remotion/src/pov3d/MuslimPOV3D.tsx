import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing";
import { DepthScene } from "./DepthScene";

// Real-time 3D POV format (17.11.2026), built with the reanimate skill against
// .reanimate/pov/spec.md: moving first-person camera, eyelid-blink shot changes,
// clock that counts up during a blink, chips that only fade, captions that
// accumulate word by word.

export type Pov3dShot = { start: number; end: number; time: string; cam: string; image: string; depth: string;
  chip?: { title: string; sub: string } | null; video?: string; videoSeconds?: number };
export type Pov3dProps = {
  audio: string;
  shots: Pov3dShot[];
  words: { text: string; start: number; end: number }[];
  durationSeconds: number;
  date: string; place: string; hook: string;
  ending?: { arabic: string; word: string; reminder: string; source: string } | null;
  endStart?: number;
  handle?: string;
};

const ORANGE = "#f2a03d";
const SERIF = "'Iowan Old Style', 'Palatino', Georgia, serif";
const SANS = "'SF Pro Display', 'Helvetica Neue', Arial, sans-serif";
const io = Easing.inOut(Easing.cubic);
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const cl = (t: number, a: number, b: number) => interpolate(t, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

// camera moves inside the depth plane (u = s since shot start, d = shot length).
// Values per spec rows 4, 6, 10: settle/push-in, tilt, walking dolly with step bob.
type Cam = { pos: [number, number, number]; look: [number, number, number]; roll?: number; fov?: number };
const CAMS: Record<string, (u: number, d: number) => Cam> = {
  // waking up: slight drift down + roll settling (ref #6-#26)
  settle: (u, d) => {
    const k = Easing.out(Easing.cubic)(cl(u, 0, Math.min(2.4, d)));
    return { pos: [lerp(0.03, 0, k), lerp(0.1, -0.02, k), lerp(2.15, 1.85, k)], look: [0, lerp(0.05, -0.08, k), -1], roll: lerp(0.12, 0.02, k) };
  },
  // look up and lean in (ref #30-#44): tilt from low to level, then push
  tilt: (u, d) => {
    const a = io(cl(u, 0, 1.2)), b = io(cl(u, 0.8, d));
    return { pos: [0, lerp(-0.25, 0, a), lerp(2.1, 1.6, b)], look: [0, lerp(-0.6, 0.02, a), -1], roll: lerp(0.04, 0, a) };
  },
  // walking forward (ref #120-#135): constant dolly + 1.9 Hz bob + sway
  walk: (u) => {
    const bob = Math.sin(u * Math.PI * 2 * 1.9) * 0.012, sway = Math.sin(u * Math.PI * 1.9) * 0.014;
    return { pos: [sway, bob - 0.02, 2.1 - u * 0.11], look: [sway * 2, bob * 1.5 - 0.02, -1], roll: sway * 0.6 };
  },
  // slow look around (pan) for wide views
  pan: (u, d) => {
    const k = io(cl(u, 0, d));
    return { pos: [lerp(-0.12, 0.12, k), 0, 1.95 - k * 0.12], look: [lerp(-0.05, 0.05, k), 0, -1], roll: 0 };
  },
};

const Camera: React.FC<{ cam: Cam }> = ({ cam }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  camera.position.set(...cam.pos);
  camera.up.set(Math.sin(cam.roll ?? 0), Math.cos(cam.roll ?? 0), 0);
  camera.lookAt(...cam.look);
  camera.fov = cam.fov ?? 50; camera.near = 0.01; camera.far = 20;
  camera.updateProjectionMatrix();
  return null;
};

const toMin = (s: string) => { const [h, m] = s.split(":").map(Number); return h * 60 + m; };
const fmt = (m: number) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(Math.round(m) % 60).padStart(2, "0")}`;

export const MuslimPOV3D: React.FC<Pov3dProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const i = Math.max(0, p.shots.findIndex((s, k) => t >= s.start && t < (p.shots[k + 1]?.start ?? 1e9)));
  const s = p.shots[i];
  const u = t - s.start, d = s.end - s.start;
  const cam = (CAMS[s.cam] ?? CAMS.walk)(u, d);

  // eyelids (spec rows 1 + 5): double blink at the start, close/open 200 ms each around every shot change
  let open = 1;
  if (t < 0.6) open = interpolate(t, [0, 0.15, 0.3, 0.42, 0.6], [0, 0.5, 0.22, 0.3, 1], { easing: io });
  for (const sh of p.shots.slice(1)) {
    if (Math.abs(t - sh.start) < 0.22) open = Math.min(open, io(Math.abs(t - sh.start) / 0.22));
  }
  const lidY = open * 62;  // ellipse half-height in % of the frame

  // clock (rows 3 + 11): counts up from the previous shot's time across the blink
  const prev = p.shots[i - 1];
  const mins = prev ? lerp(toMin(prev.time), toMin(s.time), cl(u, -0.1, 0.5)) : toMin(s.time);
  const clockOp = cl(t, 0.5, 0.8);
  const chipOp = s.chip ? cl(u, 0.9, 1.2) * (1 - cl(u, d - 0.4, d - 0.1)) : 0;

  const ws = p.words.filter((w) => w.start >= s.start - 0.05 && w.start < s.end && w.start <= t + 0.04);
  const hookOp = 1 - cl(t, 3.0, 3.3);

  return (
    <AbsoluteFill style={{ backgroundColor: "#07070c" }}>
      {/* 19.11.: scenes with an LTX clip play the clip (real motion + ambient sound);
          the clip is stretched to the shot length, its sound sits under the voice */}
      {p.shots.map((sh, k) => sh.video ? (
        <Sequence key={k} from={Math.round(sh.start * fps)} durationInFrames={Math.max(1, Math.round((sh.end - sh.start + 0.05) * fps))}>
          <OffthreadVideo src={staticFile(sh.video)} volume={0.45}
            playbackRate={Math.min(1, Math.max(0.6, (sh.videoSeconds ?? 4) / Math.max(0.5, sh.end - sh.start)))}
            style={{ width: "100%", height: "100%", objectFit: "cover", transform: "scale(1.02)" }} />
        </Sequence>
      ) : null)}
      {!s.video ? (
      <ThreeCanvas width={width} height={height} linear={false}>
        <Camera cam={cam} />
        <DepthScene key={i} image={s.image} depth={s.depth} />
        <EffectComposer multisampling={0}>
          <Bloom intensity={0.55} luminanceThreshold={0.86} luminanceSmoothing={0.2} mipmapBlur />
          <Vignette offset={0.25} darkness={0.55} />
        </EffectComposer>
      </ThreeCanvas>
      ) : null}
      {/* soft depth: vignette + slight bottom haze */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(10,8,20,0.5) 100%)" }} />
      {/* eyelids */}
      <AbsoluteFill style={{ backgroundColor: "#05050a",
        WebkitMaskImage: `radial-gradient(ellipse 85% ${lidY}% at 50% 47%, transparent 62%, #000 100%)`,
        maskImage: `radial-gradient(ellipse 85% ${lidY}% at 50% 47%, transparent 62%, #000 100%)`,
        opacity: open >= 0.999 ? 0 : 1 }} />
      {/* clock */}
      <div style={{ position: "absolute", left: 70, top: 150, opacity: clockOp }}>
        <div style={{ display: "flex", alignItems: "stretch" }}>
          <div style={{ width: 6, background: ORANGE, borderRadius: 3, marginRight: 22 }} />
          <div>
            <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 104, color: "#fff", lineHeight: 1, letterSpacing: -2,
              textShadow: "0 4px 24px rgba(0,0,0,0.45)" }}>{fmt(mins)}</div>
            <div style={{ fontFamily: SANS, fontSize: 30, color: "rgba(255,255,255,0.85)", marginTop: 8,
              textShadow: "0 2px 10px rgba(0,0,0,0.6)" }}>{p.date} · {p.place}</div>
          </div>
        </div>
        {s.chip ? (
          <div style={{ marginTop: 34, display: "inline-block", background: "rgba(30,30,34,0.72)", borderRadius: 18,
            padding: "18px 26px", opacity: chipOp, maxWidth: 760 }}>
            <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 36, color: "#fff" }}>
              <span style={{ color: ORANGE, marginRight: 10 }}>•</span>{s.chip.title}</div>
            <div style={{ fontFamily: SANS, fontSize: 27, color: "rgba(255,255,255,0.75)", marginTop: 6 }}>{s.chip.sub}</div>
          </div>
        ) : null}
      </div>
      {/* hook */}
      <div style={{ position: "absolute", top: 520, width: "100%", textAlign: "center", opacity: hookOp, fontFamily: SANS,
        fontWeight: 700, fontSize: 64, color: "#fff", textShadow: "0 4px 24px rgba(0,0,0,0.6)" }}>
        <span style={{ color: ORANGE }}>POV:</span>{p.hook.replace(/^POV:/, "")}
      </div>
      {/* caption: accumulates, no pop */}
      {ws.length ? (
        <div style={{ position: "absolute", left: 90, right: 90, top: 1250, textAlign: "center", fontFamily: SERIF, fontSize: 64,
          lineHeight: 1.25, color: "#fff", textShadow: "0 2px 6px rgba(0,0,0,0.85), 0 0 26px rgba(0,0,0,0.55)" }}>
          {ws.map((w) => w.text).join(" ")}
        </div>
      ) : null}
      {p.ending && p.endStart ? <Ending e={p.ending} start={p.endStart} image={p.shots[p.shots.length - 1].image} /> : null}
      {p.handle ? (
        <div style={{ position: "absolute", bottom: 70, width: "100%", textAlign: "center", fontFamily: SANS,
          fontWeight: 600, fontSize: 28, color: "rgba(255,255,255,0.5)" }}>{p.handle}</div>
      ) : null}
      <Audio src={staticFile(p.audio)} />
    </AbsoluteFill>
  );
};

// closing card: eyes close on the last shot, then the reminder over the blurred last image
const Ending: React.FC<{ e: NonNullable<Pov3dProps["ending"]>; start: number; image: string }> = ({ e, start, image }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < start - 0.25) return null;
  const k = cl(t, start - 0.25, start + 0.5);
  const op = (d: number) => cl(t, start + d, start + d + 0.7);
  return (
    <AbsoluteFill style={{ opacity: k, backgroundColor: "#05050a" }}>
      <Img src={staticFile(image)} style={{ width: "100%", height: "100%", objectFit: "cover",
        filter: "blur(18px) brightness(0.4)", transform: "scale(1.15)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 90, textAlign: "center" }}>
        <div style={{ fontFamily: "Amiri, 'Geeza Pro', serif", fontSize: 140, color: ORANGE, direction: "rtl", opacity: op(0.2) }}>{e.arabic}</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 40, color: "#fff", letterSpacing: 4,
          textTransform: "uppercase", marginTop: 16, opacity: op(0.5) }}>{e.word}</div>
        <div style={{ fontFamily: SERIF, fontSize: 56, lineHeight: 1.35, color: "#fff", marginTop: 50, opacity: op(0.9) }}>“{e.reminder}”</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 38, color: ORANGE, marginTop: 40, opacity: op(1.4) }}>{e.source}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
