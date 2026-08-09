"""
Support and Resistance Levels Detection Module for AI Trading Assistant.

Calculates key price levels using pivot points and local rolling extrema.
"""

import logging
from typing import Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger("Levels")


def calculate_levels(df: pd.DataFrame, window: int = 14) -> Dict[str, float]:
    """
    Calculates primary Support and Resistance levels from historical candles.
    """
    if df is None or df.empty or len(df) < window:
        return {"support": 0.0, "resistance": 0.0}

    cols = {str(c).lower(): c for c in df.columns}
    high_col = cols.get("high", "High")
    low_col = cols.get("low", "Low")
    close_col = cols.get("close", "Close")

    if high_col not in df.columns or low_col not in df.columns:
        return {"support": 0.0, "resistance": 0.0}

    # Rolling Min/Max Support and Resistance
    recent_df = df.tail(window)
    support = float(recent_df[low_col].min())
    resistance = float(recent_df[high_col].max())

    # Fallback Pivot Point logic if range is zero
    if support == resistance and close_col in df.columns:
        last_close = float(df.iloc[-1][close_col])
        pivot = (float(df.iloc[-1][high_col]) + float(df.iloc[-1][low_col]) + last_close) / 3.0
        support = round(2 * pivot - float(df.iloc[-1][high_col]), 2)
        resistance = round(2 * pivot - float(df.iloc[-1][low_col]), 2)

    return {
        "support": round(support, 2),
        "resistance": round(resistance, 2)
    }
