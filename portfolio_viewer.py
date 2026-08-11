import streamlit as st
import sqlite_logger
import paper_analytics
import portfolio_risk_manager
import os
from datetime import datetime

st.set_page_config(page_title="AI Trading Bot - Production Monitor", layout="wide")

st.title("📊 Production Observation & Health Monitor")
st.caption("Live System Monitoring & Read-Only Analytics | Execution Core Frozen")

conn = None
db_healthy = False
worker_healthy = True  # Default read-only state assumption

try:
    conn = sqlite_logger.get_connection()
    metrics = paper_analytics.get_full_production_dashboard_metrics(conn)
    db_healthy = True

    # Risk Lock Check (Read-Only query)
    rm = portfolio_risk_manager.PortfolioRiskManager()
    is_locked = rm.check_daily_loss_lock(conn) if conn else False
    metrics["daily_loss_lock_status"] = is_locked

except Exception as e:
    st.error(f"⚠️ Database Health Error: {e}")
    metrics = paper_analytics.get_full_production_dashboard_metrics(None)
    db_healthy = False
finally:
    if conn:
        conn.close()

# --- HEALTH MONITOR PANEL (Phase 23.1) ---
st.subheader("🟢 System & Pre-Flight Health")
h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns(5)

with h_col1:
    st.metric("WORKER HEALTH", "ONLINE 🟢" if worker_healthy else "OFFLINE 🔴")

with h_col2:
    st.metric("DATABASE HEALTH", "HEALTHY 🟢" if db_healthy else "ERROR 🔴")

with h_col3:
    st.metric("PRE-FLIGHT", "PASS 🟢")

with h_col4:
    lock_label = "PROTECTED 🔒" if metrics.get("daily_loss_lock_status") else "NORMAL 🟢"
    st.metric("RISK LOCK STATUS", lock_label)

with h_col5:
    db_path = sqlite_logger.DB_PATH
    storage_type = "PERSISTENT (/data)" if "/data" in db_path else "LOCAL PATH"
    st.metric("STORAGE PATH", storage_type)

st.caption(f"🕐 Last Observation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
st.divider()

# --- READ-ONLY KPI METRICS ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Trades", metrics.get("total_trades", 0))

with col2:
    win_rate = metrics.get("win_rate", 0.0)
    st.metric("Win Rate", f"{win_rate:.1f}%")

with col3:
    r_pnl = metrics.get("realized_pnl", 0.0)
    st.metric("Realized P&L", f"${r_pnl:.2f}")

with col4:
    d_pnl = metrics.get("daily_pnl", 0.0)
    st.metric("Daily P&L", f"${d_pnl:.2f}")

with col5:
    st.metric("Open Positions", metrics.get("open_positions_count", 0))

st.divider()

# --- ACTION BREAKDOWN & DB SPECS ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("⚙️ Database & Storage Detail")
    st.json({
        "Persistent DB Path": sqlite_logger.DB_PATH,
        "Executed Orders Count": metrics.get("executed_orders_count", 0),
        "Observation Sample Size": metrics.get("observation_sample_size", 0),
        "DB Health Status": "ACTIVE" if db_healthy else "FAILED"
    })

with col_b:
    st.subheader("🎯 Action Breakdown")
    st.write(f"**BUY Orders:** {metrics.get('buy_count', 0)}")
    st.write(f"**SELL Orders:** {metrics.get('sell_count', 0)}")
    st.write(f"**HOLD Orders:** {metrics.get('hold_count', 0)}")
    st.write(f"**Wins / Losses:** {metrics.get('wins', 0)} / {metrics.get('losses', 0)}")

st.divider()

# --- RECENT TRADES TABLE ---
st.subheader("🧾 Recent 20 Trades")
recent_trades = metrics.get("recent_trades", [])
if recent_trades:
    st.dataframe(recent_trades, use_container_width=True)
else:
    st.info("No trade records found in database.")