"use client";

import React from "react";
import { SentimentData } from "@/lib/api";
import { Newspaper, Cpu, ExternalLink, Sparkles } from "lucide-react";

interface NewsSentimentFeedProps {
  sentiment: SentimentData | null;
  loading: boolean;
}

export const NewsSentimentFeed: React.FC<NewsSentimentFeedProps> = ({ sentiment, loading }) => {
  if (loading || !sentiment) {
    return (
      <div className="glass-card p-6 mb-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/3 mb-4"></div>
        <div className="h-24 bg-slate-800 rounded mb-4"></div>
        <div className="h-32 bg-slate-800 rounded"></div>
      </div>
    );
  }

  const isPositive = sentiment.overall_sentiment === "POSITIVE";
  const isNegative = sentiment.overall_sentiment === "NEGATIVE";

  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-gray-100">Actualités TSX & Sentiment IA</h2>
        </div>
        <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-400/30 font-medium">
          <Cpu className="w-3.5 h-3.5" /> Gemini 2.5 Flash
        </span>
      </div>

      {/* AI Sentiment Score Header */}
      <div className="bg-slate-900/70 border border-white/5 p-4 rounded-xl mb-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <span className="text-xs text-gray-400 block mb-1">Score de Sentiment Global</span>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-extrabold font-mono text-gray-100">
                {Math.round(sentiment.sentiment_score)}
                <span className="text-xs font-sans text-gray-400">/100</span>
              </span>
              <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                isPositive
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                  : isNegative
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                  : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              }`}>
                {sentiment.overall_sentiment}
              </span>
            </div>
          </div>

          {/* Bullish / Bearish distribution bars */}
          <div className="w-full sm:w-64 flex flex-col gap-2">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Bullish: <strong className="text-emerald-400">{Math.round(sentiment.bullish_score)}%</strong></span>
              <span>Bearish: <strong className="text-rose-400">{Math.round(sentiment.bearish_score)}%</strong></span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden flex">
              <div style={{ width: `${sentiment.bullish_score}%` }} className="bg-emerald-500 transition-all duration-500"></div>
              <div style={{ width: `${sentiment.bearish_score}%` }} className="bg-rose-500 transition-all duration-500"></div>
            </div>
          </div>
        </div>

        {/* AI Summary Text */}
        <div className="mt-4 pt-3 border-t border-white/5">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Synthèse Gemini IA
          </h4>
          <p className="text-sm text-gray-200 leading-relaxed">{sentiment.ai_summary}</p>
        </div>

        {/* Key Drivers */}
        {sentiment.key_drivers && sentiment.key_drivers.length > 0 && (
          <div className="mt-3">
            <ul className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {sentiment.key_drivers.map((driver, idx) => (
                <li key={idx} className="bg-white/5 border-l-2 border-purple-500 px-2.5 py-1.5 rounded text-xs text-gray-300">
                  {driver}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* News Feed Cards List */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Dernières dépêches d'actualités ({sentiment.articles_analyzed_count})
        </h3>
        <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
          {sentiment.articles.map((art, idx) => (
            <div key={idx} className="bg-slate-900/60 border border-white/5 p-3.5 rounded-xl hover:border-blue-500/30 transition-all">
              <div className="flex items-start justify-between gap-2">
                <a
                  href={art.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1.5 line-clamp-1"
                >
                  {art.title} <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>
              <p className="text-xs text-gray-300 mt-1 line-clamp-2">{art.summary}</p>
              <div className="text-[10px] text-gray-500 mt-2 font-mono">
                Source : {art.publisher} {art.published_at ? `• ${art.published_at}` : ''}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
