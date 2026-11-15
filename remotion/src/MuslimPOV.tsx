import React from "react";
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile,
  useCurrentFrame, useVideoConfig, Easing,
} from "remotion";

// "POV: you wake up in <city>" format (15.11.2026), modelled on @wander_frame_:
// first-person shots, clock + date/place top-left, small fact chips,
// serif inner-monologue captions, gentle handheld camera sway.

export type PovWord = { text: string; start: number; end: number };
export type PovScene = {
  start: number; end: number; time: string;
  chip?: { title: string; sub: string } | null;
};
export type PovProps = {
  audio: string;
  images: string[];
  videos?: ({ src: string; start: number } | null)[];
  scenes: PovScene[];
  words: PovWord[];
  durationSeconds: number;
  date: string;
  place: string;
  hook: string;
  ending: { arabic: string; word: string; reminder: string; source: string };
  handle?: string;
};

const ORANGE = "#f2a03d";
const SERIF = "'Iowan Old Style', 'Palatino', Georgia, serif";
const SANS = "'SF Pro Display', 'Helvetica Neue', Arial, sans-serif";
const FADE = 0.35;

const Shot: React.FC<{ src: string; start: number; end: number; idx: number;
  video?: { src: string; start: number } | null }> = ({ src, start, end, idx, video }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < start - FADE || t > end + FADE) return null;
  const p = interpolate(t, [start - FADE, end + FADE], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // slow push-in like walking forward + a small handheld sway
  const scale = 1.06 + p * 0.1;
  const sway = Math.sin((t + idx) * 1.3) * 6;
  const bob = Math.sin((t + idx) * 2.1) * 4;
  const opacity = interpolate(t, [start - FADE, start, end, end + FADE], [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const style: React.CSSProperties = {
    width: "100%", height: "100%", objectFit: "cover",
    transform: `scale(${scale}) translate(${sway}px, ${bob}px)`,
  };
  return (
    <AbsoluteFill style={{ opacity }}>
      {video ? (
        <Sequence from={Math.round(video.start * fps)} layout="none">
          <OffthreadVideo src={staticFile(video.src)} muted style={style} />
        </Sequence>
      ) : <Img src={staticFile(src)} style={style} />}
    </AbsoluteFill>
  );
};

const Clock: React.FC<{ scenes: PovScene[]; date: string; place: string; until: number }> = ({ scenes, date, place, until }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t >= until) return null;
  const i = Math.max(0, scenes.findIndex((s, k) => t >= s.start - 0.05 && t < (scenes[k + 1]?.start ?? 1e9)));
  const s = scenes[i];
  const pop = interpolate(t, [s.start, s.start + 0.35], [0.4, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const chipIn = interpolate(t, [s.start + 0.5, s.start + 1.0], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <div style={{ position: "absolute", left: 70, top: 150 }}>
      <div style={{ display: "flex", alignItems: "stretch" }}>
        <div style={{ width: 6, background: ORANGE, borderRadius: 3, marginRight: 22 }} />
        <div>
          <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 104, color: "#fff", lineHeight: 1,
            letterSpacing: -2, opacity: pop, textShadow: "0 4px 24px rgba(0,0,0,0.45)" }}>{s.time}</div>
          <div style={{ fontFamily: SANS, fontSize: 30, color: "rgba(255,255,255,0.85)", marginTop: 8,
            textShadow: "0 2px 10px rgba(0,0,0,0.6)" }}>{date} · {place}</div>
        </div>
      </div>
      {s.chip ? (
        <div style={{ marginTop: 34, display: "inline-block", background: "rgba(30,30,34,0.72)",
          borderRadius: 18, padding: "18px 26px", opacity: chipIn, transform: `translateY(${(1 - chipIn) * 14}px)`,
          maxWidth: 760 }}>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 36, color: "#fff" }}>
            <span style={{ color: ORANGE, marginRight: 10 }}>•</span>{s.chip.title}</div>
          <div style={{ fontFamily: SANS, fontSize: 27, color: "rgba(255,255,255,0.75)", marginTop: 6 }}>{s.chip.sub}</div>
        </div>
      ) : null}
    </div>
  );
};

const Hook: React.FC<{ hook: string }> = ({ hook }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t > 3.2) return null;
  const op = interpolate(t, [0.2, 0.6, 2.7, 3.2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const [pov, ...rest] = hook.split(":");
  return (
    <div style={{ position: "absolute", top: 520, width: "100%", textAlign: "center", opacity: op,
      fontFamily: SANS, fontWeight: 700, fontSize: 64, color: "#fff", textShadow: "0 4px 24px rgba(0,0,0,0.6)" }}>
      {rest.length ? <><span style={{ color: ORANGE }}>{pov}:</span>{rest.join(":")}</> : hook}
    </div>
  );
};

// whole spoken line, words appear as they are spoken (serif, like the reference)
const Captions: React.FC<{ words: PovWord[]; scenes: PovScene[]; until: number }> = ({ words, scenes, until }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t >= until) return null;
  const s = scenes.find((x, k) => t >= x.start - 0.05 && t < (scenes[k + 1]?.start ?? 1e9));
  if (!s) return null;
  const ws = words.filter((w) => w.start >= s.start - 0.05 && w.start < s.end);
  const shown = ws.filter((w) => w.start <= t + 0.05);
  if (!shown.length) return null;
  return (
    <div style={{ position: "absolute", left: 90, right: 90, top: 1250, textAlign: "center",
      fontFamily: SERIF, fontSize: 64, lineHeight: 1.25, color: "#fff",
      textShadow: "0 2px 6px rgba(0,0,0,0.85), 0 0 26px rgba(0,0,0,0.55)" }}>
      {shown.map((w) => w.text).join(" ")}
    </div>
  );
};

const Ending: React.FC<{ e: PovProps["ending"]; start: number; image: string }> = ({ e, start, image }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < start - 0.4) return null;
  const k = interpolate(t, [start - 0.4, start + 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = (d: number) => interpolate(t, [start + d, start + d + 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Img src={staticFile(image)} style={{ width: "100%", height: "100%", objectFit: "cover",
        filter: "blur(16px) brightness(0.4)", transform: "scale(1.15)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 90, textAlign: "center" }}>
        <div style={{ fontFamily: "Amiri, 'Geeza Pro', serif", fontSize: 140, color: ORANGE, direction: "rtl", opacity: op(0.1) }}>{e.arabic}</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 40, color: "#fff", letterSpacing: 4,
          textTransform: "uppercase", marginTop: 16, opacity: op(0.4) }}>{e.word}</div>
        <div style={{ fontFamily: SERIF, fontSize: 56, lineHeight: 1.35, color: "#fff", marginTop: 50, opacity: op(0.8) }}>“{e.reminder}”</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 38, color: ORANGE, marginTop: 40, opacity: op(1.3) }}>{e.source}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const MuslimPOV: React.FC<PovProps> = (p) => {
  const n = p.images.length;
  const endStart = p.scenes[n]?.start ?? p.durationSeconds - 6;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {p.images.map((src, i) => (
        <Shot key={i} src={src} idx={i} video={p.videos?.[i]} start={p.scenes[i].start}
          end={i === n - 1 ? endStart : p.scenes[i].end} />
      ))}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.35) 100%)" }} />
      <Clock scenes={p.scenes.slice(0, n)} date={p.date} place={p.place} until={endStart - 0.1} />
      <Hook hook={p.hook} />
      <Captions words={p.words} scenes={p.scenes.slice(0, n)} until={endStart - 0.1} />
      <Ending e={p.ending} start={endStart} image={p.images[n - 1]} />
      {p.handle ? (
        <div style={{ position: "absolute", bottom: 70, width: "100%", textAlign: "center",
          fontFamily: SANS, fontWeight: 600, fontSize: 28, color: "rgba(255,255,255,0.5)" }}>{p.handle}</div>
      ) : null}
      <Audio src={staticFile(p.audio)} />
    </AbsoluteFill>
  );
};
