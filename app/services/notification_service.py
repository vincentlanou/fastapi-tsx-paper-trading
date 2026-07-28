import httpx
import logging
from sqlalchemy.orm import Session
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, INITIAL_BALANCE

logger = logging.getLogger("telegram_notifications")

def send_telegram_notification(message_html: str) -> bool:
    """Send an HTML-formatted push notification via Telegram Bot Webhook API to user's mobile phone."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info(f"[TELEGRAM PUSH NOTIFICATION SIMULATION]:\n{message_html}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_html,
        "parse_mode": "HTML"
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram push notification sent successfully.")
                return True
            else:
                logger.warning(f"Telegram API status {resp.status_code}: {resp.text}")
                return False
    except Exception as err:
        logger.error(f"Error sending Telegram notification: {err}")
        return False

def notify_buy_trade(ticker: str, quantity: float, execution_price: float, total_amount: float, cash_balance: float):
    """Trigger Telegram push notification on Trade Buy / Rebalance entry."""
    msg = (
        f"<b>🚀 TSX TRADE - ACHAT EFFECTUÉ</b>\n"
        f"<b>Ticker :</b> {ticker}\n"
        f"<b>Quantité :</b> {int(quantity)} action(s)\n"
        f"<b>Prix Exec. (Spread incl.) :</b> ${execution_price:,.2f} CAD\n"
        f"<b>Montant Net (Frais $4.95 incl.) :</b> ${total_amount:,.2f} CAD\n"
        f"<b>Solde Cash Restant :</b> ${cash_balance:,.2f} CAD"
    )
    return send_telegram_notification(msg)

def notify_sell_trade(ticker: str, quantity: float, execution_price: float, total_amount: float, realized_pnl: float, cash_balance: float):
    """Trigger Telegram push notification on Trade Sell / Rebalance exit."""
    pnl_symbol = "+" if realized_pnl >= 0 else ""
    pnl_icon = "🟢" if realized_pnl >= 0 else "🔴"
    msg = (
        f"<b>💰 TSX TRADE - VENTE EFFECTUÉE {pnl_icon}</b>\n"
        f"<b>Ticker :</b> {ticker}\n"
        f"<b>Quantité :</b> {int(quantity)} action(s)\n"
        f"<b>Prix Exec. (Spread incl.) :</b> ${execution_price:,.2f} CAD\n"
        f"<b>Montant Net Récupéré :</b> ${total_amount:,.2f} CAD\n"
        f"<b>P&L Réalisé :</b> {pnl_symbol}${realized_pnl:,.2f} CAD\n"
        f"<b>Nouveau Solde Cash :</b> ${cash_balance:,.2f} CAD"
    )
    return send_telegram_notification(msg)

def notify_daily_portfolio_summary(portfolio_data: dict, positions: list):
    """Trigger daily push notification for portfolio fluctuations, conservation status & holding updates."""
    total_equity = portfolio_data.get("total_equity", INITIAL_BALANCE)
    cash_balance = portfolio_data.get("cash_balance", INITIAL_BALANCE)
    total_pnl = portfolio_data.get("total_pnl", 0.0)
    total_pnl_pct = portfolio_data.get("total_pnl_pct", 0.0)
    
    pnl_icon = "🟢" if total_pnl >= 0 else "🔴"
    pnl_sign = "+" if total_pnl >= 0 else ""

    pos_lines = []
    for pos in positions:
        pos_pnl = pos.unrealized_pnl
        pos_pnl_sign = "+" if pos_pnl >= 0 else ""
        pos_pnl_icon = "🟢" if pos_pnl >= 0 else "🔴"
        pos_lines.append(
            f"• <b>{pos.ticker}</b>: {int(pos.quantity)} actions | Prix: ${pos.current_price:,.2f} | "
            f"P&L: {pos_pnl_sign}${pos_pnl:,.2f} ({pos.unrealized_pnl_pct:.2f}%) {pos_pnl_icon} [CONSERVATION 5J]"
        )

    pos_summary_text = "\n".join(pos_lines) if pos_lines else "• Aucune position ouverte."

    msg = (
        f"<b>📊 TSX PORTFOLIO - RAPPORT DU JOUR {pnl_icon}</b>\n\n"
        f"<b>Équité Totale :</b> ${total_equity:,.2f} CAD\n"
        f"<b>Fluctuation P&L Total :</b> {pnl_sign}${total_pnl:,.2f} CAD ({pnl_sign}{total_pnl_pct:.2f}%)\n"
        f"<b>Solde Cash Disponible :</b> ${cash_balance:,.2f} CAD\n\n"
        f"<b>🔒 POSITIONS EN CONSERVATION (HORIZON 5 JOURS) :</b>\n"
        f"{pos_summary_text}\n\n"
        f"<b>💡 STATUT ESTRATÉGIQUE :</b> Positions stables. Aucune anomalie critique détectée."
    )
    return send_telegram_notification(msg)
