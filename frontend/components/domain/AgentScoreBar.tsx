import { cn } from '@/lib/cn';

/**
 * Score d'un agent (−1 → +1) en barre bipolaire centrée sur zéro.
 * Vert = haussier, rouge = baissier, neutre au centre.
 */
export function AgentScoreBar({
  name,
  score,
  className,
}: {
  name: string;
  score: number;
  className?: string;
}) {
  const clamped = Math.max(-1, Math.min(1, score));
  const width = Math.abs(clamped) * 50; // % depuis le centre
  const tone = clamped > 0.1 ? 'bg-buy' : clamped < -0.1 ? 'bg-sell' : 'bg-muted';
  const textTone = clamped > 0.1 ? 'text-buy' : clamped < -0.1 ? 'text-sell' : 'text-muted';
  return (
    <div className={cn('flex items-center gap-2 text-[11px]', className)}>
      <span className="w-20 shrink-0 truncate capitalize text-gray-400">{name}</span>
      <div className="relative h-1.5 flex-1 rounded-full bg-border">
        <span className="absolute left-1/2 top-0 h-full w-px bg-muted/40" />
        <span
          className={cn('absolute top-0 h-full rounded-full', tone)}
          style={
            clamped >= 0
              ? { left: '50%', width: `${width}%` }
              : { right: '50%', width: `${width}%` }
          }
        />
      </div>
      <span className={cn('w-10 shrink-0 text-right font-mono', textTone)}>
        {clamped >= 0 ? '+' : ''}
        {clamped.toFixed(2)}
      </span>
    </div>
  );
}
