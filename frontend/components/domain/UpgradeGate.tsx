'use client';

import { Lock } from 'lucide-react';
import { Card, Button } from '@/components/ui';
import { cn } from '@/lib/cn';

/**
 * Barrière d'upgrade unifiée (erreur 402 / fonctionnalité réservée à un plan).
 * Remplace les messages « réservé au plan Pro » copiés-collés dans 6 pages.
 */
export function UpgradeGate({
  feature,
  plan = 'Pro',
  description,
  className,
}: {
  feature: string;
  plan?: string;
  description?: string;
  className?: string;
}) {
  return (
    <Card variant="glass" className={cn('flex flex-col items-center gap-3 py-8 text-center', className)}>
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent">
        <Lock size={20} />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-white">
          {feature} — réservé au plan <span className="text-gradient">{plan}</span>
        </h3>
        <p className="mx-auto mt-1 max-w-sm text-xs text-muted">
          {description ?? 'Passez à un plan supérieur pour débloquer cette fonctionnalité.'}
        </p>
      </div>
      <a href="/plans">
        <Button size="sm">Voir les plans →</Button>
      </a>
    </Card>
  );
}

/** Détecte une erreur de type 402 (plan) à partir d'un message ou d'un statut. */
export function isPlanError(err: unknown): boolean {
  if (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 402) {
    return true;
  }
  const msg = err instanceof Error ? err.message : String(err ?? '');
  return msg.includes('402') || /plan|réservé/i.test(msg);
}
