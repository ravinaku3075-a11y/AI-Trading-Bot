import unittest
from portfolio_risk_manager import validate_portfolio_risk

class TestPortfolioRiskManager(unittest.TestCase):

    def setUp(self):
        self.valid_request = {
            "symbol": "BTC/USDT",
            "side": "BUY",
            "price": 100.0,
            "quantity": 10.0
        }
        self.valid_state = {
            "available_cash": 10000.0,
            "open_positions": {},
            "daily_realized_pnl": 0.0,
            "realized_drawdown_pct": 0.0,
            "current_prices": {"BTC/USDT": 100.0}
        }
        self.limits = {
            "max_symbol_exposure_pct": 25.0,
            "max_portfolio_exposure_pct": 80.0,
            "max_daily_loss_pct": 5.0,
            "max_realized_drawdown_pct": 15.0
        }

    def test_safe_buy_order_passes(self):
        res = validate_portfolio_risk(self.valid_request, self.valid_state, self.limits)
        self.assertTrue(res["allowed"])
        self.assertEqual(res["status"], "SAFE")

    def test_missing_mark_price_blocks_buy(self):
        state = dict(self.valid_state)
        state["current_prices"] = {}  # Missing BTC/USDT price
        res = validate_portfolio_risk(self.valid_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "ERROR")
        self.assertIn("Missing current mark price", res["reasons"][0])

    def test_symbol_concentration_limit_blocks_buy(self):
        request = dict(self.valid_request)
        request["quantity"] = 35.0  # Order value 3500 on 10000 equity = 35% > 25% limit
        res = validate_portfolio_risk(request, self.valid_state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Proposed symbol exposure", res["reasons"][0])

    def test_portfolio_exposure_limit_blocks_buy(self):
        state = dict(self.valid_state)
        state["available_cash"] = 2000.0
        state["open_positions"] = {"ETH/USDT": {"quantity": 70.0}}
        state["current_prices"] = {"BTC/USDT": 100.0, "ETH/USDT": 100.0}
        
        request = dict(self.valid_request)
        request["quantity"] = 15.0  # Total exposure 7000 + 1500 = 8500 / 9000 = 94.4% > 80%
        res = validate_portfolio_risk(request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Proposed portfolio exposure", res["reasons"][0])

    def test_daily_loss_limit_blocks_buy(self):
        state = dict(self.valid_state)
        state["daily_realized_pnl"] = -600.0  # -600 on 10000 equity = -6% > -5% limit
        res = validate_portfolio_risk(self.valid_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Daily realized loss", res["reasons"][0])

    def test_realized_drawdown_guard_blocks_buy(self):
        state = dict(self.valid_state)
        state["realized_drawdown_pct"] = 18.0  # 18% > 15% limit
        res = validate_portfolio_risk(self.valid_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Realized drawdown guard limit", res["reasons"][0])

    def test_risk_reducing_sell_allowed(self):
        state = dict(self.valid_state)
        state["open_positions"] = {"BTC/USDT": {"quantity": 10.0}}
        sell_request = {"symbol": "BTC/USDT", "side": "SELL", "price": 100.0, "quantity": 5.0}
        res = validate_portfolio_risk(sell_request, state, self.limits)
        self.assertTrue(res["allowed"])
        self.assertEqual(res["status"], "SAFE")

    def test_oversized_sell_blocked(self):
        state = dict(self.valid_state)
        state["open_positions"] = {"BTC/USDT": {"quantity": 10.0}}
        sell_request = {"symbol": "BTC/USDT", "side": "SELL", "price": 100.0, "quantity": 15.0}
        res = validate_portfolio_risk(sell_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "ERROR")
        self.assertIn("Cannot SELL quantity", res["reasons"][0])

    def test_insufficient_cash_blocks_buy(self):
        state = dict(self.valid_state)
        state["available_cash"] = 500.0
        res = validate_portfolio_risk(self.valid_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "BLOCKED")
        self.assertIn("Insufficient available cash", res["reasons"][0])

    def test_invalid_order_fields_fails_safely(self):
        bad_request = {"symbol": "BTC/USDT", "side": "BUY", "price": -10.0, "quantity": 10.0}
        res = validate_portfolio_risk(bad_request, self.valid_state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "ERROR")

    def test_zero_or_negative_equity_fails_safely(self):
        state = dict(self.valid_state)
        state["available_cash"] = 0.0
        res = validate_portfolio_risk(self.valid_request, state, self.limits)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["status"], "ERROR")

    def test_no_side_effects_or_broker_calls(self):
        # Pure function check: Ensure state passed in is unchanged after validation
        state_copy = dict(self.valid_state)
        validate_portfolio_risk(self.valid_request, self.valid_state, self.limits)
        self.assertEqual(self.valid_state, state_copy)

def run_risk_manager_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPortfolioRiskManager)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_risk_manager_tests()
    if not success:
        exit(1)
        