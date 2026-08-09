import numpy as np

def validate_portfolio_risk(order_request, portfolio_state, risk_limits=None):
    """
    Pure function portfolio risk validator.
    Evaluates order requests against portfolio exposure, daily loss, and realized drawdown limits.
    Strictly isolated: No database mutations, no broker calls, no side effects.
    """
    if risk_limits is None:
        risk_limits = {
            "max_symbol_exposure_pct": 25.0,
            "max_portfolio_exposure_pct": 80.0,
            "max_daily_loss_pct": 5.0,
            "max_realized_drawdown_pct": 15.0
        }

    reasons = []
    
    # 1. Validate order request payload
    if not isinstance(order_request, dict):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Invalid order_request payload format."],
            "metrics": {}
        }

    symbol = str(order_request.get("symbol", "")).upper()
    side = str(order_request.get("side", "")).upper()

    try:
        price = float(order_request.get("price", 0.0))
        quantity = float(order_request.get("quantity", 0.0))
    except (ValueError, TypeError):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Non-numeric price or quantity in order_request."],
            "metrics": {}
        }

    if not symbol or price <= 0 or quantity <= 0 or not np.isfinite(price) or not np.isfinite(quantity):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Invalid symbol, price, or quantity supplied."],
            "metrics": {}
        }

    # 2. Validate portfolio state payload
    if not isinstance(portfolio_state, dict):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Invalid portfolio_state payload format."],
            "metrics": {}
        }

    try:
        available_cash = float(portfolio_state.get("available_cash", 0.0))
        open_positions = portfolio_state.get("open_positions", {})
        daily_realized_pnl = float(portfolio_state.get("daily_realized_pnl", 0.0))
        realized_drawdown_pct = float(portfolio_state.get("realized_drawdown_pct", 0.0))
        current_prices = portfolio_state.get("current_prices", {})
    except (ValueError, TypeError):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Corrupt numerical values in portfolio_state."],
            "metrics": {}
        }

    # Classify Order Side
    symbol_holding = open_positions.get(symbol, {}) if isinstance(open_positions, dict) else {}
    held_qty = float(symbol_holding.get("quantity", 0.0)) if isinstance(symbol_holding, dict) else 0.0

    if side in ["BUY", "LONG"]:
        is_risk_increasing = True
    elif side in ["SELL", "SHORT"]:
        if quantity > held_qty + 1e-8:
            return {
                "allowed": False,
                "status": "ERROR",
                "reasons": [f"Cannot SELL quantity ({quantity}) greater than held position ({held_qty})."],
                "metrics": {}
            }
        is_risk_increasing = False
    else:
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": [f"Unsupported order side '{side}'."],
            "metrics": {}
        }

    # If Risk-Reducing SELL, allow if held quantity is valid
    if not is_risk_increasing:
        return {
            "allowed": True,
            "status": "SAFE",
            "reasons": ["Risk-reducing order approved."],
            "metrics": {
                "daily_realized_pnl": daily_realized_pnl,
                "realized_drawdown_pct": realized_drawdown_pct
            }
        }

    # --- STRICT CHECKS FOR RISK-INCREASING BUY ORDERS ---

    # Price Validation Check: Missing/Stale price fails safely for BUYs (No entry price fallback)
    symbol_mark_price = current_prices.get(symbol)
    if symbol_mark_price is None:
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": [f"Missing current mark price for symbol {symbol}. BUY order blocked."],
            "metrics": {}
        }
    try:
        symbol_mark_price = float(symbol_mark_price)
        if symbol_mark_price <= 0 or not np.isfinite(symbol_mark_price):
            raise ValueError
    except (ValueError, TypeError):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": [f"Invalid mark price ({symbol_mark_price}) for {symbol}. BUY order blocked."],
            "metrics": {}
        }

    order_value = price * quantity

    # Available Cash Check
    if order_value > available_cash:
        reasons.append(f"Insufficient available cash (${available_cash:.2f}) for order value (${order_value:.2f}).")

    # Valuation of Portfolio & Holdings
    total_open_value = 0.0
    symbol_open_value = 0.0

    if isinstance(open_positions, dict):
        for sym, pos in open_positions.items():
            if not isinstance(pos, dict):
                continue
            p_qty = float(pos.get("quantity", 0.0))
            if p_qty <= 0:
                continue
            
            p_mark = current_prices.get(sym)
            if p_mark is None or float(p_mark) <= 0 or not np.isfinite(float(p_mark)):
                return {
                    "allowed": False,
                    "status": "ERROR",
                    "reasons": [f"Missing valid mark price for existing portfolio position {sym}."],
                    "metrics": {}
                }
            
            val = p_qty * float(p_mark)
            total_open_value += val
            if sym == symbol:
                symbol_open_value = val

    total_equity = available_cash + total_open_value
    if total_equity <= 0 or not np.isfinite(total_equity):
        return {
            "allowed": False,
            "status": "ERROR",
            "reasons": ["Invalid or non-positive total portfolio equity."],
            "metrics": {}
        }

    # 1. Symbol Concentration Check
    proposed_symbol_value = symbol_open_value + order_value
    proposed_symbol_exp_pct = (proposed_symbol_value / total_equity) * 100.0
    max_sym_limit = float(risk_limits.get("max_symbol_exposure_pct", 25.0))
    if proposed_symbol_exp_pct > max_sym_limit:
        reasons.append(f"Proposed symbol exposure ({proposed_symbol_exp_pct:.2f}%) exceeds limit ({max_sym_limit:.2f}%).")

    # 2. Portfolio Exposure Check
    proposed_portfolio_value = total_open_value + order_value
    proposed_port_exp_pct = (proposed_portfolio_value / total_equity) * 100.0
    max_port_limit = float(risk_limits.get("max_portfolio_exposure_pct", 80.0))
    if proposed_port_exp_pct > max_port_limit:
        reasons.append(f"Proposed portfolio exposure ({proposed_port_exp_pct:.2f}%) exceeds limit ({max_port_limit:.2f}%).")

    # 3. Daily Realized Loss Limit Check
    max_daily_loss_pct = float(risk_limits.get("max_daily_loss_pct", 5.0))
    max_daily_loss_amount = (max_daily_loss_pct / 100.0) * total_equity
    if daily_realized_pnl < 0 and abs(daily_realized_pnl) >= max_daily_loss_amount:
        reasons.append(f"Daily realized loss (${abs(daily_realized_pnl):.2f}) reached max limit (${max_daily_loss_amount:.2f}).")

    # 4. Realized Drawdown Guard Check
    max_realized_dd_limit = float(risk_limits.get("max_realized_drawdown_pct", 15.0))
    if realized_drawdown_pct >= max_realized_dd_limit:
        reasons.append(f"Realized drawdown guard limit ({realized_drawdown_pct:.2f}%) reached max limit ({max_realized_dd_limit:.2f}%).")

    allowed = len(reasons) == 0
    status = "SAFE" if allowed else "BLOCKED"

    return {
        "allowed": allowed,
        "status": status,
        "reasons": reasons if reasons else ["Order passes all risk checks."],
        "metrics": {
            "current_symbol_exposure_pct": round((symbol_open_value / total_equity) * 100.0, 2),
            "proposed_symbol_exposure_pct": round(proposed_symbol_exp_pct, 2),
            "current_portfolio_exposure_pct": round((total_open_value / total_equity) * 100.0, 2),
            "proposed_portfolio_exposure_pct": round(proposed_port_exp_pct, 2),
            "daily_realized_pnl": round(daily_realized_pnl, 2),
            "realized_drawdown_pct": round(realized_drawdown_pct, 2)
        }
    }