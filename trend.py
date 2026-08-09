"""
Trend Analysis Module for AI Trading Bot.

Determines market trend direction (Uptrend, Downtrend, Sideways)
using price structure, SMA/EMA relationships, and custom indicators.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

logger = logging.getLogger(__name__)


def _get_column_name(df: pd.DataFrame, target: str) -> str | tuple | None:
    """Safely locate column name handling case-insensitivity and MultiIndex structures."""
    target_lower = target.lower()
    for col in df.columns:
        if isinstance(col, tuple):
            if str(col[0]).lower() == target_lower:
                return col
        elif str(col).lower() == target_lower:
            return col
    return None


def determine_trend(
    df: pd.DataFrame,
    short_window: int = 20,
    long_window: int = 50,
    **kwargs: Any
) -> str:
    """
    Determine the primary market trend using Moving Average relationships and price action.
    """
    if df is None or df.empty or len(df) < 2:
        return "Sideways"

    close_col = _get_column_name(df, "close")
    sma_short_col = _get_column_name(df, f"sma_{short_window}") or _get_column_name(df, "sma_20") or _get_column_name(df, "sma")
    sma_long_col = _get_column_name(df, f"sma_{long_window}") or _get_column_name(df, "sma_50")

    if not close_col:
        logger.warning("Missing close price column for trend determination.")
        return "Sideways"

    try:
        current_close = float(df[close_col].iloc[-1])

        if sma_short_col and sma_long_col:
            short_ma = float(df[sma_short_col].iloc[-1])
            long_ma = float(df[sma_long_col].iloc[-1])

            if current_close > short_ma > long_ma:
                return "Uptrend"
            elif current_close < short_ma < long_ma:
                return "Downtrend"
            return "Sideways"

        prev_close = float(df[close_col].iloc[-2])
        if current_close > prev_close * 1.01:
            return "Uptrend"
        elif current_close < prev_close * 0.99:
            return "Downtrend"

    except (ValueError, TypeError, KeyError, IndexError) as exc:
        logger.warning(f"Error evaluating trend: {exc}")
        return "Sideways"

    return "Sideways"


def analyze_trend_strength(df: pd.DataFrame, **kwargs: Any) -> Dict[str, Union[str, float]]:
    """
    Analyze the direction and quantitative strength of the current trend.
    """
    default_result: Dict[str, Union[str, float]] = {"trend": "Sideways", "strength": 0.0}

    if df is None or df.empty:
        return default_result

    trend = determine_trend(df, **kwargs)
    rsi_col = _get_column_name(df, "rsi")

    strength = 50.0
    if rsi_col:
        try:
            latest_rsi = float(df[rsi_col].iloc[-1])
            if trend == "Uptrend":
                strength = min(100.0, max(0.0, latest_rsi))
            elif trend == "Downtrend":
                strength = min(100.0, max(0.0, 100.0 - latest_rsi))
        except (ValueError, TypeError, KeyError, IndexError):
            strength = 50.0

    return {
        "trend": trend,
        "strength": round(strength, 2)
    }


def detect_trend(df: pd.DataFrame, *args: Any, **kwargs: Any) -> str:
    """Legacy alias for backward compatibility with backtest.py and main.py."""
    return determine_trend(df, *args, **kwargs)


def find_swing_points(df: pd.DataFrame, window: int = 5, **kwargs: Any) -> Dict[str, List[float]]:
    """
    Identify recent swing high and swing low price points for legacy modules.
    """
    default_swings: Dict[str, List[float]] = {"swing_highs": [], "swing_lows": []}
    if df is None or df.empty:
        return default_swings

    high_col = _get_column_name(df, "high")
    low_col = _get_column_name(df, "low")

    if not (high_col and low_col):
        return default_swings

    try:
        highs = df[high_col].tail(window).tolist()
        lows = df[low_col].tail(window).tolist()
        return {
            "swing_highs": [round(float(max(highs)), 2)] if highs else [],
            "swing_lows": [round(float(min(lows)), 2)] if lows else []
        }
    except (ValueError, TypeError, KeyError):
        return default_swings
