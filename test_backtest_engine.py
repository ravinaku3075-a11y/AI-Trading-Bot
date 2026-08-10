import pandas as pd
import numpy as np
from backtest_engine import run_backtest

def create_synthetic_data(num_bars=30):
    dates = pd.date_range("2026-01-01", periods=num_bars, freq="D")
    prices = [100.0 + i for i in range(num_bars)]
    df = pd.DataFrame({
        "Open": prices,
        "High": [p + 2 for p in prices],
        "Low": [p - 2 for p in prices],
        "Close": [p + 1 for p in prices],
        "Volume": [1000] * num_bars
    }, index=dates)
    return df

def run_backtest_engine_tests():
    print("--- RUNNING BACKTEST ENGINE TESTS ---")

    # A. Warm-up Test
    df = create_synthetic_data(25)
    called_indices = []
    def mock_strat_warmup(data_slice):
        called_indices.append(len(data_slice))
        return "BUY"

    res = run_backtest(df, strategy_fn=mock_strat_warmup, warmup_bars=20)
    assert res["success"] is True
    assert min(called_indices) >= 20
    print("A. Warm-up Test: PASSED")

    # B. Lookahead Isolation Test
    df_short = create_synthetic_data(22)
    df_long = create_synthetic_data(35)
    
    signals_short = []
    signals_long = []

    def mock_strat_short(slice_data):
        sig = "BUY" if len(slice_data) == 21 else "HOLD"
        signals_short.append((len(slice_data), sig))
        return sig

    def mock_strat_long(slice_data):
        sig = "BUY" if len(slice_data) == 21 else "HOLD"
        signals_long.append((len(slice_data), sig))
        return sig

    run_backtest(df_short, strategy_fn=mock_strat_short, warmup_bars=20)
    run_backtest(df_long, strategy_fn=mock_strat_long, warmup_bars=20)

    assert signals_short[0] == signals_long[0]
    print("B. Lookahead Isolation Test: PASSED")

    # C. Next-Bar Open Execution Test
    df = create_synthetic_data(25)
    def mock_strat_next_bar(slice_data):
        if len(slice_data) == 20:
            return "BUY"
        if len(slice_data) == 22:
            return "SELL"
        return "HOLD"

    res = run_backtest(df, strategy_fn=mock_strat_next_bar, warmup_bars=20, commission_pct=0.0, slippage_pct=0.0)
    assert res["success"] is True
    assert res["total_trades"] == 1
    assert res["trades"][0]["entry_price"] == df["Open"].iloc[20]
    assert res["trades"][0]["exit_price"] == df["Open"].iloc[22]
    print("C. Next-Bar Open Execution Test: PASSED")

    # D. Fee and Slippage Math Test
    res_no_fee = run_backtest(df, strategy_fn=mock_strat_next_bar, warmup_bars=20, commission_pct=0.0, slippage_pct=0.0)
    res_fee = run_backtest(df, strategy_fn=mock_strat_next_bar, warmup_bars=20, commission_pct=0.01, slippage_pct=0.01)
    
    assert res_fee["trades"][0]["entry_price"] > res_no_fee["trades"][0]["entry_price"]
    assert res_fee["trades"][0]["exit_price"] < res_no_fee["trades"][0]["exit_price"]
    assert res_fee["net_profit"] < res_no_fee["net_profit"]
    print("D. Fee and Slippage Math Test: PASSED")

    # E. No Duplicate Position Test
    def mock_strat_dup(slice_data):
        return "BUY"

    res = run_backtest(df, strategy_fn=mock_strat_dup, warmup_bars=20)
    assert res["success"] is True
    assert res["total_trades"] == 0
    assert res["open_position"] is True
    print("E. No Duplicate Position Test: PASSED")

    # F. Drawdown Test
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    df_dd = pd.DataFrame({
        "Open": [100, 100, 100, 100, 100],
        "High": [105, 105, 105, 105, 105],
        "Low": [95, 95, 95, 95, 95],
        "Close": [100, 120, 90, 80, 110],
        "Volume": [1000] * 5
    }, index=dates)

    def mock_strat_dd(slice_data):
        if len(slice_data) == 1:
            return "BUY"
        return "HOLD"

    res = run_backtest(df_dd, strategy_fn=mock_strat_dd, warmup_bars=1, commission_pct=0.0, slippage_pct=0.0)
    assert res["success"] is True
    assert round(res["max_drawdown_pct"], 1) == 33.3
    print("F. Drawdown Test: PASSED")

    # G. Multi-Trade Metrics Test
    df_multi = create_synthetic_data(35)
    def mock_strat_multi(slice_data):
        idx = len(slice_data)
        if idx in [20, 26]:
            return "BUY"
        if idx in [23, 29]:
            return "SELL"
        return "HOLD"

    res = run_backtest(df_multi, strategy_fn=mock_strat_multi, warmup_bars=20, commission_pct=0.0, slippage_pct=0.0)
    assert res["success"] is True
    assert res["total_trades"] == 2
    assert res["winning_trades"] == 2
    assert res["win_rate_pct"] == 100.0
    print("G. Multi-Trade Metrics Test: PASSED")

    # H. Final Open Position Test
    df_open = create_synthetic_data(25)
    def mock_strat_open(slice_data):
        if len(slice_data) == 20:
            return "BUY"
        return "HOLD"

    res = run_backtest(df_open, strategy_fn=mock_strat_open, warmup_bars=20)
    assert res["success"] is True
    assert res["open_position"] is True or res["total_trades"] == 0
    print("H. Final Open Position Test: PASSED")

    # I. No-Trade Case Test
    def mock_strat_none(slice_data):
        return "HOLD"

    res = run_backtest(df, strategy_fn=mock_strat_none, warmup_bars=20)
    assert res["success"] is True
    assert res["total_trades"] == 0
    assert res["net_profit"] == 0.0
    assert res["profit_factor"] == 0.0
    print("I. No-Trade Case Test: PASSED")

    # J. Invalid Input Test
    res_empty = run_backtest(None)
    assert res_empty["success"] is False
    assert "empty or invalid" in res_empty["error"]

    res_short = run_backtest(create_synthetic_data(5), warmup_bars=20)
    assert res_short["success"] is False
    assert "Insufficient historical bars" in res_short["error"]
    print("J. Invalid Input Test: PASSED")

    print("ALL BACKTEST ENGINE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_backtest_engine_tests()