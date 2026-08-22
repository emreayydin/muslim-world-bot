import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  Easing,
  Audio,
  staticFile,
} from "remotion";

// ---------- types ----------
export type Caption = { text: string; start: number; end: number };
export type ShortProps = {
  badge: string;
  title: string;
  source: string;
  arabic?: string;
  captions: Caption[];
  audio?: string; // filename in public/
  top: [number, number, number];
  bottom: [number, number, number];
};

const GOLD = "#d4af37";
const FONT = "Arial, Helvetica, sans-serif";

// deterministic PRNG so stars are stable across frames/renders
const mulberry32 = (a: number) => () => {
  a |= 0;
  a = (a + 0x6d2b79f5) | 0;
  let t = Math.imul(a ^ (a >>> 15), 1 | a);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const rgb = (c: [number, number, number]) => `rgb(${c[0]},${c[1]},${c[2]})`;

// ---------- background layers ----------
const Sky: React.FC<{ top: string; bottom: string }> = ({ top, bottom }) => {
  const frame = useCurrentFrame();
  const shift = interpolate(frame, [0, 900], [0, 40]);
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${160 + shift * 0.1}deg, ${top} 0%, ${bottom} 60%, ${top} 100%)`,
      }}
    />
  );
};

const Stars: React.FC = () => {
  const frame = useCurrentFrame();
  const rnd = mulberry32(7);
  const stars = React.useMemo(() => {
    const r = mulberry32(7);
    return Array.from({ length: 90 }, () => ({
      x: r() * 1080,
      y: r() * 1920,
      s: 1 + r() * 3,
      ph: r() * Math.PI * 2,
      sp: 0.6 + r() * 1.2,
    }));
  }, []);
  void rnd;
  return (
    <AbsoluteFill>
      {stars.map((st, i) => {
        const tw = 0.25 + 0.75 * Math.abs(Math.sin(frame / (18 * st.sp) + st.ph));
        const y = (st.y - frame * 0.15) % 1920;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: st.x,
              top: y < 0 ? y + 1920 : y,
              width: st.s,
              height: st.s,
              borderRadius: "50%",
              background: "#fff",
              opacity: tw * 0.8,
              filter: "blur(0.4px)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// an 8-point Islamic star (Khatim) as an SVG, slowly rotating behind content
const GeoStar: React.FC = () => {
  const frame = useCurrentFrame();
  const rot = interpolate(frame, [0, 1800], [0, 360]);
  const pulse = 0.10 + 0.05 * Math.sin(frame / 40);
  const pts = (rotate: number) => {
    const p: string[] = [];
    for (let i = 0; i < 8; i++) {
      const a = (Math.PI / 4) * i + (rotate * Math.PI) / 180;
      p.push(`${500 + Math.cos(a) * 470},${500 + Math.sin(a) * 470}`);
    }
    return p.join(" ");
  };
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: pulse }}>
      <svg
        width={1300}
        height={1300}
        viewBox="0 0 1000 1000"
        style={{ rotate: `${rot}deg` }}
      >
        <polygon points={pts(0)} fill="none" stroke={GOLD} strokeWidth={3} />
        <polygon points={pts(22.5)} fill="none" stroke={GOLD} strokeWidth={3} />
        <circle cx={500} cy={500} r={470} fill="none" stroke={GOLD} strokeWidth={2} />
        <circle cx={500} cy={500} r={330} fill="none" stroke={GOLD} strokeWidth={2} />
      </svg>
    </AbsoluteFill>
  );
};

const Glow: React.FC = () => {
  const frame = useCurrentFrame();
  const o = 0.35 + 0.12 * Math.sin(frame / 50);
  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 50% 22%, rgba(255,236,180,0.55) 0%, rgba(255,236,180,0) 45%)",
        opacity: o,
        mixBlendMode: "screen",
      }}
    />
  );
};

const Scrim: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 28%, rgba(0,0,0,0.15) 70%, rgba(0,0,0,0.6) 100%)",
    }}
  />
);

// ---------- foreground ----------
const Badge: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [0, 14], [0.6, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const o = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        alignSelf: "center",
        background: GOLD,
        color: "#0b1428",
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 40,
        letterSpacing: 2,
        padding: "14px 34px",
        borderRadius: 22,
        opacity: o,
        scale: String(s),
      }}
    >
      {text}
    </div>
  );
};

const Title: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [6, 24], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  const y = interpolate(frame, [6, 24], [20, 0], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  return (
    <div
      style={{
        textAlign: "center",
        color: "#fff",
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 60,
        lineHeight: 1.15,
        maxWidth: 900,
        margin: "0 auto",
        textShadow: "0 3px 12px rgba(0,0,0,0.6)",
        opacity: o,
        translate: `0px ${y}px`,
      }}
    >
      {text}
    </div>
  );
};

const Caption: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cur = captions.find((c) => t >= c.start && t < c.end);
  if (!cur) return null;
  const words = cur.text.toUpperCase().split(" ");
  const prog = (t - cur.start) / Math.max(0.3, cur.end - cur.start);
  const active = Math.floor(prog * words.length);
  const local = (frame - cur.start * fps);
  const s = interpolate(local, [0, 8], [0.85, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const o = interpolate(local, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "0 22px",
        maxWidth: 940,
        margin: "0 auto",
        opacity: o,
        scale: String(s),
      }}
    >
      {words.map((w, i) => (
        <span
          key={i}
          style={{
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 92,
            lineHeight: 1.1,
            color: i === active ? GOLD : "#fff",
            textShadow: "0 4px 16px rgba(0,0,0,0.85)",
          }}
        >
          {w}
        </span>
      ))}
    </div>
  );
};

const Arabic: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [10, 40], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  const s = interpolate(frame, [10, 40], [0.9, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <div
      style={{
        textAlign: "center",
        color: "#fff",
        fontFamily: "'Amiri','Geeza Pro','Scheherazade New',serif",
        fontSize: 74,
        lineHeight: 1.7,
        direction: "rtl",
        maxWidth: 940,
        margin: "0 auto",
        textShadow: `0 0 22px ${GOLD}, 0 3px 12px rgba(0,0,0,0.7)`,
        opacity: o,
        scale: String(s),
      }}
    >
      {text}
    </div>
  );
};

const Source: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [10, 26], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        bottom: 130,
        left: 0,
        right: 0,
        textAlign: "center",
        color: GOLD,
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 46,
        textShadow: "0 2px 10px rgba(0,0,0,0.8)",
        opacity: o,
      }}
    >
      — {text}
    </div>
  );
};

// ---------- main ----------
export const MuslimShort: React.FC<ShortProps> = (props) => {
  const { badge, title, source, arabic, captions, audio, top, bottom } = props;
  return (
    <AbsoluteFill style={{ backgroundColor: rgb(bottom) }}>
      <Sky top={rgb(top)} bottom={rgb(bottom)} />
      <GeoStar />
      <Stars />
      <Glow />
      <Scrim />

      {/* top block: badge + title */}
      <AbsoluteFill style={{ padding: "150px 80px 0", display: "block" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 34 }}>
          <Badge text={badge} />
          <Title text={title} />
        </div>
      </AbsoluteFill>

      {/* arabic (optional) sits in the upper-middle band */}
      {arabic ? (
        <AbsoluteFill
          style={{
            alignItems: "center",
            justifyContent: "flex-start",
            paddingTop: 560,
            paddingLeft: 70,
            paddingRight: 70,
          }}
        >
          <Arabic text={arabic} />
        </AbsoluteFill>
      ) : null}

      {/* captions sit in the lower-middle, clear of the arabic */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          paddingLeft: 70,
          paddingRight: 70,
          translate: "0px 300px",
        }}
      >
        <Caption captions={captions} />
      </AbsoluteFill>

      <Source text={source} />

      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
