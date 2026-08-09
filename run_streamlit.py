import streamlit as st
import os
import pandas as pd

from paper_trading import PaperTradingEngine
from paper_analytics_ui import render_paper_analytics_ui
from risk_controls_ui import render_risk_controls_ui

st.set_page_config(
    page_title="AI Trading Bot Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize global paper trading engine in session state if not already present
if "paper_engine" not in st.session_state:
    st.session_state["paper_engine"] = PaperTradingEngine()

st.title("🤖 AI Trading Bot Dashboard")

# Top-Level Dashboard Tabs
tab1, tab2 = st.tabs(["📊 Live / Paper Monitor", "🧪 Historical Backtest"])

with tab1:
    # Sub-tabs under Live / Paper Monitor
    subtab1, subtab2, subtab3 = st.tabs([
        "🔴 Live Bot Monitor", 
        "📈 Paper Analytics", 
        "🛡️ Risk Controls"
    ])
    
    with subtab1:
        st.header("🔴 Live Bot & Paper Monitor")
        st.write("Real-time trading bot controls, open positions, and live price feeds.")
        
        # Display current paper engine balance summary
        engine = st.session_state["paper_engine"]
        col1, col2 = st.columns(2)
        col1.metric("Available Cash", f"${engine.cash:,.2f}")
        col2.metric("Open Positions Count", len(engine.positions))

    with subtab2:
        # Render Paper Trading Analytics Tab
        render_paper_analytics_ui()

    with subtab3:
        # Render Read-Only Portfolio Risk Controls Tab
        engine = st.session_state["paper_engine"]
        # Pass optional live mark prices from active feeds if available in session state
        live_prices = st.session_state.get("live_prices", {})
        render_risk_controls_ui(engine, current_prices=live_prices)

with tab2:
    st.header("🧪 Historical Backtest Engine")
    st.write("Backtest strategies against historical market data.")
    
    # Placeholder for Backtest UI module
    try:
        from backtest_ui import render_backtest_ui
        render_backtest_ui()
    except ImportError:
        st.info("Backtest UI module (backtest_ui.py) is isolated and can be rendered here.")