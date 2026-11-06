import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export type StoryWord = { text: string; start: number; end: number; speaker?: string };
export type StoryProps = {
  audio: string;
  images: string[];
  videos?: ({ src: string; start: number } | null)[];
  scenes: { start: number; end: number }[];
  words: StoryWord[];
  durationSeconds: number;
  ending: { arabic: string; word: string; reminder: string; source: string };
  handle?: string;
};

const GOLD = "#f5c542";
const FONT = "'Montserrat', 'Arial Black', Arial, Helvetica, sans-serif";
const FADE = 0.35; // crossfade seconds

// ---------- one picture with Ken-Burns motion ----------
const Shot: React.FC<{ src: string; start: number; end: number; idx: number;
  video?: { src: string; start: number } | null }> = ({ src, start, end, idx, video }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < start - FADE || t > end + FADE) return null;
  const p = interpolate(t, [start - FADE, end + FADE], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const zoomIn = idx % 2 === 0;
  const scale = zoomIn ? 1.04 + p * 0.12 : 1.16 - p * 0.12;
  const dx = (idx % 3 === 0 ? -1 : idx % 3 === 1 ? 1 : 0) * 26 * (p - 0.5);
  const dy = (idx % 2 === 0 ? 1 : -1) * 18 * (p - 0.5);
  const opacity = interpolate(t, [start - FADE, start, end, end + FADE], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ opacity }}>
      {video ? (
        <Sequence from={Math.round(video.start * fps)} layout="none">
          <OffthreadVideo
            src={staticFile(video.src)}
            muted
            style={{
              width: "100%", height: "100%", objectFit: "cover",
              transform: `scale(${scale}) translate(${dx}px, ${dy}px)`,
            }}
          />
        </Sequence>
      ) : (
        <Img
          src={staticFile(src)}
          style={{
            width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${scale}) translate(${dx}px, ${dy}px)`,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

// ---------- word-by-word captions (2-3 words, current one highlighted) ----------
type Chunk = { words: StoryWord[]; start: number; end: number };
const chunkWords = (words: StoryWord[]): Chunk[] => {
  const out: Chunk[] = [];
  let cur: StoryWord[] = [];
  const flush = () => {
    if (cur.length) out.push({ words: cur, start: cur[0].start, end: cur[cur.length - 1].end });
    cur = [];
  };
  words.forEach((w, i) => {
    const prev = words[i - 1];
    if (prev && (prev.speaker !== w.speaker || w.start - prev.end > 0.35)) flush();
    cur.push(w);
    const len = cur.map((x) => x.text).join(" ").length;
    if (cur.length >= 3 || len > 16 || /[.,!?…]$/.test(w.text)) flush();
  });
  flush();
  return out;
};

const Captions: React.FC<{ words: StoryWord[]; until: number }> = ({ words, until }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const chunks = React.useMemo(() => chunkWords(words), [words]);
  if (t >= until) return null;
  const idx = chunks.findIndex((c, i) => t >= c.start - 0.05 && t < (chunks[i + 1]?.start ?? c.end + 0.6));
  if (idx < 0) return null;
  const c = chunks[idx];
  const pop = spring({ frame: frame - Math.round(c.start * fps), fps, config: { damping: 12, stiffness: 220 } });
  return (
    <div
      style={{
        position: "absolute", left: 60, right: 60, top: 1180, textAlign: "center",
        transform: `scale(${0.85 + 0.15 * pop})`,
      }}
    >
      {c.words.map((w, i) => {
        const active = t >= w.start - 0.03 && t < (c.words[i + 1]?.start ?? c.end + 0.5);
        return (
          <span
            key={i}
            style={{
              fontFamily: FONT, fontWeight: 900, fontSize: 78, lineHeight: 1.15,
              color: active ? GOLD : "#ffffff",
              WebkitTextStroke: "3px #000",
              paintOrder: "stroke fill",
              textShadow: "0 6px 18px rgba(0,0,0,0.85)",
              marginRight: 18, display: "inline-block",
              transform: active ? "translateY(-4px)" : "none",
            }}
          >
            {w.text.replace(/[,]$/, "")}
          </span>
        );
      })}
    </div>
  );
};

// ---------- closing reminder card ----------
const Ending: React.FC<{ e: StoryProps["ending"]; start: number; image: string }> = ({ e, start, image }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < start - 0.4) return null;
  const k = interpolate(t, [start - 0.4, start + 0.6], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });
  const rise = (d: number) =>
    interpolate(t, [start + d, start + d + 0.7], [40, 0], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
    });
  const op = (d: number) =>
    interpolate(t, [start + d, start + d + 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Img src={staticFile(image)} style={{ width: "100%", height: "100%", objectFit: "cover",
        filter: "blur(14px) brightness(0.45)", transform: "scale(1.15)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(6,14,34,0.55), rgba(6,14,34,0.9))" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 90, textAlign: "center" }}>
        <div style={{ fontFamily: "Amiri, 'Geeza Pro', serif", fontSize: 170, color: GOLD, direction: "rtl",
          textShadow: "0 0 40px rgba(245,197,66,0.55)", opacity: op(0.1), transform: `translateY(${rise(0.1)}px)` }}>
          {e.arabic}
        </div>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 50, color: "#fff", letterSpacing: 6,
          textTransform: "uppercase", marginTop: 10, opacity: op(0.4), transform: `translateY(${rise(0.4)}px)` }}>
          {e.word}
        </div>
        <div style={{ width: 160, height: 4, background: GOLD, margin: "46px 0", opacity: op(0.6) }} />
        <div style={{ fontFamily: "Georgia, serif", fontSize: 58, lineHeight: 1.35, color: "#fdf6e3",
          opacity: op(0.8), transform: `translateY(${rise(0.8)}px)` }}>
          “{e.reminder}”
        </div>
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 42, color: GOLD, marginTop: 44,
          opacity: op(1.3) }}>
          {e.source}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const MuslimStory: React.FC<StoryProps> = (p) => {
  const n = p.images.length;
  const endStart = p.scenes[n]?.start ?? p.durationSeconds - 6;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {p.images.map((src, i) => (
        <Shot key={i} src={src} idx={i} video={p.videos?.[i]} start={p.scenes[i].start}
          end={i === n - 1 ? endStart : p.scenes[i].end} />
      ))}
      {/* soft vignette so captions always read */}
      <AbsoluteFill style={{ background:
        "radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)" }} />
      <Captions words={p.words} until={endStart - 0.1} />
      <Ending e={p.ending} start={endStart} image={p.images[n - 1]} />
      {p.handle ? (
        <div style={{ position: "absolute", bottom: 70, width: "100%", textAlign: "center",
          fontFamily: FONT, fontWeight: 700, fontSize: 30, color: "rgba(255,255,255,0.55)" }}>
          {p.handle}
        </div>
      ) : null}
      <Audio src={staticFile(p.audio)} />
    </AbsoluteFill>
  );
};
