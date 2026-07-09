'use client';

import { TIMEFRAMES } from '@/lib/markets';
import { Segmented } from '@/components/ui';

/**
 * Sélecteur de timeframe partagé. `by` choisit la clé de valeur :
 * - 'tf' → scalp/intraday/swing/position
 * - 'interval' → 5m/15m/1h/4h
 */
export function TimeframePicker({
  value,
  onChange,
  by = 'tf',
  size = 'sm',
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  by?: 'tf' | 'interval';
  size?: 'sm' | 'md';
  className?: string;
}) {
  return (
    <Segmented
      size={size}
      aria-label="Timeframe"
      className={className}
      value={value}
      onChange={onChange}
      options={TIMEFRAMES.map((t) => ({ value: t[by], label: t.label }))}
    />
  );
}
