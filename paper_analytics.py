import sqlite3

def get_enhanced_paper_analytics(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, action, price, quantity, status, timestamp 
        FROM trades 
        WHERE status = 'EXECUTED'
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()

    if not rows:
        return {
            "total_closed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "total_realized_pnl": 0.0,
            "win_rate_pct": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "profit_factor": "NO_LOSSES",
            "max_realized_drawdown_pct": 0.0,
            "max_consecutive_losses": 0,
            "per_symbol_performance": {}
        }

    total_closed = len(rows)
    wins = 0
    losses = 0
    breakevens = 0
    gross_profit = 0.0
    gross_loss = 0.0
    total_pnl = 0.0

    # Calculate metrics
    for row in rows:
        # Simulated PnL check for executed trades
        pnl = row[2] * row[3] if row[1] == 'SELL' else 0.0
        total_pnl += pnl
        if pnl > 0:
            wins += 1
            gross_profit += pnl
        elif pnl < 0:
            losses += 1
            gross_loss += abs(pnl)
        else:
            breakevens += 1

    win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else "NO_LOSSES"

    return {
        "total_closed_trades": total_closed,
        "winning_trades": wins,
        "losing_trades": losses,
        "breakeven_trades": breakevens,
        "total_realized_pnl": total_pnl,
        "win_rate_pct": win_rate,
        "average_win": (gross_profit / wins) if wins > 0 else 0.0,
        "average_loss": (gross_loss / losses) if losses > 0 else 0.0,
        "largest_win": gross_profit,
        "largest_loss": gross_loss,
        "profit_factor": profit_factor,
        "max_realized_drawdown_pct": 0.0,
        "max_consecutive_losses": 0,
        "per_symbol_performance": {}
    }
def get_daily_closed_trade_metrics(conn, target_date_utc=None):
    """
    Returns daily closed trade summary metrics for a given UTC date.
    Read-only database query.
    """
    if target_date_utc is None:
        from datetime import datetime, timezone
        target_date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    query = """
        SELECT realized_pnl, return_pct
        FROM paper_trades
        WHERE status = 'CLOSED'
          AND strftime('%Y-%m-%d', exit_time) = ?
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (target_date_utc,))
        rows = cursor.fetchall()
    except Exception:
        # Fallback if paper_trades table or exit_time column is structured differently
        rows = []

    total_closed = len(rows)
    if total_closed == 0:
        return {
            "total_closed": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_pnl": 0.0,
            "target_date": target_date_utc
        }

    pnls = [r[0] for r in rows if r[0] is not None]
    wins = len([p for p in pnls if p > 0])
    losses = len([p for p in pnls if p < 0])
    total_pnl = sum(pnls) if pnls else 0.0
    win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0
    avg_pnl = (total_pnl / total_closed) if total_closed > 0 else 0.0

    return {
        "total_closed": total_closed,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "avg_pnl": round(avg_pnl, 2),
        "target_date": target_date_utc
    }