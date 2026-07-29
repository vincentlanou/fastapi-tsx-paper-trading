"use client";

import React, { useState } from "react";
import { Search, TrendingUp, ShieldCheck } from "lucide-react";

interface NavbarProps {
  currentTicker: string;
  universe: string[];
  onSelectTicker: (ticker: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTicker, universe, onSelectTicker }) => {
  const [searchInput, setSearchInput] = useState("");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSelectTicker(searchInput.trim());
      setSearchInput("");
    }
  };

  return (
    <header className="glass-card p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="bg-blue-600/20 p-2.5 rounded-xl border border-blue-500/30 text-blue-400">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-2">
            QuantPulse TSX <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30">Bourse de Toronto</span>
          </h1>
          <p className="text-xs text-gray-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Large Cap Only (CAD)
          </p>
        </div>
      </div>

      {/* Search & Universe Selector */}
      <div className="flex flex-col sm:flex-row items-center gap-3 w-full lg:w-auto">
        <form onSubmit={handleSearchSubmit} className="flex items-center bg-slate-900/80 border border-white/10 rounded-xl px-4 py-1.5 w-full sm:w-64 focus-within:border-blue-500 transition-all">
          <Search className="w-4 h-4 text-gray-400 mr-2" />
          <input
            type="text"
            placeholder="Rechercher (ex: SHOP.TO)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="bg-transparent border-none outline-none text-sm text-gray-100 placeholder-gray-500 w-full"
          />
          <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1 rounded-lg transition-all ml-2">
            GO
          </button>
        </form>

        <select 
          value={currentTicker}
          onChange={(e) => onSelectTicker(e.target.value)}
          className="bg-slate-900/80 border border-white/10 text-gray-300 text-sm rounded-xl px-4 py-2 focus:border-blue-500 outline-none w-full sm:w-64 cursor-pointer"
        >
          <option value="" disabled>Parcourir l'Univers (75 Actions)</option>
          {universe.map(ticker => (
            <option key={ticker} value={ticker}>{ticker}</option>
          ))}
        </select>
      </div>
    </header>
  );
};
