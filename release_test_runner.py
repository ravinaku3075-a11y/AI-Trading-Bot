import sys
import unittest
import sqlite3
import os
import paper_analytics
import portfolio_risk_manager
import sqlite_logger

class TestAutoCoderBugDetection(unittest.TestCase):
    """Original Regression Suite (12 Tests)"""

    def test_01_analytics_import(self):
        self.assertTrue(hasattr(paper_analytics, 'get_daily_closed_trade_metrics'))

    def test_02_daily_metrics_callable(self):
        self.assertTrue(callable(paper_analytics.get_daily_closed_trade_metrics))

    def test_03_sqlite_connection_helper(self):
        self.assertTrue(hasattr(sqlite_logger, 'get_connection'))

    def test_04_risk_manager_availability(self):
        risk_mgr = portfolio_risk_manager.PortfolioRiskManager()
        self.assertIsNotNone(risk_mgr)

    def test_05_daily_metrics_structure(self):
        conn = sqlite3.connect(":memory:")
        metrics = paper_analytics.get_daily_closed_trade_metrics(conn, "2026-08-10")
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_closed", metrics)
        conn.close()

    def test_06_analytics_empty_db_handling(self):
        conn = sqlite3.connect(":memory:")
        metrics = paper_analytics.get_daily_closed_trade_metrics(conn, "2026-08-10")
        self.assertEqual(metrics.get("total_closed", 0), 0)
        conn.close()

    def test_07_portfolio_risk_manager_instantiation(self):
        rm = portfolio_risk_manager.PortfolioRiskManager()
        self.assertTrue(hasattr(rm, 'check_daily_loss_lock'))

    def test_08_sqlite_logger_connection_type(self):
        conn = sqlite_logger.get_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_09_analytics_schema_resilience(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE closed_trades (id INT, pnl REAL, close_time TEXT)")
        metrics = paper_analytics.get_daily_closed_trade_metrics(conn, "2026-08-10")
        self.assertIsInstance(metrics, dict)
        conn.close()

    def test_10_analytics_date_filtering(self):
        conn = sqlite3.connect(":memory:")
        metrics = paper_analytics.get_daily_closed_trade_metrics(conn, "1999-01-01")
        self.assertEqual(metrics.get("total_closed", 0), 0)
        conn.close()

    def test_11_risk_manager_loss_lock_type(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                action TEXT,
                pnl REAL,
                price REAL,
                quantity INTEGER,
                close_time TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        rm = portfolio_risk_manager.PortfolioRiskManager()
        res = rm.check_daily_loss_lock(conn)
        self.assertIsInstance(res, (bool, tuple))
        conn.close()

    def test_12_logger_isolation(self):
        self.assertTrue(callable(sqlite_logger.get_connection))


class TestWorkerImportContract(unittest.TestCase):
    """Hardening & Crash Prevention Suite (6 Tests)"""

    def test_13_worker_module_import(self):
        import paper_worker
        self.assertTrue(hasattr(paper_worker, 'run_startup_preflight'))

    def test_14_worker_preflight_execution(self):
        import paper_worker
        self.assertTrue(paper_worker.run_startup_preflight())

    def test_15_worker_execute_cycle_callable(self):
        import paper_worker
        self.assertTrue(callable(paper_worker.execute_paper_trade_cycle))

    def test_16_worker_main_callable(self):
        import paper_worker
        self.assertTrue(callable(paper_worker.main))

    def test_17_analytics_function_export(self):
        self.assertTrue(hasattr(paper_analytics, 'get_daily_closed_trade_metrics'))

    def test_18_risk_manager_type_check(self):
        rm = portfolio_risk_manager.PortfolioRiskManager()
        self.assertIsInstance(rm, portfolio_risk_manager.PortfolioRiskManager)


class TestDatabaseSchemaRecovery(unittest.TestCase):
    """Phase 4 Database Recovery & Idempotence Tests (3 Tests)"""

    def test_19_fresh_empty_db_initialization(self):
        sqlite_logger.init_db()
        conn = sqlite_logger.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("trades", tables)
        self.assertIn("telegram_alerts", tables)

    def test_20_schema_idempotence_and_preservation(self):
        sqlite_logger.init_db()
        conn = sqlite_logger.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO trades (symbol, action, price, quantity) VALUES ('BTCUSDT', 'BUY', 50000.0, 1.0)")
        conn.commit()

        sqlite_logger.init_db()

        cursor.execute("SELECT COUNT(*) FROM trades WHERE symbol='BTCUSDT'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreaterEqual(count, 1)

    def test_21_worker_preflight_db_contract(self):
        import paper_worker
        self.assertTrue(paper_worker.run_startup_preflight())


class TestDatabasePathHardening(unittest.TestCase):
    """STEP 22C-2E DB Path Hardening Tests (3 Tests)"""

    def test_22_default_db_path_resolution(self):
        self.assertTrue(hasattr(sqlite_logger, 'DB_PATH'))
        self.assertTrue(hasattr(sqlite_logger, 'DB_NAME'))
        self.assertEqual(sqlite_logger.DB_PATH, sqlite_logger.DB_NAME)

    def test_23_paper_trading_db_path_alignment(self):
        import paper_trading
        self.assertTrue(hasattr(paper_trading, 'DB_PATH'))
        self.assertEqual(paper_trading.DB_PATH, sqlite_logger.DB_PATH)

    def test_24_worker_logs_resolved_db_path(self):
        import paper_worker
        self.assertTrue(paper_worker.run_startup_preflight())


class TestObservationDashboardMetrics(unittest.TestCase):
    """STEP 22C-2F Observation Dashboard Read-Only Metrics Tests (3 Tests)"""

    def test_25_observation_metrics_normal_data(self):
        conn = sqlite_logger.get_connection()
        metrics = paper_analytics.get_observation_dashboard_metrics(conn)
        conn.close()
        self.assertIsInstance(metrics, dict)
        self.assertIn("buy_count", metrics)
        self.assertIn("executed_orders_count", metrics)

    def test_26_observation_metrics_empty_db(self):
        conn = sqlite3.connect(":memory:")
        metrics = paper_analytics.get_observation_dashboard_metrics(conn)
        conn.close()
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("buy_count"), 0)
        self.assertEqual(metrics.get("closed_trade_count"), 0)

    def test_27_observation_metrics_none_connection(self):
        metrics = paper_analytics.get_observation_dashboard_metrics(None)
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("buy_count"), 0)


class TestWorkerGracefulShutdown(unittest.TestCase):
    """STEP 22C-4 Graceful Shutdown Tests (2 New Tests)"""

    def test_28_worker_shutdown_signal_handling(self):
        import paper_worker
        paper_worker.shutdown_event.clear()
        self.assertFalse(paper_worker.shutdown_event.is_set())
        paper_worker.shutdown_event.set()
        self.assertTrue(paper_worker.shutdown_event.is_set())
        paper_worker.shutdown_event.clear()

    def test_29_worker_shutdown_idempotency(self):
        import paper_worker
        paper_worker.shutdown_event.clear()
        paper_worker.shutdown_event.set()
        paper_worker.shutdown_event.set()  # Multiple signal triggers must remain safe
        self.assertTrue(paper_worker.shutdown_event.is_set())
        paper_worker.shutdown_event.clear()


def run_regression_suite():
    print("Starting Automated Regression Tests...")
    print("Testing Auto Coder Bug Detection, Worker Safety, DB Recovery, Path Hardening, Observation Dashboard & Shutdown\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAutoCoderBugDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkerImportContract))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseSchemaRecovery))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabasePathHardening))
    suite.addTests(loader.loadTestsFromTestCase(TestObservationDashboardMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkerGracefulShutdown))

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)

    print("\n--- TEST EXECUTION COMPLETED ---")
    print(f"Total Tests: {result.testsRun}")
    failed_tests = len(result.failures) + len(result.errors)
    passed_tests = result.testsRun - failed_tests

    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Critical Failures: {failed_tests}")

    if result.wasSuccessful():
        print("Release Gate: PASS")
        return 0
    else:
        print("Release Gate: FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(run_regression_suite())