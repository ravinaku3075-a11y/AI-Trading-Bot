import os
import tempfile
import pandas as pd
from historical_data_loader import load_historical_csv

def run_historical_data_tests():
    print("--- RUNNING HISTORICAL DATA LOADER TESTS ---")

    # 1. Valid CSV Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-01,100,105,95,102,1000\n")
        tmp.write("2026-01-02,102,108,101,107,1200\n")
        tmp.write("2026-01-03,107,110,104,105,1100\n")
        tmp.write("2026-01-04,105,106,100,101,900\n")
        tmp.write("2026-01-05,101,103,99,102,950\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path, min_rows=5)
    os.remove(tmp_path)
    assert res["success"] is True
    assert res["rows_loaded"] == 5
    assert isinstance(res["data"].index, pd.DatetimeIndex)
    print("1. Valid CSV Test: PASSED")

    # 2. Missing File Test
    res = load_historical_csv("non_existent_file.csv")
    assert res["success"] is False
    assert "File not found" in res["error"]
    print("2. Missing File Test: PASSED")

    # 3. Empty CSV Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path)
    os.remove(tmp_path)
    assert res["success"] is False
    assert "empty" in res["error"].lower()
    print("3. Empty CSV Test: PASSED")

    # 4. Schema Validation Test (Missing Column)
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close\n")  # Volume missing
        tmp.write("2026-01-01,100,105,95,102\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path)
    os.remove(tmp_path)
    assert res["success"] is False
    assert "Missing required OHLCV columns" in res["error"]
    print("4. Schema Validation Test: PASSED")

    # 5. Invalid Date Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("invalid_date,100,105,95,102,1000\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path)
    os.remove(tmp_path)
    assert res["success"] is False
    assert "No valid datetime rows found" in res["error"]
    print("5. Invalid Date Test: PASSED")

    # 6. NaN / Non-Numeric Validation Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-01,100,abc,95,102,1000\n")  # Non-numeric High
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path)
    os.remove(tmp_path)
    assert res["success"] is False
    print("6. NaN/Non-Numeric Validation Test: PASSED")

    # 7. Duplicate Timestamp Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-01,100,105,95,102,1000\n")
        tmp.write("2026-01-01,100,105,95,103,1000\n")  # Duplicate date
        tmp.write("2026-01-02,102,108,101,107,1200\n")
        tmp.write("2026-01-03,107,110,104,105,1100\n")
        tmp.write("2026-01-04,105,106,100,101,900\n")
        tmp.write("2026-01-05,101,103,99,102,950\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path, min_rows=5)
    os.remove(tmp_path)
    assert res["success"] is True
    assert res["rows_loaded"] == 5
    assert res["data"].loc["2026-01-01"]["Close"] == 103  # Kept last duplicate
    print("7. Duplicate Timestamp Test: PASSED")

    # 8. Chronological Sorting Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-05,101,103,99,102,950\n")  # Unsorted order
        tmp.write("2026-01-01,100,105,95,102,1000\n")
        tmp.write("2026-01-02,102,108,101,107,1200\n")
        tmp.write("2026-01-03,107,110,104,105,1100\n")
        tmp.write("2026-01-04,105,106,100,101,900\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path, min_rows=5)
    os.remove(tmp_path)
    assert res["success"] is True
    assert list(res["data"].index.strftime("%Y-%m-%d")) == [
        "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"
    ]
    print("8. Chronological Sorting Test: PASSED")

    # 9. Insufficient Data Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-01,100,105,95,102,1000\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path, min_rows=5)
    os.remove(tmp_path)
    assert res["success"] is False
    assert "Insufficient data rows" in res["error"]
    print("9. Insufficient Data Test: PASSED")

    # 10. Timezone Normalization Test
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        tmp.write("Date,Open,High,Low,Close,Volume\n")
        tmp.write("2026-01-01T00:00:00+05:30,100,105,95,102,1000\n")
        tmp.write("2026-01-02T00:00:00+05:30,102,108,101,107,1200\n")
        tmp.write("2026-01-03T00:00:00+05:30,107,110,104,105,1100\n")
        tmp.write("2026-01-04T00:00:00+05:30,105,106,100,101,900\n")
        tmp.write("2026-01-05T00:00:00+05:30,101,103,99,102,950\n")
        tmp_path = tmp.name

    res = load_historical_csv(tmp_path, min_rows=5)
    os.remove(tmp_path)
    assert res["success"] is True
    assert res["data"].index.tz is None  # Timezone stripped/normalized to tz-naive
    print("10. Timezone Normalization Test: PASSED")

    print("ALL HISTORICAL DATA TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_historical_data_tests()