import React, { useMemo } from "react";
import * as THREE from "three";

// Low-poly Madinah world for the 3D POV format (17.11.2026). One world, several
// camera shots: hotel room (y=12) whose window looks at the Prophet's Mosque,
// and the marble courtyard with umbrellas in front of it. Everything is built
// from primitives, no external assets.

const MARBLE = "#efe7da";
const WALL = "#f3ead9";
const SKY_TOP = "#27305a";
const SKY_LOW = "#f2b08a";

const useTexture = (draw: (g: CanvasRenderingContext2D, w: number, h: number) => void, w = 256, h = 256) =>
  useMemo(() => {
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    draw(c.getContext("2d")!, w, h);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

const Glow: React.FC<{ pos: [number, number, number]; size: number; color?: string; opacity?: number }> = ({ pos, size, color = "#ffd9a0", opacity = 0.9 }) => {
  const tex = useTexture((g, w, h) => {
    const r = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
    r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.25, "rgba(255,255,255,0.55)"); r.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = r; g.fillRect(0, 0, w, h);
  }, 128, 128);
  return (
    <sprite position={pos} scale={[size, size, 1]}>
      <spriteMaterial map={tex} color={color} transparent opacity={opacity} blending={THREE.AdditiveBlending} depthWrite={false} />
    </sprite>
  );
};

const Minaret: React.FC<{ x: number; z: number; h?: number }> = ({ x, z, h = 26 }) => (
  <group position={[x, 0, z]}>
    <mesh position={[0, h * 0.3, 0]}><boxGeometry args={[2.2, h * 0.6, 2.2]} /><meshStandardMaterial color={WALL} /></mesh>
    <mesh position={[0, h * 0.62, 0]}><cylinderGeometry args={[1.5, 1.5, 0.5, 12]} /><meshStandardMaterial color="#d9c9a8" /></mesh>
    <mesh position={[0, h * 0.75, 0]}><cylinderGeometry args={[0.8, 1.0, h * 0.26, 10]} /><meshStandardMaterial color={WALL} /></mesh>
    <mesh position={[0, h * 0.89, 0]}><cylinderGeometry args={[1.15, 1.15, 0.4, 12]} /><meshStandardMaterial color="#d9c9a8" /></mesh>
    <mesh position={[0, h * 0.95, 0]}><cylinderGeometry args={[0.5, 0.6, h * 0.1, 8]} /><meshStandardMaterial color={WALL} /></mesh>
    <mesh position={[0, h * 1.04, 0]}><coneGeometry args={[0.6, h * 0.1, 8]} /><meshStandardMaterial color="#c9a24a" /></mesh>
    <Glow pos={[0, h * 0.64, 0]} size={7} opacity={0.75} />
    <Glow pos={[0, h * 0.9, 0]} size={5} opacity={0.7} />
  </group>
);

const Mosque: React.FC = () => {
  const arches = [-30, -22, -14, -6, 6, 14, 22, 30];
  return (
    <group position={[0, 0, -84]}>
      <mesh position={[0, 5, 0]}><boxGeometry args={[78, 10, 18]} /><meshStandardMaterial color={WALL} /></mesh>
      <mesh position={[0, 10.3, 0]}><boxGeometry args={[80, 0.7, 19]} /><meshStandardMaterial color="#d9c9a8" /></mesh>
      {arches.map((x) => (
        <group key={x} position={[x, 0, 9.05]}>
          <mesh position={[0, 3, 0]}><boxGeometry args={[4, 6, 0.3]} /><meshBasicMaterial color="#ffcf8a" /></mesh>
          <mesh position={[0, 6, 0]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[2, 2, 0.3, 16, 1, false, -Math.PI / 2, Math.PI]} /><meshBasicMaterial color="#ffcf8a" /></mesh>
          <Glow pos={[0, 3.5, 1]} size={9} opacity={0.35} />
        </group>
      ))}
      {/* main gate */}
      <mesh position={[0, 6.5, 9.2]}><boxGeometry args={[9, 13, 1]} /><meshStandardMaterial color="#e9dcc3" /></mesh>
      <mesh position={[0, 4, 9.75]}><boxGeometry args={[4.4, 8, 0.2]} /><meshBasicMaterial color="#ffd9a0" /></mesh>
      {/* green dome */}
      <mesh position={[14, 12.5, -2]}><cylinderGeometry args={[5.2, 5.2, 4, 16]} /><meshStandardMaterial color="#e9dcc3" /></mesh>
      <mesh position={[14, 14.5, -2]}><sphereGeometry args={[5.4, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#2f8f5b" roughness={0.6} /></mesh>
      <mesh position={[14, 20.4, -2]}><coneGeometry args={[0.35, 2, 8]} /><meshStandardMaterial color="#c9a24a" /></mesh>
      <Glow pos={[14, 15, 2]} size={22} color="#9fe3b8" opacity={0.35} />
      {/* small white domes */}
      {[-24, -12, 0, -34].map((x, i) => (
        <mesh key={x} position={[x, 10.6, -3 - (i % 2) * 4]}><sphereGeometry args={[2.6, 14, 10, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#f6f0e4" /></mesh>
      ))}
      <Minaret x={-37} z={8} /><Minaret x={37} z={8} /><Minaret x={-20} z={-6} h={30} /><Minaret x={26} z={-6} h={30} />
    </group>
  );
};

const Umbrella: React.FC<{ x: number; z: number }> = ({ x, z }) => (
  <group position={[x, 0, z]}>
    <mesh position={[0, 4, 0]}><cylinderGeometry args={[0.28, 0.4, 8, 8]} /><meshStandardMaterial color="#e8dcc6" /></mesh>
    <mesh position={[0, 8.2, 0]} rotation={[0, Math.PI / 4, 0]}><coneGeometry args={[5.6, 1.6, 4]} /><meshStandardMaterial color="#fbf6ec" side={THREE.DoubleSide} /></mesh>
    <mesh position={[0, 9.2, 0]}><coneGeometry args={[0.3, 0.8, 6]} /><meshStandardMaterial color="#c9a24a" /></mesh>
    <Glow pos={[0, 6.4, 0]} size={5} opacity={0.5} />
  </group>
);

// distant worshippers, always seen from behind, walking towards the mosque
const People: React.FC<{ t: number }> = ({ t }) => {
  const list = useMemo(() => Array.from({ length: 60 }, (_, i) => {
    const r = (n: number) => { const s = Math.sin(i * 127.1 + n * 311.7) * 43758.5453; return s - Math.floor(s); };
    return { x: (r(1) - 0.5) * 30, z: -12 - r(2) * 58, s: 0.5 + r(3) * 0.5, c: r(4) > 0.25 ? "#fbf8f1" : "#3a3f4c", ph: r(5) * 6 };
  }), []);
  return (
    <>
      {list.map((p, i) => {
        const z = p.z - t * p.s * 0.9;
        const bob = Math.abs(Math.sin(t * 4 + p.ph)) * 0.06;
        return (
          <group key={i} position={[p.x, bob, z]}>
            <mesh position={[0, 0.75, 0]}><cylinderGeometry args={[0.2, 0.34, 1.5, 8]} /><meshStandardMaterial color={p.c} /></mesh>
            <mesh position={[0, 1.68, 0]}><sphereGeometry args={[0.2, 10, 8]} /><meshStandardMaterial color={p.c === "#fbf8f1" ? "#f1ede4" : "#22252e"} /></mesh>
          </group>
        );
      })}
    </>
  );
};

const Motes: React.FC<{ t: number }> = ({ t }) => {
  const geo = useMemo(() => {
    const n = 500, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const r = (k: number) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };
      a[i * 3] = (r(1) - 0.5) * 60; a[i * 3 + 1] = r(2) * 22; a[i * 3 + 2] = 6 - r(3) * 80;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(a, 3));
    return g;
  }, []);
  return (
    <points geometry={geo} position={[Math.sin(t * 0.3) * 0.6, -((t * 0.35) % 2), 0]}>
      <pointsMaterial color="#fff3d6" size={0.09} transparent opacity={0.7} depthWrite={false} />
    </points>
  );
};

const Room: React.FC<{ time: string }> = ({ time }) => {
  const Y = 12;
  const phone = useTexture((g, w, h) => {
    g.fillStyle = "#0e1a3a"; g.fillRect(0, 0, w, h);
    g.fillStyle = "#9db3e8"; g.font = "600 22px Helvetica"; g.textAlign = "center"; g.fillText("Fri, 20 Nov", w / 2, 60);
    g.fillStyle = "#fff"; g.font = "600 84px Helvetica"; g.fillText(time, w / 2, 160);
    g.fillStyle = "#9db3e8"; g.font = "500 26px Helvetica"; g.fillText("Fajr in 22 min", w / 2, 230);
    g.fillStyle = "#f2a03d"; g.beginPath(); g.roundRect(w / 2 - 80, 300, 160, 54, 27); g.fill();
    g.fillStyle = "#1a1a1a"; g.font = "700 26px Helvetica"; g.fillText("Stop", w / 2, 336);
  }, 256, 440);
  const wallMat = <meshStandardMaterial color="#e9dfd0" />;
  return (
    <group>
      <mesh position={[0, Y - 0.05, 3]}><boxGeometry args={[9, 0.1, 8]} /><meshStandardMaterial color="#8a6a4d" /></mesh>
      {/* window wall at z=0 with an opening x[-1.4,1.4] y[Y+0.9,Y+2.9] */}
      <mesh position={[-2.95, Y + 1.6, 0]}><boxGeometry args={[3.1, 3.4, 0.2]} />{wallMat}</mesh>
      <mesh position={[2.95, Y + 1.6, 0]}><boxGeometry args={[3.1, 3.4, 0.2]} />{wallMat}</mesh>
      <mesh position={[0, Y + 0.45, 0]}><boxGeometry args={[2.8, 0.9, 0.2]} />{wallMat}</mesh>
      <mesh position={[0, Y + 3.1, 0]}><boxGeometry args={[2.8, 0.4, 0.2]} />{wallMat}</mesh>
      <mesh position={[0, Y + 0.92, 0.12]}><boxGeometry args={[3.0, 0.08, 0.35]} /><meshStandardMaterial color="#fff" /></mesh>
      <mesh position={[0, Y + 1.9, 0]}><boxGeometry args={[0.06, 2, 0.08]} /><meshStandardMaterial color="#fff" /></mesh>
      {/* side walls + ceiling */}
      <mesh position={[-4.5, Y + 1.6, 3.5]}><boxGeometry args={[0.2, 3.4, 7.2]} />{wallMat}</mesh>
      <mesh position={[4.5, Y + 1.6, 3.5]}><boxGeometry args={[0.2, 3.4, 7.2]} />{wallMat}</mesh>
      <mesh position={[0, Y + 3.35, 3.5]}><boxGeometry args={[9, 0.1, 7.2]} />{wallMat}</mesh>
      {/* curtains */}
      <mesh position={[-1.75, Y + 1.8, 0.2]}><boxGeometry args={[0.7, 2.7, 0.12]} /><meshStandardMaterial color="#c9772b" /></mesh>
      <mesh position={[1.75, Y + 1.8, 0.2]}><boxGeometry args={[0.7, 2.7, 0.12]} /><meshStandardMaterial color="#c9772b" /></mesh>
      {/* bed + blanket hill + phone */}
      <mesh position={[0.2, Y + 0.3, 3.9]}><boxGeometry args={[2.4, 0.5, 3.4]} /><meshStandardMaterial color="#f5f1ea" /></mesh>
      <mesh position={[0.2, Y + 0.5, 3.3]} scale={[1.15, 0.28, 1.3]}><sphereGeometry args={[1, 18, 12]} /><meshStandardMaterial color="#fbf9f5" /></mesh>
      <group position={[0.45, Y + 0.86, 3.45]} rotation={[-1.05, 0.25, 0.1]}>
        <mesh><boxGeometry args={[0.36, 0.62, 0.03]} /><meshStandardMaterial color="#10131c" /></mesh>
        <mesh position={[0, 0, 0.017]}><planeGeometry args={[0.33, 0.58]} /><meshBasicMaterial map={phone} /></mesh>
      </group>
      <pointLight position={[0.45, Y + 1.2, 3.3]} color="#9db3ff" intensity={2.2} distance={3} />
    </group>
  );
};

export const World: React.FC<{ t: number; phoneTime: string }> = ({ t, phoneTime }) => {
  const sky = useTexture((g, w, h) => {
    const l = g.createLinearGradient(0, 0, 0, h);
    l.addColorStop(0, SKY_TOP); l.addColorStop(0.55, "#8a6f9e"); l.addColorStop(0.78, SKY_LOW); l.addColorStop(1, "#ffd7a8");
    g.fillStyle = l; g.fillRect(0, 0, w, h);
  }, 16, 512);
  const tiles = useTexture((g, w, h) => {
    g.fillStyle = MARBLE; g.fillRect(0, 0, w, h);
    g.strokeStyle = "rgba(150,130,100,0.35)"; g.lineWidth = 2; g.strokeRect(0, 0, w, h);
    g.fillStyle = "rgba(190,170,140,0.25)"; g.fillRect(w * 0.35, h * 0.35, w * 0.3, h * 0.3);
  }, 128, 128);
  tiles.wrapS = tiles.wrapT = THREE.RepeatWrapping; tiles.repeat.set(40, 40);
  const umb: [number, number][] = [];
  for (const x of [-16, -6.5, 6.5, 16]) for (const z of [-12, -24, -36, -48, -60]) umb.push([x, z]);
  return (
    <>
      <fog attach="fog" args={["#c79aa0", 40, 170]} />
      <ambientLight intensity={0.85} color="#d9cfe8" />
      <directionalLight position={[-30, 40, 20]} intensity={0.9} color="#ffd9b0" />
      <mesh position={[0, 30, -150]}><planeGeometry args={[420, 130]} /><meshBasicMaterial map={sky} fog={false} /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -40]}><planeGeometry args={[200, 200]} /><meshStandardMaterial map={tiles} roughness={0.35} /></mesh>
      <Mosque />
      {umb.map(([x, z]) => <Umbrella key={`${x}_${z}`} x={x} z={z} />)}
      <People t={t} />
      <Motes t={t} />
      <Room time={phoneTime} />
    </>
  );
};
