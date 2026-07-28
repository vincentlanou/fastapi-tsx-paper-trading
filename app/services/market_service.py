import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from app.config import ALLOWED_TSX_TICKERS, MIN_MARKET_CAP_TSX
from app.schemas.market import StockMarketDataResponse, MomentumIndicators, PricePoint

def normalize_tsx_ticker(raw_ticker: str) -> str:
    """Normalize input ticker to TSX format (.TO extension)."""
    clean = raw_ticker.strip().upper()
    if not clean.endswith(".TO") and not clean.endswith(".V"):
        clean += ".TO"
    return clean

def validate_tsx_large_cap(ticker: str) -> Tuple[str, Dict[str, Any]]:
    """Validate that ticker is a Large Cap stock listed on the Toronto Stock Exchange (TSX)."""
    norm_ticker = normalize_tsx_ticker(ticker)
    yticker = yf.Ticker(norm_ticker)
    info = getattr(yticker, "info", {}) or {}
    
    if norm_ticker in ALLOWED_TSX_TICKERS:
        return norm_ticker, info
        
    exchange = (info.get("exchange") or info.get("financialCurrency") or "").upper()
    market_cap = info.get("marketCap") or 0
    
    is_tsx = norm_ticker.endswith(".TO") or "TOR" in exchange or "TSX" in exchange
    is_large_cap = market_cap >= MIN_MARKET_CAP_TSX or norm_ticker in ALLOWED_TSX_TICKERS
    
    if not is_tsx or not is_large_cap:
        raise ValueError(
            f"L'action '{ticker}' n'est pas autorisée. "
            f"Seules les actions Large Cap de la Bourse de Toronto (TSX, ex: SHOP.TO, RY.TO, TD.TO, ENB.TO) sont acceptées."
        )
        
    return norm_ticker, info

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Moving Average Convergence Divergence (MACD)."""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def get_stock_data_and_indicators(ticker: str, period: str = "6mo") -> StockMarketDataResponse:
    """Fetch TSX market data via yfinance and calculate momentum indicators & 5-day horizon flags."""
    norm_ticker, info = validate_tsx_large_cap(ticker)
    yticker = yf.Ticker(norm_ticker)
    
    df = yticker.history(period=period)
    if df.empty:
        df = yticker.history(period="1mo")
        if df.empty:
            raise ValueError(f"Données de marché indisponibles pour '{norm_ticker}'.")
    
    close_prices = df["Close"]
    rsi_series = calculate_rsi(close_prices, period=14)
    macd_line, signal_line, histogram = calculate_macd(close_prices, fast=12, slow=26, signal=9)
    
    df["RSI"] = rsi_series
    df["MACD"] = macd_line
    df["Signal"] = signal_line
    df["Histogram"] = histogram
    
    latest_price = float(close_prices.iloc[-1])
    prev_close = float(close_prices.iloc[-2]) if len(close_prices) > 1 else latest_price
    price_change = latest_price - prev_close
    price_change_pct = (price_change / prev_close) * 100 if prev_close else 0.0
    
    curr_rsi = float(df["RSI"].iloc[-1])
    curr_macd = float(df["MACD"].iloc[-1])
    curr_signal = float(df["Signal"].iloc[-1])
    curr_hist = float(df["Histogram"].iloc[-1])
    
    if curr_rsi >= 70:
        rsi_status = "OVERBOUGHT"
    elif curr_rsi <= 30:
        rsi_status = "OVERSOLD"
    else:
        rsi_status = "NEUTRAL"
        
    if curr_hist > 0 and (len(df) > 1 and df["Histogram"].iloc[-2] <= 0):
        macd_status = "BULLISH_CROSSOVER"
    elif curr_hist < 0 and (len(df) > 1 and df["Histogram"].iloc[-2] >= 0):
        macd_status = "BEARISH_CROSSOVER"
    elif curr_hist > 0:
        macd_status = "BULLISH"
    else:
        macd_status = "BEARISH"
        
    macd_score_contrib = np.clip(curr_hist / (latest_price * 0.02), -1.0, 1.0) * 50 + 50
    momentum_score = float(np.round((curr_rsi * 0.5) + (macd_score_contrib * 0.5), 2))
    
    if momentum_score >= 60:
        overall_momentum_signal = "BULLISH"
    elif momentum_score <= 40:
        overall_momentum_signal = "BEARISH"
    else:
        overall_momentum_signal = "NEUTRAL"

    # 5-Day Horizon Rule Triggers
    if momentum_score <= 35 or macd_status == "BEARISH_CROSSOVER" or curr_rsi <= 32:
        recommended_action = "CRITICAL_EXIT_RISK"
    elif momentum_score >= 75 and macd_status == "BULLISH_CROSSOVER":
        recommended_action = "CRITICAL_BUY_OPPORTUNITY"
    else:
        recommended_action = "HOLD_5_DAYS"
        
    indicators = MomentumIndicators(
        current_rsi=round(curr_rsi, 2),
        rsi_status=rsi_status,
        current_macd=round(curr_macd, 4),
        current_macd_signal=round(curr_signal, 4),
        current_macd_histogram=round(curr_hist, 4),
        macd_status=macd_status,
        overall_momentum_signal=overall_momentum_signal,
        momentum_score=momentum_score
    )
    
    chart_data = []
    for idx, row in df.tail(90).iterrows():
        chart_data.append(PricePoint(
            date=idx.strftime("%Y-%m-%d"),
            price=round(float(row["Close"]), 2),
            rsi=round(float(row["RSI"]), 2) if not np.isnan(row["RSI"]) else None,
            macd=round(float(row["MACD"]), 4) if not np.isnan(row["MACD"]) else None,
            signal_line=round(float(row["Signal"]), 4) if not np.isnan(row["Signal"]) else None,
            histogram=round(float(row["Histogram"]), 4) if not np.isnan(row["Histogram"]) else None
        ))
        
    company_name = info.get("shortName") or info.get("longName") or norm_ticker
    
    return StockMarketDataResponse(
        ticker=norm_ticker,
        company_name=company_name,
        current_price=round(latest_price, 2),
        previous_close=round(prev_close, 2),
        price_change=round(price_change, 2),
        price_change_pct=round(price_change_pct, 2),
        currency=info.get("currency", "CAD"),
        indicators=indicators,
        chart_data=chart_data
    )
