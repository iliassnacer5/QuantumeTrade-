import type { Metadata } from 'next';
import './globals.css';
import { NavBar } from '@/components/NavBar';
import { Disclaimer } from '@/components/Disclaimer';

export const metadata: Metadata = {
  title: 'Quantum Trade AI',
  description: 'Plateforme de trading augmentée par agents IA — aide à la décision, pas un conseil en investissement.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className="flex min-h-screen flex-col">
        <NavBar />
        <div className="flex-1">{children}</div>
        <Disclaimer />
      </body>
    </html>
  );
}
