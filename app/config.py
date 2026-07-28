import os
from dotenv import load_dotenv

load_dotenv()

# Application Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paper_trading.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# BNCD Zero-Commission & Risk Parity Settings ($5,000 CAD Capital)
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "5000.0"))
DEFAULT_ACCOUNT_NAME = "Global 75 Risk Parity Account"

TRANSACTION_FEE_CAD = 0.00        # BNCD $0.00 CAD commission per trade
BID_ASK_SPREAD_SLIPPAGE = 0.0005  # 0.05% standard TSX Large Cap bid/ask spread
RISK_FREE_RATE = 0.025             # 2.5% CAD annual risk-free benchmark rate

MAX_POSITIONS = 5                  # Maximum 3 to 5 active long positions allowed
MIN_POSITIONS = 3

# GLOBAL 75 TSX UNIVERSE (Top 30 S&P 500 CDRs + Top 15 TSX 60 + Top 30 MSCI EAFE on TSX)
MIN_MARKET_CAP_TSX = 4_000_000_000
ALLOWED_TSX_TICKERS = {
    # 1. Top 15 TSX 60 Canadian Leaders
    "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO",

    # 2. Top 30 S&P 500 US Leaders (Traded on TSX via CDRs)
    "NVDA.TO", "AAPL.TO", "MSFT.TO", "AMZN.TO", "GOOG.TO", "TSLA.TO",
    "META.TO", "BRK.TO", "JPM.TO", "V.TO", "WMT.TO", "XOM.TO",
    "PG.TO", "HD.TO", "JNJ.TO", "COST.TO", "ORCL.TO", "CRM.TO",
    "CVX.TO", "AMD.TO", "KO.TO", "PEP.TO", "DIS.TO", "NFLX.TO",
    "ABT.TO", "BAC.TO", "CAT.TO", "IBM.TO", "LLY.TO", "AVGO.TO",

    # 3. Top 30 MSCI EAFE International Leaders Traded on TSX
    "ASML.TO", "AZN.TO", "SAP.TO", "SHEL.TO", "BTI.TO", "TTE.TO",
    "RHHBY.TO", "SNY.TO", "BAP.TO", "BP.TO", "UL.TO", "DEO.TO",
    "GSK.TO", "SONY.TO", "RIO.TO", "BHP.TO", "NVO.TO", "NVS.TO",
    "TM.TO", "HSBC.TO", "IMO.TO", "L.TO", "TECK-B.TO", "FNV.TO", "AEM.TO"
}
