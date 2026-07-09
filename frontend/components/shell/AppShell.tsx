'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { BottomNav } from './BottomNav';
import { PageTransition } from './PageTransition';
import { CommandPalette } from './CommandPalette';
import { BARE_ROUTES } from './nav';
import { Disclaimer } from '@/components/Disclaimer';
import { api } from '@/lib/api';

/**
 * App shell : sidebar groupée + topbar + layout responsive.
 * Les pages « nues » (landing / auth) sont rendues sans chrome.
 * Le chrome n'apparaît qu'une fois authentifié (évite le flash sur les redirections /login).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [email, setEmail] = useState<string | undefined>();

  const bare = BARE_ROUTES.includes(pathname);

  useEffect(() => {
    if (bare) return;
    const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('qta_token');
    setAuthed(hasToken);
    if (hasToken) api.me().then((m) => setEmail(m.email)).catch(() => {});
  }, [pathname, bare]);

  // Ferme le drawer mobile à chaque navigation.
  useEffect(() => setMobileOpen(false), [pathname]);

  if (bare) return <>{children}</>;

  // Pas encore authentifié (ou en cours de redirection) : rendu nu, la page gère le redirect.
  if (!authed) {
    return <PageTransition key={pathname}>{children}</PageTransition>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMenu={() => setMobileOpen(true)} email={email} />
        <main className="flex-1 pb-16 lg:pb-0">
          <PageTransition key={pathname}>{children}</PageTransition>
        </main>
        <Disclaimer />
      </div>
      <BottomNav />
      <CommandPalette />
    </div>
  );
}
