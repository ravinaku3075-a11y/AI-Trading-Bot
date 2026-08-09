"""
Risk Management Module for AI Trading Bot.

Calculates position sizing, stop-loss/take-profit levels,
and portfolio risk exposure parameters.
"""

import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def calculate_position_size(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss_price: float
) -> Dict[str, Union[int, float]]:
    """
    Calculate optimal trade position size based on account risk limits.
    """
    default_result: Dict[str, Union[int, float]] = {
        "shares": 0,
        "risk_amount": 0.0,
        "position_value": 0.0,
    }

    try:
        balance = float(account_balance)
        risk_pct = float(risk_percentage)
        entry = float(entry_price)
        stop_loss = float(stop_loss_price)

        if balance <= 0 or entry <= 0 or stop_loss <= 0:
            return default_result

        per_share_risk = abs(entry - stop_loss)
        if per_share_risk <= 0:
            logger.warning("Stop loss distance is zero or invalid.")
            return default_result

        max_risk_amount = balance * (risk_pct / 100.0)
        shares = int(max_risk_amount / per_share_risk)
        position_value = round(shares * entry, 2)

        if position_value > balance:
            shares = int(balance / entry)
            position_value = round(shares * entry, 2)

        return {
            "shares": shares,
            "risk_amount": round(shares * per_share_risk, 2),
            "position_value": position_value,
        }

    except (ValueError, TypeError, ZeroDivisionError) as exc:
        logger.warning(f"Error calculating position size: {exc}")
        return default_result


def calculate_stop_loss_take_profit(
    entry_price: float,
    signal_type: str = "BUY",
    atr: Optional[float] = None,
    risk_reward_ratio: float = 2.0,
    stop_loss_pct: float = 0.02
) -> Dict[str, float]:
    """
    Calculate dynamic Stop Loss and Take Profit levels.
    """
    try:
        entry = float(entry_price)
        if entry <= 0:
            return {"stop_loss": 0.0, "take_profit": 0.0}

        sig = str(signal_type).upper()
        rr = float(risk_reward_ratio)

        if atr is not None and atr > 0:
            sl_distance = float(atr) * 1.5
        else:
            sl_distance = entry * float(stop_loss_pct)

        tp_distance = sl_distance * rr

        if sig == "BUY":
            stop_loss = entry - sl_distance
            take_profit = entry + tp_distance
        elif sig == "SELL":
            stop_loss = entry + sl_distance
            take_profit = entry - tp_distance
        else:
            stop_loss = entry * (1.0 - stop_loss_pct)
            take_profit = entry * (1.0 + (stop_loss_pct * rr))

        return {
            "stop_loss": round(max(0.0, stop_loss), 2),
            "take_profit": round(max(0.0, take_profit), 2),
        }

    except (ValueError, TypeError) as exc:
        logger.warning(f"Error calculating SL/TP: {exc}")
        return {"stop_loss": 0.0, "take_profit": 0.0}


def calculate_risk_parameters(
    account_balance: float = 10000.0,
    risk_percentage: float = 1.0,
    entry_price: float = 100.0,
    stop_loss_price: Optional[float] = None,
    signal_type: str = "BUY",
    risk_reward_ratio: float = 2.0,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Legacy alias matching expected interface for backtest.py and main.py.
    """
    if stop_loss_price is None or stop_loss_price <= 0:
        sl_tp = calculate_stop_loss_take_profit(
            entry_price=entry_price,
            signal_type=signal_type,
            risk_reward_ratio=risk_reward_ratio
        )
        stop_loss_price = sl_tp["stop_loss"]
    else:
        sl_tp = calculate_stop_loss_take_profit(
            entry_price=entry_price,
            signal_type=signal_type,
            risk_reward_ratio=risk_reward_ratio
        )

    pos_size = calculate_position_size(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price
    )

    is_viable = pos_size["shares"] > 0 and pos_size["position_value"] > 0

    return {
        "shares": pos_size["shares"],
        "position_size": pos_size["shares"],
        "risk_amount": pos_size["risk_amount"],
        "position_value": pos_size["position_value"],
        "stop_loss": sl_tp["stop_loss"],
        "take_profit": sl_tp["take_profit"],
        "risk_reward_ratio": round(float(risk_reward_ratio), 2),
        "is_trade_viable": is_viable,
        "is_viable": is_viable
    }
