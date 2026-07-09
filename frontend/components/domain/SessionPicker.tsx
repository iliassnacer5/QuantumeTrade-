'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { cn } from '@/lib/cn';

export type SessionInfo = { id: string; label: string; window_utc: string; open: boolean };

/**
 * Sélecteur de session de marché (Asie/Londres/New York…). Charge les sessions lui-même.
 * Remplace la logique dupliquée dans 4 pages.
 */
export function SessionPicker({
  value,
  onChange,
  label = 'Session',
  className,
}: {
  value: string;
  onChange: (id: string) => void;
  label?: string | null;
  className?: string;
}) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);

  useEffect(() => {
    api.sessions().then((d) => setSessions(d.sessions)).catch(() => {});
  }, []);

  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)}>
      {label && <span className="mr-1 text-xs text-muted">{label} :</span>}
      <button
        onClick={() => onChange('')}
        className={cn(
          'rounded-lg border px-2.5 py-1 text-xs transition',
          value === '' ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface',
        )}
      >
        Toutes
      </button>
      {sessions.map((s) => (
        <button
          key={s.id}
          onClick={() => onChange(s.id)}
          className={cn(
            'rounded-lg border px-2.5 py-1 text-xs transition',
            value === s.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface',
          )}
        >
          <span className={cn('mr-1 inline-block h-1.5 w-1.5 rounded-full', s.open ? 'bg-buy' : 'bg-muted/40')} />
          {s.label.split(' ')[0]}
        </button>
      ))}
    </div>
  );
}
