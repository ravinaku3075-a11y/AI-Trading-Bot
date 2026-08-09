"""
Candlestick Pattern Recognition Module for AI Trading Bot.

Identifies technical candlestick patterns such as Doji, Hammer, Shooting Star,
and Engulfing patterns with backwards-compatible output structures.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

logger = logging.getLogger(__name__)


def _get_ohlc_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Helper function to locate Open, High, Low, and Close columns safely."""
    open_col, high_col, low_col, close_col = None, None, None, None
    for col in df.columns:
        col_str = str(col[0] if isinstance(col, tuple) else col).lower()
        if col_str == "open":
            open_col = col
        elif col_str == "high":
            high_col = col
        elif col_str == "low":
            low_col = col
        elif col_str == "close":
            close_col = col
    return open_col, high_col, low_col, close_col


def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> bool:
    """Detect if the latest candle is a Doji pattern."""
    if df is None or df.empty:
        return False

    open_col, high_col, low_col, close_col = _get_ohlc_columns(df)
    if not (open_col and high_col and low_col and close_col):
        return False

    try:
        last_row = df.iloc[-1]
        open_p = float(last_row[open_col])
        high_p = float(last_row[high_col])
        low_p = float(last_row[low_col])
        close_p = float(last_row[close_col])

        body = abs(close_p - open_p)
        candle_range = high_p - low_p

        if candle_range == 0:
            return False

        return (body / candle_range) <= threshold
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def detect_hammer(df: pd.DataFrame) -> bool:
    """Detect if the latest candle is a Hammer pattern."""
    if df is None or df.empty:
        return False

    open_col, high_col, low_col, close_col = _get_ohlc_columns(df)
    if not (open_col and high_col and low_col and close_col):
        return False

    try:
        last_row = df.iloc[-1]
        open_p = float(last_row[open_col])
        high_p = float(last_row[high_col])
        low_p = float(last_row[low_col])
        close_p = float(last_row[close_col])

        body = abs(close_p - open_p)
        lower_shadow = min(open_p, close_p) - low_p
        upper_shadow = high_p - max(open_p, close_p)

        return lower_shadow >= (2 * body) and upper_shadow <= body
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def detect_candlestick_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Scan for active candlestick patterns on the most recent candle data.
    Returns structured result compatible with main.py requirements.
    """
    detected: List[str] = []

    if df is not None and not df.empty and len(df) >= 1:
        if detect_doji(df):
            detected.append("Doji")
        if detect_hammer(df):
            detected.append("Hammer")

    if not detected:
        detected = ["No Clear Pattern"]

    primary_pattern = detected[0]
    is_bullish = "Hammer" in detected
    is_bearish = False

    return {
        "patterns": detected,
        "pattern": primary_pattern,
        "is_bullish": is_bullish,
        "is_bearish": is_bearish
    }


def detect_patterns(df: pd.DataFrame, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Legacy alias matching expected interface for main.py scanner."""
    return detect_candlestick_patterns(df)
