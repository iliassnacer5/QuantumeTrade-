import type { Metadata } from 'next';
import './globals.css';
import { AppShell } from '@/components/shell/AppShell';
import { ApiToaster } from '@/components/shell/ApiToaster';

export const metadata: Metadata = {
  title: 'Quantum Trade AI',
  description: 'Plateforme de trading augmentée par agents IA — aide à la décision, pas un conseil en investissement.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className="min-h-screen">
        <AppShell>{children}</AppShell>
        <ApiToaster />
      </body>
    </html>
  );
}
