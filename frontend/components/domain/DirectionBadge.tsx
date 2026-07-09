import { cn } from '@/lib/cn';

export type Direction = 'BUY' | 'SELL' | 'HOLD' | string;

/** Badge directionnel unifié (BUY vert / SELL rouge / HOLD neutre). */
export function DirectionBadge({
  direction,
  size = 'md',
  className,
}: {
  direction: Direction;
  size?: 'sm' | 'md';
  className?: string;
}) {
  const tone =
    direction === 'BUY'
      ? 'bg-buy-soft text-buy'
      : direction === 'SELL'
        ? 'bg-sell-soft text-sell'
        : 'bg-border text-muted';
  const pad = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';
  return (
    <span className={cn('rounded-md font-bold', pad, tone, className)}>{direction}</span>
  );
}
