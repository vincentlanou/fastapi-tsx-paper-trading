import math
import yfinance as yf
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from fastapi import HTTPException
from app.config import (
    INITIAL_BALANCE, DEFAULT_ACCOUNT_NAME,
    TRANSACTION_FEE_CAD, BID_ASK_SPREAD_SLIPPAGE, MAX_POSITIONS
)
from app.db.models import Account, Position, Trade, PortfolioSnapshot
from app.schemas.trading import PortfolioResponse, PositionResponse, TradeResponse
from app.services.market_service import validate_tsx_large_cap, normalize_tsx_ticker
from app.services.notification_service import notify_buy_trade, notify_sell_trade

def get_or_create_account(db: Session) -> Account:
    """Ensure a paper trading account exists and initial snapshot is logged."""
    account = db.query(Account).first()
    if not account:
        account = Account(name=DEFAULT_ACCOUNT_NAME, cash_balance=INITIAL_BALANCE)
        db.add(account)
        db.commit()
        db.refresh(account)
        record_snapshot(db, account)
    return account

def record_snapshot(db: Session, account: Account):
    """Record a portfolio equity & P&L snapshot for Recharts timeline."""
    raw_positions = db.query(Position).filter(Position.account_id == account.id).all()
    stock_value = 0.0
    unrealized_pnl = 0.0

    for pos in raw_positions:
        if pos.quantity <= 0:
            continue
        try:
            yt = yf.Ticker(pos.ticker)
            price = getattr(yt, "info", {}).get("currentPrice") or pos.average_buy_price
        except Exception:
            price = pos.average_buy_price
            
        mkt = price * pos.quantity
        unrealized = (price - pos.average_buy_price) * pos.quantity
        stock_value += mkt
        unrealized_pnl += unrealized

    total_equity = account.cash_balance + stock_value
    trades = db.query(Trade).filter(Trade.account_id == account.id).all()
    realized_pnl = sum(t.realized_pnl for t in trades if t.order_type == "SELL")
    total_pnl = total_equity - INITIAL_BALANCE

    snap = PortfolioSnapshot(
        account_id=account.id,
        timestamp=datetime.utcnow(),
        total_equity=round(total_equity, 2),
        cash_balance=round(account.cash_balance, 2),
        stock_value=round(stock_value, 2),
        total_pnl=round(total_pnl, 2),
        realized_pnl=round(realized_pnl, 2),
        unrealized_pnl=round(unrealized_pnl, 2)
    )
    db.add(snap)
    db.commit()

def get_live_price(ticker: str) -> float:
    """Fetch current TSX market price for a ticker via yfinance."""
    norm_ticker = normalize_tsx_ticker(ticker)
    yticker = yf.Ticker(norm_ticker)
    info = getattr(yticker, "info", {}) or {}
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    
    if not price:
        df = yticker.history(period="5d")
        if df.empty:
            raise HTTPException(status_code=400, detail=f"Prix indisponible pour le ticker TSX '{norm_ticker}'.")
        price = float(df["Close"].iloc[-1])
        
    return float(price)

def buy_stock(db: Session, ticker: str, quantity: float) -> TradeResponse:
    """Execute paper buy order with integer shares, spread slippage, and transaction fee deduction."""
    # Enforce Integer Shares (Actions complètes uniquement)
    int_qty = math.floor(quantity)
    if int_qty < 1:
        raise HTTPException(
            status_code=400,
            detail="La quantité doit être d'au moins 1 action complète (les fractions d'actions ne sont pas autorisées)."
        )
        
    try:
        norm_ticker, _ = validate_tsx_large_cap(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    account = get_or_create_account(db)
    
    # Enforce Maximum Open Positions Constraint (Max 5 positions)
    existing_pos = db.query(Position).filter(
        Position.account_id == account.id,
        Position.ticker == norm_ticker
    ).first()
    
    active_positions_count = db.query(Position).filter(
        Position.account_id == account.id,
        Position.quantity > 0
    ).count()
    
    if not existing_pos and active_positions_count >= MAX_POSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de portefeuille atteinte. Vous ne pouvez détenir que {MAX_POSITIONS} positions ouvertes simultanément pour maintenir une bonne diversification sur votre capital de ${INITIAL_BALANCE:,.0f} CAD."
        )

    # Price with Bid/Ask Spread Slippage (Achat au Ask +0.10%)
    raw_market_price = get_live_price(norm_ticker)
    execution_price = raw_market_price * (1.0 + BID_ASK_SPREAD_SLIPPAGE)
    stock_cost = execution_price * int_qty
    total_cost_with_fee = stock_cost + TRANSACTION_FEE_CAD
    
    if account.cash_balance < total_cost_with_fee:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Solde virtuel insuffisant. Requis : ${total_cost_with_fee:,.2f} CAD "
                f"(${stock_cost:,.2f} actions + ${TRANSACTION_FEE_CAD:,.2f} frais de courtage), "
                f"Disponible : ${account.cash_balance:,.2f} CAD."
            )
        )
        
    account.cash_balance -= total_cost_with_fee
    
    if existing_pos:
        new_quantity = existing_pos.quantity + int_qty
        new_avg_price = ((existing_pos.quantity * existing_pos.average_buy_price) + stock_cost) / new_quantity
        existing_pos.quantity = new_quantity
        existing_pos.average_buy_price = new_avg_price
    else:
        existing_pos = Position(
            account_id=account.id,
            ticker=norm_ticker,
            quantity=float(int_qty),
            average_buy_price=execution_price
        )
        db.add(existing_pos)
        
    trade = Trade(
        account_id=account.id,
        ticker=norm_ticker,
        order_type="BUY",
        quantity=float(int_qty),
        execution_price=execution_price,
        total_amount=total_cost_with_fee,
        realized_pnl=-TRANSACTION_FEE_CAD, # Initial fee impact
        executed_at=datetime.utcnow()
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    record_snapshot(db, account)
    
    notify_buy_trade(
        ticker=norm_ticker,
        quantity=float(int_qty),
        execution_price=execution_price,
        total_amount=total_cost_with_fee,
        cash_balance=account.cash_balance
    )
    
    return TradeResponse(
        id=trade.id,
        ticker=trade.ticker,
        order_type=trade.order_type,
        quantity=trade.quantity,
        execution_price=round(trade.execution_price, 2),
        total_amount=round(trade.total_amount, 2),
        realized_pnl=round(trade.realized_pnl, 2),
        executed_at=trade.executed_at.strftime("%Y-%m-%d %H:%M:%S")
    )

def sell_stock(db: Session, ticker: str, quantity: float) -> TradeResponse:
    """Execute paper sell order with integer shares, spread slippage, and transaction fee deduction."""
    int_qty = math.floor(quantity)
    if int_qty < 1:
        raise HTTPException(status_code=400, detail="La quantité de vente doit être d'au moins 1 action complète.")
        
    norm_ticker = normalize_tsx_ticker(ticker)
    account = get_or_create_account(db)
    
    pos = db.query(Position).filter(
        Position.account_id == account.id,
        Position.ticker == norm_ticker
    ).first()
    
    if not pos or pos.quantity < int_qty:
        available_qty = int(pos.quantity) if pos else 0
        raise HTTPException(
            status_code=400,
            detail=f"Position insuffisante sur '{norm_ticker}'. Disponible: {available_qty} action(s), Demandée: {int_qty}"
        )
        
    # Price with Bid/Ask Spread Slippage (Vente au Bid -0.10%)
    raw_market_price = get_live_price(norm_ticker)
    execution_price = raw_market_price * (1.0 - BID_ASK_SPREAD_SLIPPAGE)
    gross_proceeds = execution_price * int_qty
    net_proceeds = gross_proceeds - TRANSACTION_FEE_CAD
    
    # Calculate Net Realized P&L taking into account buy avg cost + sell fee
    cost_basis = pos.average_buy_price * int_qty
    realized_pnl = net_proceeds - cost_basis
    
    account.cash_balance += net_proceeds
    
    pos.quantity -= int_qty
    if pos.quantity <= 1e-6:
        db.delete(pos)
        
    trade = Trade(
        account_id=account.id,
        ticker=norm_ticker,
        order_type="SELL",
        quantity=float(int_qty),
        execution_price=execution_price,
        total_amount=net_proceeds,
        realized_pnl=realized_pnl,
        executed_at=datetime.utcnow()
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    record_snapshot(db, account)
    
    notify_sell_trade(
        ticker=norm_ticker,
        quantity=float(int_qty),
        execution_price=execution_price,
        total_amount=net_proceeds,
        realized_pnl=realized_pnl,
        cash_balance=account.cash_balance
    )
    
    return TradeResponse(
        id=trade.id,
        ticker=trade.ticker,
        order_type=trade.order_type,
        quantity=trade.quantity,
        execution_price=round(trade.execution_price, 2),
        total_amount=round(trade.total_amount, 2),
        realized_pnl=round(trade.realized_pnl, 2),
        executed_at=trade.executed_at.strftime("%Y-%m-%d %H:%M:%S")
    )

def get_portfolio_summary(db: Session) -> PortfolioResponse:
    """Calculate and return TSX portfolio metrics, positions, and virtual net P&L."""
    account = get_or_create_account(db)
    raw_positions = db.query(Position).filter(Position.account_id == account.id).all()
    
    position_responses = []
    total_stock_value = 0.0
    total_unrealized_pnl = 0.0
    
    for pos in raw_positions:
        if pos.quantity <= 0:
            continue
        try:
            live_price = get_live_price(pos.ticker)
        except Exception:
            live_price = pos.average_buy_price
            
        mkt_val = live_price * pos.quantity
        unrealized = (live_price - pos.average_buy_price) * pos.quantity
        unrealized_pct = ((live_price - pos.average_buy_price) / pos.average_buy_price) * 100.0 if pos.average_buy_price else 0.0
        
        total_stock_value += mkt_val
        total_unrealized_pnl += unrealized
        
        position_responses.append(PositionResponse(
            id=pos.id,
            ticker=pos.ticker,
            quantity=round(pos.quantity, 0),
            average_buy_price=round(pos.average_buy_price, 2),
            current_price=round(live_price, 2),
            market_value=round(mkt_val, 2),
            unrealized_pnl=round(unrealized, 2),
            unrealized_pnl_pct=round(unrealized_pct, 2),
            updated_at=pos.updated_at.strftime("%Y-%m-%d %H:%M:%S") if pos.updated_at else ""
        ))
        
    total_equity = account.cash_balance + total_stock_value
    trades = db.query(Trade).filter(Trade.account_id == account.id).all()
    total_realized_pnl = sum(t.realized_pnl for t in trades if t.order_type == "SELL")
    
    total_pnl = total_equity - INITIAL_BALANCE
    total_pnl_pct = ((total_equity - INITIAL_BALANCE) / INITIAL_BALANCE) * 100.0 if INITIAL_BALANCE else 0.0
    
    return PortfolioResponse(
        account_id=account.id,
        account_name=account.name,
        cash_balance=round(account.cash_balance, 2),
        portfolio_stock_value=round(total_stock_value, 2),
        total_equity=round(total_equity, 2),
        total_realized_pnl=round(total_realized_pnl, 2),
        total_unrealized_pnl=round(total_unrealized_pnl, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round(total_pnl_pct, 2),
        positions=position_responses
    )

def get_pnl_history(db: Session) -> list[dict]:
    """Retrieve P&L snapshot history for Recharts timeline."""
    account = get_or_create_account(db)
    snaps = db.query(PortfolioSnapshot).filter(PortfolioSnapshot.account_id == account.id).order_by(PortfolioSnapshot.timestamp.asc()).all()
    
    if not snaps:
        return [{
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "total_equity": INITIAL_BALANCE,
            "cash_balance": INITIAL_BALANCE,
            "total_pnl": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0
        }]

    return [
        {
            "timestamp": s.timestamp.strftime("%H:%M:%S"),
            "total_equity": round(s.total_equity, 2),
            "cash_balance": round(s.cash_balance, 2),
            "total_pnl": round(s.total_pnl, 2),
            "realized_pnl": round(s.realized_pnl, 2),
            "unrealized_pnl": round(s.unrealized_pnl, 2)
        }
        for s in snaps
    ]

def get_trade_history(db: Session) -> list[TradeResponse]:
    """Retrieve history of executed paper trades."""
    account = get_or_create_account(db)
    trades = db.query(Trade).filter(Trade.account_id == account.id).order_by(Trade.executed_at.desc()).all()
    
    return [
        TradeResponse(
            id=t.id,
            ticker=t.ticker,
            order_type=t.order_type,
            quantity=t.quantity,
            execution_price=round(t.execution_price, 2),
            total_amount=round(t.total_amount, 2),
            realized_pnl=round(t.realized_pnl, 2),
            executed_at=t.executed_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        for t in trades
    ]

def reset_account(db: Session) -> PortfolioResponse:
    """Reset virtual account cash to $5,000 CAD and wipe positions/trade history."""
    account = get_or_create_account(db)
    db.query(Position).filter(Position.account_id == account.id).delete()
    db.query(Trade).filter(Trade.account_id == account.id).delete()
    db.query(PortfolioSnapshot).filter(PortfolioSnapshot.account_id == account.id).delete()
    account.cash_balance = INITIAL_BALANCE
    db.commit()
    db.refresh(account)
    record_snapshot(db, account)
    return get_portfolio_summary(db)
