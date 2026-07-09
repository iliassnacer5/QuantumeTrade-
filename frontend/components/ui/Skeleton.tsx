import { cn } from '@/lib/cn';

export type SkeletonProps = React.HTMLAttributes<HTMLDivElement> & {
  /** Nombre de lignes empilées (utilise `h-4` par défaut). */
  lines?: number;
};

export function Skeleton({ lines, className, ...rest }: SkeletonProps) {
  if (lines && lines > 1) {
    return (
      <div className="space-y-2" {...rest}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn('shimmer h-4 rounded', i === lines - 1 && 'w-2/3', className)}
          />
        ))}
      </div>
    );
  }
  return <div className={cn('shimmer h-4 rounded', className)} {...rest} />;
}

/** Carte-squelette prête à l'emploi pour les états de chargement. */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-xl border border-border bg-surface p-4', className)}>
      <Skeleton className="mb-3 h-3 w-1/3" />
      <Skeleton className="mb-2 h-7 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
