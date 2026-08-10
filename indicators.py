"""
Technical Indicators Module for AI Trading Bot.

Provides mathematical algorithms to compute technical indicators such as
Relative Strength Index (RSI), Simple Moving Average (SMA),
Exponential Moving Average (EMA), and Average True Range (ATR).
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _get_column_name(df: pd.DataFrame, target: str) -> str | tuple | None:
    """Safely find column name whether it's a string or tuple from MultiIndex."""
    target_lower = target.lower()
    for col in df.columns:
        if isinstance(col, tuple):
            if str(col[0]).lower() == target_lower:
                return col
        elif str(col).lower() == target_lower:
            return col
    return None


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate Relative Strength Index (RSI)."""
    if df is None or df.empty:
        return df

    close_col = _get_column_name(df, "close")
    if close_col is None:
        logger.warning("Missing close price column for RSI calculation.")
        return df

    delta = df[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_series = rsi_series.fillna(50.0)

    df["RSI"] = rsi_series
    df["rsi"] = rsi_series
    return df


def calculate_sma(df: pd.DataFrame, period: int = 20, column_name: str = "SMA") -> pd.DataFrame:
    """Calculate Simple Moving Average (SMA)."""
    if df is None or df.empty:
        return df

    close_col = _get_column_name(df, "close")
    if close_col is None:
        logger.warning("Missing close price column for SMA calculation.")
        return df

    df[column_name] = df[close_col].rolling(window=period).mean()
    return df


def calculate_ema(df: pd.DataFrame, period: int = 20, column_name: str = "EMA") -> pd.DataFrame:
    """Calculate Exponential Moving Average (EMA)."""
    if df is None or df.empty:
        return df

    close_col = _get_column_name(df, "close")
    if close_col is None:
        logger.warning("Missing close price column for EMA calculation.")
        return df

    df[column_name] = df[close_col].ewm(span=period, adjust=False).mean()
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate Average True Range (ATR)."""
    if df is None or df.empty:
        return df

    high_col = _get_column_name(df, "high")
    low_col = _get_column_name(df, "low")
    close_col = _get_column_name(df, "close")

    if not (high_col and low_col and close_col):
        logger.warning("Missing required OHLC columns for ATR calculation.")
        return df

    high = df[high_col]
    low = df[low_col]
    close = df[close_col].shift(1)

    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low - close).abs()
    ], axis=1).max(axis=1)

    atr_series = tr.rolling(window=period).mean()
    df["ATR"] = atr_series
    df["atr"] = atr_series
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper function to compute all technical indicators required by the strategy.
    """
    if df is None or df.empty:
        return df

    df = calculate_rsi(df)
    df = calculate_sma(df, period=20, column_name="SMA_20")
    df = calculate_sma(df, period=50, column_name="SMA_50")
    df = calculate_ema(df, period=200, column_name="EMA_200")
    df = calculate_atr(df)

    # Legacy aliases for lower-case compatibility
    if "SMA_20" in df.columns:
        df["sma_20"] = df["SMA_20"]
    if "SMA_50" in df.columns:
        df["sma_50"] = df["SMA_50"]
    if "EMA_200" in df.columns:
        df["ema_200"] = df["EMA_200"]

    return df
