'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { X } from 'lucide-react';
import { NAV_GROUPS } from './nav';
import { cn } from '@/lib/cn';

export function Sidebar({
  mobileOpen,
  onClose,
}: {
  mobileOpen: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();

  const content = (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center justify-between px-4">
        <Link href="/today" className="flex items-center gap-2 font-bold text-white" onClick={onClose}>
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-gradient text-sm text-background">
            Q
          </span>
          Quantum<span className="text-gradient">Trade</span>
        </Link>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-muted hover:bg-surface hover:text-white lg:hidden"
          aria-label="Fermer le menu"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.title}>
            <div className="px-2 pb-1 text-2xs font-semibold uppercase tracking-wider text-muted/70">
              {group.title}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition',
                      active
                        ? 'bg-accent/15 font-medium text-white'
                        : 'text-muted hover:bg-surface hover:text-white',
                    )}
                  >
                    <Icon
                      size={17}
                      className={cn(
                        active ? 'text-accent' : item.accent ? 'text-buy' : 'text-muted group-hover:text-white',
                      )}
                    />
                    <span className="truncate">{item.label}</span>
                    {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" />}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-border px-4 py-3 text-2xs text-muted">
        Aide à la décision — pas un conseil.
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop : rail fixe */}
      <aside className="hidden w-60 shrink-0 border-r border-border bg-background/60 lg:block">
        <div className="sticky top-0 h-screen">{content}</div>
      </aside>

      {/* Mobile : drawer + overlay */}
      <div className={cn('fixed inset-0 z-50 lg:hidden', mobileOpen ? 'pointer-events-auto' : 'pointer-events-none')}>
        <div
          className={cn(
            'absolute inset-0 bg-black/60 transition-opacity',
            mobileOpen ? 'opacity-100' : 'opacity-0',
          )}
          onClick={onClose}
        />
        <aside
          className={cn(
            'absolute left-0 top-0 h-full w-64 border-r border-border bg-background shadow-elevated transition-transform',
            mobileOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          {content}
        </aside>
      </div>
    </>
  );
}
