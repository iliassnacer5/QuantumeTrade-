'use client';

import { useEffect } from 'react';
import { Toaster, toast } from 'sonner';

/**
 * Toaster global (sonner) branché sur les erreurs API.
 * On ignore 401 (auth → redirect), 402 (plan → UpgradeGate) et 404 : gérés inline par les pages.
 * Déduplication : un même message n'est pas re-notifié dans une courte fenêtre.
 */
const SILENCED = new Set([401, 402, 404]);
const recent = new Map<string, number>();

export function ApiToaster() {
  useEffect(() => {
    const handler = (e: Event) => {
      const { message, status } = (e as CustomEvent<{ message: string; status: number }>).detail ?? {};
      if (!message || SILENCED.has(status)) return;
      const now = Date.now();
      const last = recent.get(message) ?? 0;
      if (now - last < 4000) return;
      recent.set(message, now);
      toast.error(message);
    };
    window.addEventListener('qta:api-error', handler);
    return () => window.removeEventListener('qta:api-error', handler);
  }, []);

  return (
    <Toaster
      position="bottom-right"
      theme="dark"
      toastOptions={{
        style: {
          background: '#1B222B',
          border: '1px solid #232A33',
          color: '#fff',
        },
      }}
    />
  );
}
