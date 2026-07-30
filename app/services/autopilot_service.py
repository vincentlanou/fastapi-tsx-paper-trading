import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import yfinance as yf

from app.config import ALLOWED_TSX_TICKERS, MAX_POSITIONS, MIN_POSITION_SIZE, INITIAL_BALANCE
from app.db.models import Account, Position, Trade
from app.services import market_service, trading_service, notification_service
from app.services.sentiment_service import get_market_regime

logger = logging.getLogger("autopilot_service")

# --- Autopilot Settings ---
TRAILING_STOP_LOSS_PCT = -15.0   # Exit if price drops 15% from peak_price
ALPHA_DEGRADATION_THRESHOLD = 35.0  # Exit if Alpha Score drops below 35
MAX_HOLD_DAYS_WITHOUT_GAIN = 20  # Exit if held for > 20 days and unrealized_pnl_pct < 5.0%

def scan_universe() -> list[dict]:
    """
    Scans the TSX universe, calculates Alpha Score for each ticker,
    and returns a sorted list of top candidates (Alpha Score > threshold).
    Ignores tickers with insufficient/fallback data.
    """
    candidates = []
    
    # In a real environment, you might scan a larger list.
    # For this paper trading bot, we use ALLOWED_TSX_TICKERS (75 stocks)
    for ticker in ALLOWED_TSX_TICKERS:
        try:
            alpha = market_service.get_alpha_score_only(ticker)
            if alpha is not None:
                candidates.append({"ticker": ticker, "alpha_score": alpha})
        except Exception as e:
            logger.warning(f"Failed to scan {ticker}: {e}")
            continue
            
    # Sort descending by Alpha Score
    candidates.sort(key=lambda x: x["alpha_score"], reverse=True)
    return candidates

def evaluate_exits(db: Session, account: Account) -> list[dict]:
    """
    Evaluates all open positions against the 3 Exit Rules:
    1. Trailing Stop-Loss
    2. Alpha Degradation
    3. Time Expiration
    Returns a list of positions to sell.
    """
    sells = []
    positions = db.query(Position).filter(Position.account_id == account.id).all()
    
    for pos in positions:
        try:
            # Refresh current price
            norm_ticker, info = market_service.validate_tsx_large_cap(pos.ticker)
            yticker = yf.Ticker(norm_ticker)
            df = yticker.history(period="5d")
            
            if df.empty:
                continue
                
            current_price = float(df["Close"].iloc[-1])
            
            # Update peak_price if current is higher (for tracking purposes, not for exiting anymore)
            if current_price > pos.peak_price:
                pos.peak_price = current_price
                db.commit()
                
            # Rule 1: Alpha Degradation (Momentum Dead)
            alpha = market_service.get_alpha_score_only(pos.ticker)
            if alpha is not None and alpha < 35.0:
                sells.append({"position": pos, "reason": f"Alpha Dégradation ({alpha})"})
                continue
                
            # Rule 2: Opportunity Cost
            days_held = (datetime.utcnow() - pos.created_at).days
            if days_held > 20:
                # Find if there is a significantly better candidate
                candidates = scan_universe()
                if candidates:
                    top_cand = candidates[0]
                    if alpha is not None and top_cand["alpha_score"] - alpha >= 20.0:
                        sells.append({"position": pos, "reason": f"Rotation vers {top_cand['ticker']} (+{top_cand['alpha_score'] - alpha:.1f} Alpha)"})
                        continue
                
        except Exception as e:
            logger.error(f"Failed to evaluate exit for {pos.ticker}: {e}")
            
    return sells

def run_autopilot(db: Session) -> dict:
    """
    Executes the daily Autopilot rebalance cycle.
    """
    account = trading_service.get_account(db)
    summary_logs = []
    
    # 1. Determine Global Market Regime
    regime_data = get_market_regime()
    regime = regime_data["regime"]
    
    # Threshold logic based on regime
    if regime == "FALLING_KNIFE":
        buy_threshold = 101.0 # Impossible to buy
        summary_logs.append("⚠️ REGIME: FALLING KNIFE. Achats bloqués pour protéger le capital.")
    elif regime == "RECOVERY":
        buy_threshold = 55.0  # Aggressive buying
        summary_logs.append("🟢 REGIME: RECOVERY. Achats agressifs (Seuil Alpha: 55).")
    else:
        buy_threshold = 68.0  # Normal buying
        summary_logs.append("🔵 REGIME: NORMAL. Achats standards (Seuil Alpha: 68).")
        
    # 2. Evaluate Exits (Sells)
    sells = evaluate_exits(db, account)
    for sell in sells:
        pos = sell["position"]
        reason = sell["reason"]
        try:
            # We sell everything
            trading_service.execute_trade(db, "SELL", pos.ticker, pos.quantity)
            summary_logs.append(f"🔴 VENDU: {pos.ticker} | Raison: {reason}")
        except Exception as e:
            summary_logs.append(f"❌ ERREUR VENTE: {pos.ticker} - {e}")
            
    # Refresh account after sells
    db.refresh(account)
    
    # 3. Evaluate Entries (Buys)
    open_positions_count = db.query(Position).filter(Position.account_id == account.id).count()
    slots_available = MAX_POSITIONS - open_positions_count
    
    if slots_available > 0 and buy_threshold <= 100.0:
        candidates = scan_universe()
        
        # Filter candidates by threshold and exclude currently held
        held_tickers = [p.ticker for p in db.query(Position).filter(Position.account_id == account.id).all()]
        valid_candidates = [c for c in candidates if c["alpha_score"] >= buy_threshold and c["ticker"] not in held_tickers]
        
        # Take the top N available slots
        buys_to_execute = valid_candidates[:slots_available]
        
        for cand in buys_to_execute:
            ticker = cand["ticker"]
            alpha = cand["alpha_score"]
            try:
                # Need to calculate risk parity sizing
                market_data = market_service.get_stock_data_and_indicators(ticker)
                risk_weight_pct = market_data.indicators.risk_parity_weight or 20.0
                
                # Sizing: % of TOTAL EQUITY, not just cash
                total_equity = account.cash_balance + sum(
                    p.quantity * (yf.Ticker(p.ticker).history(period="1d")["Close"].iloc[-1] if not yf.Ticker(p.ticker).history(period="1d").empty else p.current_price)
                    for p in db.query(Position).filter(Position.account_id == account.id).all()
                )
                
                target_allocation_cad = total_equity * (risk_weight_pct / 100.0)
                
                # Cannot exceed available cash
                allocation_cad = min(target_allocation_cad, account.cash_balance)
                
                if allocation_cad >= MIN_POSITION_SIZE:
                    current_price = market_data.current_price
                    qty = int(allocation_cad // current_price)
                    
                    if qty > 0:
                        trading_service.execute_trade(db, "BUY", ticker, qty)
                        summary_logs.append(f"🟢 ACHETÉ: {ticker} (Alpha: {alpha}) | Sizing: {risk_weight_pct}% | Qty: {qty}")
                        db.refresh(account)
            except Exception as e:
                summary_logs.append(f"❌ ERREUR ACHAT: {ticker} - {e}")
                
    else:
        if slots_available == 0:
            summary_logs.append("ℹ️ Portefeuille plein (5/5 positions). Aucun achat possible.")
            
    # Send Autopilot summary notification
    summary_text = "\n".join(summary_logs)
    msg = (
        f"<b>🤖 AUTOPILOT CYCLE TERMINÉ</b>\n\n"
        f"{summary_text}"
    )
    notification_service.send_telegram_notification(msg)
    
    return {
        "status": "success",
        "regime": regime,
        "logs": summary_logs
    }
