import Link from 'next/link';
import { HeroBackground } from '@/components/marketing/HeroBackground';

const FEATURES = [
  { icon: '🧠', title: '8 agents experts', desc: 'Tendance, momentum, volume, smart-money, macro… un consensus, pas une boîte noire.' },
  { icon: '🗺️', title: 'Carte de l’edge', desc: 'Où gagne-t-on vraiment ? Chaque combo validé au walk-forward, frais inclus.' },
  { icon: '🛡️', title: 'Risque d’abord', desc: 'Position dimensionnée, garde-fous d’exposition, filtres de sévérité réglables.' },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <HeroBackground />

      <div className="relative z-10 flex min-h-screen flex-col">
        <nav className="flex items-center justify-between px-6 py-5">
          <span className="flex items-center gap-2 font-bold text-white">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-gradient text-sm text-background">Q</span>
            Quantum<span className="text-gradient">Trade</span>
          </span>
          <Link href="/login" className="rounded-lg border border-border px-4 py-1.5 text-sm text-muted transition hover:bg-surface hover:text-white">
            Se connecter
          </Link>
        </nav>

        <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface/60 px-3 py-1 text-2xs text-muted backdrop-blur">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-buy" />
            Analyse multi-marchés 24h/24 · crypto · forex · actions · or
          </span>
          <h1 className="max-w-3xl text-display text-white">
            Le trading augmenté par une <span className="text-gradient">équipe d’agents IA</span>
          </h1>
          <p className="mt-5 max-w-xl text-base text-muted">
            Des signaux fiables, explicables et dimensionnés selon votre risque. Prouvés au walk-forward,
            pas promis. Une aide à la décision — jamais un conseil.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/register"
              className="rounded-lg bg-brand-gradient px-6 py-3 font-semibold text-background shadow-glow transition hover:brightness-110"
            >
              Commencer gratuitement
            </Link>
            <Link href="/login" className="rounded-lg border border-border bg-surface/60 px-6 py-3 font-semibold text-white backdrop-blur transition hover:bg-surface">
              J’ai déjà un compte
            </Link>
          </div>

          <div className="mt-16 grid w-full max-w-4xl gap-4 sm:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass rounded-xl p-5 text-left">
                <div className="mb-2 text-2xl">{f.icon}</div>
                <h3 className="text-sm font-semibold text-white">{f.title}</h3>
                <p className="mt-1 text-xs text-muted">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 mx-auto max-w-md px-6 py-6 text-center text-2xs text-muted">
          ⚠️ Aide à la décision, pas un conseil en investissement. Le trading comporte un risque élevé
          de perte en capital. Les performances passées ne préjugent pas des résultats futurs.
        </p>
      </div>
    </main>
  );
}
