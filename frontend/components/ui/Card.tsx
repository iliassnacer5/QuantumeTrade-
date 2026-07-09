import { cn } from '@/lib/cn';

type Variant = 'default' | 'glass' | 'elevated' | 'stat' | 'danger';

const VARIANTS: Record<Variant, string> = {
  default: 'border border-border bg-surface',
  glass: 'glass',
  elevated: 'border border-border bg-surface shadow-elevated',
  stat: 'border border-border bg-surface',
  danger: 'border border-sell/40 bg-sell/5',
};

export type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: Variant;
  /** Ajoute un léger « lift » au survol (cartes cliquables). */
  hover?: boolean;
  padded?: boolean;
};

export function Card({ variant = 'default', hover, padded = true, className, ...rest }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl',
        VARIANTS[variant],
        padded && 'p-4',
        hover && 'cursor-pointer transition hover:-translate-y-0.5 hover:border-border/80 hover:shadow-elevated',
        className,
      )}
      {...rest}
    />
  );
}
