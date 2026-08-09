import unittest
from unittest.mock import patch
from paper_trading import PaperTradingEngine

class TestPaperTradingRiskIntegration(unittest.TestCase):

    def setUp(self):
        self.limits = {
            "max_symbol_exposure_pct": 25.0,
            "max_portfolio_exposure_pct": 80.0,
            "max_daily_loss_pct": 5.0,
            "max_realized_drawdown_pct": 15.0
        }
        self.engine = PaperTradingEngine(initial_cash=10000.0, risk_limits=self.limits)

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_safe_buy_executes_successfully(self, mock_log):
        initial_cash = self.engine.cash
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 10.0) # $1000 = 10%
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "EXECUTED")
        self.assertEqual(self.engine.cash, initial_cash - 1000.0)
        self.assertIn("BTC/USDT", self.engine.positions)
        mock_log.assert_called_once()

    def test_concentration_blocked_buy_zero_mutation(self):
        initial_cash = self.engine.cash
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 35.0) # $3500 = 35% > 25%
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertEqual(self.engine.cash, initial_cash)
        self.assertNotIn("BTC/USDT", self.engine.positions)

    def test_exposure_blocked_buy_zero_mutation(self):
        self.engine.cash = 2000.0
        self.engine.positions = {"ETH/USDT": {"quantity": 70.0, "entry_price": 100.0, "total_cost": 7000.0}}
        current_prices = {"BTC/USDT": 100.0, "ETH/USDT": 100.0}
        
        initial_cash = self.engine.cash
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 15.0, current_prices=current_prices) # 7000+1500=8500/9000=94.4% > 80%
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertEqual(self.engine.cash, initial_cash)
        self.assertNotIn("BTC/USDT", self.engine.positions)

    @patch("paper_trading.load_paper_trade_records")
    def test_daily_loss_guard_blocks_new_buy(self, mock_load):
        # Mock closed trades with deterministic dates
        mock_load.return_value = [
            {"symbol": "SOL/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-09T00:00:00Z"},
            {"symbol": "SOL/USDT", "side": "SELL", "price": 40.0, "quantity": 10.0, "commission": 0.0, "net_pnl": -600.0, "timestamp": "2026-08-09T01:00:00Z"}
        ]
        with patch("paper_trading.datetime") as mock_dt:
            mock_dt.utcnow.return_value.strftime.return_value = "2026-08-09"
            res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 10.0)
            self.assertFalse(res["success"])
            self.assertEqual(res["status"], "BLOCKED")

    @patch("paper_trading.load_paper_trade_records")
    def test_realized_drawdown_guard_blocks_new_buy(self, mock_load):
        mock_load.return_value = [
            {"symbol": "ABC/USDT", "side": "BUY", "price": 100.0, "quantity": 50.0, "commission": 0.0, "net_pnl": 0.0, "timestamp": "2026-08-01T00:00:00Z"},
            {"symbol": "ABC/USDT", "side": "SELL", "price": 150.0, "quantity": 50.0, "commission": 0.0, "net_pnl": 2500.0, "timestamp": "2026-08-02T00:00:00Z"},
            {"symbol": "XYZ/USDT", "side": "BUY", "price": 100.0, "quantity": 50.0, "commission": 0.0, "pnl": 0.0, "timestamp": "2026-08-03T00:00:00Z"},
            {"symbol": "XYZ/USDT", "side": "SELL", "price": 40.0, "quantity": 50.0, "commission": 0.0, "net_pnl": -3000.0, "timestamp": "2026-08-04T00:00:00Z"}
        ]
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 10.0)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "BLOCKED")

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_valid_risk_reducing_sell_allowed(self, mock_log):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        res = self.engine.execute_order("BTC/USDT", "SELL", 100.0, 5.0)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "EXECUTED")
        self.assertEqual(self.engine.positions["BTC/USDT"]["quantity"], 5.0)

    def test_oversized_sell_rejected(self):
        self.engine.positions = {"BTC/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        res = self.engine.execute_order("BTC/USDT", "SELL", 100.0, 15.0)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "ERROR")

    def test_multi_position_buy_missing_prices_fails_closed(self):
        self.engine.positions = {"ETH/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 10.0)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "ERROR")
        self.assertIn("Missing valid mark price", res["reason"][0])

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_complete_current_prices_allows_multi_position_buy(self, mock_log):
        self.engine.positions = {"ETH/USDT": {"quantity": 10.0, "entry_price": 100.0, "total_cost": 1000.0}}
        current_prices = {"BTC/USDT": 100.0, "ETH/USDT": 100.0}
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 10.0, current_prices=current_prices)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "EXECUTED")

    def test_malformed_state_fails_safely(self):
        res = self.engine.execute_order("BTC/USDT", "BUY", -100.0, 10.0)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "ERROR")

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_no_logging_on_risk_rejection(self, mock_log):
        res = self.engine.execute_order("BTC/USDT", "BUY", 100.0, 35.0)
        self.assertFalse(res["success"])
        mock_log.assert_not_called()

    @patch("paper_trading.PaperTradingEngine._log_trade")
    def test_existing_execution_functional_when_allowed(self, mock_log):
        res = self.engine.execute_order("BTC/USDT", "BUY", 50.0, 5.0)
        self.assertTrue(res["success"])
        self.assertEqual(self.engine.cash, 9750.0)
        self.assertEqual(self.engine.positions["BTC/USDT"]["quantity"], 5.0)

def run_integration_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPaperTradingRiskIntegration)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    if not success:
        exit(1)