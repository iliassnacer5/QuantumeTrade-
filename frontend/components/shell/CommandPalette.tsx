'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import { Search, CornerDownLeft } from 'lucide-react';
import { NAV_GROUPS } from './nav';
import { api } from '@/lib/api';

/**
 * Palette de commandes ⌘K / Ctrl+K : navigation, recherche de symbole, actions rapides.
 * Montée globalement dans l'app shell (utilisateur authentifié).
 */
export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [symbols, setSymbols] = useState<{ symbol: string; asset_class: string }[]>([]);

  // Raccourci clavier global.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  // Recherche de symboles (debounce).
  useEffect(() => {
    if (!query.trim()) {
      setSymbols([]);
      return;
    }
    const t = setTimeout(() => {
      api.symbols(query).then((d) => setSymbols(d.results.slice(0, 6))).catch(() => setSymbols([]));
    }, 160);
    return () => clearTimeout(t);
  }, [query]);

  function go(href: string) {
    setOpen(false);
    setQuery('');
    router.push(href);
  }

  const QUICK = [
    { label: 'Générer un signal', href: '/dashboard', hint: 'Dashboard' },
    { label: 'Voir les trades du jour', href: '/daily', hint: 'Daily' },
    { label: 'Ouvrir le Copilot', href: '/copilot', hint: 'Copilot' },
    { label: 'Consulter la carte de l’edge', href: '/edge', hint: 'Edge' },
  ];

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Palette de commandes"
      className="fixed inset-0 z-[100] flex items-start justify-center p-4 pt-[12vh]"
      shouldFilter={false}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} />

      <div className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-border bg-elevated shadow-elevated">
        <div className="flex items-center gap-2 border-b border-border px-4">
          <Search size={16} className="text-muted" />
          <Command.Input
            value={query}
            onValueChange={setQuery}
            placeholder="Aller à une page, chercher un symbole…"
            className="h-12 w-full bg-transparent text-sm text-white outline-none placeholder:text-muted"
          />
          <kbd className="hidden rounded border border-border px-1.5 py-0.5 text-2xs text-muted sm:block">ESC</kbd>
        </div>

        <Command.List className="max-h-[50vh] overflow-y-auto p-2">
          <Command.Empty className="px-3 py-6 text-center text-sm text-muted">
            Aucun résultat.
          </Command.Empty>

          {symbols.length > 0 && (
            <Command.Group heading="Symboles" className="px-1 text-2xs uppercase tracking-wide text-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5">
              {symbols.map((s) => (
                <Item key={s.symbol} onSelect={() => go(`/dashboard?symbol=${encodeURIComponent(s.symbol)}`)}>
                  <span className="font-mono text-white">{s.symbol}</span>
                  <span className="ml-auto text-2xs uppercase text-muted">{s.asset_class}</span>
                </Item>
              ))}
            </Command.Group>
          )}

          <Command.Group heading="Actions rapides" className="px-1 text-2xs uppercase tracking-wide text-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5">
            {QUICK.map((a) => (
              <Item key={a.label} onSelect={() => go(a.href)}>
                <span className="text-white">{a.label}</span>
                <span className="ml-auto text-2xs text-muted">{a.hint}</span>
              </Item>
            ))}
          </Command.Group>

          {NAV_GROUPS.map((group) => (
            <Command.Group
              key={group.title}
              heading={group.title}
              className="px-1 text-2xs uppercase tracking-wide text-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <Item key={item.href} onSelect={() => go(item.href)}>
                    <Icon size={15} className="text-muted" />
                    <span className="text-white">{item.label}</span>
                  </Item>
                );
              })}
            </Command.Group>
          ))}
        </Command.List>

        <div className="flex items-center gap-3 border-t border-border px-4 py-2 text-2xs text-muted">
          <span className="flex items-center gap-1"><CornerDownLeft size={11} /> ouvrir</span>
          <span>⌘K / Ctrl+K pour rouvrir</span>
        </div>
      </div>
    </Command.Dialog>
  );
}

function Item({ children, onSelect }: { children: React.ReactNode; onSelect: () => void }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm aria-selected:bg-surface data-[selected=true]:bg-surface"
    >
      {children}
    </Command.Item>
  );
}
