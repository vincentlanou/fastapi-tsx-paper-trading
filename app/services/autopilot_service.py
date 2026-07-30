import logging
from sqlalchemy.orm import Session
from datetime import datetime
import yfinance as yf

from app.config import ALLOWED_TSX_TICKERS, MAX_POSITIONS, INITIAL_BALANCE
from app.db.models import Account, Position, Trade
from app.services import market_service, trading_service, notification_service
from app.services.trading_service import check_market_regime

logger = logging.getLogger("autopilot_service")


def scan_universe() -> list[dict]:
    """
    Scans the TSX universe, calculates Alpha Score for each ticker,
    and returns a sorted list of candidates.
    """
    candidates = []
    for ticker in ALLOWED_TSX_TICKERS:
        try:
            alpha = market_service.get_alpha_score_only(ticker)
            if alpha is not None:
                candidates.append({"ticker": ticker, "alpha_score": alpha})
        except Exception as e:
            logger.warning(f"Failed to scan {ticker}: {e}")
            continue
    candidates.sort(key=lambda x: x["alpha_score"], reverse=True)
    return candidates


def evaluate_exits(db: Session, account: Account) -> list[dict]:
    """
    Evaluates all open positions against Exit Rules:
    1. Alpha Degradation (momentum dead)
    2. Opportunity Cost Rotation (after 20 days)
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

            # Update peak_price tracking
            if pos.peak_price is None or current_price > pos.peak_price:
                pos.peak_price = current_price
                db.commit()

            # Rule 1: Alpha Degradation (Momentum Dead)
            alpha = market_service.get_alpha_score_only(pos.ticker)
            if alpha is not None and alpha < 35.0:
                sells.append({"position": pos, "reason": f"Alpha Degradation ({alpha})"})
                continue

            # Rule 2: Opportunity Cost (after 20 days held)
            if pos.created_at:
                days_held = (datetime.utcnow() - pos.created_at).days
            else:
                days_held = 0

            if days_held > 20:
                candidates = scan_universe()
                if candidates:
                    top_cand = candidates[0]
                    if alpha is not None and top_cand["alpha_score"] - alpha >= 20.0:
                        sells.append({
                            "position": pos,
                            "reason": f"Rotation vers {top_cand['ticker']} (+{top_cand['alpha_score'] - alpha:.1f} Alpha)"
                        })
                        continue

        except Exception as e:
            logger.error(f"Failed to evaluate exit for {pos.ticker}: {e}")

    return sells


def run_autopilot(db: Session) -> dict:
    """
    Executes the daily Autopilot rebalance cycle.
    """
    account = trading_service.get_or_create_account(db)
    summary_logs = []

    # 1. Determine Global Market Regime
    regime, regime_msg = check_market_regime()

    if regime == "FALLING_KNIFE":
        buy_threshold = 101.0  # Impossible to buy
        summary_logs.append("REGIME: FALLING KNIFE. Achats bloques.")
    else:
        buy_threshold = 68.0
        summary_logs.append("REGIME: NORMAL. Achats standards (Seuil Alpha: 68).")

    # 2. Evaluate Exits (Sells)
    sells = evaluate_exits(db, account)
    for sell in sells:
        pos = sell["position"]
        reason = sell["reason"]
        try:
            # Use sell_stock which is the actual function in trading_service
            trading_service.sell_stock(db, pos.ticker, pos.quantity)
            summary_logs.append(f"VENDU: {pos.ticker} | Raison: {reason}")
        except Exception as e:
            summary_logs.append(f"ERREUR VENTE: {pos.ticker} - {e}")

    # Refresh account after sells
    db.refresh(account)

    # 3. Evaluate Entries (Buys)
    open_positions_count = db.query(Position).filter(Position.account_id == account.id).count()
    slots_available = MAX_POSITIONS - open_positions_count

    if slots_available > 0 and buy_threshold <= 100.0:
        candidates = scan_universe()

        # Filter candidates by threshold and exclude currently held tickers
        held_tickers = [p.ticker for p in db.query(Position).filter(Position.account_id == account.id).all()]
        valid_candidates = [c for c in candidates if c["alpha_score"] >= buy_threshold and c["ticker"] not in held_tickers]

        buys_to_execute = valid_candidates[:slots_available]

        for cand in buys_to_execute:
            ticker = cand["ticker"]
            alpha = cand["alpha_score"]
            try:
                # Get risk parity sizing from market_service
                market_data = market_service.get_stock_data_and_indicators(ticker)
                risk_weight_pct = market_data.indicators.risk_parity_weight or 20.0

                # Calculate total equity for sizing
                total_equity = account.cash_balance
                for p in db.query(Position).filter(Position.account_id == account.id).all():
                    try:
                        p_price = trading_service.get_live_price(p.ticker)
                    except Exception:
                        p_price = p.average_buy_price
                    total_equity += p.quantity * p_price

                target_allocation_cad = total_equity * (risk_weight_pct / 100.0)

                # Cannot exceed available cash
                allocation_cad = min(target_allocation_cad, account.cash_balance)

                if allocation_cad >= 500.0:
                    current_price = market_data.current_price
                    qty = int(allocation_cad // current_price)

                    if qty > 0:
                        # Use buy_stock which is the actual function in trading_service
                        trading_service.buy_stock(db, ticker, qty)
                        summary_logs.append(f"ACHETE: {ticker} (Alpha: {alpha}) | Sizing: {risk_weight_pct}% | Qty: {qty}")
                        db.refresh(account)
            except Exception as e:
                summary_logs.append(f"ERREUR ACHAT: {ticker} - {e}")

    else:
        if slots_available == 0:
            summary_logs.append("Portefeuille plein (5/5 positions). Aucun achat possible.")

    # Send Autopilot summary notification via Telegram
    summary_text = "\n".join(summary_logs)
    msg = (
        f"<b>AUTOPILOT CYCLE TERMINE</b>\n\n"
        f"{summary_text}"
    )
    notification_service.send_telegram_notification(msg)

    return {
        "status": "success",
        "regime": regime,
        "logs": summary_logs
    }
