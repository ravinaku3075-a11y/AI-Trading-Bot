import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

class TestBacktestUI(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range("2026-01-01", periods=25, freq="D")
        self.valid_df = pd.DataFrame({
            "Datetime": dates,
            "Open": [100.0 + i for i in range(25)],
            "High": [102.0 + i for i in range(25)],
            "Low": [98.0 + i for i in range(25)],
            "Close": [101.0 + i for i in range(25)],
            "Volume": [1000] * 25
        })

    @patch("backtest_ui.st")
    def test_missing_file_handling(self, mock_st):
        from backtest_ui import render_backtest_ui
        mock_st.button.return_value = False
        mock_st.file_uploader.return_value = None
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        
        render_backtest_ui()
        mock_st.info.assert_called_with("Please upload a historical OHLCV CSV file and click 'Run Historical Backtest' to begin.")

    @patch("backtest_ui.st")
    def test_missing_file_on_run_click(self, mock_st):
        from backtest_ui import render_backtest_ui
        mock_st.button.return_value = True
        mock_st.file_uploader.return_value = None
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        
        render_backtest_ui()
        mock_st.error.assert_called_with("No CSV file uploaded. Please upload a valid historical dataset.")

    @patch("backtest_ui.st")
    @patch("backtest_ui.load_historical_csv")
    def test_invalid_csv_handling(self, mock_loader, mock_st):
        from backtest_ui import render_backtest_ui
        mock_st.button.return_value = True
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"invalid,csv"
        mock_st.file_uploader.return_value = mock_file
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        
        mock_loader.return_value = {"success": False, "error": "Missing required columns"}
        
        render_backtest_ui()
        mock_st.error.assert_called_with("Data Validation Failed: Missing required columns")

    @patch("backtest_ui.st")
    @patch("backtest_ui.load_historical_csv")
    @patch("backtest_ui.run_backtest")
    def test_zero_trades_display(self, mock_bt, mock_loader, mock_st):
        from backtest_ui import render_backtest_ui
        mock_st.button.return_value = True
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"header"
        mock_st.file_uploader.return_value = mock_file
        
        # Safely mock st.columns to handle integer or list inputs
        def cols_mock_side_effect(spec):
            count = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(count)]
            
        mock_st.columns.side_effect = cols_mock_side_effect

        df_mock = pd.DataFrame({
            "Open": [100]*25, "High": [105]*25, "Low": [95]*25, "Close": [100]*25, "Volume": [1000]*25
        }, index=pd.date_range("2026-01-01", periods=25))

        mock_loader.return_value = {"success": True, "data": df_mock}
        mock_bt.return_value = {
            "success": True,
            "total_return_pct": 0.0,
            "net_profit": 0.0,
            "total_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "open_position": False,
            "equity_curve": [10000.0]*25,
            "trades": []
        }

        render_backtest_ui()
        mock_st.info.assert_called_with("No trades were triggered during this backtest simulation under the selected strategy rules and parameters.")

    @patch("sqlite3.connect")
    @patch("urllib.request.urlopen")
    def test_paper_only_isolation(self, mock_urlopen, mock_db):
        df_mock = pd.DataFrame({
            "Open": [100]*25, "High": [105]*25, "Low": [95]*25, "Close": [100]*25, "Volume": [1000]*25
        }, index=pd.date_range("2026-01-01", periods=25))

        from backtest_engine import run_backtest
        res = run_backtest(df_mock, warmup_bars=10)
        
        self.assertTrue(res["success"])
        mock_urlopen.assert_not_called()
        mock_db.assert_not_called()

def run_ui_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBacktestUI)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_ui_tests()
    if not success:
        exit(1)