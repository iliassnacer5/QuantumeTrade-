import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold">Quantum Trade AI</h1>
        <p className="mt-3 text-muted">
          Une équipe d&apos;agents IA experts analyse les marchés 24h/24 et génère des signaux
          fiables, explicables et dimensionnés selon votre risque.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/register"
            className="rounded-lg bg-accent px-6 py-3 font-semibold text-background hover:opacity-90"
          >
            Commencer
          </Link>
          <Link href="/login" className="rounded-lg border border-border px-6 py-3 hover:bg-surface">
            Se connecter
          </Link>
        </div>
      </div>

      <p className="max-w-md text-center text-[11px] text-muted">
        ⚠️ Aide à la décision, pas un conseil en investissement. Le trading comporte un risque élevé
        de perte en capital. Les performances passées ne préjugent pas des résultats futurs.
      </p>
    </main>
  );
}
