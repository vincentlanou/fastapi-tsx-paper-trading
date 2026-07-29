import math
from typing import Tuple, List
import yfinance as yf
import pandas as pd
import numpy as np

# GLOBAL 75 TSX UNIVERSE (Top 30 S&P 500 CDRs + Top 15 TSX 60 + Top 30 MSCI EAFE)
GLOBAL_75_UNIVERSE = [
    # Top 15 TSX 60
    "RY.TO", "TD.TO", "SHOP.TO", "ENB.TO", "CNQ.TO", "BNS.TO",
    "CNR.TO", "CP.TO", "BMO.TO", "TRI.TO", "ATD.TO", "SU.TO",
    "MFC.TO", "ABX.TO", "NTR.TO",
    # Top 30 S&P 500 US Leaders via TSX CDRs
    "NVDA.TO", "AAPL.TO", "MSFT.TO", "AMZN.TO", "GOOG.TO", "TSLA.TO",
    "META.TO", "BRK.TO", "JPM.TO", "V.TO", "WMT.TO", "XOM.TO",
    "PG.TO", "HD.TO", "JNJ.TO", "COST.TO", "ORCL.TO", "CRM.TO",
    "CVX.TO", "AMD.TO", "KO.TO", "PEP.TO", "DIS.TO", "NFLX.TO",
    "ABT.TO", "BAC.TO", "CAT.TO", "IBM.TO", "LLY.TO", "AVGO.TO",
    # Top MSCI EAFE International Leaders Traded on TSX
    "ASML.TO", "AZN.TO", "SAP.TO", "SHEL.TO", "BTI.TO", "TTE.TO",
    "RHHBY.TO", "SNY.TO", "BAP.TO", "BP.TO", "UL.TO", "DEO.TO",
    "GSK.TO", "SONY.TO", "RIO.TO", "BHP.TO", "NVO.TO", "NVS.TO",
    "TM.TO", "HSBC.TO", "IMO.TO", "L.TO", "TECK-B.TO", "FNV.TO", "AEM.TO"
]

INITIAL_CAPITAL = 5000.0
FEE_PER_TRADE = 0.00        # BNCD $0.00 CAD Commission
SPREAD_PCT = 0.0005         # 0.05% TSX Spread Slippage
MAX_POSITIONS = 5
HOLD_HORIZON_DAYS = 20      # 15-30 day target horizon
RISK_FREE_RATE = 0.025      # 2.5% CAD annual risk-free rate

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)

def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def calculate_rvol_series(volume: pd.Series) -> pd.Series:
    ma_vol = volume.rolling(20).mean()
    rvol = volume / ma_vol.replace(0, np.nan)
    return rvol.fillna(1.0)

def calculate_volatility(prices: pd.Series) -> float:
    ret = prices.pct_change().dropna()
    if ret.empty or len(ret) < 10:
        return 20.0
    return float(ret.std() * np.sqrt(252) * 100.0)

def run_backtest():
    print("=== STARTING 5-YEAR BACKTEST: GLOBAL 75 UNIVERSE + GEMINI 4-STAGE ALPHA + RISK PARITY (2019-2024) ===")
    print("Universe: Top 30 S&P 500 CDRs + Top 15 TSX 60 | Capital: $5,000 CAD | BNCD $0 Fee | Risk Parity Sizing\n")

    data_dict = {}
    for ticker in GLOBAL_75_UNIVERSE:
        # auto_adjust=True ensures closing prices are fully adjusted for splits and dividends
        df = yf.Ticker(ticker).history(period="5y", interval="1d", auto_adjust=True)
        # Ensure stock has a full 5-year history (~1200 trading days) to avoid CDR inception bias
        if not df.empty and len(df) >= 1200:
            df["RSI"] = calculate_rsi(df["Close"])
            macd, signal, hist = calculate_macd(df["Close"])
            df["MACD_Hist"] = hist
            
            vol_series = df["Volume"] if "Volume" in df else pd.Series([1000000]*len(df), index=df.index)
            df["RVOL"] = calculate_rvol_series(vol_series)
            
            # Step 1: 4-Stage Alpha Score (60% Momentum + 40% RVOL - Penalty)
            # Note: Historical NLP sentiment is unavailable, so weights are redistributed.
            rsi_norm = df["RSI"]
            hist_norm = np.clip(hist / (df["Close"] * 0.02), -1.0, 1.0) * 50 + 50
            momentum = (rsi_norm * 0.5) + (hist_norm * 0.5)
            rvol_score = np.clip(df["RVOL"] * 50.0, 0.0, 100.0)
            
            penalty = np.where(df["RSI"] > 70, (df["RSI"] - 70) * 0.4, 0.0)
            
            df["Alpha_Score"] = np.clip((0.60 * momentum) + (0.40 * rvol_score) - penalty, 0.0, 100.0)
            
            # Annualized volatility over 60-day window for Risk Parity Sizing
            df["Vol_60d"] = df["Close"].rolling(60).apply(lambda p: calculate_volatility(p), raw=False).fillna(20.0)
            data_dict[ticker] = df

    # Download Benchmark (TSX Composite XIU.TO) for regime detection
    bench_df = yf.Ticker("XIU.TO").history(period="5y", interval="1d", auto_adjust=True)
    bench_df["MA20"] = bench_df["Close"].rolling(20).mean()
    bench_df["MA50"] = bench_df["Close"].rolling(50).mean()
    bench_df["Vol_30d"] = bench_df["Close"].pct_change().rolling(30).std() * np.sqrt(252) * 100.0
    bench_start_price = bench_df["Close"].iloc[0]
    bench_end_price = bench_df["Close"].iloc[-1]
    bench_return_pct = ((bench_end_price - bench_start_price) / bench_start_price) * 100.0

    cash = INITIAL_CAPITAL
    positions = {}
    total_trades = 0
    winning_trades = 0
    total_spread_cost = 0.0
    
    peak_equity = INITIAL_CAPITAL
    max_drawdown = 0.0
    regime_log = {"FALLING_KNIFE": 0, "RECOVERY": 0, "NORMAL": 0}

    # Use union of all trading dates to ensure we don't skip dates if a single benchmark ticker is halted
    all_dates = pd.DatetimeIndex([])
    for df in data_dict.values():
        all_dates = all_dates.union(df.index)
    all_dates = all_dates.sort_values()
    common_dates = all_dates[60:]

    for date in common_dates:
        current_prices = {}
        alpha_scores = {}
        volatilities = {}

        for ticker, df in data_dict.items():
            if date in df.index:
                row = df.loc[date]
                current_prices[ticker] = float(row["Close"])
                alpha_scores[ticker] = float(row["Alpha_Score"])
                volatilities[ticker] = float(row["Vol_60d"])

        # --- Regime Detection (Benchmark XIU.TO) ---
        # FALLING_KNIFE: XIU below 50-day MA AND annualized vol > 30% → don't open new positions
        # RECOVERY: XIU above 20-day MA after being below 50-day MA, vol still elevated → aggressive entries
        # NORMAL: standard momentum rotation
        regime = "NORMAL"
        if date in bench_df.index:
            b_row = bench_df.loc[date]
            bench_price = float(b_row["Close"])
            bench_ma20 = float(b_row["MA20"]) if not np.isnan(b_row["MA20"]) else bench_price
            bench_ma50 = float(b_row["MA50"]) if not np.isnan(b_row["MA50"]) else bench_price
            bench_vol = float(b_row["Vol_30d"]) if not np.isnan(b_row["Vol_30d"]) else 15.0

            if bench_price < bench_ma50 and bench_vol > 30.0:
                regime = "FALLING_KNIFE"
            elif bench_price > bench_ma20 and bench_vol > 22.0 and bench_price < bench_ma50 * 1.03:
                regime = "RECOVERY"

        regime_log[regime] += 1

        # 1. Portfolio Valuation
        current_stock_val = 0.0
        for ticker, pos_info in list(positions.items()):
            price = current_prices.get(ticker, pos_info["buy_price"])
            current_stock_val += price * pos_info["qty"]
            pos_info["days_held"] += 1

        total_equity = cash + current_stock_val
        if total_equity > peak_equity:
            peak_equity = total_equity
            
        current_drawdown = (total_equity - peak_equity) / peak_equity
        if current_drawdown < max_drawdown:
            max_drawdown = current_drawdown

        # 2. Check Exits (Alpha-based only — NEVER force-liquidate based on drawdown)
        for ticker in list(positions.keys()):
            pos = positions[ticker]
            price = current_prices.get(ticker)
            if price is None:
                continue
            score = alpha_scores.get(ticker, 50.0)

            should_exit = False
            if score <= 35:
                should_exit = True
            elif pos["days_held"] >= HOLD_HORIZON_DAYS:
                top_new = max(
                    [t for t in alpha_scores if t not in positions],
                    key=lambda t: alpha_scores[t],
                    default=None
                )
                if top_new and alpha_scores[top_new] - score >= 20.0:
                    should_exit = True
                else:
                    pos["days_held"] = 0  # Rollover for zero fee

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

        # 3. Check Entries (Regime-Aware)
        available_slots = MAX_POSITIONS - len(positions)

        if regime == "FALLING_KNIFE":
            # Freeze: don't open any new positions during freefall
            pass
        elif available_slots > 0 and cash >= 800.0:
            # RECOVERY mode: lower the alpha threshold to 55 to catch V-bounce candidates
            # NORMAL mode: standard threshold of 68
            alpha_threshold = 55.0 if regime == "RECOVERY" else 68.0

            eligible_candidates = [
                t for t, s in alpha_scores.items()
                if t not in positions and s >= alpha_threshold
            ]
            eligible_candidates.sort(key=lambda t: alpha_scores[t], reverse=True)

            target_candidates = eligible_candidates[:available_slots]
            if target_candidates:
                # Step 2: Risk Parity Inverse Volatility Sizing Calculation
                cand_vols = [volatilities[t] for t in target_candidates]
                inv_vols = [1.0 / max(1.0, v) for v in cand_vols]
                sum_inv = sum(inv_vols)

                for idx, ticker in enumerate(target_candidates):
                    price = current_prices[ticker]
                    exec_price = price * (1.0 + SPREAD_PCT)

                    # Risk Parity Weight %
                    weight = inv_vols[idx] / sum_inv
                    allocation = min(cash, total_equity * weight)
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
    print("RESULTS OF 5-YEAR BACKTEST: GLOBAL 75 + GEMINI RISK PARITY")
    print("==========================================================")
    print(f"Initial Capital         : ${INITIAL_CAPITAL:,.2f} CAD")
    print(f"Final Capital           : ${final_equity:,.2f} CAD")
    print(f"Max Portfolio Drawdown  : {max_drawdown*100:.2f}%")
    
    sign = '+' if total_return_pct >= 0 else ''
    cagr_sign = '+' if cagr >= 0 else ''
    bench_sign = '+' if bench_return_pct >= 0 else ''
    bench_cagr_sign = '+' if bench_cagr >= 0 else ''
    alpha_val = cagr - bench_cagr
    alpha_sign = '+' if alpha_val >= 0 else ''
    
    print(f"Net Real Return         : {sign}{total_return_pct:.2f}% (CAGR: {cagr_sign}{cagr:.2f}% / year)")
    print(f"Benchmark (XIU.TO TSX) : {bench_sign}{bench_return_pct:.2f}% (CAGR: {bench_cagr_sign}{bench_cagr:.2f}% / year)")
    print(f"Alpha vs Benchmark      : {alpha_sign}{alpha_val:.2f}% (CAGR difference)")
    print(f"Win Rate                : {win_rate:.1f}% ({winning_trades}/{total_trades} trades)")
    print(f"Total Transactions      : {total_trades} trades executed")
    print(f"BNCD Commission Fees    : $0.00 CAD (Zero Commission)")
    print(f"Total Spread Slippage   : ${total_spread_cost:,.2f} CAD ({SPREAD_PCT*100:.2f}% TSX Spread)")
    total_regime_days = sum(regime_log.values())
    print(f"Regime Days             : NORMAL={regime_log['NORMAL']} | FALLING_KNIFE={regime_log['FALLING_KNIFE']} (frozen) | RECOVERY={regime_log['RECOVERY']} (aggressive)")
    print("==========================================================")

if __name__ == "__main__":
    run_backtest()
