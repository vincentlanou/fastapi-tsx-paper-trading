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
DEFAULT_ACCOUNT_NAME = "TSX Retail Trading Account"

TRANSACTION_FEE_CAD = 4.95        # Fixed commission per trade (Buy/Sell)
BID_ASK_SPREAD_SLIPPAGE = 0.0010  # 0.10% spread slippage (Buy higher, Sell lower)

MAX_POSITIONS = 5                  # Maximum 3 to 5 active long positions allowed
MIN_POSITIONS = 3

# TSX Traded Stocks (Canadian, US & International Large Caps Traded on TSX)
MIN_MARKET_CAP_TSX = 4_000_000_000 # 4 Billion CAD/USD Market Cap threshold
ALLOWED_TSX_TICKERS = {
    # Canadian & US/International Dual-Listed Large Caps Traded on TSX
    "SHOP.TO",  # Shopify (Tech - CAD/US)
    "RY.TO",    # Royal Bank of Canada (Financials)
    "TD.TO",    # Toronto-Dominion Bank (Financials)
    "ENB.TO",   # Enbridge (Energy - CAD/US)
    "CNQ.TO",   # Canadian Natural Resources (Energy)
    "BNS.TO",   # Bank of Nova Scotia (Financials)
    "CNR.TO",   # Canadian National Railway (Industrials)
    "CP.TO",    # Canadian Pacific Kansas City (Industrials)
    "BMO.TO",   # Bank of Montreal (Financials)
    "TRI.TO",   # Thomson Reuters (US/CAD Media)
    "ATD.TO",   # Alimentation Couche-Tard (Retail)
    "SU.TO",    # Suncor Energy (Energy)
    "MFC.TO",   # Manulife Financial (Financials/Insurance)
    "ABX.TO",   # Barrick Gold (Materials - US/CAD)
    "NTR.TO",   # Nutrien (Materials/Agriculture)
    "WCN.TO",   # Waste Connections (US-headquartered, TSX Traded)
    "QSR.TO",   # Restaurant Brands Intl / Burger King (US/CAD Consumer)
    "GIB-A.TO", # CGI Inc (Tech)
    "BCE.TO",   # BCE Inc (Telecom)
    "IMO.TO",   # Imperial Oil (ExxonMobil affiliate)
    "L.TO",     # Loblaw Companies
    "TECK-B.TO",# Teck Resources
    "FNV.TO",   # Franco-Nevada (Gold)
    "AEM.TO"    # Agnico Eagle Mines
}
