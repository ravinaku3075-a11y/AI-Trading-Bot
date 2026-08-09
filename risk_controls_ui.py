import streamlit as st

def render_risk_controls_ui(engine, current_prices: dict = None):
    """
    Renders read-only Risk Controls UI in Streamlit subtab.
    Pure display renderer without order creation or limit mutations.
    """
    st.markdown("## 🛡️ Portfolio Risk Controls & Status")
    
    if engine is None:
        st.error("PaperTradingEngine instance is unavailable.")
        return

    snapshot = engine.get_portfolio_risk_snapshot(current_prices=current_prices)
    status = snapshot.get("status", "DATA_UNAVAILABLE")

    # A. OVERALL RISK STATUS
    st.markdown("### A. Overall Risk Status")
    if status == "SAFE":
        st.success("🟢 STATUS: SAFE — All monitored exposure, loss, and drawdown metrics are within normal limits.")
    elif status == "WARNING":
        st.warning("⚠️ STATUS: WARNING — One or more risk metrics are approaching configured limits (>=80%).")
    elif status == "LIMIT_REACHED":
        st.error("🚨 STATUS: LIMIT REACHED — Configured daily loss, drawdown, or portfolio exposure threshold hit.")
    else:
        st.info("ℹ️ STATUS: DATA UNAVAILABLE — Missing mark price feeds for open positions.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Available Cash", f"${snapshot['current_cash']:,.2f}")
    
    eq = snapshot['total_portfolio_equity']
    c2.metric("Portfolio Equity", f"${eq:,.2f}" if eq is not None else "N/A")
    
    pnl = snapshot['daily_realized_pnl']
    c3.metric("Daily Realized P&L (Closed Trades)", f"${pnl:,.2f}")
    
    c4.metric("Realized Drawdown Guard", f"{snapshot['realized_drawdown_pct']:.2f}%")

    st.markdown("---")

    # B. PORTFOLIO EXPOSURE & CONCENTRATION
    st.markdown("### B. Portfolio Exposure & Concentration")
    port_exp = snapshot.get("total_portfolio_exposure_pct")
    limits = snapshot.get("risk_limits", {})
    max_port_limit = limits.get("max_portfolio_exposure_pct", 80.0)

    if port_exp is not None:
        st.write(f"**Total Portfolio Exposure:** `{port_exp:.2f}%` / Max Limit `{max_port_limit:.2f}%`")
        st.progress(min(max(port_exp / 100.0, 0.0), 1.0))
    else:
        st.warning("Total Portfolio Exposure: N/A (Missing mark prices)")

    per_sym = snapshot.get("per_symbol_exposure", {})
    max_sym_limit = limits.get("max_symbol_exposure_pct", 25.0)

    if per_sym:
        st.markdown("#### Per-Symbol Concentration")
        for sym, exp_pct in per_sym.items():
            st.write(f"- **{sym}:** `{exp_pct:.2f}%` (Max Allowed: `{max_sym_limit:.2f}%`)")
            st.progress(min(max(exp_pct / 100.0, 0.0), 1.0))
    elif status != "DATA_UNAVAILABLE":
        st.info("No open positions currently held.")

    st.markdown("---")

    # C. CONFIGURED RISK LIMITS
    st.markdown("### C. Configured Risk Limits (Read-Only)")
    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Max Symbol Exposure", f"{limits.get('max_symbol_exposure_pct', 25.0):.1f}%")
    l2.metric("Max Portfolio Exposure", f"{limits.get('max_portfolio_exposure_pct', 80.0):.1f}%")
    l3.metric("Max Daily Loss Cap", f"{limits.get('max_daily_loss_pct', 5.0):.1f}%")
    l4.metric("Max Realized Drawdown", f"{limits.get('max_realized_drawdown_pct', 15.0):.1f}%")

    st.markdown("---")

    # D. PRICE DATA & SAFETY HEALTH
    st.markdown("### D. Price Data & Safety Health")
    missing = snapshot.get("missing_price_symbols", [])
    if missing:
        st.error(f"⚠️ Missing Mark Prices for Open Positions: {', '.join(missing)}")
        st.caption("Risk valuation requires valid current mark prices. Fallback to entry price is strictly prohibited.")
    else:
        st.success("✅ Price feeds for open holdings are verified and up to date.")