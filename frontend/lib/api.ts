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
  metrics?: Record<string, any>;
  consensus_pct?: number;
  mtf?: { aligned: number; total: number; details: Record<string, string> };
  high_conviction?: boolean;
  agents?: { name: string; score: number; confidence: number; rationale: string }[];
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
  push_enabled?: boolean;
  locale?: string;
  mfa_enabled: boolean;
};

export type Branding = { brand_name: string; primary_color: string; logo_url: string; custom_domain?: string; tenant_id?: string };

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

export type HeatmapItem = { symbol: string; price: number; change_pct: number; asset_class?: string };

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

export type PlanInfo = {
  plan: string;
  features: Record<string, boolean>;
  feature_requirements: Record<string, string>;
};

export type JournalEntry = {
  id: string;
  signal_id?: string | null;
  symbol: string;
  direction: string;
  outcome: string; // open | win | loss | breakeven
  pnl?: number | null;
  agent_scores?: Record<string, number>;
  created_at?: string | null;
};

export type JournalInsights = {
  stats: {
    total_entries: number;
    closed: number;
    open: number;
    wins: number;
    losses: number;
    win_rate: number;
    total_pnl: number;
  };
  weight_multipliers: Record<string, number>;
};

export type TeamMember = { id: string; email: string; full_name?: string | null; role: string; onboarded: boolean };

export type BrokerConn = { id: string; broker: string; mode: string; key_hint: string; created_at?: string };
export type Order = { id: string; broker: string; mode: string; symbol: string; side: string; qty: number; status: string; filled_price: number | null; copied_from?: string };
export type Trader = { tenant_id: string; display_name: string; win_rate: number; total_pnl: number; closed_trades: number };
export type CopyFollow = { id: string; leader_tenant: string; allocation_pct: number; max_per_trade: number; min_confidence: number; active: boolean };
export type Listing = { id: string; title: string; kind: string; price: number; description: string; seller_tenant: string; created_at?: string };
export type ApiKey = { id: string; label: string; prefix: string; active: boolean; created_at?: string };

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
  symbols: (q?: string, asset_class?: string) => {
    const p = new URLSearchParams();
    if (q) p.set('q', q);
    if (asset_class) p.set('asset_class', asset_class);
    return req<{ results: { symbol: string; asset_class: string; label: string }[]; classes: string[] }>(`/api/market/symbols?${p}`);
  },
  scan: (asset_class?: string, timeframe = '1h', limit = 20, high_conviction_only = false) =>
    req<{ count: number; high_conviction: number; results: any[] }>(
      `/api/signals/scan?${new URLSearchParams({
        ...(asset_class ? { asset_class } : {}),
        timeframe,
        limit: String(limit),
        high_conviction_only: String(high_conviction_only),
      })}`,
    ),
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
  heatmap: (mix = false) => req<HeatmapItem[]>(`/api/market/heatmap${mix ? '?mix=true' : ''}`),
  mfaSetup: () => req<{ secret: string; otpauth_uri: string }>('/api/auth/mfa/setup', { method: 'POST' }),
  mfaEnable: (code: string) => req<Me>('/api/auth/mfa/enable', { method: 'POST', body: JSON.stringify({ code }) }),
  mfaDisable: () => req<Me>('/api/auth/mfa/disable', { method: 'POST' }),
  runBacktest: (config: BacktestConfig) => req<BacktestReport>('/api/backtest/run', { method: 'POST', body: JSON.stringify(config) }),
  listBacktests: () => req<BacktestReport[]>('/api/backtest/reports'),
  agentsStatus: () => req<AgentStatus>('/api/agents/status'),
  // Phase 3
  myPlan: () => req<PlanInfo>('/api/plan'),
  upgrade: (plan: string) => req<{ mode: string; checkout_url?: string }>(`/api/billing/checkout/${plan}`, { method: 'POST' }),
  copilotAsk: (asset: string, message: string) =>
    req<{ asset: string; answer: string }>('/api/copilot/ask', { method: 'POST', body: JSON.stringify({ asset, message }) }),
  journalList: () => req<JournalEntry[]>('/api/journal'),
  journalInsights: () => req<JournalInsights>('/api/journal/insights'),
  journalClose: (id: string, outcome: string, pnl: number | null) =>
    req<JournalEntry>(`/api/journal/${id}/close`, { method: 'POST', body: JSON.stringify({ outcome, pnl }) }),
  journalExplain: (id: string) =>
    req<{ id: string; explanation: string }>(`/api/journal/${id}/explain`, { method: 'POST' }),
  team: () => req<{ plan: string; members: TeamMember[] }>('/api/team'),
  teamInvite: (email: string, full_name?: string) =>
    req<{ member: TeamMember; temp_password: string }>('/api/team/invite', { method: 'POST', body: JSON.stringify({ email, full_name }) }),
  // Phase 4 — Exécution broker + KYC
  kycStatus: () => req<{ status: string }>('/api/kyc'),
  kycSubmit: (legal_name: string, country: string, doc_id: string) =>
    req<{ status: string }>('/api/kyc', { method: 'POST', body: JSON.stringify({ legal_name, country, doc_id }) }),
  brokers: () => req<BrokerConn[]>('/api/execution/brokers'),
  connectBroker: (broker: string, mode: string, api_key = '', api_secret = '') =>
    req<BrokerConn>('/api/execution/brokers', { method: 'POST', body: JSON.stringify({ broker, mode, api_key, api_secret }) }),
  revokeBroker: (id: string) => req<{ revoked: boolean }>(`/api/execution/brokers/${id}`, { method: 'DELETE' }),
  placeOrder: (conn_id: string, symbol: string, side: string, qty: number) =>
    req<Order>('/api/execution/orders', { method: 'POST', body: JSON.stringify({ conn_id, symbol, side, qty }) }),
  orders: () => req<Order[]>('/api/execution/orders'),
  // Phase 4 — Copy-trading
  leaderboard: () => req<Trader[]>('/api/copytrading/leaderboard'),
  publishProfile: (display_name: string) => req<unknown>('/api/copytrading/publish', { method: 'POST', body: JSON.stringify({ display_name }) }),
  following: () => req<CopyFollow[]>('/api/copytrading/following'),
  follow: (leader_tenant: string, allocation_pct: number, max_per_trade: number, min_confidence: number) =>
    req<CopyFollow>('/api/copytrading/follow', { method: 'POST', body: JSON.stringify({ leader_tenant, allocation_pct, max_per_trade, min_confidence }) }),
  unfollow: (id: string) => req<{ unfollowed: boolean }>(`/api/copytrading/follow/${id}`, { method: 'DELETE' }),
  commissions: () => req<{ total: number; count: number; items: any[] }>('/api/copytrading/commissions'),
  // Phase 4 — Marketplace
  listings: () => req<Listing[]>('/api/marketplace/listings'),
  createListing: (l: { title: string; kind: string; price: number; description: string; config: any }) =>
    req<Listing>('/api/marketplace/listings', { method: 'POST', body: JSON.stringify(l) }),
  buyListing: (id: string) => req<{ purchase_id: string; config: any }>(`/api/marketplace/listings/${id}/buy`, { method: 'POST' }),
  purchases: () => req<any[]>('/api/marketplace/purchases'),
  apiKeys: () => req<ApiKey[]>('/api/marketplace/api-keys'),
  createApiKey: (label: string) => req<{ id: string; api_key: string; prefix: string }>('/api/marketplace/api-keys', { method: 'POST', body: JSON.stringify({ label }) }),
  revokeApiKey: (id: string) => req<{ revoked: boolean }>(`/api/marketplace/api-keys/${id}`, { method: 'DELETE' }),
  // Phase 5 — i18n + white-label
  i18n: (locale: string) => req<{ locale: string; supported: string[]; messages: Record<string, string> }>(`/api/i18n/${locale}`),
  branding: () => req<Branding>('/api/branding'),
  setBranding: (b: Partial<Branding>) => req<Branding>('/api/branding', { method: 'PUT', body: JSON.stringify(b) }),
};

/** Copilot en streaming SSE. Appelle onDelta pour chaque fragment, onDone à la fin. */
export async function copilotStream(
  asset: string,
  message: string,
  onDelta: (s: string) => void,
  onDone?: () => void,
): Promise<void> {
  const t = token();
  const res = await fetch(`${API}/api/copilot/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(t ? { Authorization: `Bearer ${t}` } : {}) },
    body: JSON.stringify({ asset, message }),
  });
  if (!res.ok || !res.body) {
    throw new Error(res.status === 402 ? 'Copilot réservé au plan Pro' : `Erreur ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() ?? '';
    for (const block of lines) {
      const line = block.trim();
      if (!line.startsWith('data:')) continue;
      const payload = line.slice(5).trim();
      if (payload === '[DONE]') { onDone?.(); return; }
      try {
        const obj = JSON.parse(payload);
        if (obj.delta) onDelta(obj.delta);
      } catch { /* ignore */ }
    }
  }
  onDone?.();
}

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
