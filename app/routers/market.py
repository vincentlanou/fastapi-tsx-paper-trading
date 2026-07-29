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

@router.get("/regime/global")
def get_global_market_regime():
    """Evaluate TSX (XIU.TO) to determine the global market regime (NORMAL, FALLING_KNIFE, RECOVERY)."""
    try:
        from app.services.trading_service import check_market_regime
        regime, message = check_market_regime()
        return {"regime": regime, "message": message}
    except Exception as e:
        # Fallback to normal if yfinance fails
        return {"regime": "NORMAL", "message": "Failed to fetch benchmark, defaulting to Normal."}

@router.get("/universe")
def get_market_universe():
    """Return the list of all allowed tickers in the TSX large cap & CDR universe."""
    from app.config import ALLOWED_TSX_TICKERS
    return {"tickers": sorted(list(ALLOWED_TSX_TICKERS))}
