import sqlite3
import pandas as pd
from datetime import datetime

def get_daily_closed_trade_metrics(conn, date_str):
    """
    Existing analytics function for calculating daily closed trade performance metrics.
    """
    metrics = {
        "date": date_str,
        "total_closed": 0,
        "total_pnl": 0.0,
        "win_rate": 0.0,
        "wins": 0,
        "losses": 0
    }
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='closed_trades'")
        if not cursor.fetchone():
            return metrics

        query = "SELECT pnl FROM closed_trades WHERE DATE(close_time) = ?"
        df = pd.read_sql_query(query, conn, params=(date_str,))
        if df.empty:
            return metrics

        total_closed = len(df)
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] <= 0])
        total_pnl = float(df['pnl'].sum())
        win_rate = float(wins / total_closed) if total_closed > 0 else 0.0

        metrics.update({
            "total_closed": total_closed,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "wins": wins,
            "losses": losses
        })
    except Exception as e:
        print(f"[ANALYTICS WARNING] Error calculating daily closed metrics: {e}")
    return metrics


def get_observation_dashboard_metrics(conn):
    """
    Read-only observation dashboard helper for STEP 22C-2F.
    Guaranteed non-modifying: executes SELECT queries only with graceful fallback.
    """
    default_metrics = {
        "buy_count": 0,
        "sell_count": 0,
        "hold_count": 0,
        "confidence_rejected_count": 0,
        "risk_rejected_count": 0,
        "executed_orders_count": 0,
        "open_positions_count": 0,
        "last_signal": None,
        "last_confidence": None,
        "last_signal_timestamp": None,
        "observation_window_start": None,
        "observation_window_end": None,
        "enhanced_analytics_sample_size": 0,
        "closed_trade_count": 0
    }

    if conn is None:
        return default_metrics

    try:
        cursor = conn.cursor()

        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # 1. Action Counts & Executed Orders from 'trades' table
        if "trades" in tables:
            cursor.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]

            if "action" in columns:
                cursor.execute("SELECT LOWER(action), COUNT(*) FROM trades GROUP BY LOWER(action)")
                action_counts = dict(cursor.fetchall())
                default_metrics["buy_count"] = action_counts.get("buy", 0)
                default_metrics["sell_count"] = action_counts.get("sell", 0)
                default_metrics["hold_count"] = action_counts.get("hold", 0)

            if "status" in columns:
                cursor.execute("SELECT COUNT(*) FROM trades WHERE LOWER(status)='executed'")
                res = cursor.fetchone()
                default_metrics["executed_orders_count"] = res[0] if res else 0
            else:
                # Fallback: Total trades count if 'status' column is absent
                cursor.execute("SELECT COUNT(*) FROM trades")
                res = cursor.fetchone()
                default_metrics["executed_orders_count"] = res[0] if res else 0

        # 2. Signals & Rejections from 'telegram_alerts' table
        if "telegram_alerts" in tables:
            cursor.execute("PRAGMA table_info(telegram_alerts)")
            ta_columns = [col[1] for col in cursor.fetchall()]

            if "signal_side" in ta_columns and "event_timestamp" in ta_columns:
                cursor.execute("SELECT signal_side, event_timestamp FROM telegram_alerts ORDER BY id DESC LIMIT 1")
                last_alert = cursor.fetchone()
                if last_alert:
                    default_metrics["last_signal"] = last_alert[0]
                    default_metrics["last_signal_timestamp"] = last_alert[1]

            if "status" in ta_columns:
                cursor.execute("SELECT COUNT(*) FROM telegram_alerts WHERE LOWER(status)='failed'")
                res = cursor.fetchone()
                default_metrics["confidence_rejected_count"] = res[0] if res else 0

        # 3. Observation Window & Sample Size from 'closed_trades' table
        if "closed_trades" in tables:
            cursor.execute("PRAGMA table_info(closed_trades)")
            ct_columns = [col[1] for col in cursor.fetchall()]

            if "close_time" in ct_columns:
                cursor.execute("SELECT COUNT(*), MIN(close_time), MAX(close_time) FROM closed_trades")
                ct_res = cursor.fetchone()
                if ct_res and ct_res[0] > 0:
                    default_metrics["closed_trade_count"] = ct_res[0]
                    default_metrics["enhanced_analytics_sample_size"] = ct_res[0]
                    default_metrics["observation_window_start"] = ct_res[1]
                    default_metrics["observation_window_end"] = ct_res[2]

    except Exception as e:
        print(f"[OBSERVATION METRICS WARNING] Exception during read-only evaluation: {e}")

    return default_metrics