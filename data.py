"""
Data Engine Module for AI Trading Bot.

Handles fetching historical market data via yfinance with robust fallback logic
and network exception handling.
"""

import logging
from typing import Optional
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> Optional[pd.DataFrame]:
    """
    Fetches OHLCV historical price data for a given ticker from Yahoo Finance.

    Args:
        ticker: Ticker symbol (e.g., 'AAPL').
        period: Data period (e.g., '1y', '6m', '60d').
        interval: Data interval (e.g., '1d', '1h').

    Returns:
        pd.DataFrame or None if fetch fails.
    """
    if not ticker or not isinstance(ticker, str):
        logger.error("Invalid ticker string provided.")
        return None

    cleaned_ticker = ticker.strip().upper()

    try:
        # Download historical data with progress disabled
        df = yf.download(
            tickers=cleaned_ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )

        if df is None or df.empty:
            logger.warning(f"No data returned for ticker '{cleaned_ticker}'.")
            return None

        # Clean MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        # Standardize column names to lowercase
        df.columns = [str(col).lower() for col in df.columns]

        # Validate required columns
        required_cols = {"open", "high", "low", "close", "volume"}
        if not required_cols.issubset(set(df.columns)):
            logger.error(f"Missing required columns in fetched data for {cleaned_ticker}.")
            return None

        # Drop NaN values and ensure numeric types
        df = df.dropna().astype(float)

        if len(df) < 20:
            logger.warning(f"Insufficient historical data rows ({len(df)}) for {cleaned_ticker}.")
            return None

        return df

    except Exception as exc:
        logger.error(f"Error fetching data for ticker '{cleaned_ticker}': {exc}")
        return None
