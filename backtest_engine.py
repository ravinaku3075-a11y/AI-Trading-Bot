import math
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Callable
from strategy import generate_signals, SignalOutput

def run_backtest(
    df: pd.DataFrame,
    strategy_fn: Optional[Callable] = None,
    strategy_name: str = "SMA_RSI",
    initial_cash: float = 10000.0,
    commission_pct: float = 0.001,
    commission_per_trade: float = 0.0,
    slippage_pct: float = 0.0005,
    warmup_bars: int = 20
) -> Dict[str, Any]:
    """
    Executes a zero-lookahead, point-in-time bar-by-bar backtest simulation.
    
    Execution Timing Rule:
    - Signals are evaluated at Bar i Close using only historical data up to Bar i (df.iloc[:i+1]).
    - Execution of pending buy/sell signals occurs strictly at Bar i+1 Open price with adverse slippage and commission applied.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return _empty_results("Input DataFrame is empty or invalid.")

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            return _empty_results(f"Missing required column: {col}")

    if initial_cash <= 0 or math.isnan(initial_cash):
        return _empty_results("Initial cash must be a positive number.")

    total_bars = len(df)
    if total_bars <= warmup_bars:
        return _empty_results(f"Insufficient historical bars ({total_bars}) for warmup period ({warmup_bars}).")

    if strategy_fn is None:
        def default_strat(data_slice: pd.DataFrame):
            sig_obj = generate_signals(data_slice, strategy_name=strategy_name)
            if hasattr(sig_obj, 'signal'):
                sig_val = sig_obj.signal
            elif isinstance(sig_obj, dict) and 'signal' in sig_obj:
                sig_val = sig_obj['signal']
            else:
                sig_val = str(sig_obj)
            
            if hasattr(sig_val, 'value'):
                sig_str = str(sig_val.value).upper()
            else:
                sig_str = str(sig_val).upper()
                
            if "BUY" in sig_str:
                return "BUY"
            elif "SELL" in sig_str:
                return "SELL"
            return "HOLD"
            
        strategy_fn = default_strat

    current_cash = float(initial_cash)
    position_status = "NONE"  # "NONE" or "LONG"
    entry_price = 0.0
    entry_qty = 0.0
    entry_time = None
    entry_commission = 0.0

    trades = []
    equity_curve = []
    pending_signal = "HOLD"

    for i in range(total_bars):
        bar_time = df.index[i]
        bar_open = float(df["Open"].iloc[i])
        bar_close = float(df["Close"].iloc[i])

        if math.isnan(bar_open) or bar_open <= 0 or math.isnan(bar_close) or bar_close <= 0:
            current_equity = current_cash + (entry_qty * bar_close if position_status == "LONG" else 0.0)
            equity_curve.append(current_equity)
            continue

        # --- A. EXECUTE PENDING ORDER AT BAR i OPEN ---
        if pending_signal == "BUY" and position_status == "NONE":
            exec_price = bar_open * (1.0 + slippage_pct)
            usable_cash = current_cash - commission_per_trade
            if usable_cash > 0 and exec_price > 0:
                qty = usable_cash / (exec_price * (1.0 + commission_pct))
                if qty > 0:
                    trade_comm = (qty * exec_price * commission_pct) + commission_per_trade
                    cost = (qty * exec_price) + trade_comm
                    
                    if cost <= current_cash:
                        current_cash -= cost
                        entry_qty = qty
                        entry_price = exec_price
                        entry_time = bar_time
                        entry_commission = trade_comm
                        position_status = "LONG"

        elif pending_signal == "SELL" and position_status == "LONG":
            exec_price = bar_open * (1.0 - slippage_pct)
            if exec_price > 0 and entry_qty > 0:
                exit_comm = (entry_qty * exec_price * commission_pct) + commission_per_trade
                gross_proceeds = entry_qty * exec_price
                net_proceeds = gross_proceeds - exit_comm
                
                current_cash += net_proceeds
                pnl_actual = net_proceeds - (entry_qty * entry_price + entry_commission)
                pnl_pct = (pnl_actual / (entry_qty * entry_price + entry_commission)) * 100.0 if (entry_qty * entry_price + entry_commission) > 0 else 0.0

                trades.append({
                    "entry_time": entry_time,
                    "exit_time": bar_time,
                    "entry_price": entry_price,
                    "exit_price": exec_price,
                    "quantity": entry_qty,
                    "pnl": pnl_actual,
                    "pnl_pct": pnl_pct,
                    "total_commission": entry_commission + exit_comm
                })

                position_status = "NONE"
                entry_qty = 0.0
                entry_price = 0.0
                entry_time = None
                entry_commission = 0.0

        pending_signal = "HOLD"

        # --- B. RECORD PORTFOLIO EQUITY AT BAR i CLOSE ---
        position_value = (entry_qty * bar_close) if position_status == "LONG" else 0.0
        current_equity = current_cash + position_value
        equity_curve.append(current_equity)

        # --- C. GENERATE SIGNAL AT BAR i CLOSE ---
        if i >= warmup_bars - 1:
            historical_slice = df.iloc[:i + 1]
            try:
                sig = strategy_fn(historical_slice)
                if sig in ["BUY", "SELL", "HOLD"]:
                    pending_signal = sig
            except Exception:
                pending_signal = "HOLD"

    return _calculate_metrics(initial_cash, current_cash, position_status, entry_qty, float(df["Close"].iloc[-1]), trades, equity_curve)


def _calculate_metrics(initial_cash, current_cash, position_status, entry_qty, final_close, trades, equity_curve):
    is_open = (position_status == "LONG")
    final_equity = current_cash + (entry_qty * final_close if is_open else 0.0)
    net_profit = final_equity - initial_cash
    total_return_pct = (net_profit / initial_cash) * 100.0 if initial_cash > 0 else 0.0

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t["pnl"] > 0)
    losing_trades = sum(1 for t in trades if t["pnl"] <= 0)
    win_rate_pct = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = float('inf')
    else:
        profit_factor = 0.0

    avg_win = (gross_profit / winning_trades) if winning_trades > 0 else 0.0
    avg_loss = (gross_loss / losing_trades) if losing_trades > 0 else 0.0
    win_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else (float('inf') if avg_win > 0 else 0.0)

    max_drawdown_pct = 0.0
    if equity_curve:
        peak = equity_curve[0]
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0.0
            if dd > max_drawdown_pct:
                max_drawdown_pct = dd
    max_drawdown_pct *= 100.0

    return {
        "success": True,
        "error": None,
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "net_profit": net_profit,
        "total_return_pct": total_return_pct,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate_pct": win_rate_pct,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown_pct,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "win_loss_ratio": win_loss_ratio,
        "open_position": is_open,
        "trades": trades,
        "equity_curve": equity_curve
    }


def _empty_results(error_msg: str) -> Dict[str, Any]:
    return {
        "success": False,
        "error": error_msg,
        "initial_cash": 0.0,
        "final_equity": 0.0,
        "net_profit": 0.0,
        "total_return_pct": 0.0,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "win_rate_pct": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "profit_factor": 0.0,
        "max_drawdown_pct": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "win_loss_ratio": 0.0,
        "open_position": False,
        "trades": [],
        "equity_curve": []
    }