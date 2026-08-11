import sys
import time
import sqlite3
import paper_analytics
import portfolio_risk_manager
import sqlite_logger

def run_startup_preflight():
    print(f"[PRE-FLIGHT] Resolved DB Path: {sqlite_logger.DB_PATH}")
    print("[PRE-FLIGHT] Initializing Database Schema...")
    try:
        sqlite_logger.init_db()
        print("[PRE-FLIGHT] Database Schema Verification: PASS")
    except Exception as e:
        print(f"[PRE-FLIGHT] Database Schema Initialization FAILED: {e}")
        return False

    print("[PRE-FLIGHT] Checking paper_analytics export contract...")
    if not hasattr(paper_analytics, 'get_daily_closed_trade_metrics'):
        print("[PRE-FLIGHT] Contract Check FAILED: paper_analytics.get_daily_closed_trade_metrics missing")
        return False

    print("[PRE-FLIGHT] Checking SQLite database connection...")
    try:
        conn = sqlite_logger.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trades', 'telegram_alerts')")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        if 'trades' not in tables or 'telegram_alerts' not in tables:
            print(f"[PRE-FLIGHT] Database Contract FAILED: Required tables missing (Found: {tables})")
            return False
    except Exception as e:
        print(f"[PRE-FLIGHT] Database Connection FAILED: {e}")
        return False

    print("[PRE-FLIGHT] Checking PortfolioRiskManager initialization...")
    try:
        rm = portfolio_risk_manager.PortfolioRiskManager()
        if rm is None:
            print("[PRE-FLIGHT] PortfolioRiskManager Initialization FAILED")
            return False
    except Exception as e:
        print(f"[PRE-FLIGHT] PortfolioRiskManager Exception: {e}")
        return False

    print("WORKER PRE-FLIGHT CHECK: PASS")
    return True

def execute_paper_trade_cycle():
    try:
        conn = sqlite_logger.get_connection()
        rm = portfolio_risk_manager.PortfolioRiskManager()
        is_locked = rm.check_daily_loss_lock(conn)
        conn.close()
        if is_locked:
            print("[WORKER CYCLE] Daily Loss Lock is ACTIVE. Trading suspended.")
        else:
            print("[WORKER CYCLE] Normal polling cycle completed successfully.")
        return True
    except Exception as e:
        print(f"Error inside execute_paper_trade_cycle [{type(e).__name__}]: {e}")
        return False

def main():
    if not run_startup_preflight():
        print("WORKER FATAL: Pre-flight checks failed. Exiting worker process.")
        sys.exit(1)

    print("Paper Worker Engine Started with Daily Loss Lock & Summary Scheduler...")

    if "--oneshot" in sys.argv:
        execute_paper_trade_cycle()
    else:
        while True:
            execute_paper_trade_cycle()
            time.sleep(60)

if __name__ == "__main__":
    main()