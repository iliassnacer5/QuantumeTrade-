'use client';

import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Champ de particules « flux de marché » : une nappe de points ondule comme des vagues.
 * Chargé uniquement côté client (via next/dynamic) sur landing/login — jamais sur les pages de travail.
 */
function Waves() {
  const ref = useRef<THREE.Points>(null);
  const SIZE = 60; // 60×60 = 3600 points
  const SPACING = 0.5;

  const { positions, colors } = useMemo(() => {
    const positions = new Float32Array(SIZE * SIZE * 3);
    const colors = new Float32Array(SIZE * SIZE * 3);
    const green = new THREE.Color('#1D9E75');
    const cyan = new THREE.Color('#22C7C7');
    let i = 0;
    for (let x = 0; x < SIZE; x++) {
      for (let z = 0; z < SIZE; z++) {
        positions[i * 3] = (x - SIZE / 2) * SPACING;
        positions[i * 3 + 1] = 0;
        positions[i * 3 + 2] = (z - SIZE / 2) * SPACING;
        const c = green.clone().lerp(cyan, x / SIZE);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
        i++;
      }
    }
    return { positions, colors };
  }, []);

  useFrame(({ clock }) => {
    const pts = ref.current;
    if (!pts) return;
    const t = clock.getElapsedTime();
    const arr = pts.geometry.attributes.position.array as Float32Array;
    let i = 0;
    for (let x = 0; x < SIZE; x++) {
      for (let z = 0; z < SIZE; z++) {
        const px = (x - SIZE / 2) * SPACING;
        const pz = (z - SIZE / 2) * SPACING;
        arr[i * 3 + 1] = Math.sin(px * 0.6 + t) * 0.5 + Math.cos(pz * 0.6 + t * 0.8) * 0.5;
        i++;
      }
    }
    pts.geometry.attributes.position.needsUpdate = true;
    pts.rotation.y = t * 0.05;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.06}
        vertexColors
        transparent
        opacity={0.85}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

export default function ParticleField() {
  return (
    <Canvas
      camera={{ position: [0, 7, 11], fov: 60 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
      style={{ pointerEvents: 'none' }}
    >
      <Waves />
    </Canvas>
  );
}
