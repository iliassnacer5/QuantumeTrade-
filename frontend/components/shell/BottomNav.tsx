'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { NAV_GROUPS, MOBILE_PRIMARY } from './nav';
import { cn } from '@/lib/cn';

const ALL = NAV_GROUPS.flatMap((g) => g.items);
const PRIMARY = MOBILE_PRIMARY.map((href) => ALL.find((i) => i.href === href)!).filter(Boolean);

/** Navigation basse pour mobile (5 entrées prioritaires). */
export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-border bg-background/95 backdrop-blur-md lg:hidden">
      {PRIMARY.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-1 flex-col items-center gap-0.5 py-2 text-2xs',
              active ? 'text-accent' : 'text-muted',
            )}
          >
            <Icon size={18} />
            <span className="truncate">{item.label.split(' ')[0]}</span>
          </Link>
        );
      })}
    </nav>
  );
}
