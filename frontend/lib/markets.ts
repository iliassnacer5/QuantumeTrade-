/**
 * Source unique de vérité pour les marchés et timeframes.
 * Auparavant dupliquée dans 5+ pages (une liste crypto/forex/actions/or par page) — Phase F2.
 */
export type MarketClass = { id: string; label: string };

export const MARKET_CLASSES: MarketClass[] = [
  { id: '', label: 'Tous' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'forex', label: 'Forex' },
  { id: 'stock', label: 'Actions' },
  { id: 'commodity', label: '🥇 Or & Métaux' },
];

/** Marchés concrets (sans « Tous ») — pour les pages qui exigent un marché précis. */
export const MARKET_CLASSES_CONCRETE: MarketClass[] = MARKET_CLASSES.filter((c) => c.id);

/** Badge court par marché (listes, tableaux). */
export const MARKET_BADGE: Record<string, string> = {
  crypto: '₿ Crypto',
  forex: '💱 Forex',
  stock: '📈 Actions',
  commodity: '🥇 Or',
};

export type Timeframe = { tf: string; interval: string; label: string };

export const TIMEFRAMES: Timeframe[] = [
  { tf: 'scalp', interval: '5m', label: 'Scalp (5m)' },
  { tf: 'intraday', interval: '15m', label: 'Intraday (15m)' },
  { tf: 'swing', interval: '1h', label: 'Swing (1h)' },
  { tf: 'position', interval: '4h', label: 'Position (4h)' },
];
