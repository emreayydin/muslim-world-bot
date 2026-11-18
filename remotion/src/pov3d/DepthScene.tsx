import React, { useMemo } from "react";
import * as THREE from "three";
import { staticFile, delayRender, continueRender } from "remotion";

// One AI still turned into real 3D (18.11.2026): a dense plane displaced towards
// the camera by its depth map (bright = near, from mflux-save-depth / Depth Pro).
// Moving the camera then gives true parallax - foreground slides past faster
// than the background - which is what makes the reference feel like walking.

const loader = new THREE.TextureLoader();
const cache = new Map<string, THREE.Texture>();

const useTex = (src: string, srgb: boolean) =>
  useMemo(() => {
    const key = src + srgb;
    if (cache.has(key)) return cache.get(key)!;
    const h = delayRender(`texture ${src}`);
    const t = loader.load(staticFile(src), () => continueRender(h), undefined, () => continueRender(h));
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    t.minFilter = THREE.LinearFilter;
    cache.set(key, t);
    return t;
  }, [src, srgb]);

export const PLANE_H = 2.2;          // world units, fills the frame at camera z=2, fov 50 with overscan
export const ASPECT = 768 / 1344;
export const DEPTH = 0.55;           // how far the nearest pixel is pushed towards the camera

export const DepthScene: React.FC<{ image: string; depth: string }> = ({ image, depth }) => {
  const map = useTex(image, true);
  const disp = useTex(depth, false);
  const geo = useMemo(() => new THREE.PlaneGeometry(PLANE_H * ASPECT, PLANE_H, 220, 384), []);
  return (
    <mesh geometry={geo}>
      {/* unlit look: colour comes from the emissive map, displacement from depth */}
      <meshStandardMaterial color="#000" emissive="#fff" emissiveMap={map} emissiveIntensity={1}
        displacementMap={disp} displacementScale={DEPTH} displacementBias={-DEPTH * 0.35} roughness={1} />
    </mesh>
  );
};
