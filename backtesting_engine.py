import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

def render_backtester_tab():
    st.header("🧪 Real Historical Backtester & Strategy Comparison")

    col1, col2, col3 = st.columns(3)
    symbol = col1.text_input("Stock Ticker (Yahoo Finance)", value="RELIANCE.NS").upper()
    fast_ema = col2.number_input("Fast EMA", min_value=5, max_value=50, value=20)
    slow_ema = col3.number_input("Slow EMA", min_value=20, max_value=200, value=50)

    if st.button("Run Backtest"):
        with st.spinner(f"Fetching real data for {symbol}..."):
            try:
                df = yf.download(symbol, period="1y", interval="1d")
                if df.empty:
                    st.error("Invalid Ticker or No Data Found.")
                    return

                # Calculate Signals
                df['Fast_EMA'] = df['Close'].ewm(span=fast_ema, adjust=False).mean()
                df['Slow_EMA'] = df['Close'].ewm(span=slow_ema, adjust=False).mean()

                # Strategy: Buy when Fast > Slow, else Cash
                df['Signal'] = 0
                df.loc[df['Fast_EMA'] > df['Slow_EMA'], 'Signal'] = 1
                df['Market_Returns'] = df['Close'].pct_change()
                df['Strategy_Returns'] = df['Market_Returns'] * df['Signal'].shift(1)

                # Equity Curve
                df['Market_Equity'] = (1 + df['Market_Returns']).cumprod()
                df['Strategy_Equity'] = (1 + df['Strategy_Returns']).cumprod()

                total_return = (df['Strategy_Equity'].iloc[-1] - 1) * 100
                market_return = (df['Market_Equity'].iloc[-1] - 1) * 100

                # Metrics
                m1, m2 = st.columns(2)
                m1.metric("Strategy Total Return", f"{total_return:.2f}%")
                m2.metric("Buy & Hold Return", f"{market_return:.2f}%")

                # Chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Strategy_Equity'], name="Strategy Equity Curve", line=dict(color="green")))
                fig.add_trace(go.Scatter(x=df.index, y=df['Market_Equity'], name="Benchmark (Buy & Hold)", line=dict(color="gray", dash="dash")))
                fig.update_layout(title=f"Performance Comparison for {symbol}", xaxis_title="Date", yaxis_title="Growth Multiplier")

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Backtest Error: {str(e)}")
