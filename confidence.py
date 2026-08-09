"""
Confidence Scoring Module for AI Trading Assistant (v1.1).

Calculates dynamic confidence score (0-100%) based on confluence factors:
1. Trend Alignment (30%)
2. Pattern Confirmation (25%)
3. RSI Regime Strength (25%)
4. Support/Resistance Proximity (20%)
"""

import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger("Confidence")


def calculate_confidence_score(
    signal: str,
    trend: str,
    pattern: str,
    current_price: float,
    rsi_val: float,
    support: float,
    resistance: float
) -> int:
    """
    Calculates a weighted confidence percentage for a given signal.
    """
    if signal == "HOLD" or current_price <= 0:
        return 0

    score = 0

    # 1. Trend Alignment (Max 30 pts)
    if signal == "BUY" and trend.upper() == "UPTREND":
        score += 30
    elif signal == "SELL" and trend.upper() == "DOWNTREND":
        score += 30
    elif trend.upper() == "SIDEWAYS":
        score += 15

    # 2. Pattern Confirmation (Max 25 pts)
    bullish_patterns = ["HAMMER", "BULLISH_ENGULFING", "MORNING_STAR"]
    bearish_patterns = ["SHOOTING_STAR", "BEARISH_ENGULFING", "EVENING_STAR"]

    patt_upper = pattern.upper()
    if signal == "BUY" and any(p in patt_upper for p in bullish_patterns):
        score += 25
    elif signal == "SELL" and any(p in patt_upper for p in bearish_patterns):
        score += 25
    elif pattern.upper() not in ["NONE", "UNKNOWN", ""]:
        score += 10

    # 3. RSI Regime Strength (Max 25 pts)
    if signal == "BUY":
        if 40 <= rsi_val <= 55:
            score += 25  # Ideal momentum buildup zone
        elif rsi_val < 40:
            score += 15  # Oversold rebound
    elif signal == "SELL":
        if 60 <= rsi_val <= 75:
            score += 25  # Overbought exhaustion zone
        elif rsi_val > 75:
            score += 15

    # 4. Support/Resistance Proximity (Max 20 pts)
    if support > 0 and resistance > 0 and resistance > support:
        price_range = resistance - support
        if signal == "BUY":
            # Distance from support
            dist_from_supp = (current_price - support) / price_range
            if dist_from_supp <= 0.25:  # Buying near support level
                score += 20
            elif dist_from_supp <= 0.50:
                score += 10
        elif signal == "SELL":
            # Distance from resistance
            dist_from_res = (resistance - current_price) / price_range
            if dist_from_res <= 0.25:  # Selling near resistance level
                score += 20
            elif dist_from_res <= 0.50:
                score += 10

    return min(100, max(0, score))
