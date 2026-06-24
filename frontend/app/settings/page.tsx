'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { api, type Settings } from '@/lib/api';

export default function SettingsPage() {
  const router = useRouter();
  const [s, setS] = useState<Settings | null>(null);
  const [msg, setMsg] = useState('');
  const [plans, setPlans] = useState<{ id: string; price: number; features: string[] }[]>([]);
  const [mfaSecret, setMfaSecret] = useState('');
  const [mfaUri, setMfaUri] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  const load = useCallback(async () => {
    try {
      const [settings, pl] = await Promise.all([api.getSettings(), api.plans()]);
      setS(settings);
      setPlans(pl);
    } catch {
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  async function save(patch: Partial<Settings>) {
    setMsg('');
    try {
      const updated = await api.updateSettings(patch);
      setS(updated);
      setMsg('Enregistré ✓');
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Erreur');
    }
  }

  async function upgrade(plan: string) {
    const r = await api.checkout(plan);
    if (r.mode === 'stripe' && r.checkout_url) {
      window.location.href = r.checkout_url; // redirection Stripe Checkout
    } else {
      setMsg(`Plan changé : ${r.user?.plan ?? plan}`);
    }
  }

  async function setupMfa() {
    const r = await api.mfaSetup();
    setMfaSecret(r.secret);
    setMfaUri(r.otpauth_uri);
  }

  async function enableMfa() {
    await api.mfaEnable(mfaCode);
    setMfaSecret('');
    setMfaCode('');
    await load();
    setMsg('MFA activée ✓');
  }

  if (!s) return <main className="p-8 text-muted">Chargement…</main>;

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Paramètres</h1>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
          ← Dashboard
        </a>
      </header>
      {msg && <p className="text-sm text-accent">{msg}</p>}

      {/* Watchlist */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 font-semibold">Marchés suivis</h2>
        <input
          defaultValue={s.watchlist.join(', ')}
          onBlur={(e) => save({ watchlist: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) })}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono"
        />
      </section>

      {/* Risque */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 font-semibold">Règles de risque</h2>
        <div className="grid grid-cols-3 gap-3 text-sm">
          <label>
            Exposition max %
            <input
              type="number"
              defaultValue={s.max_exposure_pct}
              onBlur={(e) => save({ max_exposure_pct: Number(e.target.value) })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-2 py-1"
            />
          </label>
          <label>
            Signaux / jour max
            <input
              type="number"
              defaultValue={s.max_daily_signals}
              onBlur={(e) => save({ max_daily_signals: Number(e.target.value) })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-2 py-1"
            />
          </label>
          <label>
            Perte jour. max %
            <input
              type="number"
              defaultValue={s.daily_loss_limit_pct}
              onBlur={(e) => save({ daily_loss_limit_pct: Number(e.target.value) })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-2 py-1"
            />
          </label>
        </div>
      </section>

      {/* Alertes */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 font-semibold">Préférences d&apos;alerte</h2>
        <label className="mb-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={!!s.daily_digest} onChange={(e) => save({ daily_digest: e.target.checked })} />
          ★ Recevoir les « Trades du jour » chaque matin (digest automatique)
        </label>
        <label className="mb-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={s.alert_email} onChange={(e) => save({ alert_email: e.target.checked })} />
          Email
        </label>
        <label className="mb-2 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={s.alert_telegram} onChange={(e) => save({ alert_telegram: e.target.checked })} />
          Telegram
        </label>
        <input
          placeholder="Telegram chat ID"
          defaultValue={s.telegram_chat_id ?? ''}
          onBlur={(e) => save({ telegram_chat_id: e.target.value })}
          className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono"
        />
      </section>

      {/* MFA */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 font-semibold">Sécurité — MFA (TOTP)</h2>
        {s.mfa_enabled ? (
          <div className="flex items-center justify-between">
            <span className="text-buy">● Activée</span>
            <button onClick={() => api.mfaDisable().then(load)} className="rounded-lg border border-border px-3 py-1 text-sm">
              Désactiver
            </button>
          </div>
        ) : mfaSecret ? (
          <div className="space-y-2 text-sm">
            <p className="text-muted">
              Ajoutez ce secret dans votre app (Google Authenticator) :{' '}
              <code className="text-white">{mfaSecret}</code>
            </p>
            <p className="break-all text-xs text-muted">{mfaUri}</p>
            <div className="flex gap-2">
              <input
                placeholder="Code à 6 chiffres"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                className="rounded-lg border border-border bg-background px-3 py-2 font-mono"
              />
              <button onClick={enableMfa} className="rounded-lg bg-accent px-4 py-2 font-semibold text-background">
                Activer
              </button>
            </div>
          </div>
        ) : (
          <button onClick={setupMfa} className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
            Configurer la MFA
          </button>
        )}
      </section>

      {/* Abonnement */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 font-semibold">Abonnement</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {plans.map((p) => (
            <button
              key={p.id}
              onClick={() => upgrade(p.id)}
              className="rounded-lg border border-border p-3 text-left text-xs hover:border-accent"
            >
              <div className="font-semibold uppercase">{p.id}</div>
              <div className="text-accent">{p.price} $/mois</div>
              <div className="mt-1 text-muted">{p.features.join(' · ')}</div>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
