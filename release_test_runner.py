import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("PaperAnalytics")


def get_daily_closed_trade_metrics(conn, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    metrics = {
        "date": date_str,
        "total_closed": 0,
        "closed_pnl": 0.0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0
    }

    if conn is None:
        return metrics

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trades', 'closed_trades');")
        existing_tables = [row[0] for row in cursor.fetchall()]

        if "closed_trades" in existing_tables:
            query = "SELECT pnl FROM closed_trades WHERE DATE(close_time) = ?"
        elif "trades" in existing_tables:
            cursor.execute("PRAGMA table_info(trades);")
            cols = [info[1] for info in cursor.fetchall()]
            if "pnl" not in cols or "close_time" not in cols:
                return metrics
            query = "SELECT pnl FROM trades WHERE status = 'CLOSED' AND DATE(close_time) = ?"
        else:
            return metrics

        cursor.execute(query, (date_str,))
        rows = cursor.fetchall()

        total = len(rows)
        if total == 0:
            return metrics

        pnl_sum = 0.0
        wins = 0
        losses = 0

        for row in rows:
            pnl = row[0] if row[0] is not None else 0.0
            pnl_sum += pnl
            if pnl > 0:
                wins += 1
            elif pnl < 0:
                losses += 1

        metrics["total_closed"] = total
        metrics["closed_pnl"] = round(pnl_sum, 4)
        metrics["wins"] = wins
        metrics["losses"] = losses
        metrics["win_rate"] = round((wins / total) * 100.0, 2) if total > 0 else 0.0

    except Exception as e:
        logger.error(f"Error computing daily closed trade metrics: {e}")

    return metrics


def get_observation_dashboard_metrics(conn):
    default_metrics = {
        "buy_count": 0,
        "sell_count": 0,
        "hold_count": 0,
        "executed_orders_count": 0,
        "closed_trade_count": 0,
        "total_pnl": 0.0
    }

    if conn is None:
        return default_metrics

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades';")
        if not cursor.fetchone():
            return default_metrics

        cursor.execute("PRAGMA table_info(trades);")
        cols = [info[1] for info in cursor.fetchall()]

        select_pnl = "SUM(COALESCE(pnl, 0.0))" if "pnl" in cols else "0.0"
        select_status = "SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END)" if "status" in cols else "0"

        query = f"""
            SELECT
                COUNT(*),
                SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END),
                SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END),
                SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END),
                {select_status},
                {select_pnl}
            FROM trades
        """
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            default_metrics["executed_orders_count"] = row[0] or 0
            default_metrics["buy_count"] = row[1] or 0
            default_metrics["sell_count"] = row[2] or 0
            default_metrics["hold_count"] = row[3] or 0
            default_metrics["closed_trade_count"] = row[4] or 0
            default_metrics["total_pnl"] = round(row[5] or 0.0, 4)

    except Exception as e:
        logger.error(f"Error querying observation metrics: {e}")

    return default_metrics


def get_full_production_dashboard_metrics(conn):
    payload = {
        "total_trades": 0,
        "buy_count": 0,
        "sell_count": 0,
        "hold_count": 0,
        "executed_orders_count": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "realized_pnl": 0.0,
        "daily_pnl": 0.0,
        "open_positions_count": 0,
        "latest_trade": None,
        "recent_trades": [],
        "daily_loss_lock_status": False,
        "observation_sample_size": 0
    }

    if conn is None:
        return payload

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades';")
        if not cursor.fetchone():
            return payload

        cursor.execute("PRAGMA table_info(trades);")
        cols = [info[1] for info in cursor.fetchall()]

        # 1. Action Counts
        cursor.execute("""
            SELECT
                COUNT(*),
                SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END),
                SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END),
                SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END)
            FROM trades;
        """)
        row = cursor.fetchone()
        if row:
            payload["total_trades"] = row[0] or 0
            payload["executed_orders_count"] = row[0] or 0
            payload["buy_count"] = row[1] or 0
            payload["sell_count"] = row[2] or 0
            payload["hold_count"] = row[3] or 0
            payload["observation_sample_size"] = row[0] or 0

        # 2. Wins, Losses, Realized P&L
        if "pnl" in cols and "status" in cols:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END),
                    SUM(COALESCE(pnl, 0.0)),
                    COUNT(*)
                FROM trades
                WHERE status = 'CLOSED';
            """)
            pnl_row = cursor.fetchone()
            if pnl_row and pnl_row[3] and pnl_row[3] > 0:
                payload["wins"] = pnl_row[0] or 0
                payload["losses"] = pnl_row[1] or 0
                payload["realized_pnl"] = round(pnl_row[2] or 0.0, 4)
                closed_cnt = pnl_row[3]
                payload["win_rate"] = round((payload["wins"] / closed_cnt) * 100.0, 2)

        # 3. Daily P&L
        if "pnl" in cols and "status" in cols and "close_time" in cols:
            today_str = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT SUM(COALESCE(pnl, 0.0)) FROM trades WHERE status = 'CLOSED' AND DATE(close_time) = ?;", (today_str,))
            d_row = cursor.fetchone()
            if d_row and d_row[0] is not None:
                payload["daily_pnl"] = round(d_row[0], 4)

        # 4. Open Positions Count
        if "status" in cols:
            cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN';")
            open_row = cursor.fetchone()
            if open_row:
                payload["open_positions_count"] = open_row[0] or 0

        # 5. Recent Trades (Max 20)
        select_cols = [c for c in ["id", "symbol", "action", "price", "quantity", "status", "pnl", "timestamp", "close_time"] if c in cols]
        if select_cols:
            query_cols = ", ".join(select_cols)
            cursor.execute(f"SELECT {query_cols} FROM trades ORDER BY id DESC LIMIT 20;")
            trades_rows = cursor.fetchall()
            recent_list = []
            for r in trades_rows:
                trade_dict = {col_name: r[i] for i, col_name in enumerate(select_cols)}
                recent_list.append(trade_dict)

            payload["recent_trades"] = recent_list
            if recent_list:
                payload["latest_trade"] = recent_list[0]

    except Exception as e:
        logger.error(f"Error computing full production dashboard metrics: {e}")

    return payload
