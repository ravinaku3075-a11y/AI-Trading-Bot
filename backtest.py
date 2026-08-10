"""
Backtesting Module for AI Trading Assistant.

Executes vector/event-driven backtesting for specific strategies.
"""

import logging
from typing import Dict, Any
import pandas as pd

import strategy
import risk

logger = logging.getLogger("Backtest")


def run_backtest(
    df: pd.DataFrame,
    initial_balance: float = 10000.0,
    risk_pct: float = 1.0,
    strategy_name: str = "SMA_RSI"
) -> Dict[str, Any]:
    """
    Executes backtest over historical candles for a chosen strategy.
    """
    if df is None or df.empty or len(df) < 20:
        return {
            "win_rate": 0.0,
            "net_profit": "0.0%",
            "net_profit_val": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "max_drawdown": "0.0%"
        }

    close_col = next((c for c in df.columns if str(c).lower() == "close"), df.columns[0])

    balance = initial_balance
    peak_balance = initial_balance
    max_drawdown = 0.0

    position = None
    trades = []

    for i in range(20, len(df)):
        sub_df = df.iloc[:i+1]
        current_candle = df.iloc[i]
        current_price = float(current_candle[close_col])

        if position:
            sl = position["stop_loss"]
            tp = position["take_profit"]
            pos_type = position["type"]
            entry_p = position["entry_price"]
            size = position["size"]

            exit_trade = False
            pnl = 0.0

            if pos_type == "BUY":
                if current_price <= sl:
                    pnl = (sl - entry_p) * size
                    exit_trade = True
                elif current_price >= tp:
                    pnl = (tp - entry_p) * size
                    exit_trade = True
            elif pos_type == "SELL":
                if current_price >= sl:
                    pnl = (entry_p - sl) * size
                    exit_trade = True
                elif current_price <= tp:
                    pnl = (entry_p - tp) * size
                    exit_trade = True

            if exit_trade:
                balance += pnl
                trades.append(pnl)
                position = None

        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

        if not position:
            sig_res = strategy.generate_signals(sub_df, strategy_name=strategy_name)
            sig_str = sig_res.signal if hasattr(sig_res, "signal") else "HOLD"

            if sig_str in ["BUY", "SELL"]:
                r_params = risk.calculate_risk_parameters(
                    account_balance=balance,
                    risk_percentage=risk_pct,
                    entry_price=current_price,
                    signal_type=sig_str
                )
                if r_params.get("is_trade_viable", False):
                    position = {
                        "type": sig_str,
                        "entry_price": current_price,
                        "size": r_params["position_size"],
                        "stop_loss": r_params["stop_loss"],
                        "take_profit": r_params["take_profit"]
                    }

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t > 0)
    losing_trades = sum(1 for t in trades if t <= 0)

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    gross_win = sum(t for t in trades if t > 0)
    gross_loss = abs(sum(t for t in trades if t < 0))
    profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else (round(gross_win, 2) if gross_win > 0 else 0.0)

    net_profit_pct = ((balance - initial_balance) / initial_balance) * 100

    return {
        "win_rate": round(win_rate, 2),
        "net_profit": f"{net_profit_pct:+.2f}%",
        "net_profit_val": round(net_profit_pct, 2),
        "profit_factor": profit_factor,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "max_drawdown": f"{max_drawdown * 100:.2f}%"
    }


def print_backtest_report(bt_res: Dict[str, Any]) -> None:
    """Prints formatted summary report to console."""
    if not bt_res:
        return
    print("\n==================================================")
    print("                 BACKTEST REPORT                  ")
    print("==================================================")
    print(f"Total Trades     : {bt_res.get('total_trades', 0)}")
    print(f"Winning Trades   : {bt_res.get('winning_trades', 0)}")
    print(f"Losing Trades    : {bt_res.get('losing_trades', 0)}")
    print(f"Win Rate         : {bt_res.get('win_rate', 0.0)}%")
    print(f"Net Profit       : {bt_res.get('net_profit', '0.0%')}")
    print(f"Profit Factor    : {bt_res.get('profit_factor', 0.0)}")
    print(f"Max Drawdown     : {bt_res.get('max_drawdown', '0.0%')}")
    print("==================================================")
