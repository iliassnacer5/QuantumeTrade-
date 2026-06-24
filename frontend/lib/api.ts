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

export type Settings = {
  watchlist: string[];
  max_exposure_pct: number;
  max_daily_signals: number;
  daily_loss_limit_pct: number;
  alert_email: boolean;
  alert_telegram: boolean;
  telegram_chat_id: string | null;
  mfa_enabled: boolean;
};

export type RiskStatus = {
  capital: number;
  exposure_value: number;
  exposure_pct: number;
  max_exposure_pct: number;
  daily_signals: number;
  max_daily_signals: number;
  breaches: string[];
  ok: boolean;
};

export type Position = {
  id?: string;
  asset: string;
  direction: string;
  entry: number;
  current_price: number | null;
  size: number;
  value: number;
  pnl: number;
};

export type Portfolio = {
  total_pnl: number;
  total_value: number;
  pnl_pct: number;
  positions: Position[];
};

export type HeatmapItem = { symbol: string; price: number; change_pct: number };

export type BacktestConfig = {
  symbol: string;
  timeframe: string;
  start_time: string;
  end_time: string;
  initial_capital: number;
  risk_per_trade_pct: number;
  use_llm?: boolean;
};

export type BacktestMetrics = {
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  total_pnl: number;
  total_pnl_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
};

export type BacktestReport = {
  id: string;
  config: BacktestConfig;
  metrics: BacktestMetrics;
  trades: any[];
  equity_curve: any[];
  created_at: string;
};

export type AgentInfo = { name: string; role: string; desc: string; model: string };

export type AgentStatus = {
  status: string;
  llm_enabled: boolean;
  providers: { anthropic: boolean; google: boolean };
  agents: AgentInfo[];
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
  checkout: (plan: string) =>
    req<{ mode: string; checkout_url?: string; user?: Me }>(`/api/billing/checkout/${plan}`, {
      method: 'POST',
    }),
  getSettings: () => req<Settings>('/api/settings'),
  updateSettings: (patch: Partial<Settings>) =>
    req<Settings>('/api/settings', { method: 'PATCH', body: JSON.stringify(patch) }),
  riskStatus: () => req<RiskStatus>('/api/risk/status'),
  portfolio: () => req<Portfolio>('/api/portfolio'),
  heatmap: () => req<HeatmapItem[]>('/api/market/heatmap'),
  mfaSetup: () => req<{ secret: string; otpauth_uri: string }>('/api/auth/mfa/setup', { method: 'POST' }),
  mfaEnable: (code: string) => req<Me>('/api/auth/mfa/enable', { method: 'POST', body: JSON.stringify({ code }) }),
  mfaDisable: () => req<Me>('/api/auth/mfa/disable', { method: 'POST' }),
  runBacktest: (config: BacktestConfig) => req<BacktestReport>('/api/backtest/run', { method: 'POST', body: JSON.stringify(config) }),
  listBacktests: () => req<BacktestReport[]>('/api/backtest/reports'),
  agentsStatus: () => req<AgentStatus>('/api/agents/status'),
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
