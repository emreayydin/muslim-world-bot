import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";

export type ThumbProps = {
  title: string;
  count: number;
  top: [number, number, number];
  bottom: [number, number, number];
};

const GOLD = "#d4af37";
const FONT = "Arial, Helvetica, sans-serif";
const rgb = (c: [number, number, number]) => `rgb(${c[0]},${c[1]},${c[2]})`;

const GeoStar: React.FC = () => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 0.14 }}>
    <svg width={900} height={900} viewBox="0 0 1000 1000" style={{ transform: "translateX(24%) rotate(12deg)" }}>
      {[0, 22.5].map((rot, k) => (
        <polygon
          key={k}
          points={Array.from({ length: 8 }, (_, i) => {
            const a = (Math.PI / 4) * i + (rot * Math.PI) / 180;
            return `${500 + Math.cos(a) * 470},${500 + Math.sin(a) * 470}`;
          }).join(" ")}
          fill="none" stroke={GOLD} strokeWidth={4}
        />
      ))}
      <circle cx={500} cy={500} r={470} fill="none" stroke={GOLD} strokeWidth={3} />
      <circle cx={500} cy={500} r={330} fill="none" stroke={GOLD} strokeWidth={3} />
    </svg>
  </AbsoluteFill>
);

export const MuslimThumb: React.FC<ThumbProps> = ({ title, count, top, bottom }) => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: rgb(bottom) }}>
      <AbsoluteFill style={{ background: `linear-gradient(145deg, ${rgb(top)} 0%, ${rgb(bottom)} 70%)` }} />
      <GeoStar />
      <AbsoluteFill style={{ background: "radial-gradient(circle at 82% 46%, rgba(255,236,180,0.4) 0%, rgba(255,236,180,0) 42%)" }} />
      {/* left-weighted scrim so the title pops */}
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 55%, rgba(0,0,0,0) 75%)" }} />
      {/* thin gold frame */}
      <AbsoluteFill style={{ border: `6px solid ${GOLD}`, opacity: 0.5, margin: 18 }} />

      {/* badge */}
      <div style={{
        position: "absolute", top: 46, left: 56, background: GOLD, color: "#0b1428",
        fontFamily: FONT, fontWeight: 900, fontSize: 34, letterSpacing: 2,
        padding: "10px 26px", borderRadius: 16,
      }}>
        MUSLIM WORLD
      </div>

      {/* giant number, right */}
      <div style={{
        position: "absolute", right: 40, top: 0, bottom: 0, width: 480,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: FONT, fontWeight: 900, fontSize: 420, color: GOLD,
        WebkitTextStroke: "10px rgba(0,0,0,0.85)",
        textShadow: `0 0 60px ${GOLD}`,
      }}>
        {count}
      </div>

      {/* title, left */}
      <div style={{
        position: "absolute", left: 56, top: 150, width: width * 0.58,
        color: "#fff", fontFamily: FONT, fontWeight: 900, fontSize: 92, lineHeight: 1.08,
        textShadow: "0 4px 4px #000, 0 6px 22px rgba(0,0,0,0.85)",
      }}>
        {title}
      </div>
    </AbsoluteFill>
  );
};
