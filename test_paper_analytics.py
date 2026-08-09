import unittest
import pandas as pd
from paper_analytics import analyze_paper_trades

class TestPaperAnalytics(unittest.TestCase):

    def test_empty_trade_history(self):
        res = analyze_paper_trades([])
        self.assertTrue(res["success"])
        self.assertEqual(res["metrics"]["total_closed_trades"], 0)
        self.assertEqual(res["metrics"]["total_realized_pnl"], 0.0)
        self.assertEqual(res["equity_curve"], [10000.0])

    def test_single_profitable_round_trip(self):
        trades = [
            {"symbol": "BTC/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 1.0},
            {"symbol": "BTC/USDT", "side": "SELL", "price": 120.0, "quantity": 10.0, "commission": 1.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        self.assertEqual(res["metrics"]["total_closed_trades"], 1)
        # Gross = (120-100)*10 = 200, Commissions = 2.0 -> Net PnL = 198.0
        self.assertEqual(res["metrics"]["total_realized_pnl"], 198.0)
        self.assertEqual(res["metrics"]["winning_trades"], 1)
        self.assertEqual(res["metrics"]["win_rate_pct"], 100.0)

    def test_single_losing_round_trip(self):
        trades = [
            {"symbol": "BTC/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 1.0},
            {"symbol": "BTC/USDT", "side": "SELL", "price": 80.0, "quantity": 10.0, "commission": 1.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        self.assertEqual(res["metrics"]["total_closed_trades"], 1)
        # Gross = (80-100)*10 = -200, Commissions = 2.0 -> Net PnL = -202.0
        self.assertEqual(res["metrics"]["total_realized_pnl"], -202.0)
        self.assertEqual(res["metrics"]["losing_trades"], 1)
        self.assertEqual(res["metrics"]["win_rate_pct"], 0.0)

    def test_multiple_buy_entries_weighted_average(self):
        trades = [
            {"symbol": "BTC/USDT", "side": "BUY", "price": 100.0, "quantity": 10.0, "commission": 0.0},
            {"symbol": "BTC/USDT", "side": "BUY", "price": 200.0, "quantity": 10.0, "commission": 0.0},
            {"symbol": "BTC/USDT", "side": "SELL", "price": 180.0, "quantity": 20.0, "commission": 0.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        # Avg entry = (1000 + 2000)/20 = 150. Gross PnL = (180 - 150)*20 = 600.
        self.assertEqual(res["metrics"]["total_realized_pnl"], 600.0)

    def test_partial_sell_exit(self):
        trades = [
            {"symbol": "BTC/USDT", "side": "BUY", "price": 100.0, "quantity": 20.0, "commission": 2.0},
            {"symbol": "BTC/USDT", "side": "SELL", "price": 110.0, "quantity": 10.0, "commission": 1.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["open_positions"]), 1)
        self.assertEqual(res["open_positions"][0]["quantity"], 10.0)
        # Closed 10 units: Gross PnL = (110 - 100)*10 = 100. Entry comm = 1.0, Exit comm = 1.0. Net = 98.0
        self.assertEqual(res["metrics"]["total_realized_pnl"], 98.0)

    def test_commission_deduction_integrity(self):
        trades = [
            {"symbol": "ETH/USDT", "side": "BUY", "price": 1000.0, "quantity": 1.0, "commission": 5.0},
            {"symbol": "ETH/USDT", "side": "SELL", "price": 1000.0, "quantity": 1.0, "commission": 5.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertEqual(res["metrics"]["total_realized_pnl"], -10.0)

    def test_win_loss_breakeven_counts(self):
        trades = [
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 20.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 5.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 10.0, "quantity": 1.0, "commission": 0.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertEqual(res["metrics"]["winning_trades"], 1)
        self.assertEqual(res["metrics"]["losing_trades"], 1)
        self.assertEqual(res["metrics"]["breakeven_trades"], 1)
        self.assertAlmostEqual(res["metrics"]["win_rate_pct"], 33.33, places=2)

    def test_best_worst_trade_math(self):
        trades = [
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 50.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 5.0, "quantity": 1.0, "commission": 0.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertEqual(res["metrics"]["best_trade"], 40.0)
        self.assertEqual(res["metrics"]["worst_trade"], -5.0)

    def test_maximum_drawdown_calculation(self):
        # Initial 10000. Trades net: +1000 (Eq 11000), -2200 (Eq 8800). Peak 11000 -> 8800 DD = 2200/11000 = 20.0%
        trades = [
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": 100.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 20.0, "quantity": 100.0, "commission": 0.0},
            {"symbol": "A", "side": "BUY", "price": 100.0, "quantity": 100.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 78.0, "quantity": 100.0, "commission": 0.0}
        ]
        res = analyze_paper_trades(trades, initial_capital=10000.0)
        self.assertEqual(res["metrics"]["max_drawdown_pct"], 20.0)

    def test_open_position_separation(self):
        trades = [
            {"symbol": "SOL/USDT", "side": "BUY", "price": 100.0, "quantity": 5.0, "commission": 1.0}
        ]
        res = analyze_paper_trades(trades, current_prices={"SOL/USDT": 120.0})
        self.assertEqual(res["metrics"]["total_closed_trades"], 0)
        self.assertEqual(res["metrics"]["total_realized_pnl"], 0.0)
        self.assertEqual(len(res["open_positions"]), 1)
        # Unrealized PnL = (120 - 100)*5 - 1.0 = 99.0
        self.assertEqual(res["unrealized_pnl"], 99.0)

    def test_invalid_and_malformed_records(self):
        trades = [
            "invalid string record",
            {"symbol": "A", "side": "BUY", "price": -10.0, "quantity": 1.0},
            {"symbol": "A", "side": "BUY", "price": 10.0, "quantity": "invalid_qty"},
            {"symbol": "A", "side": "BUY", "price": 100.0, "quantity": 1.0, "commission": 0.0},
            {"symbol": "A", "side": "SELL", "price": 110.0, "quantity": 1.0, "commission": 0.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        self.assertEqual(res["metrics"]["total_closed_trades"], 1)

    def test_sell_without_sufficient_open_quantity(self):
        trades = [
            {"symbol": "A", "side": "SELL", "price": 100.0, "quantity": 10.0}
        ]
        res = analyze_paper_trades(trades)
        self.assertTrue(res["success"])
        self.assertEqual(res["metrics"]["total_closed_trades"], 0)

    def test_invalid_initial_capital(self):
        res = analyze_paper_trades([], initial_capital=-500.0)
        self.assertFalse(res["success"])
        self.assertIn("Invalid initial capital", res["error"])

def run_analytics_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPaperAnalytics)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_analytics_tests()
    if not success:
        exit(1)