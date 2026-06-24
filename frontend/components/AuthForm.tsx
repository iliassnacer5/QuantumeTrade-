'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { api, setToken } from '@/lib/api';

export function AuthForm({ mode }: { mode: 'login' | 'register' }) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isRegister = mode === 'register';

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = isRegister ? await api.register(email, password) : await api.login(email, password);
      setToken(res.access_token);
      const me = await api.me();
      router.push(me.onboarded ? '/dashboard' : '/onboarding');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border border-border bg-surface p-6">
      <h1 className="text-xl font-bold">{isRegister ? 'Créer un compte' : 'Connexion'}</h1>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
      />
      <input
        type="password"
        placeholder="Mot de passe (8+ caractères)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
        className="w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
      />
      {error && <p className="text-sm text-sell">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-accent py-2 font-semibold text-background hover:opacity-90 disabled:opacity-50"
      >
        {loading ? '...' : isRegister ? 'Créer mon compte' : 'Se connecter'}
      </button>
      <p className="text-center text-xs text-muted">
        {isRegister ? (
          <a href="/login" className="hover:text-white">
            Déjà un compte ? Se connecter
          </a>
        ) : (
          <a href="/register" className="hover:text-white">
            Pas de compte ? Créer un compte
          </a>
        )}
      </p>
    </form>
  );
}
