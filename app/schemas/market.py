from typing import List, Optional
from pydantic import BaseModel

class PricePoint(BaseModel):
    date: str
    price: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    signal_line: Optional[float] = None
    histogram: Optional[float] = None

class MomentumIndicators(BaseModel):
    current_rsi: float
    rsi_status: str  # OVERBOUGHT, OVERSOLD, NEUTRAL
    current_macd: float
    current_macd_signal: float
    current_macd_histogram: float
    macd_status: str # BULLISH_CROSSOVER, BEARISH_CROSSOVER, NEUTRAL
    overall_momentum_signal: str # BULLISH, BEARISH, NEUTRAL
    momentum_score: float # 0 to 100
    
    # 4-Stage Alpha Score & Gemini Risk Parity Indicators
    # 4-Stage Alpha Score & Gemini Risk Parity Indicators
    rvol: Optional[float] = None           # Relative Volume (Volume / MA20)
    mean_reversion_penalty: Optional[float] = None # 0 to 10 points penalty
    alpha_score: Optional[float] = None   # 4-stage Alpha Score (0-100)
    risk_parity_weight: Optional[float] = None # Suggested position size %
    
    # Risk-Adjusted Ratios
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    volatility_annualized: Optional[float] = None # in %
    max_drawdown: Optional[float] = None # in %
    var_10d_95: Optional[float] = None # 10-day Parametric VaR (95%)
    cvar_10d_95: Optional[float] = None # 10-day Expected Shortfall (95%)

class StockMarketDataResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: float
    previous_close: float
    price_change: float
    price_change_pct: float
    currency: str = "CAD"
    indicators: MomentumIndicators
    chart_data: List[PricePoint]
