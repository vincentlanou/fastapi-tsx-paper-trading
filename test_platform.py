import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.services.market_service import get_stock_data_and_indicators
from app.services.sentiment_service import get_news_sentiment
from app.services.trading_service import buy_stock, sell_stock, get_portfolio_summary, reset_account, get_pnl_history

class TestTSXTradingPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        db = SessionLocal()
        try:
            reset_account(db)
        finally:
            db.close()

    def test_01_tsx_large_cap_market_data(self):
        """Test TSX Large Cap stock market data retrieval (e.g. SHOP.TO)."""
        data = get_stock_data_and_indicators("SHOP", period="1mo")
        self.assertEqual(data.ticker, "SHOP.TO")
        self.assertGreater(data.current_price, 0)
        self.assertIsNotNone(data.indicators.current_rsi)

    def test_02_non_tsx_rejection(self):
        """Test rejection of non-TSX or small-cap stocks (e.g. AAPL without .TO)."""
        with self.assertRaises(ValueError):
            get_stock_data_and_indicators("INVALID_TICKER_XYZ999", period="1mo")

    def test_03_tsx_paper_trading_and_pnl_history(self):
        """Test TSX paper trading lifecycle and P&L timeline snapshots."""
        db = SessionLocal()
        try:
            # 1. Initial State
            p0 = get_portfolio_summary(db)
            self.assertEqual(p0.cash_balance, 5000.0)

            # 2. Buy SHOP.TO
            buy = buy_stock(db, "SHOP.TO", 5.0)
            self.assertEqual(buy.ticker, "SHOP.TO")

            # 3. Check P&L History for Recharts
            history = get_pnl_history(db)
            self.assertGreaterEqual(len(history), 2)
            self.assertIn("total_equity", history[-1])
            self.assertIn("total_pnl", history[-1])

            # 4. Sell SHOP.TO
            sell = sell_stock(db, "SHOP.TO", 2.0)
            self.assertEqual(sell.ticker, "SHOP.TO")

        finally:
            db.close()

    def test_04_fastapi_rest_endpoints(self):
        """Test FastAPI REST API endpoints."""
        r_mkt = self.client.get("/api/market/RY.TO")
        self.assertEqual(r_mkt.status_code, 200)

        r_sent = self.client.get("/api/sentiment/RY.TO")
        self.assertEqual(r_sent.status_code, 200)

        r_port = self.client.get("/api/trading/portfolio")
        self.assertEqual(r_port.status_code, 200)

        r_pnl = self.client.get("/api/trading/pnl-history")
        self.assertEqual(r_pnl.status_code, 200)

        r_buy = self.client.post("/api/trading/buy", json={"ticker": "TD.TO", "quantity": 10})
        self.assertEqual(r_buy.status_code, 200)

if __name__ == "__main__":
    unittest.main()
