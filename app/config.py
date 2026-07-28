import os
from dotenv import load_dotenv

load_dotenv()

# Application Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paper_trading.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# BNCD (Banque Nationale Courtage Direct) Zero-Commission Pricing & Retail Rules
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "5000.0"))
DEFAULT_ACCOUNT_NAME = "BNCD $0 Fee TSX Account"

TRANSACTION_FEE_CAD = 0.00        # BNCD $0.00 CAD commission per trade (Free stock & ETF trades)
BID_ASK_SPREAD_SLIPPAGE = 0.0005  # 0.05% standard TSX Large Cap bid/ask spread (e.g., $0.05 spread on $100 stock)
RISK_FREE_RATE = 0.025             # 2.5% CAD annual risk-free benchmark rate

MAX_POSITIONS = 5                  # Maximum 3 to 5 active long positions allowed
MIN_POSITIONS = 3

# TSX Traded Stocks (Canadian, US & International Large Caps Traded on TSX)
MIN_MARKET_CAP_TSX = 4_000_000_000 # 4 Billion CAD/USD Market Cap threshold
ALLOWED_TSX_TICKERS = {
    "SHOP.TO", "RY.TO", "TD.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO", "WCN.TO", "QSR.TO", "GIB-A.TO",
    "BCE.TO", "IMO.TO", "L.TO", "TECK-B.TO", "FNV.TO", "AEM.TO"
}
