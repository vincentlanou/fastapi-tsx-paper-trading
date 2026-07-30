import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
import math
from functools import lru_cache

from app.config import ALLOWED_TSX_TICKERS, MIN_MARKET_CAP_TSX, TRANSACTION_FEE_CAD, BID_ASK_SPREAD_SLIPPAGE, RISK_FREE_RATE
from app.schemas.market import StockMarketDataResponse, MomentumIndicators, PricePoint
from app.services.sentiment_service import get_news_sentiment

logger = logging.getLogger(__name__)

def normalize_tsx_ticker(raw_ticker: str) -> str:
    """Normalize input ticker to TSX format (.TO extension)."""
    clean = raw_ticker.strip().upper()
    if not clean.endswith(".TO") and not clean.endswith(".V"):
        clean += ".TO"
    return clean

@lru_cache(maxsize=1)
def get_benchmark_returns() -> pd.Series:
    """Returns 60-day historical returns for XIU.TO to calculate correlation bonus. Caches the result."""
    yticker = yf.Ticker("XIU.TO")
    df = yticker.history(period="3mo")
    if df.empty:
        return pd.Series()
    return df["Close"].pct_change().dropna()

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
            f"The stock '{ticker}' is not eligible. "
            f"Only Large Cap stocks traded on the Toronto Stock Exchange (TSX, e.g. SHOP.TO, RY.TO, NVDA.TO, AAPL.TO, AZN.TO) are allowed."
        )
        
    return norm_ticker, info

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using Wilder's Exponential Smoothing."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
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

def calculate_rvol(volume_series: pd.Series, window: int = 20) -> float:
    """Calculate Relative Volume (RVOL = Volume / MA20_Volume)."""
    if volume_series.empty or len(volume_series) < window:
        return 1.0
    latest_vol = float(volume_series.iloc[-1])
    ma_vol = float(volume_series.tail(window).mean())
    return round(latest_vol / ma_vol, 2) if ma_vol > 0 else 1.0

def calculate_mean_reversion_penalty(prices: pd.Series, rsi: float) -> float:
    """Calculate Mean Reversion Penalty (0 to 10 points subtracted if stock is overbought/overextended)."""
    penalty = 0.0
    if rsi > 70.0:
        penalty += (rsi - 70.0) * 0.4  # e.g., RSI=80 -> +4.0 penalty
        
    if len(prices) >= 20:
        ma20 = prices.tail(20).mean()
        std20 = prices.tail(20).std()
        upper_bb = ma20 + (2.0 * std20)
        curr_p = prices.iloc[-1]
        if curr_p > upper_bb and upper_bb > 0:
            overextension = ((curr_p - upper_bb) / upper_bb) * 100.0
            penalty += min(6.0, overextension * 2.0)
            
    return round(min(10.0, penalty), 1)

def calculate_sharpe_and_sortino(prices: pd.Series, risk_free_rate: float = RISK_FREE_RATE) -> Tuple[float, float, float, float]:
    """Calculate Sharpe Ratio, Sortino Ratio, Annualized Volatility, and Max Drawdown."""
    daily_returns = prices.pct_change().dropna()
    if daily_returns.empty or len(daily_returns) < 10:
        return None, None, None, None
        
    ann_return = daily_returns.mean() * 252
    ann_vol = daily_returns.std() * np.sqrt(252)
    
    sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 1e-6 else 0.0
    
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else ann_vol
    sortino = (ann_return - risk_free_rate) / downside_vol if downside_vol > 1e-6 else sharpe
    
    cum_max = prices.cummax()
    drawdowns = (prices - cum_max) / cum_max
    max_dd = float(drawdowns.min() * 100.0) if not drawdowns.empty else 0.0
    
    return round(float(sharpe), 2), round(float(sortino), 2), round(float(ann_vol * 100.0), 1), round(max_dd, 1)

def calculate_tail_risk(prices: pd.Series) -> Tuple[float, float]:
    """Calculate 10-day Parametric VaR (95%) and Historical CVaR (95%)."""
    daily_returns = prices.pct_change().dropna()
    if len(daily_returns) < 10:
        return None, None
        
    rolling_10d_returns = daily_returns.rolling(10).apply(lambda x: (1 + x).prod() - 1, raw=False).dropna()
    if rolling_10d_returns.empty:
        return None, None
        
    mu = rolling_10d_returns.mean()
    sigma = rolling_10d_returns.std()
    
    # Parametric VaR 95%
    var_95 = -(mu - 1.645 * sigma) * 100.0
    
    # Historical CVaR 95% (Expected Shortfall)
    threshold = rolling_10d_returns.quantile(0.05)
    tail_losses = rolling_10d_returns[rolling_10d_returns <= threshold]
    cvar_95 = -tail_losses.mean() * 100.0 if not tail_losses.empty else var_95
    
    return round(float(var_95), 2), round(float(cvar_95), 2)

def calculate_risk_parity_weights(volatilities: List[float]) -> List[float]:
    """Calculate Step 2 Risk Parity Position Sizing (Inverse Volatility Weighting)."""
    inv_vols = [1.0 / max(1.0, v) for v in volatilities]
    total_inv_vol = sum(inv_vols)
    if total_inv_vol <= 0:
        return [100.0 / len(volatilities)] * len(volatilities)
    return [round((iv / total_inv_vol) * 100.0, 1) for iv in inv_vols]

def get_stock_data_and_indicators(ticker: str, period: str = "6mo") -> StockMarketDataResponse:
    """Fetch TSX market data via yfinance and calculate 4-Stage Alpha Score & Risk Parity indicators."""
    norm_ticker, info = validate_tsx_large_cap(ticker)
    yticker = yf.Ticker(norm_ticker)
    
    df = yticker.history(period=period)
    if df.empty:
        df = yticker.history(period="1mo")
        if df.empty:
            raise ValueError(f"Données de marché indisponibles pour '{norm_ticker}'.")
    
    close_prices = df["Close"]
    volume_series = df["Volume"] if "Volume" in df else pd.Series([1000000]*len(df))
    
    rsi_series = calculate_rsi(close_prices, period=14)
    macd_line, signal_line, histogram = calculate_macd(close_prices, fast=12, slow=26, signal=9)
    rvol = calculate_rvol(volume_series, window=20)
    sharpe, sortino, volatility, max_dd = calculate_sharpe_and_sortino(close_prices)
    var_10d, cvar_10d = calculate_tail_risk(close_prices)
    
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
        
    # Step 1: 4-Stage Alpha Score Components (0-100)
    # 1) NLP News Sentiment Baseline via Gemini / Fallback
    try:
        sentiment_data = get_news_sentiment(norm_ticker)
        nlp_sentiment_score = sentiment_data.sentiment_score
    except Exception:
        nlp_sentiment_score = 50.0  # Safe neutral fallback if fetching fails
    # 2) Momentum Score (RSI + MACD)
    macd_score_contrib = np.clip(curr_hist / (latest_price * 0.02), -1.0, 1.0) * 50 + 50
    momentum_score = (curr_rsi * 0.5) + (macd_score_contrib * 0.5)
    rvol_score = min(100.0, rvol * 50.0)
    penalty = calculate_mean_reversion_penalty(close_prices, curr_rsi)
    
    alpha_score = np.clip((0.70 * momentum_score) + (0.30 * rvol_score) - penalty, 0.0, 100.0)
    
    # Decorrelation bonus
    bench_returns = get_benchmark_returns()
    returns = close_prices.pct_change().dropna()
    if not bench_returns.empty and len(returns) >= 20:
        aligned = pd.concat([returns, bench_returns], axis=1, join="inner").dropna()
        if len(aligned) >= 20:
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            if not np.isnan(corr):
                decorr_bonus = (1.0 - corr) * 10.0
                alpha_score = np.clip(alpha_score + decorr_bonus, 0.0, 100.0)
                
    alpha_score = float(np.round(alpha_score, 2))

    # Risk Parity Sizing (Expected Return vs Downside Risk)
    neg_returns = returns[returns < 0]
    if not neg_returns.empty and len(neg_returns) >= 5:
        downside_vol = neg_returns.std() * np.sqrt(252) * 100.0
    else:
        downside_vol = 15.0
        
    downside_vol = max(1.0, downside_vol)
    # Give a weight proportional to Alpha / Downside Vol. We'll clip between 10 and 33.
    # Typical Alpha/Downside ratio is around 50 / 15 = 3.3. So multiplying by 5 gives ~ 16%.
    ratio = alpha_score / downside_vol
    risk_parity_weight = float(np.round(np.clip(ratio * 5.0, 10.0, 33.0), 2))
    
    if alpha_score >= 60:
        overall_momentum_signal = "BULLISH"
    elif alpha_score <= 40:
        overall_momentum_signal = "BEARISH"
    else:
        overall_momentum_signal = "NEUTRAL"

    indicators = MomentumIndicators(
        current_rsi=round(curr_rsi, 2),
        rsi_status=rsi_status,
        current_macd=round(curr_macd, 4),
        current_macd_signal=round(curr_signal, 4),
        current_macd_histogram=round(curr_hist, 4),
        macd_status=macd_status,
        overall_momentum_signal=overall_momentum_signal,
        momentum_score=alpha_score,
        rvol=rvol,
        mean_reversion_penalty=penalty,
        alpha_score=alpha_score,
        risk_parity_weight=risk_parity_weight,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        volatility_annualized=volatility,
        max_drawdown=max_dd,
        var_10d_95=var_10d,
        cvar_10d_95=cvar_10d
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

def get_alpha_score_only(ticker: str) -> float | None:
    """Fast-path to calculate just the Alpha Score for autopilot ranking."""
    try:
        norm_ticker, info = validate_tsx_large_cap(ticker)
        yticker = yf.Ticker(norm_ticker)
        df = yticker.history(period="1mo")
        if df.empty or len(df) < 20:
            return None
            
        close_prices = df["Close"]
        volume_series = df["Volume"] if "Volume" in df else pd.Series([1000000]*len(df))
        
        rsi_series = calculate_rsi(close_prices, period=14)
        macd_line, signal_line, histogram = calculate_macd(close_prices, fast=12, slow=26, signal=9)
        rvol = calculate_rvol(volume_series, window=20)
        
        curr_rsi = float(rsi_series.iloc[-1])
        curr_hist = float(histogram.iloc[-1])
        latest_price = float(close_prices.iloc[-1])
        
        try:
            sentiment_data = get_news_sentiment(norm_ticker)
            nlp_sentiment_score = sentiment_data.sentiment_score
        except Exception:
            return None
            
        macd_score_contrib = np.clip(curr_hist / (latest_price * 0.02), -1.0, 1.0) * 50 + 50
        momentum_score = (curr_rsi * 0.5) + (macd_score_contrib * 0.5)
        rvol_score = min(100.0, rvol * 50.0)
        penalty = calculate_mean_reversion_penalty(close_prices, curr_rsi)
        
        alpha_score = np.clip((0.70 * momentum_score) + (0.30 * rvol_score) - penalty, 0.0, 100.0)
        
        bench_returns = get_benchmark_returns()
        returns = close_prices.pct_change().dropna()
        if not bench_returns.empty and len(returns) >= 20:
            aligned = pd.concat([returns, bench_returns], axis=1, join="inner").dropna()
            if len(aligned) >= 20:
                corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
                if not np.isnan(corr):
                    decorr_bonus = (1.0 - corr) * 10.0
                    alpha_score = np.clip(alpha_score + decorr_bonus, 0.0, 100.0)
        
        return float(np.round(alpha_score, 2))
    except Exception:
        return None
