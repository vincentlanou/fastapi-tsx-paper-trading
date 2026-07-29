"use client";

import React from "react";
import { PortfolioSummary, PnlSnapshot } from "@/lib/api";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Wallet, TrendingUp, RefreshCw, ShieldCheck } from "lucide-react";

interface PortfolioOverviewProps {
  portfolio: PortfolioSummary | null;
  pnlHistory: PnlSnapshot[];
  benchmarks: Record<string, {name: string, return_pct: number}>;
  onReset: () => void;
}

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({
  portfolio,
  pnlHistory,
  benchmarks,
  onReset
}) => {
  if (!portfolio) {
    return (
      <div className="glass-panel p-6 mb-6 animate-pulse rounded-2xl">
        <div className="h-6 bg-slate-800/50 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-20 bg-slate-800/50 rounded-xl"></div>
          <div className="h-20 bg-slate-800/50 rounded-xl"></div>
          <div className="h-20 bg-slate-800/50 rounded-xl"></div>
          <div className="h-20 bg-slate-800/50 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const isPos = portfolio.total_pnl >= 0;

  return (
    <div className="glass-panel p-6 mb-6 rounded-2xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-gray-100">Portefeuille BNCD ($5,000 CAD) & Évolution P&L</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> BNCD Courtage $0.00
          </span>
          {portfolio.created_at && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800/50 text-slate-300 font-medium border border-slate-700/50">
              Début: {portfolio.created_at.split(' ')[0]}
            </span>
          )}
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 border border-rose-500/30 hover:bg-rose-500/10 px-3 py-1.5 rounded-lg transition-all"
            title="Réinitialiser à $5,000 CAD"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset $5k
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="glass-panel glass-panel-hover p-5 rounded-xl">
          <span className="text-xs text-slate-400 block mb-1">Valeur Totale Équité</span>
          <span className="text-2xl font-bold tracking-tight text-white">
            ${portfolio.total_equity.toLocaleString('fr-CA', { minimumFractionDigits: 2 })} CAD
          </span>
        </div>

        <div className="glass-panel glass-panel-hover p-5 rounded-xl">
          <span className="text-xs text-slate-400 block mb-1">Solde Cash Disponible</span>
          <span className="text-2xl font-bold tracking-tight text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.3)]">
            ${portfolio.cash_balance.toLocaleString('fr-CA', { minimumFractionDigits: 2 })} CAD
          </span>
        </div>

        <div className="glass-panel glass-panel-hover p-5 rounded-xl relative overflow-hidden">
          <div className={`absolute inset-0 opacity-10 ${isPos ? 'bg-gradient-to-r from-emerald-500 to-transparent' : 'bg-gradient-to-r from-rose-500 to-transparent'}`}></div>
          <span className="text-xs text-slate-400 block mb-1 relative z-10">P&L Net Total ($)</span>
          <span className={`text-2xl font-bold tracking-tight relative z-10 ${isPos ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,0.3)]' : 'text-rose-400 drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]'}`}>
            {isPos ? '+' : ''}${portfolio.total_pnl.toFixed(2)} CAD
          </span>
        </div>

        <div className="glass-panel glass-panel-hover p-5 rounded-xl relative overflow-hidden">
          <div className={`absolute inset-0 opacity-10 ${isPos ? 'bg-gradient-to-l from-emerald-500 to-transparent' : 'bg-gradient-to-l from-rose-500 to-transparent'}`}></div>
          <span className="text-xs text-slate-400 block mb-1 relative z-10">Rendement Net (%)</span>
          <span className={`text-2xl font-bold tracking-tight relative z-10 ${isPos ? 'text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,0.3)]' : 'text-rose-400 drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]'}`}>
            {isPos ? '+' : ''}{portfolio.total_pnl_pct.toFixed(2)}%
          </span>
          
          <div className="mt-2 flex flex-col gap-1 relative z-10">
            {Object.entries(benchmarks).map(([ticker, data]) => (
              <div key={ticker} className="flex items-center justify-between text-[10px] bg-slate-800/50 px-2 py-0.5 rounded border border-slate-700/50">
                <span className="text-slate-400">{data.name}</span>
                <span className={data.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}>
                  {data.return_pct >= 0 ? '+' : ''}{data.return_pct.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recharts P&L Evolution Chart */}
      <div className="mt-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-purple-400" /> Graphique d'Évolution du P&L Net (Recharts)
        </h3>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={pnlHistory}>
              <defs>
                <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis dataKey="timestamp" stroke="#6b7280" tick={{ fontSize: 11 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: 'rgba(255,255,255,0.1)',
                  borderRadius: '0.75rem',
                  fontSize: '0.85rem'
                }}
                formatter={(val: number) => [`$${val.toFixed(2)} CAD`, "P&L Total"]}
              />
              <Area
                type="monotone"
                dataKey="total_pnl"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#pnlGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
