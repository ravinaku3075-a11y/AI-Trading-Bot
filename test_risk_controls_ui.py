import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from paper_trading import PaperTradingEngine
from risk_controls_ui import render_risk_controls_ui

class TestRiskControlsUI(unittest.TestCase):

    def setUp(self):
        self.limits = {
            "max_symbol_exposure_pct": 25.0,
            "max_portfolio_exposure_pct": 80.0,
            "max_daily_loss_pct": 5.0,
            "max_realized_drawdown_pct": 15.0
        }
        self.engine = PaperTradingEngine(initial_cash=10000.0, risk_limits=self.limits)

    def test_empty_portfolio_snapshot(self):
        snap = self.engine.get_portfolio_risk_snapshot()
        self.assertEqual(snap["status"], "SAFE")
        self.assertEqual(snap["total_portfolio_exposure_pct"], 0.0)
        self.assertEqual(snap["total_portfolio_equity"], 10000.0)

    def test_single_position_valid_mark_price(self):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        prices = {"BTC/USDT": 100.0}
        snap = self.engine.get_portfolio_risk_snapshot(current_prices=prices)
        self.assertEqual(snap["status"], "SAFE")
        self.assertEqual(snap["total_portfolio_equity"], 11000.0)
        self.assertAlmostEqual(snap["total_portfolio_exposure_pct"], 9.09, places=2)
        self.assertAlmostEqual(snap["per_symbol_exposure"]["BTC/USDT"], 9.09, places=2)

    def test_multi_position_complete_prices(self):
        self.engine.positions = {
            "BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0},
            "ETH/USDT": {"quantity": 20.0, "entry_price": 50.0, "total_cost": 1000.0}
        }
        prices = {"BTC/USDT": 100.0, "ETH/USDT": 50.0}
        snap = self.engine.get_portfolio_risk_snapshot(current_prices=prices)
        self.assertEqual(snap["status"], "SAFE")
        self.assertEqual(snap["total_portfolio_equity"], 12000.0)
        self.assertAlmostEqual(snap["total_portfolio_exposure_pct"], 16.67, places=2)

    def test_missing_price_returns_data_unavailable(self):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        snap = self.engine.get_portfolio_risk_snapshot(current_prices={})
        self.assertEqual(snap["status"], "DATA_UNAVAILABLE")
        self.assertIn("BTC/USDT", snap["missing_price_symbols"])
        self.assertIsNone(snap["total_portfolio_equity"])

    def test_invalid_price_returns_data_unavailable(self):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        prices = {"BTC/USDT": np.nan}
        snap = self.engine.get_portfolio_risk_snapshot(current_prices=prices)
        self.assertEqual(snap["status"], "DATA_UNAVAILABLE")

    @patch("paper_trading.load_paper_trade_records")
    def test_daily_loss_warning_threshold(self, mock_load):
        mock_load.return_value = [
            {"symbol": "SOL/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-09T00:00:00Z"},
            {"symbol": "SOL/USDT", "side": "SELL", "price": 58.0, "quantity": 10.0, "commission": 0.0, "pnl": -420.0, "net_pnl": -420.0, "timestamp": "2026-08-09T01:00:00Z"}
        ]
        with patch("paper_trading.datetime") as mock_dt:
            mock_dt.utcnow.return_value.strftime.return_value = "2026-08-09"
            snap = self.engine.get_portfolio_risk_snapshot()
            self.assertEqual(snap["status"], "WARNING")

    @patch("paper_trading.load_paper_trade_records")
    def test_daily_loss_limit_reached(self, mock_load):
        mock_load.return_value = [
            {"symbol": "SOL/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-09T00:00:00Z"},
            {"symbol": "SOL/USDT", "side": "SELL", "price": 45.0, "quantity": 10.0, "commission": 0.0, "pnl": -550.0, "net_pnl": -550.0, "timestamp": "2026-08-09T01:00:00Z"}
        ]
        with patch("paper_trading.datetime") as mock_dt:
            mock_dt.utcnow.return_value.strftime.return_value = "2026-08-09"
            snap = self.engine.get_portfolio_risk_snapshot()
            self.assertEqual(snap["status"], "LIMIT_REACHED")

    @patch("paper_trading.load_paper_trade_records")
    def test_drawdown_warning_threshold(self, mock_load):
        mock_load.return_value = [
            {"symbol": "A/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-01T00:00:00Z"},
            {"symbol": "A/USDT", "side": "SELL", "price": 200.0, "quantity": 10.0, "commission": 0.0, "pnl": 1000.0, "net_pnl": 1000.0, "timestamp": "2026-08-02T00:00:00Z"},
            {"symbol": "B/USDT", "side": "BUY", "price": 200.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-03T00:00:00Z"},
            {"symbol": "B/USDT", "side": "SELL", "price": 65.0, "quantity": 10.0, "commission": 0.0, "pnl": -1350.0, "net_pnl": -1350.0, "timestamp": "2026-08-04T00:00:00Z"}
        ]
        with patch("paper_trading.analyze_paper_trades") as mock_analytics:
            mock_analytics.return_value = {
                "success": True,
                "closed_trades": mock_load.return_value,
                "metrics": {"max_drawdown_pct": 12.5}
            }
            snap = self.engine.get_portfolio_risk_snapshot()
            self.assertEqual(snap["status"], "WARNING")

    @patch("paper_trading.load_paper_trade_records")
    def test_drawdown_limit_reached(self, mock_load):
        mock_load.return_value = [
            {"symbol": "A/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-01T00:00:00Z"},
            {"symbol": "A/USDT", "side": "SELL", "price": 200.0, "quantity": 10.0, "commission": 0.0, "pnl": 1000.0, "net_pnl": 1000.0, "timestamp": "2026-08-02T00:00:00Z"},
            {"symbol": "B/USDT", "side": "BUY", "price": 200.0, "quantity": 10.0, "commission": 0.0, "pnl": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-03T00:00:00Z"},
            {"symbol": "B/USDT", "side": "SELL", "price": 0.0, "quantity": 10.0, "commission": 0.0, "pnl": -2000.0, "net_pnl": -2000.0, "timestamp": "2026-08-04T00:00:00Z"}
        ]
        with patch("paper_trading.analyze_paper_trades") as mock_analytics:
            mock_analytics.return_value = {
                "success": True,
                "closed_trades": mock_load.return_value,
                "metrics": {"max_drawdown_pct": 18.0}
            }
            snap = self.engine.get_portfolio_risk_snapshot()
            self.assertEqual(snap["status"], "LIMIT_REACHED")

    def test_snapshot_zero_cash_mutation(self):
        cash_before = self.engine.cash
        self.engine.get_portfolio_risk_snapshot()
        self.assertEqual(self.engine.cash, cash_before)

    def test_snapshot_zero_position_mutation(self):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        pos_before = dict(self.engine.positions)
        self.engine.get_portfolio_risk_snapshot(current_prices={"BTC/USDT": 100.0})
        self.assertEqual(self.engine.positions, pos_before)

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_snapshot_zero_sqlite_csv_writes(self, mock_log):
        self.engine.get_portfolio_risk_snapshot()
        mock_log.assert_not_called()

    def test_backtest_isolation(self):
        snap = self.engine.get_portfolio_risk_snapshot()
        self.assertNotIn("backtest", snap)

    def test_broker_network_isolation(self):
        snap = self.engine.get_portfolio_risk_snapshot()
        self.assertIn("status", snap)

    @patch("streamlit.error")
    def test_ui_none_engine_renders_safely(self, mock_err):
        render_risk_controls_ui(None)
        mock_err.assert_called_once_with("PaperTradingEngine instance is unavailable.")

    @patch("streamlit.markdown")
    def test_ui_renders_valid_snapshot_safely(self, mock_md):
        render_risk_controls_ui(self.engine)
        self.assertTrue(mock_md.called)

def run_risk_controls_ui_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRiskControlsUI)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_risk_controls_ui_tests()
    if not success:
        exit(1)