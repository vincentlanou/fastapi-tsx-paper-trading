from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class TradeRequest(BaseModel):
    ticker: str
    quantity: float

class PositionResponse(BaseModel):
    id: int
    ticker: str
    quantity: float
    average_buy_price: float
    peak_price: Optional[float] = 0.0
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    updated_at: str

class PortfolioResponse(BaseModel):
    account_id: int
    account_name: str
    created_at: str
    cash_balance: float
    portfolio_stock_value: float
    total_equity: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[PositionResponse]

class TradeResponse(BaseModel):
    id: int
    ticker: str
    order_type: str
    quantity: float
    execution_price: float
    total_amount: float
    realized_pnl: float
    executed_at: str
