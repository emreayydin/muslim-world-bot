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

export type Caption = { text: string; start: number; end: number };
export type Section = {
  label: string; // "intro" | "point" | "outro"
  start: number;
  end: number;
  index?: number;
  headline?: string;
  source?: string;
};
export type LongProps = {
  title: string;
  count: number;
  sections: Section[];
  captions: Caption[];
  audio?: string;
  top: [number, number, number];
  bottom: [number, number, number];
};

const GOLD = "#d4af37";
const FONT = "Arial, Helvetica, sans-serif";
const rgb = (c: [number, number, number]) => `rgb(${c[0]},${c[1]},${c[2]})`;

// ---------- animated background (size-aware) ----------
const Sky: React.FC<{ top: string; bottom: string }> = ({ top, bottom }) => {
  const frame = useCurrentFrame();
  const shift = interpolate(frame, [0, 1800], [0, 30]);
  return (
    <AbsoluteFill
      style={{ background: `linear-gradient(${155 + shift * 0.1}deg, ${top} 0%, ${bottom} 62%, ${top} 100%)` }}
    />
  );
};

const Stars: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const stars = React.useMemo(() => {
    let a = 11;
    const r = () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    return Array.from({ length: 110 }, () => ({
      x: r() * width, y: r() * height, s: 1 + r() * 3, ph: r() * 6.28, sp: 0.6 + r() * 1.2,
    }));
  }, [width, height]);
  return (
    <AbsoluteFill>
      {stars.map((st, i) => {
        const tw = 0.25 + 0.75 * Math.abs(Math.sin(frame / (18 * st.sp) + st.ph));
        const y = (st.y - frame * 0.12) % height;
        return (
          <div key={i} style={{
            position: "absolute", left: st.x, top: y < 0 ? y + height : y,
            width: st.s, height: st.s, borderRadius: "50%", background: "#fff",
            opacity: tw * 0.8, filter: "blur(0.4px)",
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

const GeoStar: React.FC = () => {
  const frame = useCurrentFrame();
  const rot = interpolate(frame, [0, 2400], [0, 360]);
  const pulse = 0.09 + 0.04 * Math.sin(frame / 45);
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
      <svg width={1100} height={1100} viewBox="0 0 1000 1000" style={{ rotate: `${rot}deg` }}>
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
  const o = 0.32 + 0.1 * Math.sin(frame / 55);
  return (
    <AbsoluteFill style={{
      background: "radial-gradient(circle at 50% 26%, rgba(255,236,180,0.5) 0%, rgba(255,236,180,0) 46%)",
      opacity: o, mixBlendMode: "screen",
    }} />
  );
};

const Scrim: React.FC = () => (
  <AbsoluteFill style={{
    background: "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.15) 24%, rgba(0,0,0,0.15) 66%, rgba(0,0,0,0.66) 100%)",
  }} />
);

// ---------- foreground ----------
const cur = <T extends { start: number; end: number }>(items: T[], t: number) =>
  items.find((c) => t >= c.start && t < c.end);

const Banner: React.FC<{ section?: Section; title: string; count: number }> = ({ section, title, count }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = section ? frame - section.start * fps : frame;
  const o = interpolate(local, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const y = interpolate(local, [0, 12], [-18, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  if (!section || section.label === "intro") {
    return (
      <div style={{ opacity: o, translate: `0px ${y}px`, display: "flex", flexDirection: "column", gap: 26, alignItems: "center" }}>
        <div style={{ background: GOLD, color: "#0b1428", fontFamily: FONT, fontWeight: 800, fontSize: 44, letterSpacing: 2, padding: "14px 40px", borderRadius: 24 }}>
          {count} REMINDERS
        </div>
        <div style={{ color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 84, textAlign: "center", maxWidth: 1500, lineHeight: 1.12, textShadow: "0 4px 16px rgba(0,0,0,0.7)" }}>
          {title}
        </div>
      </div>
    );
  }
  if (section.label === "outro") {
    return (
      <div style={{ opacity: o, translate: `0px ${y}px`, background: GOLD, color: "#0b1428", fontFamily: FONT, fontWeight: 800, fontSize: 52, letterSpacing: 1, padding: "18px 48px", borderRadius: 28 }}>
        SUBSCRIBE FOR A DAILY REMINDER
      </div>
    );
  }
  // point banner
  return (
    <div style={{ opacity: o, translate: `0px ${y}px`, display: "flex", alignItems: "center", gap: 28, maxWidth: 1600 }}>
      <div style={{ background: GOLD, color: "#0b1428", fontFamily: FONT, fontWeight: 900, fontSize: 52, padding: "10px 26px", borderRadius: 18, whiteSpace: "nowrap" }}>
        {section.index}/{count}
      </div>
      <div style={{ color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 66, lineHeight: 1.12, textShadow: "0 4px 14px rgba(0,0,0,0.75)" }}>
        {section.headline}
      </div>
    </div>
  );
};

const Captions: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const c = cur(captions, t);
  if (!c) return null;
  const words = c.text.toUpperCase().split(" ");
  const prog = (t - c.start) / Math.max(0.3, c.end - c.start);
  const active = Math.floor(prog * words.length);
  const local = frame - c.start * fps;
  const o = interpolate(local, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 20px", maxWidth: 1500, margin: "0 auto", opacity: o }}>
      {words.map((w, i) => (
        <span key={i} style={{ fontFamily: FONT, fontWeight: 900, fontSize: 78, lineHeight: 1.15, color: i === active ? GOLD : "#fff", textShadow: "0 4px 16px rgba(0,0,0,0.85)" }}>
          {w}
        </span>
      ))}
    </div>
  );
};

export const MuslimLong: React.FC<LongProps> = ({ title, count, sections, captions, audio, top, bottom }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const section = cur(sections, t);
  const source = section && section.label === "point" ? section.source : "";
  return (
    <AbsoluteFill style={{ backgroundColor: rgb(bottom) }}>
      <Sky top={rgb(top)} bottom={rgb(bottom)} />
      <GeoStar />
      <Stars />
      <Glow />
      <Scrim />

      {/* top banner (badge/title | N/count + headline | subscribe) */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 120, paddingLeft: 90, paddingRight: 90 }}>
        <Banner section={section} title={title} count={count} />
      </AbsoluteFill>

      {/* kinetic captions, lower-middle */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingLeft: 120, paddingRight: 120, translate: "0px 210px" }}>
        <Captions captions={captions} />
      </AbsoluteFill>

      {/* current point's source */}
      {source ? (
        <div style={{ position: "absolute", bottom: 70, left: 0, right: 0, textAlign: "center", color: GOLD, fontFamily: FONT, fontWeight: 700, fontSize: 46, textShadow: "0 2px 10px rgba(0,0,0,0.8)" }}>
          — {source}
        </div>
      ) : null}

      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
