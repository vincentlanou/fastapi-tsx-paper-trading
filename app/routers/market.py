from fastapi import APIRouter, HTTPException, Query
from app.schemas.market import StockMarketDataResponse
from app.services.market_service import get_stock_data_and_indicators

router = APIRouter(prefix="/api/market", tags=["Market Data & Indicators"])

@router.get("/{ticker}", response_model=StockMarketDataResponse)
def get_market_data(ticker: str, period: str = Query(default="6mo", description="Period: 1mo, 3mo, 6mo, 1y")):
    """Get real-time market data, price action, RSI (14) & MACD (12,26,9) indicators."""
    try:
        return get_stock_data_and_indicators(ticker, period=period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
