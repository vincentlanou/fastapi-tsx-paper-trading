"use client";

import React, { useState, useEffect } from "react";
import {
  fetchMarketData,
  fetchSentiment,
  fetchPortfolio,
  fetchPnlHistory,
  resetPortfolio,
  StockMarketData,
  SentimentData,
  PortfolioSummary,
  PnlSnapshot
} from "@/lib/api";
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
    } catch (err) {
      console.error("Error loading portfolio:", err);
    }
  };

  useEffect(() => {
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
      <Navbar currentTicker={currentTicker} onSelectTicker={handleSelectTicker} />

      {errorMsg && (
        <div className="bg-rose-500/20 border border-rose-500/40 text-rose-300 p-4 rounded-xl text-sm font-semibold">
          {errorMsg}
        </div>
      )}

      {/* REQUIREMENT 1: Solde du portefeuille et graphique d'évolution du P&L (Recharts) */}
      <PortfolioOverview
        portfolio={portfolioData}
        pnlHistory={pnlHistoryData}
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
            currentTicker={currentTicker}
            currentPrice={marketData?.current_price || 0}
            activePositionsCount={portfolioData?.positions.length || 0}
            onTradeSuccess={loadPortfolioAndHistory}
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
