# QuantPulse TSX - Paper Trading & AI Sentiment Analytics Platform

A modern quantitative finance web application and REST API built with **FastAPI**, **Next.js 14**, **TailwindCSS**, **Recharts**, and **Gemini AI**.

Designed specifically for trading **Canadian, US, and International Large Cap stocks listed on the Toronto Stock Exchange (TSX)** (tickers ending in `.TO`, e.g., `SHOP.TO`, `RY.TO`, `TD.TO`, `ENB.TO`, `WCN.TO`, `QSR.TO`).

---

## ⚡ Key Features

1. **TSX Traded Large Cap Scope**
   - Supports any Canadian, American, or International Large Cap stock traded on the Toronto Stock Exchange (TSX).
   - Minimum market capitalization threshold of **$4 Billion CAD/USD**.
   - Automatic ticker normalization (e.g., searching `SHOP` resolves to `SHOP.TO`).

2. **Retail Quantitative Trading Rules ($5,000 CAD Capital)**
   - Initial Virtual Capital: **$5,000.00 CAD**.
   - **Whole Shares Only**: Fractional shares are disabled; quantity is automatically rounded down to whole shares (`floor`).
   - **Realistic Friction Costs**:
     - Fixed Commission Fee: **$4.95 CAD** per trade (Buy/Sell).
     - Bid/Ask Spread Slippage: **0.10%** execution penalty ($P_{buy} = P \times 1.001$, $P_{sell} = P \times 0.999$).
   - **Portfolio Diversification**: Strictly limited to **3 to 5 concurrent long positions**.

3. **5-Day Holding Horizon Strategy & Daily Screening**
   - **5-Day Base Target Horizon**: Positions are held for 5 trading days to allow Momentum (RSI + MACD) and Gemini AI Sentiment catalysts to play out.
   - **Daily Critical Screening**: Early exits or rebalancing occur only upon critical triggers:
     - 🔴 **Critical Risk Exit**: RSI $\le 32$, MACD Bearish Crossover, or Momentum Score $\le 35$.
     - 🟢 **Critical Opportunity Entry**: Momentum Score $\ge 75$ with MACD Bullish Crossover.

4. **Gemini AI Financial News Sentiment**
   - Analyzes financial news headlines via **Gemini 2.5 Flash API**.
   - Generates overall sentiment score (0 to 100), Bullish/Bearish breakdown, executive summary, and key catalyst drivers.
   - Built-in rule-based news parser fallback when API key is unconfigured.

5. **Telegram Push Notifications (Mobile)**
   - **Real-time Order Alerts**: Instant notifications for simulated BUY and SELL orders with execution price, transaction fees, and updated cash balance.
   - **Daily Portfolio Summary & Conservation Report**: Daily push updates featuring total equity, daily P&L fluctuation ($ & %), cash balance, and 5-day holding status for all active positions (`[CONSERVATION 5J]`).

6. **Next.js 14 + Recharts Frontend Dashboard**
   - Glassmorphic dark theme dashboard.
   - **Recharts AreaChart**: Interactive P&L evolution timeline graph over time.
   - **Open Positions Table**: Real-time market value, unrealized P&L ($ & %), and quick sell actions.
   - **Gemini AI Sentiment Card & TSX News Stream**.

---

## 🛠️ Project Architecture

```
fastapi_paper_trading/
├── app/                         # Backend FastAPI Application
│   ├── main.py                  # Entry point & CORS/Static config
│   ├── config.py                # TSX tickers, $5k capital, $4.95 fee & rules
│   ├── db/
│   │   ├── database.py          # SQLAlchemy SQLite connection
│   │   └── models.py            # Account, Position, Trade, PortfolioSnapshot
│   ├── services/
│   │   ├── market_service.py    # TSX yfinance data, RSI(14), MACD(12,26,9)
│   │   ├── sentiment_service.py # Gemini AI financial news sentiment
│   │   ├── trading_service.py   # Paper trading engine, fees & P&L history
│   │   └── notification_service.py # Telegram push notifications
│   └── routers/                 # FastAPI REST API endpoints
├── frontend/                    # Next.js 14 Web Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Main Dashboard SPA
│   │   │   └── globals.css      # TailwindCSS directives
│   │   ├── components/
│   │   │   ├── Navbar.tsx       # TSX Search & Quick Tickers
│   │   │   ├── PortfolioOverview.tsx # Capital & Recharts P&L evolution
│   │   │   ├── PositionsList.tsx     # Open TSX positions table
│   │   │   ├── NewsSentimentFeed.tsx # Gemini AI sentiment & news feed
│   │   │   ├── MarketChart.tsx       # Recharts price & MACD chart
│   │   │   └── TradingPanel.tsx      # Integer share order terminal
│   │   └── lib/
│   │       └── api.ts           # REST API client
├── test_platform.py             # Integration test suite
├── .gitignore
└── README.md
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/market/{ticker}` | Returns TSX real-time price, RSI, MACD, and Momentum Score |
| `GET` | `/api/sentiment/{ticker}` | Returns Gemini AI financial news sentiment evaluation |
| `GET` | `/api/trading/portfolio` | Returns portfolio equity, cash, active positions, and net P&L |
| `GET` | `/api/trading/pnl-history` | Returns P&L snapshot history for Recharts timeline |
| `GET` | `/api/trading/history` | Returns complete audit log of executed trades |
| `POST` | `/api/trading/buy` | Executes simulated buy order (`{"ticker": "SHOP.TO", "quantity": 10}`) |
| `POST` | `/api/trading/sell` | Executes simulated sell order (`{"ticker": "SHOP.TO", "quantity": 5}`) |
| `POST` | `/api/trading/reset` | Resets account balance to $5,000.00 CAD |
| `POST` | `/api/notifications/test` | Triggers a test Telegram mobile push notification |
| `POST` | `/api/notifications/daily-summary` | Triggers daily portfolio P&L & position conservation push report |

---

## 🚀 Quick Start Guide

### 1. Start FastAPI Backend (Port 8000)
```bash
cd C:\Users\lanou\.gemini\antigravity\scratch\fastapi_paper_trading
C:\Users\lanou\python311\python.exe -m app.main
```
- API Documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start Next.js Frontend (Port 3000)
```bash
cd C:\Users\lanou\.gemini\antigravity\scratch\fastapi_paper_trading\frontend
cmd /c "set PATH=C:\Users\lanou\nodejs;%PATH% && npm run dev"
```
- Web Application: [http://localhost:3000](http://localhost:3000)

### 3. Run Automated Integration Tests
```bash
C:\Users\lanou\python311\python.exe test_platform.py
```
