import { cn } from '@/lib/cn';

type Tone = 'neutral' | 'accent' | 'buy' | 'sell' | 'warn' | 'muted';

const TONES: Record<Tone, string> = {
  neutral: 'border border-border bg-surface text-white',
  accent: 'border border-accent/40 bg-accent/10 text-accent',
  buy: 'border border-buy/40 bg-buy-soft text-buy',
  sell: 'border border-sell/40 bg-sell-soft text-sell',
  warn: 'border border-warn/40 bg-warn-soft text-warn',
  muted: 'border border-border bg-background text-muted',
};

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: Tone;
  dot?: boolean;
};

export function Badge({ tone = 'neutral', dot, className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-2xs font-medium',
        TONES[tone],
        className,
      )}
      {...rest}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
