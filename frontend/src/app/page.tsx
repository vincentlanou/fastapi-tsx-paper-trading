"use client";

import React, { useState, useEffect } from "react";
import {
  fetchMarketData,
  fetchSentiment,
  fetchPortfolio,
  fetchPnlHistory,
  resetPortfolio,
  fetchMarketRegime,
  fetchUniverse,
  fetchBenchmarks,
  StockMarketData,
  SentimentData,
  PortfolioSummary,
  PnlSnapshot,
  MarketRegime
} from "@/lib/api";
import { ShieldAlert, TrendingUp, Activity } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { PortfolioOverview } from "@/components/PortfolioOverview";
import { PositionsList } from "@/components/PositionsList";
import { NewsSentimentFeed } from "@/components/NewsSentimentFeed";
import { MarketChart } from "@/components/MarketChart";
import { TradingPanel } from "@/components/TradingPanel";

export default function DashboardPage() {
  const [currentTicker, setCurrentTicker] = useState<string>("SHOP.TO");
  const [marketData, setMarketData] = useState<StockMarketData | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioSummary | null>(null);
  const [pnlHistoryData, setPnlHistoryData] = useState<PnlSnapshot[]>([]);
  const [marketRegime, setMarketRegime] = useState<MarketRegime | null>(null);
  const [universe, setUniverse] = useState<string[]>([]);
  const [benchmarks, setBenchmarks] = useState<Record<string, {name: string, return_pct: number}>>({});

  const [loadingMarket, setLoadingMarket] = useState<boolean>(true);
  const [loadingSentiment, setLoadingSentiment] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load Market Data & Sentiment for selected TSX ticker
  const loadTickerData = async (ticker: string) => {
    setErrorMsg(null);
    setLoadingMarket(true);
    setLoadingSentiment(true);

    try {
      const data = await fetchMarketData(ticker);
      setMarketData(data);
      setCurrentTicker(data.ticker);
    } catch (err: any) {
      setErrorMsg(err.message || "Impossible de charger les données TSX.");
    } finally {
      setLoadingMarket(false);
    }

    try {
      const sent = await fetchSentiment(ticker);
      setSentimentData(sent);
    } catch (err) {
      console.error("Error loading sentiment:", err);
    } finally {
      setLoadingSentiment(false);
    }
  };

  // Load Portfolio & P&L History
  const loadPortfolioAndHistory = async () => {
    try {
      const port = await fetchPortfolio();
      setPortfolioData(port);
      const history = await fetchPnlHistory();
      setPnlHistoryData(history);
      const regime = await fetchMarketRegime();
      setMarketRegime(regime);
      const bench = await fetchBenchmarks();
      setBenchmarks(bench);
    } catch (err) {
      console.error("Error loading portfolio or regime:", err);
    }
  };

  const loadUniverse = async () => {
    try {
      const u = await fetchUniverse();
      setUniverse(u);
    } catch (err) {
      console.error("Error loading universe:", err);
    }
  };

  useEffect(() => {
    loadUniverse();
    loadTickerData("SHOP.TO");
    loadPortfolioAndHistory();
  }, []);

  const handleSelectTicker = (ticker: string) => {
    loadTickerData(ticker);
  };

  const handleQuickSell = (ticker: string, qty: number) => {
    loadTickerData(ticker);
  };

  const handleResetPortfolio = async () => {
    if (confirm("Voulez-vous vraiment réinitialiser votre portefeuille virtuel TSX à $100,000 CAD ?")) {
      await resetPortfolio();
      loadPortfolioAndHistory();
    }
  };

  return (
    <main className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Top Navigation */}
      <Navbar currentTicker={currentTicker} universe={universe} onSelectTicker={handleSelectTicker} />

      {/* Global Regime Banner */}
      {marketRegime && marketRegime.regime !== "NORMAL" && (
        <div className={`p-4 rounded-xl text-sm font-semibold flex items-center gap-3 shadow-lg ${
          marketRegime.regime === "FALLING_KNIFE" 
            ? "bg-rose-500/10 border border-rose-500/40 text-rose-400 shadow-rose-500/10 animate-pulse-glow"
            : "bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 shadow-emerald-500/10"
        }`}>
          {marketRegime.regime === "FALLING_KNIFE" ? <ShieldAlert className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
          <div>
            <span className="block text-white">GLOBAL TSX REGIME: {marketRegime.regime}</span>
            <span className="font-normal opacity-80">{marketRegime.message}</span>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-500/20 border border-rose-500/40 text-rose-300 p-4 rounded-xl text-sm font-semibold">
          {errorMsg}
        </div>
      )}

      {/* REQUIREMENT 1: Solde du portefeuille et graphique d'évolution du P&L (Recharts) */}
      <PortfolioOverview
        portfolio={portfolioData}
        pnlHistory={pnlHistoryData}
        benchmarks={benchmarks}
        onReset={handleResetPortfolio}
      />

      {/* Main Grid: Left (Market Chart & News Sentiment Feed) | Right (Trading Terminal & Open Positions) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Price & Technical Indicators Chart */}
          <MarketChart data={marketData} loading={loadingMarket} />

          {/* REQUIREMENT 3: Feed des dernières actualités et leur score de sentiment IA */}
          <NewsSentimentFeed sentiment={sentimentData} loading={loadingSentiment} />
        </div>

        {/* Right Column */}
        <div className="lg:col-span-5 space-y-6">
          {/* Trading Order Terminal */}
          <TradingPanel
            data={marketData}
            currentTicker={currentTicker}
            currentPrice={marketData?.current_price || 0}
            activePositionsCount={portfolioData?.positions.length || 0}
            onTradeSuccess={loadPortfolioAndHistory}
            marketRegime={marketRegime?.regime || "NORMAL"}
          />


          {/* REQUIREMENT 2: La liste des positions ouvertes */}
          <PositionsList
            positions={portfolioData?.positions || []}
            onQuickSell={handleQuickSell}
          />
        </div>

      </div>
    </main>
  );
}
