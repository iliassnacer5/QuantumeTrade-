'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { clearToken } from '@/lib/api';

const LINKS: { href: string; label: string; accent?: boolean }[] = [
  { href: '/today', label: '☀️ Ma journée', accent: true },
  { href: '/edge', label: '🗺️ Edge' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/daily', label: '★ Trades du jour', accent: true },
  { href: '/scanner', label: 'Scanner' },
  { href: '/copilot', label: 'Copilot' },
  { href: '/journal', label: 'Journal' },
  { href: '/strategies', label: 'Stratégies' },
  { href: '/backtest', label: 'Backtest' },
  { href: '/track-record', label: 'Track Record' },
  { href: '/agents', label: 'Agents' },
  { href: '/execution', label: 'Paper Trading' },
  { href: '/wallet', label: '💰 Portefeuille' },
  { href: '/copytrading', label: 'Copy' },
  { href: '/marketplace', label: 'Marketplace' },
  { href: '/branding', label: 'White-label' },
  { href: '/plans', label: 'Plans' },
  { href: '/settings', label: 'Paramètres' },
];

// Pages sans navbar (accueil + parcours d'authentification).
const HIDDEN = ['/', '/login', '/register', '/onboarding'];

export function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(typeof window !== 'undefined' && !!localStorage.getItem('qta_token'));
  }, [pathname]);

  if (HIDDEN.includes(pathname) || !authed) return null;

  function logout() {
    clearToken();
    router.push('/login');
  }

  return (
    <nav className="sticky top-0 z-50 flex flex-wrap items-center gap-1 border-b border-border bg-background/95 px-4 py-2 backdrop-blur">
      <span className="mr-2 font-bold text-white">Quantum<span className="text-accent">Trade</span></span>
      {LINKS.map((l) => {
        const active = pathname === l.href;
        return (
          <a
            key={l.href}
            href={l.href}
            className={`rounded-lg px-3 py-1 text-sm transition ${
              active
                ? 'bg-accent/20 text-white'
                : l.accent
                  ? 'text-buy hover:bg-buy/10'
                  : 'text-muted hover:bg-surface hover:text-white'
            }`}
          >
            {l.label}
          </a>
        );
      })}
      <button onClick={logout} className="ml-auto rounded-lg border border-border px-3 py-1 text-sm text-muted hover:bg-surface hover:text-white">
        Déconnexion
      </button>
    </nav>
  );
}
