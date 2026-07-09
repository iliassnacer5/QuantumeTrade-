'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Menu, Search, LogOut } from 'lucide-react';
import { api, clearToken } from '@/lib/api';
import { Segmented } from '@/components/ui';
import { cn } from '@/lib/cn';

const MODES = [
  { value: 'strict', label: '🛡️', title: 'Strict — moins de signaux, mieux filtrés' },
  { value: 'balanced', label: '⚖️', title: 'Équilibré' },
  { value: 'aggressive', label: '⚡', title: 'Agressif — plus de signaux, plus de bruit' },
] as const;

export function Topbar({ onOpenMenu, email }: { onOpenMenu: () => void; email?: string }) {
  const router = useRouter();
  const [mode, setMode] = useState<string>('strict');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{ symbol: string; asset_class: string }[]>([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.signalMode().then((d) => setMode(d.mode)).catch(() => {});
  }, []);

  // Recherche symbole (debounce léger).
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const t = setTimeout(() => {
      api.symbols(query).then((d) => setResults(d.results.slice(0, 8))).catch(() => setResults([]));
    }, 180);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  function changeMode(m: string) {
    setMode(m);
    api.setSignalMode(m).catch(() => {});
  }

  function pick(symbol: string) {
    setQuery('');
    setOpen(false);
    router.push(`/dashboard?symbol=${encodeURIComponent(symbol)}`);
  }

  function logout() {
    clearToken();
    router.push('/login');
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-md">
      <button
        onClick={onOpenMenu}
        className="rounded-lg p-1.5 text-muted hover:bg-surface hover:text-white lg:hidden"
        aria-label="Ouvrir le menu"
      >
        <Menu size={20} />
      </button>

      {/* Recherche symbole */}
      <div ref={boxRef} className="relative w-full max-w-xs">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5">
          <Search size={15} className="text-muted" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value.toUpperCase());
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && results[0]) pick(results[0].symbol);
            }}
            placeholder="Rechercher un symbole…"
            className="w-full bg-transparent text-sm outline-none placeholder:text-muted"
            aria-label="Rechercher un symbole"
          />
        </div>
        {open && results.length > 0 && (
          <ul className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-border bg-elevated shadow-elevated">
            {results.map((r) => (
              <li key={r.symbol}>
                <button
                  onClick={() => pick(r.symbol)}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-surface"
                >
                  <span className="font-mono text-white">{r.symbol}</span>
                  <span className="text-2xs uppercase text-muted">{r.asset_class}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="ml-auto flex items-center gap-3">
        <div className="hidden items-center gap-1.5 sm:flex">
          <span className="text-2xs text-muted">Sévérité</span>
          <Segmented
            size="sm"
            aria-label="Mode de sévérité des filtres"
            options={MODES.map((m) => ({ value: m.value, label: m.label, title: m.title }))}
            value={mode as (typeof MODES)[number]['value']}
            onChange={changeMode}
          />
        </div>

        <span
          className="hidden items-center gap-1.5 rounded-full border border-buy/40 bg-buy-soft px-2.5 py-1 text-2xs font-medium text-buy md:inline-flex"
          title="Flux de données de marché actif"
        >
          <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-buy" />
          LIVE
        </span>

        <div className="flex items-center gap-2">
          {email && (
            <span
              className={cn(
                'hidden max-w-[10rem] truncate text-2xs text-muted xl:inline',
              )}
              title={email}
            >
              {email}
            </span>
          )}
          <button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs text-muted transition hover:bg-surface hover:text-white"
          >
            <LogOut size={14} />
            <span className="hidden sm:inline">Déconnexion</span>
          </button>
        </div>
      </div>
    </header>
  );
}
