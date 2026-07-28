"use client";

import React, { useState } from "react";
import { StockMarketData, buyStock, sellStock } from "@/lib/api";
import { DollarSign, ShieldCheck, Zap } from "lucide-react";

interface TradingPanelProps {
  data?: StockMarketData | null;
  currentTicker?: string;
  currentPrice?: number;
  activePositionsCount: number;
  onBuy?: (ticker: string, quantity: number) => void;
  onSell?: (ticker: string, quantity: number) => void;
  onTradeSuccess?: () => void;
}

export const TradingPanel: React.FC<TradingPanelProps> = ({
  data,
  currentTicker,
  currentPrice,
  activePositionsCount,
  onBuy,
  onSell,
  onTradeSuccess
}) => {
  const [quantity, setQuantity] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [tradeStatus, setTradeStatus] = useState<string | null>(null);

  const activeTicker = data?.ticker || currentTicker || "SHOP.TO";
  const price = data?.current_price || currentPrice || 100.0;
  const spreadSlippage = price * 0.0005; // 0.05% standard TSX spread
  const buyExecPrice = price + spreadSlippage;
  const sellExecPrice = Math.max(0.01, price - spreadSlippage);
  const bncdFee = 0.00; // BNCD $0.00 commission

  const totalEstCost = Math.round(quantity) * buyExecPrice + bncdFee;

  const handleBuyClick = async () => {
    if (onBuy) {
      onBuy(activeTicker, Math.round(quantity));
      return;
    }
    try {
      setLoading(true);
      setTradeStatus(null);
      await buyStock(activeTicker, Math.round(quantity));
      setTradeStatus(`Achat réussi de ${Math.round(quantity)} action(s) de ${activeTicker} (BNCD $0 Frais) !`);
      if (onTradeSuccess) onTradeSuccess();
    } catch (err: any) {
      setTradeStatus(`Erreur : ${err.message || 'Échec de la transaction'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSellClick = async () => {
    if (onSell) {
      onSell(activeTicker, Math.round(quantity));
      return;
    }
    try {
      setLoading(true);
      setTradeStatus(null);
      await sellStock(activeTicker, Math.round(quantity));
      setTradeStatus(`Vente réussie de ${Math.round(quantity)} action(s) de ${activeTicker} (BNCD $0 Frais) !`);
      if (onTradeSuccess) onTradeSuccess();
    } catch (err: any) {
      setTradeStatus(`Erreur : ${err.message || 'Échec de la transaction'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-100 flex items-center gap-2">
          <Zap className="w-5 h-5 text-emerald-400" /> Terminal d'Ordres BNCD ($0 Frais)
        </h3>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30 flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-emerald-400" /> Courtage BNCD ($0.00 CAD)
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-semibold text-gray-400 mb-1">
            Quantité d'actions {activeTicker} (Entier strict)
          </label>
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full bg-slate-900/90 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-100 font-mono focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="bg-slate-900/60 p-3 rounded-lg border border-white/5 text-xs font-mono space-y-1">
          <div className="flex justify-between text-gray-400">
            <span>Prix Exéc. Achat (Spread 0.05%) :</span>
            <span className="text-gray-100">${buyExecPrice.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-gray-400">
            <span>Frais Commission BNCD :</span>
            <span className="text-emerald-400 font-bold">$0.00 CAD</span>
          </div>
          <div className="flex justify-between text-gray-400 border-t border-white/5 pt-1">
            <span>Montant Total Estimé :</span>
            <span className="text-blue-400 font-bold">${totalEstCost.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {tradeStatus && (
        <div className="mb-4 text-xs font-semibold p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-center">
          {tradeStatus}
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleBuyClick}
          disabled={loading || activePositionsCount >= 5}
          className={`flex-1 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center justify-center gap-1 ${
            activePositionsCount >= 5
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed border border-white/5'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
          }`}
        >
          <DollarSign className="w-4 h-4" /> Acheter {Math.round(quantity)} action(s) (BNCD $0)
        </button>

        <button
          onClick={handleSellClick}
          disabled={loading}
          className="flex-1 bg-rose-600 hover:bg-rose-500 text-white py-2.5 rounded-lg font-semibold text-sm transition-all shadow-lg shadow-rose-500/20 flex items-center justify-center gap-1"
        >
          Vendre {Math.round(quantity)} action(s) (BNCD $0)
        </button>
      </div>
    </div>
  );
};
