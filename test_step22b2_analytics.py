import unittest
import sqlite3
import datetime
from paper_analytics import get_enhanced_paper_analytics
from signal_adapter import normalize_signal

class TestStep22B2AnalyticsAndSignal(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                action TEXT,
                price REAL,
                quantity INTEGER,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_empty_trade_analytics(self):
        res = get_enhanced_paper_analytics(self.conn)
        self.assertEqual(res["total_closed_trades"], 0)
        self.assertEqual(res["profit_factor"], "NO_LOSSES")

    def test_signal_normalization_hold_safety(self):
        raw = {"symbol": "NVDA", "action": "BUY", "price": -10}
        norm = normalize_signal(raw)
        self.assertEqual(norm["action"], "HOLD")
        self.assertIsNone(norm["price"])

    def test_valid_signal_normalization(self):
        raw = {"symbol": "NVDA", "action": "BUY", "price": 150.0, "confidence": 85.0}
        norm = normalize_signal(raw)
        self.assertEqual(norm["action"], "BUY")
        self.assertEqual(norm["price"], 150.0)
        self.assertEqual(norm["confidence"], 85.0)

if __name__ == "__main__":
    unittest.main()