import { cn } from '@/lib/cn';

export type PageHeaderProps = {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
};

export function PageHeader({ title, subtitle, icon, actions, className }: PageHeaderProps) {
  return (
    <header className={cn('mb-6 flex flex-wrap items-start justify-between gap-3', className)}>
      <div className="flex items-start gap-3">
        {icon && <div className="mt-0.5 text-accent">{icon}</div>}
        <div>
          <h1 className="text-h1 text-white">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
