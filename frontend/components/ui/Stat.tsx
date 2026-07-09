'use client';

import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/cn';

/** Compteur animé (respecte prefers-reduced-motion). */
function useCountUp(target: number, duration = 600): number {
  const [value, setValue] = useState(target);
  const fromRef = useRef(target);

  useEffect(() => {
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const from = fromRef.current;
    if (reduce || from === target) {
      fromRef.current = target;
      setValue(target);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(from + (target - from) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);

  return value;
}

export type StatProps = {
  label: string;
  value: number | string;
  /** Formatte la valeur numérique animée (ex. USD, %). */
  format?: (n: number) => string;
  delta?: number;
  hint?: string;
  tone?: 'default' | 'buy' | 'sell';
  className?: string;
};

export function Stat({ label, value, format, delta, hint, tone = 'default', className }: StatProps) {
  const numeric = typeof value === 'number';
  const animated = useCountUp(numeric ? (value as number) : 0);
  const display = numeric ? (format ? format(animated) : Math.round(animated).toString()) : (value as string);

  const valueTone =
    tone === 'buy' ? 'text-buy' : tone === 'sell' ? 'text-sell' : 'text-white';

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <span className="text-2xs uppercase tracking-wide text-muted">{label}</span>
      <span className={cn('font-mono text-2xl font-bold tabular-nums', valueTone)}>{display}</span>
      <div className="flex items-center gap-2 text-2xs">
        {delta != null && (
          <span className={cn('font-medium', delta >= 0 ? 'text-buy' : 'text-sell')}>
            {delta >= 0 ? '▲' : '▼'} {Math.abs(delta)}%
          </span>
        )}
        {hint && <span className="text-muted">{hint}</span>}
      </div>
    </div>
  );
}
