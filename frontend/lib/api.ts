'use client';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const WS = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000/ws';

export type Signal = {
  id?: string;
  asset: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2?: number;
  take_profit_3?: number;
  risk_reward: number;
  confidence: number;
  timeframe: string;
  rationale: string;
};

export type Candle = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

export type Me = {
  id: string;
  email: string;
  full_name?: string;
  risk_profile: string;
  capital: number;
  watchlist: string[];
  onboarded: boolean;
  plan: string;
};

function token(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('qta_token');
}

export function setToken(t: string) {
  localStorage.setItem('qta_token', t);
}

export function clearToken() {
  localStorage.removeItem('qta_token');
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(opts.headers as object) };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Erreur ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string) =>
    req<{ access_token: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    req<{ access_token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => req<Me>('/api/auth/me'),
  onboard: (risk_profile: string, capital: number, watchlist: string[]) =>
    req<Me>('/api/onboarding', { method: 'POST', body: JSON.stringify({ risk_profile, capital, watchlist }) }),
  listSignals: () => req<Signal[]>('/api/signals'),
  ohlcv: (asset: string, timeframe: string) =>
    req<Candle[]>(`/api/market/ohlcv?asset=${encodeURIComponent(asset)}&timeframe=${timeframe}`),
  generate: (asset: string, timeframe: string, notify = false) =>
    req<Signal>('/api/signals/generate', { method: 'POST', body: JSON.stringify({ asset, timeframe, notify }) }),
  plans: () => req<{ id: string; price: number; features: string[] }[]>('/api/billing/plans'),
  checkout: (plan: string) => req<Me>(`/api/billing/checkout/${plan}`, { method: 'POST' }),
};

export function openSignalStream(onSignal: (s: Signal) => void): WebSocket | null {
  const t = token();
  if (!t) return null;
  const ws = new WebSocket(`${WS}/signals?token=${t}`);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'signal') onSignal(msg.data as Signal);
    } catch {
      /* ignore */
    }
  };
  return ws;
}
