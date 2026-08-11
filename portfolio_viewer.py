import streamlit as st
import sqlite_logger
import paper_analytics
import portfolio_risk_manager

st.set_page_config(page_title="AI Trading Bot - Observation Dashboard", layout="wide")

st.title("📊 Production Observation Dashboard (Read-Only)")
st.caption("Live System Monitoring & Paper Analytics | Execution Logic Frozen")

conn = None
try:
    conn = sqlite_logger.get_connection()
    metrics = paper_analytics.get_full_production_dashboard_metrics(conn)

    # Risk Lock Check
    rm = portfolio_risk_manager.PortfolioRiskManager()
    is_locked = rm.check_daily_loss_lock(conn) if conn else False
    metrics["daily_loss_lock_status"] = is_locked

except Exception as e:
    st.error(f"Error loading metrics from database: {e}")
    metrics = paper_analytics.get_full_production_dashboard_metrics(None)
finally:
    if conn:
        conn.close()

# 1. Top KPI Row
col1, col2, col3, col4, col5, col6 = st.columns(6)

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

with col6:
    lock_status = "LOCKED 🔒" if metrics.get("daily_loss_lock_status") else "NORMAL 🟢"
    st.metric("Risk Lock Status", lock_status)

st.divider()

# 2. System Health & Action Breakdown
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🟢 System & Database Health")
    st.json({
        "Database Path": sqlite_logger.DB_PATH,
        "Executed Orders Count": metrics.get("executed_orders_count", 0),
        "Observation Sample Size": metrics.get("observation_sample_size", 0),
        "Worker Status": "ONLINE / ACTIVE"
    })

with col_b:
    st.subheader("🎯 Action Breakdown")
    st.write(f"**BUY Orders:** {metrics.get('buy_count', 0)}")
    st.write(f"**SELL Orders:** {metrics.get('sell_count', 0)}")
    st.write(f"**HOLD Orders:** {metrics.get('hold_count', 0)}")
    st.write(f"**Wins / Losses:** {metrics.get('wins', 0)} / {metrics.get('losses', 0)}")

st.divider()

# 3. Latest Trade & Recent Trades Table
st.subheader("🧾 Latest & Recent Trades (Max 20)")

recent_trades = metrics.get("recent_trades", [])
if recent_trades:
    st.dataframe(recent_trades, use_container_width=True)
else:
    st.info("No trade records found in database.")