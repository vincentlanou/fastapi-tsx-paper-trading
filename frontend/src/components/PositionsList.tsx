"use client";

import React from "react";
import { Position } from "@/lib/api";
import { Layers, ArrowUpRight, ArrowDownRight, RefreshCw, ShieldCheck } from "lucide-react";

interface PositionsListProps {
  positions: Position[];
  onQuickSell: (ticker: string, quantity: number) => void;
}

export const PositionsList: React.FC<PositionsListProps> = ({ positions, onQuickSell }) => {
  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-bold text-gray-100">Positions Ouvertes & Suivi Horizon 5J</h2>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 font-semibold border border-purple-400/30">
          {positions.length} / 5 max
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-white/5">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/90 text-gray-400 font-semibold text-xs uppercase tracking-wider">
            <tr>
              <th className="p-3">Ticker</th>
              <th className="p-3">Qté</th>
              <th className="p-3">Prix Moyen</th>
              <th className="p-3">Prix Actuel</th>
              <th className="p-3">P&L Net ($ / %)</th>
              <th className="p-3">Statut 5J & Friction</th>
              <th className="p-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-mono">
            {positions.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-6 text-center text-gray-500 font-sans text-sm">
                  Aucune position ouverte. Utilisez le terminal pour simuler un ordre d'achat.
                </td>
              </tr>
            ) : (
              positions.map((pos) => {
                const isPos = pos.unrealized_pnl >= 0;
                return (
                  <tr key={pos.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-sans font-bold text-gray-100 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      {pos.ticker}
                    </td>
                    <td className="p-3 text-gray-200">{pos.quantity}</td>
                    <td className="p-3 text-gray-300">${pos.average_buy_price.toFixed(2)}</td>
                    <td className="p-3 text-gray-100 font-semibold">${pos.current_price.toFixed(2)}</td>
                    <td className={`p-3 font-semibold flex items-center gap-1 ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isPos ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {isPos ? '+' : ''}${pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_pct.toFixed(2)}%)
                    </td>
                    <td className="p-3 font-sans">
                      <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                        <ShieldCheck className="w-3 h-3 text-emerald-400" /> Conserver & Renouveler 5J
                      </span>
                    </td>
                    <td className="p-3 text-right font-sans">
                      <button
                        onClick={() => onQuickSell(pos.ticker, pos.quantity)}
                        className="bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-semibold px-3 py-1 rounded-lg transition-all"
                      >
                        Vendre
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
