"""
Strategy Engine for AI Trading Assistant (v1.1 Multi-Strategy Architecture).

Contains independent modular strategies:
1. SMA_RSI (Default Crossover + RSI Regime Filter)
2. RSI_BREAKOUT (Mean Reversion / Oversold Overbought)
"""

import logging
from typing import NamedTuple
import pandas as pd

logger = logging.getLogger("Strategy")


class SignalOutput(NamedTuple):
    signal: str  # "BUY", "SELL", or "HOLD"
    reason: str


def strategy_sma_rsi(df: pd.DataFrame) -> SignalOutput:
    """Strategy 1: SMA-20/50 Crossover with RSI (45-68) regime filter."""
    if df is None or len(df) < 50:
        return SignalOutput("HOLD", "Insufficient Data")

    close_col = next((c for c in df.columns if str(c).lower() == "close"), df.columns[0])

    sma20 = df['SMA_20'] if 'SMA_20' in df.columns else df[close_col].rolling(20).mean()
    sma50 = df['SMA_50'] if 'SMA_50' in df.columns else df[close_col].rolling(50).mean()
    rsi = df['RSI'] if 'RSI' in df.columns else pd.Series(50, index=df.index)

    curr_sma20, prev_sma20 = float(sma20.iloc[-1]), float(sma20.iloc[-2])
    curr_sma50, prev_sma50 = float(sma50.iloc[-1]), float(sma50.iloc[-2])
    curr_rsi = float(rsi.iloc[-1])

    if prev_sma20 <= prev_sma50 and curr_sma20 > curr_sma50 and (45 <= curr_rsi <= 68):
        return SignalOutput("BUY", f"Bullish SMA Crossover (RSI: {curr_rsi:.1f})")

    if prev_sma20 >= prev_sma50 and curr_sma20 < curr_sma50 and (curr_rsi < 55 or curr_rsi > 70):
        return SignalOutput("SELL", f"Bearish SMA Crossover (RSI: {curr_rsi:.1f})")

    return SignalOutput("HOLD", "No Crossover Signal")


def strategy_rsi_breakout(df: pd.DataFrame) -> SignalOutput:
    """Strategy 2: RSI Oversold (<35 BUY) / Overbought (>65 SELL)."""
    if df is None or len(df) < 14:
        return SignalOutput("HOLD", "Insufficient Data")

    rsi = df['RSI'] if 'RSI' in df.columns else pd.Series(50, index=df.index)
    curr_rsi = float(rsi.iloc[-1])

    if curr_rsi < 35:
        return SignalOutput("BUY", f"RSI Oversold Dip ({curr_rsi:.1f})")
    elif curr_rsi > 65:
        return SignalOutput("SELL", f"RSI Overbought High ({curr_rsi:.1f})")

    return SignalOutput("HOLD", f"RSI Neutral ({curr_rsi:.1f})")


STRATEGY_MAP = {
    "SMA_RSI": strategy_sma_rsi,
    "RSI_BREAKOUT": strategy_rsi_breakout,
}


def generate_signals(df: pd.DataFrame, strategy_name: str = "SMA_RSI") -> SignalOutput:
    """Main strategy dynamic router."""
    selected_func = STRATEGY_MAP.get(strategy_name.upper(), strategy_sma_rsi)
    return selected_func(df)
