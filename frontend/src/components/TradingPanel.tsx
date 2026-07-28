"use client";

import React, { useState } from "react";
import { buyStock, sellStock } from "@/lib/api";
import { Zap, ArrowUpRight, ArrowDownRight, ShieldAlert } from "lucide-react";

interface TradingPanelProps {
  currentTicker: string;
  currentPrice: number;
  activePositionsCount: number;
  onTradeSuccess: () => void;
}

export const TradingPanel: React.FC<TradingPanelProps> = ({
  currentTicker,
  currentPrice,
  activePositionsCount,
  onTradeSuccess
}) => {
  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState<string>("10");
  const [loading, setLoading] = useState<boolean>(false);
  const [msg, setMsg] = useState<{ text: string; isError: boolean } | null>(null);

  const numQty = Math.floor(parseFloat(quantity) || 0);
  const slippageMultiplier = orderType === "BUY" ? 1.0010 : 0.9990;
  const estimatedExecutionPrice = currentPrice * slippageMultiplier;
  const grossTotal = numQty * estimatedExecutionPrice;
  const fee = 4.95; // Fixed CAD commission per order
  const netTotal = orderType === "BUY" ? grossTotal + fee : grossTotal - fee;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!numQty || numQty < 1) {
      setMsg({ text: "Saisissez un nombre d'actions complètes (au moins 1).", isError: true });
      return;
    }

    setLoading(true);
    setMsg(null);

    try {
      if (orderType === "BUY") {
        await buyStock(currentTicker, numQty);
        setMsg({ text: `Achat exécuté : ${numQty} action(s) ${currentTicker} @ $${estimatedExecutionPrice.toFixed(2)} CAD (Frais : $4.95 CAD)!`, isError: false });
      } else {
        await sellStock(currentTicker, numQty);
        setMsg({ text: `Vente exécutée : ${numQty} action(s) ${currentTicker} @ $${estimatedExecutionPrice.toFixed(2)} CAD (Frais : $4.95 CAD)!`, isError: false });
      }
      onTradeSuccess();
    } catch (err: any) {
      setMsg({ text: err.message || "Erreur lors du passage d'ordre.", isError: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-bold text-gray-100">Terminal de Paper Trading</h2>
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
          activePositionsCount >= 5
            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
        }`}>
          Positions : {activePositionsCount} / 5 max
        </span>
      </div>

      {/* Buy/Sell Tabs */}
      <div className="grid grid-cols-2 gap-2 mb-4 bg-slate-900/60 p-1 rounded-xl border border-white/5">
        <button
          type="button"
          onClick={() => setOrderType("BUY")}
          className={`py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
            orderType === "BUY"
              ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/30"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <ArrowUpRight className="w-4 h-4" /> ACHAT
        </button>
        <button
          type="button"
          onClick={() => setOrderType("SELL")}
          className={`py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-1 ${
            orderType === "SELL"
              ? "bg-rose-600 text-white shadow-lg shadow-rose-600/30"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <ArrowDownRight className="w-4 h-4" /> VENTE
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs text-gray-400 block mb-1">Symbole Action TSX</label>
          <input
            type="text"
            value={currentTicker}
            readOnly
            className="w-full bg-slate-900/90 border border-white/10 rounded-xl px-3.5 py-2 text-sm text-gray-100 font-bold font-mono outline-none opacity-80"
          />
        </div>

        <div>
          <label className="text-xs text-gray-400 block mb-1">Quantité (Actions complètes uniquement)</label>
          <input
            type="number"
            step="1"
            min="1"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Ex: 10"
            className="w-full bg-slate-900 border border-white/10 rounded-xl px-3.5 py-2 text-sm text-gray-100 font-mono outline-none focus:border-blue-500 transition-colors"
            required
          />
        </div>

        {/* Calculation summary including fees and spread */}
        <div className="bg-slate-900/80 border border-white/5 p-3.5 rounded-xl space-y-1.5 text-xs">
          <div className="flex justify-between text-gray-400">
            <span>Prix du Marché :</span>
            <strong className="font-mono text-gray-200">${currentPrice.toFixed(2)} CAD</strong>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Prix Exec. (Spread 0.10%) :</span>
            <strong className="font-mono text-gray-200">${estimatedExecutionPrice.toFixed(2)} CAD</strong>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Frais Fixes de Courtage :</span>
            <strong className="font-mono text-amber-400">$4.95 CAD</strong>
          </div>
          <div className="flex justify-between text-gray-100 border-t border-white/5 pt-1.5 text-sm font-semibold">
            <span>Montant Net Total :</span>
            <strong className="font-mono text-blue-400">${netTotal.toFixed(2)} CAD</strong>
          </div>
        </div>

        {msg && (
          <div className={`p-3 rounded-xl text-xs font-medium border ${
            msg.isError ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
          }`}>
            {msg.text}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || (orderType === "BUY" && activePositionsCount >= 5)}
          className={`w-full py-3 rounded-xl text-sm font-bold text-white transition-all shadow-lg ${
            orderType === "BUY"
              ? "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-emerald-600/25"
              : "bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 shadow-rose-600/25"
          } ${loading || (orderType === "BUY" && activePositionsCount >= 5) ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {loading ? "Exécution en cours..." : `Simuler ${orderType === 'BUY' ? "l'Achat" : "la Vente"}`}
        </button>

        {activePositionsCount >= 5 && orderType === "BUY" && (
          <p className="text-[11px] text-rose-400 flex items-center gap-1 justify-center">
            <ShieldAlert className="w-3.5 h-3.5" /> Limite atteinte (5 positions max). Vendez une position pour en ouvrir une nouvelle.
          </p>
        )}
      </form>
    </div>
  );
};
