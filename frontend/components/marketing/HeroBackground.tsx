'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// 3D chargée uniquement côté client, jamais en SSR (bundle isolé de la landing/login).
const ParticleField = dynamic(() => import('./ParticleField'), { ssr: false });

/**
 * Fond héro : nappe de particules WebGL, avec repli statique (dégradé) tant que le
 * canvas n'est pas prêt, sur mobile étroit, ou si prefers-reduced-motion est actif.
 */
export function HeroBackground() {
  const [enable3D, setEnable3D] = useState(false);

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const wideEnough = window.innerWidth >= 768;
    setEnable3D(!reduce && wideEnough);
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Repli statique : toujours présent en fond. */}
      <div className="absolute inset-0 bg-brand-radial" />
      <div className="absolute -left-1/4 top-1/3 h-[40rem] w-[40rem] rounded-full bg-accent/10 blur-[120px]" />
      <div className="absolute -right-1/4 top-0 h-[36rem] w-[36rem] rounded-full bg-cyan/10 blur-[120px]" />
      {enable3D && (
        <div className="absolute inset-0 opacity-70">
          <ParticleField />
        </div>
      )}
      {/* Fondu vers le bas pour la lisibilité du contenu. */}
      <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
}
