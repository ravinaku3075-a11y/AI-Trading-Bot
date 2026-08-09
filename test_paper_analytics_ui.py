import unittest
from unittest.mock import patch, MagicMock
from paper_analytics_ui import render_paper_analytics_ui, load_paper_trade_records

class TestPaperAnalyticsUI(unittest.TestCase):

    @patch("paper_analytics_ui.st")
    @patch("paper_analytics_ui.load_paper_trade_records")
    def test_empty_trade_history_rendering(self, mock_load, mock_st):
        mock_load.return_value = []
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
        
        render_paper_analytics_ui()
        mock_st.info.assert_any_call("No closed paper trades recorded yet.")

    @patch("paper_analytics_ui.st")
    @patch("paper_analytics_ui.load_paper_trade_records")
    def test_valid_analytics_rendering(self, mock_load, mock_st):
        mock_load.return_value = [
            {"symbol": "BTC/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 1.0},
            {"symbol": "BTC/USDT", "side": "SELL", "price": 120.0, "quantity": 10.0, "commission": 1.0}
        ]
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
        
        render_paper_analytics_ui()
        mock_st.header.assert_called_with("📊 Paper Trading Analytics")

    @patch("os.path.exists")
    @patch("pandas.read_sql_query")
    @patch("pandas.read_csv")
    @patch("sqlite3.connect")
    def test_sqlite_primary_csv_fallback(self, mock_connect, mock_csv, mock_sql, mock_exists):
        # Scenario 1: SQLite fails -> CSV fallback
        mock_exists.side_effect = lambda p: True
        mock_sql.side_effect = Exception("DB Lock")
        mock_df_csv = MagicMock()
        mock_df_csv.empty = False
        mock_df_csv.to_dict.return_value = [{"symbol": "CSV_DATA"}]
        mock_csv.return_value = mock_df_csv

        records = load_paper_trade_records()
        self.assertEqual(records, [{"symbol": "CSV_DATA"}])

    @patch("paper_analytics_ui.st")
    @patch("paper_analytics_ui.analyze_paper_trades")
    def test_analytics_error_handling(self, mock_analyze, mock_st):
        mock_analyze.return_value = {"success": False, "error": "Corrupt state"}
        render_paper_analytics_ui()
        mock_st.error.assert_called_with("Failed to calculate analytics: Corrupt state")

    @patch("sqlite3.connect")
    @patch("urllib.request.urlopen")
    def test_paper_backtest_broker_isolation(self, mock_urlopen, mock_db):
        from paper_analytics import analyze_paper_trades
        res = analyze_paper_trades([])
        self.assertTrue(res["success"])
        mock_urlopen.assert_not_called()
        mock_db.assert_not_called()

def run_ui_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPaperAnalyticsUI)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_ui_tests()
    if not success:
        exit(1)