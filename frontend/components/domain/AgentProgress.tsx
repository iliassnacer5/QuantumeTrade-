'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/cn';

const AGENTS = ['Tendance', 'Momentum', 'Volume', 'Smart-money', 'Volatilité', 'Sentiment', 'Macro', 'Master'];

/**
 * Progression visuelle de l'analyse : les 8 agents « s'allument » l'un après l'autre
 * pendant qu'un signal se génère. Purement décoratif (rythme la latence perçue).
 */
export function AgentProgress({ active, className }: { active: boolean; className?: string }) {
  const [lit, setLit] = useState(0);

  useEffect(() => {
    if (!active) {
      setLit(0);
      return;
    }
    setLit(1);
    const id = setInterval(() => setLit((n) => (n >= AGENTS.length ? AGENTS.length : n + 1)), 320);
    return () => clearInterval(id);
  }, [active]);

  if (!active) return null;

  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)}>
      <span className="text-2xs text-muted">Analyse :</span>
      {AGENTS.map((a, i) => {
        const on = i < lit;
        return (
          <span
            key={a}
            className={cn(
              'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-2xs transition-all duration-300',
              on ? 'border-accent/50 bg-accent/10 text-accent' : 'border-border text-muted/50',
            )}
          >
            <span className={cn('h-1.5 w-1.5 rounded-full', on ? 'bg-accent' : 'bg-muted/30')} />
            {a}
          </span>
        );
      })}
    </div>
  );
}
