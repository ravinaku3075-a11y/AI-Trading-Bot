import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]

def load_historical_csv(file_path: str, min_rows: int = 5) -> dict:
    """
    Loads historical OHLCV market data from a CSV file, performs strict validation,
    normalizes timezones to UTC-naive, sorts chronologically, and cleans up NaNs/duplicates.
    
    Returns:
        dict: {
            "success": bool,
            "data": pd.DataFrame or None,
            "error": str or None,
            "rows_loaded": int
        }
    """
    # 1. Check File Existence
    if not os.path.exists(file_path):
        return {"success": False, "data": None, "error": f"File not found: {file_path}", "rows_loaded": 0}

    # 2. Check File Size / Empty File
    if os.path.getsize(file_path) == 0:
        return {"success": False, "data": None, "error": "CSV file is empty", "rows_loaded": 0}

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return {"success": False, "data": None, "error": f"Failed to parse CSV: {str(e)}", "rows_loaded": 0}

    if df.empty:
        return {"success": False, "data": None, "error": "CSV file contains no data rows", "rows_loaded": 0}

    # 3. Identify Date/Datetime Column
    date_col = None
    for col in df.columns:
        if col.strip().lower() in ["date", "datetime", "timestamp", "time"]:
            date_col = col
            break

    if not date_col:
        return {"success": False, "data": None, "error": "Missing required Date/Datetime column", "rows_loaded": 0}

    # 4. Check OHLCV Required Columns
    # Standardize column name case mapping
    col_mapping = {}
    for col in df.columns:
        c_lower = col.strip().lower()
        if c_lower in ["open", "high", "low", "close", "volume"]:
            col_mapping[col] = c_lower.capitalize()

    df.rename(columns=col_mapping, inplace=True)

    missing_cols = [req for req in REQUIRED_COLUMNS if req not in df.columns]
    if missing_cols:
        return {"success": False, "data": None, "error": f"Missing required OHLCV columns: {missing_cols}", "rows_loaded": 0}

    # 5. Parse Datetime & Normalize Timezone
    try:
        df["Datetime"] = pd.to_datetime(df[date_col], errors="coerce")
    except Exception as e:
        return {"success": False, "data": None, "error": f"Invalid date format: {str(e)}", "rows_loaded": 0}

    # Drop rows with invalid dates
    df = df.dropna(subset=["Datetime"]).copy()
    if df.empty:
        return {"success": False, "data": None, "error": "No valid datetime rows found", "rows_loaded": 0}

    # Timezone normalization: convert to tz-naive UTC
    if df["Datetime"].dt.tz is not None:
        df["Datetime"] = df["Datetime"].dt.tz_convert("UTC").dt.tz_localize(None)

    df.set_index("Datetime", inplace=True)

    # 6. Validate Numeric Types for OHLCV
    for col in REQUIRED_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop NaNs in OHLCV
    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    if df.empty:
        return {"success": False, "data": None, "error": "All OHLCV rows contain invalid/non-numeric values or NaNs", "rows_loaded": 0}

    # 7. Remove Duplicate Timestamps (Keep Last)
    df = df[~df.index.duplicated(keep="last")].copy()

    # 8. Sort Chronologically
    df.sort_index(inplace=True)

    # Select only standard columns
    df = df[REQUIRED_COLUMNS]

    # 9. Verify Minimum Row Count
    if len(df) < min_rows:
        return {
            "success": False,
            "data": None,
            "error": f"Insufficient data rows ({len(df)} valid bars). Required minimum: {min_rows}",
            "rows_loaded": len(df)
        }

    return {
        "success": True,
        "data": df,
        "error": None,
        "rows_loaded": len(df)
    }