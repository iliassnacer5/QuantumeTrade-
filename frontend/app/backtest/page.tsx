'use client';

import { useState } from 'react';
import { api, BacktestConfig, BacktestReport } from '@/lib/api';
import { PageHeader, RouteTabs, PROVE_TABS } from '@/components/ui';

export default function BacktestPage() {
  const [report, setReport] = useState<BacktestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<BacktestConfig>({
    symbol: 'BTC/USDT',
    timeframe: '1h',
    start_time: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    end_time: new Date().toISOString(),
    initial_capital: 10000,
    risk_per_trade_pct: 1.0,
    use_llm: false
  });

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await api.runBacktest(config);
      setReport(res);
    } catch (e) {
      console.error(e);
      alert('Erreur lors du backtest');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 text-white">
      <PageHeader title="Moteur de Backtesting" subtitle="Teste une configuration sur l’historique — frais et slippage inclus." />
      <RouteTabs items={PROVE_TABS} />

      <div className="bg-[#1A1A1A] p-6 rounded-xl border border-white/5 space-y-4">
        <h2 className="text-xl font-semibold">Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Actif</label>
            <input 
              type="text" 
              className="w-full bg-[#2A2A2A] rounded px-3 py-2 text-white"
              value={config.symbol}
              onChange={e => setConfig({...config, symbol: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Timeframe</label>
            <input 
              type="text" 
              className="w-full bg-[#2A2A2A] rounded px-3 py-2 text-white"
              value={config.timeframe}
              onChange={e => setConfig({...config, timeframe: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Capital Initial ($)</label>
            <input 
              type="number" 
              className="w-full bg-[#2A2A2A] rounded px-3 py-2 text-white"
              value={config.initial_capital}
              onChange={e => setConfig({...config, initial_capital: Number(e.target.value)})}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Risque / Trade (%)</label>
            <input 
              type="number" 
              step="0.1"
              className="w-full bg-[#2A2A2A] rounded px-3 py-2 text-white"
              value={config.risk_per_trade_pct}
              onChange={e => setConfig({...config, risk_per_trade_pct: Number(e.target.value)})}
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2 pt-2">
          <input 
            type="checkbox" 
            id="use_llm"
            checked={config.use_llm}
            onChange={e => setConfig({...config, use_llm: e.target.checked})}
            className="rounded bg-[#2A2A2A] border-transparent"
          />
          <label htmlFor="use_llm" className="text-sm">Activer les LLM (Grounding, Sentiment)</label>
        </div>
        
        <button 
          onClick={handleRun} 
          disabled={loading}
          className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium disabled:opacity-50"
        >
          {loading ? 'Simulation en cours...' : 'Lancer le Backtest'}
        </button>
      </div>

      {report && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5">
              <div className="text-sm text-gray-400">Total PnL</div>
              <div className={`text-2xl font-bold ${report.metrics.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                ${report.metrics.total_pnl.toFixed(2)} ({report.metrics.total_pnl_pct.toFixed(2)}%)
              </div>
            </div>
            <div className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5">
              <div className="text-sm text-gray-400">Win Rate</div>
              <div className="text-2xl font-bold">{(report.metrics.win_rate * 100).toFixed(1)}%</div>
            </div>
            <div className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5">
              <div className="text-sm text-gray-400">Profit Factor</div>
              <div className="text-2xl font-bold">{report.metrics.profit_factor.toFixed(2)}</div>
            </div>
            <div className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5">
              <div className="text-sm text-gray-400">Max Drawdown</div>
              <div className="text-2xl font-bold text-red-500">{report.metrics.max_drawdown_pct.toFixed(2)}%</div>
            </div>
          </div>
          
          <div className="bg-[#1A1A1A] p-6 rounded-xl border border-white/5">
            <h2 className="text-xl font-semibold mb-4">Historique des Trades ({report.metrics.total_trades})</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-400 uppercase bg-[#2A2A2A]">
                  <tr>
                    <th className="px-4 py-3">Date Entry</th>
                    <th className="px-4 py-3">Sens</th>
                    <th className="px-4 py-3">Prix Entrée</th>
                    <th className="px-4 py-3">Prix Sortie</th>
                    <th className="px-4 py-3">PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {report.trades.map((t, i) => (
                    <tr key={i} className="border-b border-white/5">
                      <td className="px-4 py-3">{new Date(t.entry_time).toLocaleString()}</td>
                      <td className={`px-4 py-3 font-medium ${t.direction === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                        {t.direction}
                      </td>
                      <td className="px-4 py-3">${t.entry_price.toFixed(2)}</td>
                      <td className="px-4 py-3">${t.exit_price.toFixed(2)}</td>
                      <td className={`px-4 py-3 font-medium ${t.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        ${t.pnl.toFixed(2)} ({t.pnl_pct.toFixed(2)}%)
                      </td>
                    </tr>
                  ))}
                  {report.trades.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-4 text-center text-gray-500">Aucun trade exécuté</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
