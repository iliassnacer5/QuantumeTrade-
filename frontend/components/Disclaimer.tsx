'use client';

// Avertissement risque omniprésent (exigence conformité : « éditeur d'outils », pas conseiller).
// Affiché en bas de chaque page, discret mais toujours visible.
export function Disclaimer() {
  return (
    <footer className="mt-8 border-t border-border bg-background/95 px-4 py-2 text-center text-[11px] text-muted">
      ⚠️ Le trading comporte un risque élevé de perte. Quantum Trade AI fournit une <b>aide à la décision</b>,
      pas un conseil en investissement. Les performances passées ne préjugent pas des résultats futurs.{' '}
      <a href="/track-record" className="underline hover:text-white">Voir la validation</a>.
    </footer>
  );
}
