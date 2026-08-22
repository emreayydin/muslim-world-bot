import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { MuslimShort, ShortProps } from "./MuslimShort";
import "./index.css";

const FPS = 30;

const SAMPLE: ShortProps = {
  badge: "QUR'AN",
  title: "The Verse That Calms Every Heart",
  source: "Qur'an 2:286",
  arabic: "لَا يُكَلِّفُ ٱللَّهُ نَفْسًا إِلَّا وُسْعَهَا",
  top: [8, 46, 38],
  bottom: [4, 22, 30],
  captions: [
    { text: "Allah never burdens", start: 0.0, end: 1.6 },
    { text: "a soul beyond", start: 1.6, end: 3.0 },
    { text: "what it can bear", start: 3.0, end: 4.8 },
    { text: "Whatever you face today", start: 4.8, end: 7.0 },
    { text: "you were made able", start: 7.0, end: 8.8 },
    { text: "to carry it", start: 8.8, end: 10.6 },
    { text: "Hold on", start: 10.6, end: 11.8 },
    { text: "your relief is written", start: 11.8, end: 14.0 },
  ],
};

const calc: CalculateMetadataFunction<ShortProps> = ({ props }) => {
  const end = props.captions.length
    ? Math.max(...props.captions.map((c) => c.end))
    : 14;
  return {
    durationInFrames: Math.ceil((end + 1.2) * FPS),
    fps: FPS,
    width: 1080,
    height: 1920,
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MuslimShort"
      component={MuslimShort}
      durationInFrames={450}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={SAMPLE}
      calculateMetadata={calc}
    />
  );
};
