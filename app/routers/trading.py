from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.trading import TradeRequest, TradeResponse, PortfolioResponse
from app.services import trading_service

router = APIRouter(prefix="/api/trading", tags=["Paper Trading Engine"])

@router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(db: Session = Depends(get_db)):
    """Retrieve current TSX paper trading portfolio summary, positions, equity & P&L."""
    return trading_service.get_portfolio_summary(db)

@router.get("/pnl-history", response_model=List[Dict[str, Any]])
def get_pnl_history(db: Session = Depends(get_db)):
    """Retrieve P&L snapshot evolution timeline for Recharts."""
    return trading_service.get_pnl_history(db)

@router.get("/history", response_model=List[TradeResponse])
def get_history(db: Session = Depends(get_db)):
    """Retrieve complete trade execution audit log."""
    return trading_service.get_trade_history(db)

@router.post("/buy", response_model=TradeResponse)
def execute_buy(trade_req: TradeRequest, db: Session = Depends(get_db)):
    """Simulate stock buy order for TSX Large Cap stock."""
    return trading_service.buy_stock(db, ticker=trade_req.ticker, quantity=trade_req.quantity)

@router.post("/sell", response_model=TradeResponse)
def execute_sell(trade_req: TradeRequest, db: Session = Depends(get_db)):
    """Simulate stock sell order and record realized P&L."""
    return trading_service.sell_stock(db, ticker=trade_req.ticker, quantity=trade_req.quantity)

@router.post("/reset", response_model=PortfolioResponse)
def reset_portfolio(db: Session = Depends(get_db)):
    """Reset virtual cash balance to $100,000 CAD and clear active positions & trade history."""
    return trading_service.reset_account(db)

@router.get("/benchmarks")
def get_benchmarks(db: Session = Depends(get_db)):
    """Get TSX 60 and S&P 500 performance since portfolio inception."""
    try:
        from app.services.trading_service import get_benchmarks_performance
        return get_benchmarks_performance(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
