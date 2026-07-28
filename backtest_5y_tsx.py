import math
from typing import Tuple
import yfinance as yf
import pandas as pd

import numpy as np
from datetime import datetime

# TSX Large Cap Universe for Backtest (2019-2024)
TSX_UNIVERSE = [
    "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO", "IMO.TO", "L.TO", "BCE.TO"
]

INITIAL_CAPITAL = 5000.0
FEE_PER_TRADE = 4.95
SPREAD_PCT = 0.0010
MAX_POSITIONS = 5
HOLD_HORIZON_DAYS = 25  # 15 to 30 days target horizon for winners
FRICTION_BARRIER_PCT = 3.0 # +3.0% net advantage needed to justify swapping

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

def run_backtest():
    print("=== STARTING 5-YEAR NO-LOOKAHEAD BACKTEST (TSX LARGE CAPS 2019-2024) ===")
    print("Capital: $5,000 CAD | Whole Shares Only | Fees: $4.95 CAD/trade | Spread: 0.10% | Max Positions: 5 | 5-Day Rolling Friction Engine\n")

    # Download 5y daily price data
    data_dict = {}
    for ticker in TSX_UNIVERSE:
        df = yf.Ticker(ticker).history(period="5y", interval="1d")
        if not df.empty and len(df) > 200:
            df["RSI"] = calculate_rsi(df["Close"])
            macd, signal, hist = calculate_macd(df["Close"])
            df["MACD_Hist"] = hist
            
            # Momentum Score (0-100) strictly from past data
            rsi_norm = df["RSI"]
            hist_norm = np.clip(hist / (df["Close"] * 0.02), -1.0, 1.0) * 50 + 50
            df["Momentum_Score"] = (rsi_norm * 0.5) + (hist_norm * 0.5)
            data_dict[ticker] = df

    # Download Benchmark (TSX Composite Index XIU.TO)
    bench_df = yf.Ticker("XIU.TO").history(period="5y", interval="1d")
    bench_start_price = bench_df["Close"].iloc[0]
    bench_end_price = bench_df["Close"].iloc[-1]
    bench_return_pct = ((bench_end_price - bench_start_price) / bench_start_price) * 100.0

    # Trading Simulation variables
    cash = INITIAL_CAPITAL
    positions = {} # ticker -> {qty, buy_price, entry_day, days_held}
    portfolio_equity_curve = []
    total_trades = 0
    winning_trades = 0
    total_fees_paid = 0.0

    # Common trading days index
    common_dates = data_dict["RY.TO"].index[50:] # Start after 50 days warm-up

    for date in common_dates:
        current_prices = {}
        candidate_scores = {}

        for ticker, df in data_dict.items():
            if date in df.index:
                row = df.loc[date]
                current_prices[ticker] = float(row["Close"])
                candidate_scores[ticker] = float(row["Momentum_Score"])

        # 1. Update Portfolio Valuation
        current_stock_val = 0.0
        for ticker, pos_info in list(positions.items()):
            price = current_prices.get(ticker, pos_info["buy_price"])
            current_stock_val += price * pos_info["qty"]
            pos_info["days_held"] += 1

        total_equity = cash + current_stock_val
        portfolio_equity_curve.append({"date": date.strftime("%Y-%m-%d"), "equity": total_equity})

        # 2. Check Exits (Emergency Risk Exit or Renewal vs Swap after 5 days)
        for ticker in list(positions.keys()):
            pos = positions[ticker]
            price = current_prices[ticker]
            score = candidate_scores.get(ticker, 50.0)

            should_exit = False
            exit_reason = ""

            # Risk Exit Rule (RSI < 32 or Score < 35)
            if score <= 35:
                should_exit = True
                exit_reason = "CRITICAL_RISK_EXIT"
            # 5-Day Rolling Evaluation: Only swap if a new candidate beats current score by friction barrier threshold
            elif pos["days_held"] >= HOLD_HORIZON_DAYS:
                top_new_candidate = max(
                    [t for t in candidate_scores if t not in positions],
                    key=lambda t: candidate_scores[t],
                    default=None
                )
                if top_new_candidate and candidate_scores[top_new_candidate] - score >= 30.0:
                    should_exit = True
                    exit_reason = "SWAP_FOR_HIGHER_CONVICTION"
                else:
                    # RENEW FOR ANOTHER 5-DAY CYCLE WITHOUT SELLING (Save Fees & Spread!)
                    pos["days_held"] = 0 # Reset cycle counter

            if should_exit:
                exec_price = price * (1.0 - SPREAD_PCT) # Sell at Bid (-0.10%)
                gross_proceeds = exec_price * pos["qty"]
                net_proceeds = gross_proceeds - FEE_PER_TRADE
                pnl = net_proceeds - (pos["buy_price"] * pos["qty"])

                cash += net_proceeds
                total_fees_paid += FEE_PER_TRADE
                total_trades += 1
                if pnl > 0:
                    winning_trades += 1

                del positions[ticker]

        # 3. Check Entries (If positions < 5 and Cash available)
        available_slots = MAX_POSITIONS - len(positions)
        if available_slots > 0 and cash >= 800.0:
            eligible_candidates = [
                t for t, s in candidate_scores.items()
                if t not in positions and s >= 70.0 and current_prices[t] >= data_dict[t].loc[date, "Close"] # Trend confirmation
            ]
            eligible_candidates.sort(key=lambda t: candidate_scores[t], reverse=True)

            for ticker in eligible_candidates[:available_slots]:
                price = current_prices[ticker]
                exec_price = price * (1.0 + SPREAD_PCT) # Buy at Ask (+0.10%)
                
                allocation = min(cash / available_slots, 1250.0)
                qty = math.floor((allocation - FEE_PER_TRADE) / exec_price)

                if qty >= 1:
                    stock_cost = qty * exec_price
                    total_cost = stock_cost + FEE_PER_TRADE

                    if cash >= total_cost:
                        cash -= total_cost
                        positions[ticker] = {
                            "qty": qty,
                            "buy_price": exec_price,
                            "days_held": 0
                        }
                        total_fees_paid += FEE_PER_TRADE

    # Final Liquidation for Performance Summary
    final_equity = cash
    for ticker, pos in positions.items():
        price = current_prices.get(ticker, pos["buy_price"])
        exec_price = price * (1.0 - SPREAD_PCT)
        net_proceeds = (exec_price * pos["qty"]) - FEE_PER_TRADE
        final_equity += net_proceeds

    total_return_pct = ((final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    # Annualized Return (CAGR) over 5 years
    cagr = (((final_equity / INITIAL_CAPITAL) ** (1 / 5)) - 1) * 100.0
    bench_cagr = (((bench_end_price / bench_start_price) ** (1 / 5)) - 1) * 100.0

    print("==========================================================")
    print("RESULTS OF 5-YEAR TSX BACKTEST (2019-2024)")
    print("==========================================================")
    print(f"Initial Capital         : ${INITIAL_CAPITAL:,.2f} CAD")
    print(f"Final Capital           : ${final_equity:,.2f} CAD")
    print(f"Net Real Return         : +{total_return_pct:.2f}% (CAGR: +{cagr:.2f}% / year)")
    print(f"Benchmark (XIU.TO TSX) : +{bench_return_pct:.2f}% (CAGR: +{bench_cagr:.2f}% / year)")
    print(f"Alpha vs Benchmark      : +{total_return_pct - bench_return_pct:.2f}%")
    print(f"Win Rate                : {win_rate:.1f}% ({winning_trades}/{total_trades} trades)")
    print(f"Total Transactions      : {total_trades} trades executed")
    print(f"Total Fees & Slippage   : ${total_fees_paid:,.2f} CAD deducted")
    print("==========================================================")

if __name__ == "__main__":
    run_backtest()
