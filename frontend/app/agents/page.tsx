'use client';

import { useEffect, useState } from 'react';
import { api, AgentStatus } from '@/lib/api';

export default function AgentsPage() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.agentsStatus()
      .then(setStatus)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-white">Chargement...</div>;

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold text-white">Supervision des Agents IA</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-[#1A1A1A] p-6 rounded-xl border border-white/5">
          <h2 className="text-gray-400 text-sm mb-1">Statut Système</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${status?.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-white text-xl capitalize">{status?.status || 'Inconnu'}</span>
          </div>
        </div>

        <div className="bg-[#1A1A1A] p-6 rounded-xl border border-white/5">
          <h2 className="text-gray-400 text-sm mb-1">Moteur LLM</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${status?.llm_enabled ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="text-white text-xl">
              {status?.llm_enabled ? 'Activé (Hybride)' : 'Désactivé (Déterministe)'}
            </span>
          </div>
        </div>
      </div>

      <h2 className="text-xl font-semibold text-white mt-8 mb-4">Agents Actifs ({status?.agents.length ?? 0})</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {status?.agents.map(agent => (
          <div key={agent.name} className="bg-[#1A1A1A] p-4 rounded-xl border border-white/5 flex flex-col justify-between h-36">
            <div>
              <h3 className="text-white capitalize font-medium">{agent.name}</h3>
              <p className="text-xs text-gray-400 mt-1">{agent.desc}</p>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-gray-500 font-mono truncate">{agent.model}</span>
              <span className="text-xs text-green-400 bg-green-400/10 px-2 py-1 rounded w-fit">Actif</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
