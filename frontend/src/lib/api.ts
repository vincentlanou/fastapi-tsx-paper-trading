const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface StockMarketData {
  ticker: string;
  company_name: string;
  current_price: number;
  previous_close: number;
  price_change: number;
  price_change_pct: number;
  currency: string;
  indicators: {
    current_rsi: number;
    rsi_status: string;
    current_macd: number;
    current_macd_signal: number;
    current_macd_histogram: number;
    macd_status: string;
    overall_momentum_signal: string;
    momentum_score: number;
  };
  chart_data: Array<{
    date: string;
    price: number;
    rsi: number;
    macd: number;
    signal_line: number;
    histogram: number;
  }>;
}

export interface NewsArticle {
  title: string;
  publisher: string;
  link: string;
  published_at?: string;
  summary: string;
}

export interface SentimentData {
  ticker: string;
  overall_sentiment: string;
  sentiment_score: number;
  bullish_score: number;
  bearish_score: number;
  ai_summary: string;
  key_drivers: string[];
  articles_analyzed_count: number;
  articles: NewsArticle[];
  is_ai_powered: boolean;
}

export interface Position {
  id: number;
  ticker: string;
  quantity: number;
  average_buy_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  updated_at: string;
}

export interface PortfolioSummary {
  account_id: number;
  account_name: string;
  cash_balance: number;
  portfolio_stock_value: number;
  total_equity: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions: Position[];
}

export interface PnlSnapshot {
  timestamp: string;
  total_equity: number;
  cash_balance: number;
  total_pnl: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

export interface Trade {
  id: number;
  ticker: string;
  order_type: string;
  quantity: number;
  execution_price: number;
  total_amount: number;
  realized_pnl: number;
  executed_at: string;
}

export async function fetchMarketData(ticker: string): Promise<StockMarketData> {
  const res = await fetch(`${API_BASE_URL}/api/market/${encodeURIComponent(ticker)}`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Erreur de chargement des données TSX.");
  }
  return res.json();
}

export async function fetchSentiment(ticker: string): Promise<SentimentData> {
  const res = await fetch(`${API_BASE_URL}/api/sentiment/${encodeURIComponent(ticker)}`);
  if (!res.ok) throw new Error("Erreur de récupération du sentiment.");
  return res.json();
}

export async function fetchPortfolio(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE_URL}/api/trading/portfolio`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Erreur de récupération du portefeuille.");
  return res.json();
}

export async function fetchPnlHistory(): Promise<PnlSnapshot[]> {
  const res = await fetch(`${API_BASE_URL}/api/trading/pnl-history`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Erreur de récupération de l'historique P&L.");
  return res.json();
}

export async function fetchTradeHistory(): Promise<Trade[]> {
  const res = await fetch(`${API_BASE_URL}/api/trading/history`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Erreur de récupération de l'historique des trades.");
  return res.json();
}

export async function buyStock(ticker: string, quantity: number): Promise<Trade> {
  const res = await fetch(`${API_BASE_URL}/api/trading/buy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, quantity })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Échec de l'ordre d'achat.");
  return data;
}

export async function sellStock(ticker: string, quantity: number): Promise<Trade> {
  const res = await fetch(`${API_BASE_URL}/api/trading/sell`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, quantity })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Échec de l'ordre de vente.");
  return data;
}

export async function resetPortfolio(): Promise<PortfolioSummary> {
  const res = await fetch(`${API_BASE_URL}/api/trading/reset`, { method: "POST" });
  if (!res.ok) throw new Error("Échec de la réinitialisation du portefeuille.");
  return res.json();
}
