import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import Base, engine, SessionLocal
from app.services.trading_service import buy_stock, sell_stock, get_portfolio_summary, reset_account

print("=== STARTING DIRECT INTEGRATION TEST ===")
Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    reset_account(db)
    print("1. Account reset OK.")

    p0 = get_portfolio_summary(db)
    print(f"2. Initial Cash: ${p0.cash_balance:,.2f}")

    buy = buy_stock(db, "AAPL", 10)
    print(f"3. Simulated BUY: {buy.quantity} {buy.ticker} @ ${buy.execution_price:,.2f} | Total: ${buy.total_amount:,.2f}")

    p1 = get_portfolio_summary(db)
    print(f"4. Portfolio Equity: ${p1.total_equity:,.2f} | Cash: ${p1.cash_balance:,.2f} | Active Holdings: {len(p1.positions)}")

    sell = sell_stock(db, "AAPL", 5)
    print(f"5. Simulated SELL: {sell.quantity} {sell.ticker} @ ${sell.execution_price:,.2f} | Realized P&L: ${sell.realized_pnl:,.2f}")

    p2 = get_portfolio_summary(db)
    print(f"6. Updated Equity: ${p2.total_equity:,.2f} | Realized P&L Total: ${p2.total_realized_pnl:,.2f}")

    print("=== ALL PAPER TRADING & SQLITE TESTS PASSED SUCCESSFULLY ===")

finally:
    db.close()
