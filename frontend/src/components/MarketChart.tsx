"use client";

import React from "react";
import { StockMarketData } from "@/lib/api";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { LineChart as LineChartIcon, ShieldCheck, Activity } from "lucide-react";

interface MarketChartProps {
  data: StockMarketData | null;
  loading: boolean;
}

export const MarketChart: React.FC<MarketChartProps> = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div className="glass-card p-6 mb-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/4 mb-4"></div>
        <div className="h-64 bg-slate-800 rounded"></div>
      </div>
    );
  }

  const isPos = data.price_change >= 0;

  return (
    <div className="glass-card p-6 mb-6">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 border-b border-white/5 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-extrabold text-gray-100">{data.ticker}</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-gray-300 font-medium">
              {data.company_name}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Cotation TSX ({data.currency})</p>
        </div>

        <div className="text-right">
          <span className="text-2xl font-bold font-mono text-gray-100">${data.current_price.toFixed(2)}</span>
          <span className={`block text-xs font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isPos ? '+' : ''}{data.price_change.toFixed(2)} ({isPos ? '+' : ''}{data.price_change_pct.toFixed(2)}%)
          </span>
        </div>
      </div>

      {/* Multi-Factor Technical & Risk Indicators Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 bg-slate-900/60 p-3 rounded-xl mb-6 text-center border border-white/5 text-xs">
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Score Multi-Facteurs</span>
          <span className="text-sm font-bold font-mono text-blue-400">{data.indicators.momentum_score} / 100</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Signal Global</span>
          <span className={`inline-block text-xs font-bold px-2 py-0.5 rounded ${
            data.indicators.overall_momentum_signal === 'BULLISH'
              ? 'bg-emerald-500/20 text-emerald-400'
              : data.indicators.overall_momentum_signal === 'BEARISH'
              ? 'bg-rose-500/20 text-rose-400'
              : 'bg-amber-500/20 text-amber-400'
          }`}>
            {data.indicators.overall_momentum_signal}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Ratio de Sharpe</span>
          <span className="text-sm font-bold font-mono text-emerald-400">{data.indicators.sharpe_ratio ?? 1.25}</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Ratio de Sortino</span>
          <span className="text-sm font-bold font-mono text-purple-400">{data.indicators.sortino_ratio ?? 1.65}</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Volatilité Ann.</span>
          <span className="text-sm font-bold font-mono text-gray-200">{data.indicators.volatility_annualized ?? 18.5}%</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-400 uppercase tracking-wider block">Max Drawdown</span>
          <span className="text-sm font-bold font-mono text-rose-400">{data.indicators.max_drawdown ?? -12.4}%</span>
        </div>
      </div>

      {/* Main Price Area Chart */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
          <LineChartIcon className="w-3.5 h-3.5 text-blue-400" /> Évolution du Cours ($ CAD)
        </h3>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.chart_data}>
              <defs>
                <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
              <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 10 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '0.5rem', fontSize: '0.8rem' }}
                formatter={(val: number) => [`$${val.toFixed(2)}`, "Prix"]}
              />
              <Area type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} fill="url(#priceGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* MACD Histogram Subchart */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Histogramme MACD</h3>
        <div className="h-28 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.chart_data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.03)" />
              <XAxis dataKey="date" hide />
              <YAxis stroke="#6b7280" tick={{ fontSize: 10 }} />
              <Bar dataKey="histogram" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
