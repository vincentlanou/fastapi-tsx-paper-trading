const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface MomentumIndicators {
  current_rsi: number;
  rsi_status: string;
  current_macd: number;
  current_macd_signal: number;
  current_macd_histogram: number;
  macd_status: string;
  overall_momentum_signal: string;
  momentum_score: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  volatility_annualized?: number;
  max_drawdown?: number;
}

export interface StockMarketData {
  ticker: string;
  company_name?: string;
  current_price: number;
  previous_close: number;
  price_change: number;
  price_change_pct: number;
  currency: string;
  indicators: MomentumIndicators;
  chart_data: Array<{
    date: string;
    price: number;
    rsi?: number;
    macd?: number;
    signal_line?: number;
    histogram?: number;
  }>;
}

export interface NewsArticle {
  title: string;
  publisher: string;
  link: string;
  providerPublishTime: number;
  type: string;
}

export interface SentimentAnalysis {
  ticker: string;
  company_name: string;
  overall_score: number;
  sentiment_score?: number;
  sentiment_label: string;
  overall_sentiment?: string;
  summary: string;
  key_drivers: string[];
  bullish_percentage: number;
  bearish_percentage: number;
  news_count: number;
  articles: NewsArticle[];
}

export type SentimentData = SentimentAnalysis;

export interface Position {
  id: number;
  ticker: string;
  quantity: number;
  average_buy_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface Trade {
  id: number;
  ticker: string;
  trade_type: string;
  quantity: number;
  execution_price: number;
  total_amount: number;
  realized_pnl?: number;
  created_at: string;
}

export interface PortfolioSummary {
  account_name: string;
  cash_balance: number;
  total_stock_value: number;
  total_equity: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions: Position[];
}

export interface PnLSnapshot {
  timestamp: string;
  total_equity: number;
  cash_balance: number;
  total_pnl: number;
  total_pnl_pct: number;
}

export type PnlSnapshot = PnLSnapshot;

export async function fetchStockData(ticker: string): Promise<StockMarketData> {
  const res = await fetch(`${API_BASE_URL}/market/${ticker}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch stock data for ${ticker}`);
  return res.json();
}

export const fetchMarketData = fetchStockData;

export async function fetchSentiment(ticker: string): Promise<SentimentAnalysis> {
  const res = await fetch(`${API_BASE_URL}/sentiment/${ticker}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch sentiment for ${ticker}`);
  return res.json();
}

export async function fetchPortfolio(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE_URL}/trading/portfolio`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Failed to fetch portfolio");
  return res.json();
}

export async function fetchPnLHistory(): Promise<PnLSnapshot[]> {
  const res = await fetch(`${API_BASE_URL}/trading/pnl-history`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Failed to fetch PnL history");
  return res.json();
}

export const fetchPnlHistory = fetchPnLHistory;

export async function fetchTradesHistory(): Promise<Trade[]> {
  const res = await fetch(`${API_BASE_URL}/trading/history`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Failed to fetch trade history");
  return res.json();
}

export async function buyStock(ticker: string, quantity: number): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trading/buy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, quantity })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute buy order");
  }
  return res.json();
}

export async function sellStock(ticker: string, quantity: number): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trading/sell`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, quantity })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute sell order");
  }
  return res.json();
}

export async function resetAccount(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trading/reset`, { method: 'POST' });
  if (!res.ok) throw new Error("Failed to reset account");
  return res.json();
}

export const resetPortfolio = resetAccount;
