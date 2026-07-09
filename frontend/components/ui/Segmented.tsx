'use client';

import { cn } from '@/lib/cn';

export type SegmentedOption<T extends string> = {
  value: T;
  label: React.ReactNode;
  title?: string;
};

export type SegmentedProps<T extends string> = {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  className?: string;
  'aria-label'?: string;
};

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  size = 'md',
  className,
  'aria-label': ariaLabel,
}: SegmentedProps<T>) {
  const pad = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm';
  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn('inline-flex rounded-lg border border-border bg-background p-0.5', className)}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            role="tab"
            aria-selected={active}
            title={o.title}
            onClick={() => onChange(o.value)}
            className={cn(
              'rounded-md font-medium transition',
              pad,
              active ? 'bg-accent text-background shadow-card' : 'text-muted hover:text-white',
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
