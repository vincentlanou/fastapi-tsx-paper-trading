"use client";

import React from "react";
import { PortfolioSummary, PnlSnapshot } from "@/lib/api";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Wallet, TrendingUp, DollarSign, RefreshCw } from "lucide-react";

interface PortfolioOverviewProps {
  portfolio: PortfolioSummary | null;
  pnlHistory: PnlSnapshot[];
  onReset: () => void;
}

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({
  portfolio,
  pnlHistory,
  onReset
}) => {
  if (!portfolio) {
    return (
      <div className="glass-card p-6 mb-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-20 bg-slate-800 rounded"></div>
          <div className="h-20 bg-slate-800 rounded"></div>
          <div className="h-20 bg-slate-800 rounded"></div>
          <div className="h-20 bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  const isRealizedPos = portfolio.total_realized_pnl >= 0;
  const isUnrealizedPos = portfolio.total_unrealized_pnl >= 0;

  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-gray-100">Portefeuille Virtuel & Évolution P&L</h2>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 border border-rose-500/30 hover:bg-rose-500/10 px-3 py-1.5 rounded-lg transition-all"
          title="Réinitialiser à $100,000 CAD"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Reset $100k
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900/60 border border-white/5 p-4 rounded-xl">
          <span className="text-xs text-gray-400 block mb-1">Valeur Totale Équité</span>
          <span className="text-xl font-bold font-mono text-gray-100">
            ${portfolio.total_equity.toLocaleString('fr-CA', { minimumFractionDigits: 2 })} CAD
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-4 rounded-xl">
          <span className="text-xs text-gray-400 block mb-1">Solde Cash Disponible</span>
          <span className="text-xl font-bold font-mono text-blue-400">
            ${portfolio.cash_balance.toLocaleString('fr-CA', { minimumFractionDigits: 2 })} CAD
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-4 rounded-xl">
          <span className="text-xs text-gray-400 block mb-1">P&L Non Réalisé</span>
          <span className={`text-xl font-bold font-mono ${isUnrealizedPos ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isUnrealizedPos ? '+' : ''}${portfolio.total_unrealized_pnl.toFixed(2)} CAD
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-4 rounded-xl">
          <span className="text-xs text-gray-400 block mb-1">P&L Réalisé Total</span>
          <span className={`text-xl font-bold font-mono ${isRealizedPos ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isRealizedPos ? '+' : ''}${portfolio.total_realized_pnl.toFixed(2)} CAD
          </span>
        </div>
      </div>

      {/* Recharts P&L Evolution Chart */}
      <div className="mt-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-purple-400" /> Graphique d'Évolution du P&L (Recharts)
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
