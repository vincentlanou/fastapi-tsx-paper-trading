import math
from typing import Tuple
import yfinance as yf
import pandas as pd
import numpy as np

# TSX Large Cap Universe for Backtest (2019-2024)
TSX_UNIVERSE = [
    "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO", "IMO.TO", "L.TO", "BCE.TO"
]

INITIAL_CAPITAL = 5000.0
FEE_PER_TRADE = 0.00        # BNCD (Banque Nationale Courtage Direct) $0.00 Commission
SPREAD_PCT = 0.0005         # Standard TSX Large Cap Bid/Ask Spread (0.05%)
MAX_POSITIONS = 5
HOLD_HORIZON_DAYS = 20      # 15 to 30 days target horizon for winners
RISK_FREE_RATE = 0.025      # 2.5% CAD annual risk-free rate

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)

def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def calculate_sharpe(prices: pd.Series) -> float:
    ret = prices.pct_change().dropna()
    if ret.empty or len(ret) < 10:
        return 1.0
    ann_ret = ret.mean() * 252
    ann_vol = ret.std() * np.sqrt(252)
    return float((ann_ret - RISK_FREE_RATE) / ann_vol) if ann_vol > 1e-6 else 0.0

def run_backtest():
    print("=== STARTING 5-YEAR BACKTEST: BNCD $0 FEES + SHARPE MULTI-FACTOR MODEL (2019-2024) ===")
    print("Capital: $5,000 CAD | BNCD Fee: $0.00 CAD | Spread: 0.05% | Sharpe Risk Filter | 15-30 Day Horizon\n")

    data_dict = {}
    for ticker in TSX_UNIVERSE:
        df = yf.Ticker(ticker).history(period="5y", interval="1d")
        if not df.empty and len(df) > 200:
            df["RSI"] = calculate_rsi(df["Close"])
            macd, signal, hist = calculate_macd(df["Close"])
            df["MACD_Hist"] = hist
            
            # Sharpe Ratio over 60-day rolling window
            rolling_sharpe = df["Close"].rolling(60).apply(lambda p: calculate_sharpe(p), raw=False).fillna(1.0)
            df["Sharpe"] = rolling_sharpe

            # Multi-Factor Score: 40% Momentum + 30% MACD + 30% Sharpe Ratio
            rsi_norm = df["RSI"]
            hist_norm = np.clip(hist / (df["Close"] * 0.02), -1.0, 1.0) * 50 + 50
            sharpe_norm = np.clip(rolling_sharpe / 2.0, 0.0, 1.0) * 100.0
            
            df["MultiFactor_Score"] = (rsi_norm * 0.4) + (hist_norm * 0.3) + (sharpe_norm * 0.3)
            data_dict[ticker] = df

    # Download Benchmark (TSX Composite XIU.TO)
    bench_df = yf.Ticker("XIU.TO").history(period="5y", interval="1d")
    bench_start_price = bench_df["Close"].iloc[0]
    bench_end_price = bench_df["Close"].iloc[-1]
    bench_return_pct = ((bench_end_price - bench_start_price) / bench_start_price) * 100.0

    cash = INITIAL_CAPITAL
    positions = {}
    total_trades = 0
    winning_trades = 0
    total_spread_cost = 0.0

    common_dates = data_dict["RY.TO"].index[60:]

    for date in common_dates:
        current_prices = {}
        candidate_scores = {}
        candidate_sharpes = {}

        for ticker, df in data_dict.items():
            if date in df.index:
                row = df.loc[date]
                current_prices[ticker] = float(row["Close"])
                candidate_scores[ticker] = float(row["MultiFactor_Score"])
                candidate_sharpes[ticker] = float(row["Sharpe"])

        # 1. Portfolio Valuation
        current_stock_val = 0.0
        for ticker, pos_info in list(positions.items()):
            price = current_prices.get(ticker, pos_info["buy_price"])
            current_stock_val += price * pos_info["qty"]
            pos_info["days_held"] += 1

        # 2. Check Exits (Emergency Risk or Rebalance)
        for ticker in list(positions.keys()):
            pos = positions[ticker]
            price = current_prices[ticker]
            score = candidate_scores.get(ticker, 50.0)

            should_exit = False
            if score <= 35:
                should_exit = True
            elif pos["days_held"] >= HOLD_HORIZON_DAYS:
                top_new = max(
                    [t for t in candidate_scores if t not in positions],
                    key=lambda t: candidate_scores[t],
                    default=None
                )
                if top_new and candidate_scores[top_new] - score >= 20.0:
                    should_exit = True
                else:
                    pos["days_held"] = 0 # Rollover for zero fee

            if should_exit:
                exec_price = price * (1.0 - SPREAD_PCT)
                net_proceeds = exec_price * pos["qty"]
                pnl = net_proceeds - (pos["buy_price"] * pos["qty"])

                cash += net_proceeds
                total_spread_cost += (price * SPREAD_PCT * pos["qty"])
                total_trades += 1
                if pnl > 0:
                    winning_trades += 1
                del positions[ticker]

        # 3. Check Entries (If positions < 5 and Cash available)
        available_slots = MAX_POSITIONS - len(positions)
        if available_slots > 0 and cash >= 800.0:
            eligible_candidates = [
                t for t, s in candidate_scores.items()
                if t not in positions and s >= 68.0 and candidate_sharpes[t] >= 0.8
            ]
            eligible_candidates.sort(key=lambda t: candidate_scores[t], reverse=True)

            for ticker in eligible_candidates[:available_slots]:
                price = current_prices[ticker]
                exec_price = price * (1.0 + SPREAD_PCT)
                
                allocation = min(cash / available_slots, 1250.0)
                qty = math.floor(allocation / exec_price)

                if qty >= 1:
                    stock_cost = qty * exec_price
                    if cash >= stock_cost:
                        cash -= stock_cost
                        positions[ticker] = {
                            "qty": qty,
                            "buy_price": exec_price,
                            "days_held": 0
                        }
                        total_spread_cost += (price * SPREAD_PCT * qty)

    # Final Liquidation for Performance Summary
    final_equity = cash
    for ticker, pos in positions.items():
        price = current_prices.get(ticker, pos["buy_price"])
        exec_price = price * (1.0 - SPREAD_PCT)
        final_equity += (exec_price * pos["qty"])

    total_return_pct = ((final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    cagr = (((final_equity / INITIAL_CAPITAL) ** (1 / 5)) - 1) * 100.0
    bench_cagr = (((bench_end_price / bench_start_price) ** (1 / 5)) - 1) * 100.0

    print("==========================================================")
    print("RESULTS OF 5-YEAR BACKTEST: BNCD $0 FEES + SHARPE MODEL")
    print("==========================================================")
    print(f"Initial Capital         : ${INITIAL_CAPITAL:,.2f} CAD")
    print(f"Final Capital           : ${final_equity:,.2f} CAD")
    print(f"Net Real Return         : +{total_return_pct:.2f}% (CAGR: +{cagr:.2f}% / year)")
    print(f"Benchmark (XIU.TO TSX) : +{bench_return_pct:.2f}% (CAGR: +{bench_cagr:.2f}% / year)")
    print(f"Alpha vs Benchmark      : +{total_return_pct - bench_return_pct:.2f}%")
    print(f"Win Rate                : {win_rate:.1f}% ({winning_trades}/{total_trades} trades)")
    print(f"Total Transactions      : {total_trades} trades executed")
    print(f"BNCD Commission Fees    : $0.00 CAD (Zero Commission)")
    print(f"Total Spread Slippage   : ${total_spread_cost:,.2f} CAD (0.05% TSX Spread)")
    print("==========================================================")

if __name__ == "__main__":
    run_backtest()
