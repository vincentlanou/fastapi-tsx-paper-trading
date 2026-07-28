import os
from dotenv import load_dotenv

load_dotenv()

# Application Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paper_trading.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Retail Strategy Settings ($5,000 CAD, Fees, Whole Shares, Max 5 Positions)
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "5000.0"))
DEFAULT_ACCOUNT_NAME = "TSX 5K Retail Account"

TRANSACTION_FEE_CAD = 4.95        # Fixed commission per trade (Buy/Sell)
BID_ASK_SPREAD_SLIPPAGE = 0.0010  # 0.10% spread slippage (Buy higher, Sell lower)

MAX_POSITIONS = 5                  # Maximum 3 to 5 active long positions allowed
MIN_POSITIONS = 3

# TSX Large Cap Trading Constraints
MIN_MARKET_CAP_TSX = 5_000_000_000 # 5 Billion CAD
ALLOWED_TSX_TICKERS = {
    "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO", "WCN.TO", "IMO.TO", "L.TO",
    "GIB-A.TO", "BCE.TO", "CM.TO", "TRP.TO", "TOU.TO", "POW.TO"
}
