import os
import sqlite3
import pandas as pd
import streamlit as st
from paper_analytics import analyze_paper_trades

DB_PATH = "trades.db"
CSV_PATH = "trade_journal.csv"

def load_paper_trade_records():
    """
    Loads paper trade records with SQLite as primary source and CSV fallback.
    Prevents double-counting by accessing CSV only if SQLite is unavailable/empty.
    """
    records = []
    
    # 1. Primary Source: SQLite Database
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            df_sql = pd.read_sql_query("SELECT * FROM trades", conn)
            conn.close()
            if not df_sql.empty:
                return df_sql.to_dict(orient="records")
        except Exception:
            pass

    # 2. Fallback Source: CSV File
    if os.path.exists(CSV_PATH):
        try:
            df_csv = pd.read_csv(CSV_PATH)
            if not df_csv.empty:
                return df_csv.to_dict(orient="records")
        except Exception:
            pass

    return records

def render_paper_analytics_ui():
    """
    Renders the Paper Trading Analytics interface in Streamlit.
    Strictly isolated from live broker execution, order placement, and historical backtests.
    """
    st.header("📊 Paper Trading Analytics")
    st.caption("Performance insights and trade journal derived from paper trading executions.")

    records = load_paper_trade_records()
    res = analyze_paper_trades(records)

    if not res.get("success", False):
        st.error(f"Failed to calculate analytics: {res.get('error', 'Unknown error')}")
        return

    metrics = res.get("metrics", {})
    
    # --- Section 1: REALIZED PERFORMANCE ---
    st.subheader("📈 REALIZED PERFORMANCE")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Realized P&L", f"${metrics.get('total_realized_pnl', 0.0):.2f}")
    m2.metric("Total Return", f"{metrics.get('total_return_pct', 0.0):.2f}%")
    m3.metric("Closed Trades", f"{metrics.get('total_closed_trades', 0)}")
    m4.metric("Win Rate", f"{metrics.get('win_rate_pct', 0.0):.1f}%")
    m5.metric("Max Drawdown", f"{metrics.get('max_drawdown_pct', 0.0):.2f}%")

    m6, m7, m8, m9, m10 = st.columns(5)
    m6.metric("Winning Trades", f"{metrics.get('winning_trades', 0)}")
    m7.metric("Losing Trades", f"{metrics.get('losing_trades', 0)}")
    m8.metric("Breakeven Trades", f"{metrics.get('breakeven_trades', 0)}")
    m9.metric("Best Trade", f"${metrics.get('best_trade', 0.0):.2f}")
    m10.metric("Worst Trade", f"${metrics.get('worst_trade', 0.0):.2f}")

    # --- Realized Equity Curve ---
    st.divider()
    st.subheader("📉 Realized Equity Curve")
    equity_curve = res.get("equity_curve", [])
    if len(equity_curve) > 1:
        st.line_chart(equity_curve)
    else:
        st.info("Insufficient closed trade history to generate equity curve.")

    # --- Closed Trade Journal ---
    st.divider()
    st.subheader("📝 Closed Trade Journal")
    closed_trades = res.get("closed_trades", [])
    if closed_trades:
        st.dataframe(pd.DataFrame(closed_trades), use_container_width=True)
    else:
        st.info("No closed paper trades recorded yet.")

    # --- Section 2: CURRENT UNREALIZED POSITION STATUS ---
    st.divider()
    st.subheader("📌 CURRENT UNREALIZED POSITION STATUS")
    open_positions = res.get("open_positions", [])
    unrealized_pnl = res.get("unrealized_pnl", 0.0)

    st.metric("Total Unrealized P&L", f"${unrealized_pnl:.2f}")

    if open_positions:
        st.dataframe(pd.DataFrame(open_positions), use_container_width=True)
    else:
        st.info("No open paper positions currently active.")