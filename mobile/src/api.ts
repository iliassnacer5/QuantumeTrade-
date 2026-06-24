/**
 * Client API mobile — réutilise EXACTEMENT le même backend FastAPI que le web (Phase 3.1 :
 * réutilisation maximale de la logique). Le token JWT est persisté via AsyncStorage.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const API: string = (Constants.expoConfig?.extra?.apiUrl as string) ?? 'http://localhost:8080';
const TOKEN_KEY = 'qta_token';

export type Signal = {
  id?: string;
  asset: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  confidence: number;
  timeframe: string;
  rationale: string;
};

export type Me = { id: string; email: string; plan: string; capital: number; watchlist: string[] };

let cachedToken: string | null = null;

export async function getToken(): Promise<string | null> {
  if (cachedToken) return cachedToken;
  cachedToken = await AsyncStorage.getItem(TOKEN_KEY);
  return cachedToken;
}
export async function setToken(t: string) {
  cachedToken = t;
  await AsyncStorage.setItem(TOKEN_KEY, t);
}
export async function clearToken() {
  cachedToken = null;
  await AsyncStorage.removeItem(TOKEN_KEY);
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const t = await getToken();
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(t ? { Authorization: `Bearer ${t}` } : {}),
      ...(opts.headers as object),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Erreur ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  apiUrl: API,
  login: (email: string, password: string) =>
    req<{ access_token: string }>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string) =>
    req<{ access_token: string }>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => req<Me>('/api/auth/me'),
  signals: () => req<Signal[]>('/api/signals'),
  generate: (asset: string, timeframe = 'swing') =>
    req<Signal>('/api/signals/generate', { method: 'POST', body: JSON.stringify({ asset, timeframe, notify: true }) }),
  copilotAsk: (asset: string, message: string) =>
    req<{ asset: string; answer: string }>('/api/copilot/ask', { method: 'POST', body: JSON.stringify({ asset, message }) }),
  registerPushToken: (push_token: string) =>
    req<unknown>('/api/settings', { method: 'PATCH', body: JSON.stringify({ push_token }) }).catch(() => {}),
};

export function wsUrl(token: string): string {
  return `${API.replace(/^http/, 'ws')}/ws/signals?token=${token}`;
}
