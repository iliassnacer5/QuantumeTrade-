import { cn } from '@/lib/cn';

/**
 * Table pro : header sticky, scroll horizontal encapsulé (le body ne déborde jamais).
 * Composants légers ; la logique de tri reste au consommateur.
 */
export function Table({ className, children, ...rest }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border">
      <table className={cn('w-full border-collapse text-sm', className)} {...rest}>
        {children}
      </table>
    </div>
  );
}

export function THead({ className, children, ...rest }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn('sticky top-0 z-10 bg-elevated text-2xs uppercase tracking-wide text-muted', className)}
      {...rest}
    >
      {children}
    </thead>
  );
}

export function TR({ className, ...rest }: React.HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn('border-b border-border/60 last:border-0', className)} {...rest} />;
}

export function TH({ className, ...rest }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return <th className={cn('whitespace-nowrap px-3 py-2 text-left font-medium', className)} {...rest} />;
}

export function TD({ className, ...rest }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn('whitespace-nowrap px-3 py-2.5', className)} {...rest} />;
}

export function TBody({ children, ...rest }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className="[&>tr:hover]:bg-surface/60" {...rest}>
      {children}
    </tbody>
  );
}
