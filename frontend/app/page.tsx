import { SignalCard, type Signal } from '@/components/SignalCard';

const demo: Signal = {
  asset: 'BTC/USDT',
  direction: 'BUY',
  entry: 64250,
  stopLoss: 62800,
  takeProfit: [66000, 68500, 71000],
  riskReward: 3.2,
  confidence: 82,
  timeframe: 'Swing (H4)',
  rationale: 'Cassure de résistance + sentiment positif + momentum haussier.',
};

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Quantum Trade AI</h1>
        <p className="mt-2 text-sm text-muted">
          Plateforme de trading augmentée par agents IA — Phase 0 (squelette)
        </p>
      </div>

      <SignalCard s={demo} />

      <p className="max-w-md text-center text-[11px] text-muted">
        ⚠️ Aide à la décision, pas un conseil en investissement. Le trading comporte un risque élevé
        de perte en capital. Les performances passées ne préjugent pas des résultats futurs.
      </p>
    </main>
  );
}
