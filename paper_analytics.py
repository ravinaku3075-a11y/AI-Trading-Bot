import pandas as pd
import numpy as np

def analyze_paper_trades(trade_records, initial_capital=10000.0, current_prices=None):
    """
    Analyzes paper trading trade records chronologically.
    Calculates realized metrics, equity curve, max drawdown, closed trades, and open positions.
    Strictly PAPER-ONLY and isolated from live broker APIs, databases, or historical backtest engine state.
    """
    if initial_capital <= 0 or not np.isfinite(initial_capital):
        return {
            "success": False,
            "metrics": {},
            "equity_curve": [10000.0],
            "closed_trades": [],
            "open_positions": [],
            "unrealized_pnl": 0.0,
            "error": "Invalid initial capital provided."
        }

    # Normalize input into list of dicts
    if trade_records is None:
        records = []
    elif isinstance(trade_records, pd.DataFrame):
        records = trade_records.to_dict(orient="records")
    elif isinstance(trade_records, list):
        records = list(trade_records)
    else:
        return {
            "success": False,
            "metrics": {},
            "equity_curve": [initial_capital],
            "closed_trades": [],
            "open_positions": [],
            "unrealized_pnl": 0.0,
            "error": "Unsupported trade records data format."
        }

    if not records:
        return {
            "success": True,
            "metrics": {
                "total_realized_pnl": 0.0,
                "total_return_pct": 0.0,
                "total_closed_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "breakeven_trades": 0,
                "win_rate_pct": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "max_drawdown_pct": 0.0
            },
            "equity_curve": [float(initial_capital)],
            "closed_trades": [],
            "open_positions": [],
            "unrealized_pnl": 0.0,
            "error": None
        }

    # State tracking per symbol
    open_positions = {}  # symbol -> {"quantity": float, "total_cost": float, "entry_commission": float}
    closed_trades = []

    # Sort records chronologically if timestamp exists
    valid_records = []
    for r in records:
        if not isinstance(r, dict):
            continue
        symbol = str(r.get("symbol", r.get("asset_pair", "DEFAULT"))).upper()
        side = str(r.get("side", r.get("type", ""))).upper()
        
        try:
            price = float(r.get("price", 0.0))
            quantity = float(r.get("quantity", r.get("size", 0.0)))
            commission = float(r.get("commission", r.get("fee", 0.0)))
        except (ValueError, TypeError):
            continue

        if price <= 0 or quantity <= 0 or not np.isfinite(price) or not np.isfinite(quantity):
            continue

        timestamp = r.get("timestamp", r.get("datetime", ""))
        valid_records.append({
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "commission": max(0.0, commission) if np.isfinite(commission) else 0.0,
            "timestamp": timestamp
        })

    # Process executions sequentially
    for trade in valid_records:
        sym = trade["symbol"]
        side = trade["side"]
        qty = trade["quantity"]
        px = trade["price"]
        comm = trade["commission"]
        ts = trade["timestamp"]

        if sym not in open_positions:
            open_positions[sym] = {"quantity": 0.0, "total_cost": 0.0, "entry_commission": 0.0}

        pos = open_positions[sym]

        if side in ["BUY", "LONG"]:
            pos["quantity"] += qty
            pos["total_cost"] += (qty * px)
            pos["entry_commission"] += comm

        elif side in ["SELL", "SHORT"]:
            if pos["quantity"] <= 0:
                continue  # Skip SELL without active long quantity

            sell_qty = min(qty, pos["quantity"])
            avg_entry_price = pos["total_cost"] / pos["quantity"]
            proportional_entry_comm = (sell_qty / pos["quantity"]) * pos["entry_commission"]

            gross_pnl = (px - avg_entry_price) * sell_qty
            exit_comm = (sell_qty / qty) * comm
            net_pnl = gross_pnl - proportional_entry_comm - exit_comm

            closed_trades.append({
                "symbol": sym,
                "quantity": sell_qty,
                "entry_price": round(avg_entry_price, 4),
                "exit_price": round(px, 4),
                "gross_pnl": round(gross_pnl, 4),
                "net_pnl": round(net_pnl, 4),
                "total_commission": round(proportional_entry_comm + exit_comm, 4),
                "timestamp": ts
            })

            # Update remaining open position
            pos["quantity"] -= sell_qty
            pos["total_cost"] -= (sell_qty * avg_entry_price)
            pos["entry_commission"] -= proportional_entry_comm

            if pos["quantity"] <= 1e-8:
                pos["quantity"] = 0.0
                pos["total_cost"] = 0.0
                pos["entry_commission"] = 0.0

    # Clean up open positions dictionary
    active_open_positions = []
    unrealized_pnl = 0.0

    for sym, pos in open_positions.items():
        if pos["quantity"] > 0:
            avg_entry = pos["total_cost"] / pos["quantity"]
            curr_price = avg_entry
            if current_prices and isinstance(current_prices, dict) and sym in current_prices:
                try:
                    curr_price = float(current_prices[sym])
                except (ValueError, TypeError):
                    curr_price = avg_entry

            u_pnl = (curr_price - avg_entry) * pos["quantity"] - pos["entry_commission"]
            unrealized_pnl += u_pnl

            active_open_positions.append({
                "symbol": sym,
                "quantity": round(pos["quantity"], 4),
                "avg_entry_price": round(avg_entry, 4),
                "current_price": round(curr_price, 4),
                "unrealized_pnl": round(u_pnl, 4)
            })

    # Compute realized performance metrics
    total_closed = len(closed_trades)
    pnls = [t["net_pnl"] for t in closed_trades]

    total_realized_pnl = float(sum(pnls))
    total_return_pct = (total_realized_pnl / initial_capital) * 100.0

    winning_trades = sum(1 for p in pnls if p > 0)
    losing_trades = sum(1 for p in pnls if p < 0)
    breakeven_trades = sum(1 for p in pnls if p == 0)

    win_rate_pct = (winning_trades / total_closed * 100.0) if total_closed > 0 else 0.0
    best_trade = max(pnls) if total_closed > 0 else 0.0
    worst_trade = min(pnls) if total_closed > 0 else 0.0

    # Build chronological realized equity curve & peak-to-trough max drawdown
    equity_curve = [float(initial_capital)]
    running_eq = float(initial_capital)
    running_peak = float(initial_capital)
    max_dd_pct = 0.0

    for pnl in pnls:
        running_eq += pnl
        equity_curve.append(round(running_eq, 4))
        if running_eq > running_peak:
            running_peak = running_eq
        if running_peak > 0:
            dd = (running_peak - running_eq) / running_peak * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd

    return {
        "success": True,
        "metrics": {
            "total_realized_pnl": round(total_realized_pnl, 4),
            "total_return_pct": round(total_return_pct, 4),
            "total_closed_trades": total_closed,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "breakeven_trades": breakeven_trades,
            "win_rate_pct": round(win_rate_pct, 2),
            "best_trade": round(best_trade, 4),
            "worst_trade": round(worst_trade, 4),
            "max_drawdown_pct": round(max_dd_pct, 4)
        },
        "equity_curve": equity_curve,
        "closed_trades": closed_trades,
        "open_positions": active_open_positions,
        "unrealized_pnl": round(unrealized_pnl, 4),
        "error": None
    }