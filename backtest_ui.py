import os
import tempfile
import pandas as pd
import streamlit as st
from historical_data_loader import load_historical_csv
from backtest_engine import run_backtest

def render_backtest_ui():
    """
    Renders the isolated Backtest UI section in Streamlit.
    Connects CSV Upload -> historical_data_loader -> backtest_engine -> Streamlit displays.
    Strictly PAPER-ONLY and isolated from broker APIs or DB mutations.
    """
    st.header("📊 Historical Backtesting Engine")
    st.caption("Run zero-lookahead, point-in-time simulations on validated historical OHLCV data.")

    # --- UI Inputs Column Layout ---
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload Historical OHLCV CSV Data", type=["csv"])
        strategy_name = st.selectbox(
            "Select Strategy",
            ["SMA_RSI", "RSI_Breakout"],
            help="Select an available strategy compatible with strategy.py"
        )

    with col2:
        initial_cash = st.number_input("Initial Cash ($)", min_value=10.0, value=10000.0, step=500.0)
        commission_pct = st.number_input("Commission Rate (%)", min_value=0.0, max_value=5.0, value=0.1, step=0.01) / 100.0
        slippage_pct = st.number_input("Adverse Slippage (%)", min_value=0.0, max_value=5.0, value=0.05, step=0.01) / 100.0
        warmup_bars = st.number_input("Warm-up Period (Bars)", min_value=1, value=20, step=1)

    run_clicked = st.button("🚀 Run Historical Backtest", use_container_width=True)

    if not run_clicked:
        if uploaded_file is None:
            st.info("Please upload a historical OHLCV CSV file and click 'Run Historical Backtest' to begin.")
        return

    if uploaded_file is None:
        st.error("No CSV file uploaded. Please upload a valid historical dataset.")
        return

    # --- Step 1: Load and Validate Data via historical_data_loader ---
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        loader_res = load_historical_csv(tmp_path, min_required_bars=warmup_bars + 1)
    except Exception as e:
        st.error(f"Failed to process uploaded CSV file: {str(e)}")
        return
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    if not loader_res.get("success", False):
        st.error(f"Data Validation Failed: {loader_res.get('error', 'Invalid CSV format')}")
        return

    df_clean = loader_res.get("data")
    if df_clean is None or df_clean.empty:
        st.error("Historical data loader returned an empty dataset.")
        return

    st.success(f"Dataset successfully validated! Loaded {len(df_clean)} clean OHLCV bars.")

    # --- Step 2: Run Backtest Simulation ---
    try:
        bt_res = run_backtest(
            df=df_clean,
            strategy_name=strategy_name,
            initial_cash=initial_cash,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
            warmup_bars=warmup_bars
        )
    except Exception as e:
        st.error(f"Backtest Engine Execution Error: {str(e)}")
        return

    if not bt_res.get("success", False):
        st.error(f"Backtest Execution Failed: {bt_res.get('error', 'Engine failure')}")
        return

    # --- Step 3: Render Performance Metrics ---
    st.divider()
    st.subheader("📈 Performance Metrics")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Return", f"{bt_res['total_return_pct']:.2f}%")
    m2.metric("Net Profit", f"${bt_res['net_profit']:.2f}")
    m3.metric("Total Trades", f"{bt_res['total_trades']}")
    m4.metric("Win Rate", f"{bt_res['win_rate_pct']:.1f}%")
    pf_str = "∞" if bt_res['profit_factor'] == float('inf') else f"{bt_res['profit_factor']:.2f}"
    m5.metric("Profit Factor", pf_str)
    m6.metric("Max Drawdown", f"{bt_res['max_drawdown_pct']:.2f}%")

    if bt_res.get("open_position"):
        st.warning("⚠️ Final Position Status: Position remains OPEN at the end of dataset (Marked-to-market using final Close).")

    # --- Step 4: Render Equity Curve ---
    st.divider()
    st.subheader("📉 Portfolio Equity Curve")
    if bt_res.get("equity_curve"):
        equity_df = pd.DataFrame({"Equity ($)": bt_res["equity_curve"]}, index=df_clean.index)
        st.line_chart(equity_df)

    # --- Step 5: Render Completed Trades Journal ---
    st.divider()
    st.subheader("📝 Completed Trade Journal")
    trades = bt_res.get("trades", [])
    if trades:
        trades_df = pd.DataFrame(trades)
        st.dataframe(trades_df, use_container_width=True)
    else:
        st.info("No trades were triggered during this backtest simulation under the selected strategy rules and parameters.")