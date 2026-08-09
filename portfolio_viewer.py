import streamlit as st
import sqlite3
import pandas as pd
import os

DB_PATH = "trading_bot.db"

def get_portfolio_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def render_portfolio_tab():
    st.header("📊 Portfolio & Trades Log")
    df = get_portfolio_data()

    if df.empty:
        st.info("Koi trade history nahi mili. Terminal se new trades execute karein.")
        return

    st.subheader("📈 Trade History Table")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Trades Executed", len(df))
    with col2:
        buy_count = len(df[df['action'] == 'BUY']) if 'action' in df.columns else 0
        st.metric("Total Buy Trades", buy_count)

# Autonomous Smart Patch
def check_price_break_alert(symbol: str, price: float, support: float, resistance: float) -> dict:
    """Analyzes support and resistance breakout for portfolio_viewer.py"""
    if price >= resistance:
        return {'alert': 'RESISTANCE_BREAKOUT', 'symbol': symbol, 'price': price}
    elif price <= support:
        return {'alert': 'SUPPORT_BREAKDOWN', 'symbol': symbol, 'price': price}
    return {'alert': 'RANGE_BOUND', 'symbol': symbol, 'price': price}
