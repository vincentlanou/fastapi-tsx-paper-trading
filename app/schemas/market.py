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

class StockMarketDataResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    current_price: float
    previous_close: float
    price_change: float
    price_change_pct: float
    currency: str = "USD"
    indicators: MomentumIndicators
    chart_data: List[PricePoint]
