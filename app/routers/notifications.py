from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import trading_service
from app.services.notification_service import send_telegram_notification, notify_daily_portfolio_summary

router = APIRouter(prefix="/api/notifications", tags=["Telegram Webhook Notifications"])

@router.post("/test")
def trigger_test_notification():
    """Trigger a test Telegram push notification to mobile phone."""
    test_msg = (
        "<b>🔔 TELEGRAM PUSH NOTIFICATION CONNECTED</b>\n"
        "Votre téléphone est désormais prêt à recevoir les alertes TSX !"
    )
    success = send_telegram_notification(test_msg)
    return {
        "status": "sent" if success else "simulated_console_only",
        "message": "Notification push envoyée sur Telegram !" if success else "Token/Chat ID Telegram non configurés. Message consigné sur la console."
    }

@router.post("/daily-summary")
def trigger_daily_summary(db: Session = Depends(get_db)):
    """Trigger daily portfolio fluctuation & conservation status push notification."""
    portfolio = trading_service.get_portfolio_summary(db)
    portfolio_dict = {
        "total_equity": portfolio.total_equity,
        "cash_balance": portfolio.cash_balance,
        "total_pnl": portfolio.total_pnl,
        "total_pnl_pct": portfolio.total_pnl_pct
    }
    success = notify_daily_portfolio_summary(portfolio_dict, portfolio.positions)
    return {
        "status": "sent" if success else "simulated_console_only",
        "message": "Rapport quotidien push transmis sur votre Telegram !" if success else "Token/Chat ID Telegram non configurés."
    }
