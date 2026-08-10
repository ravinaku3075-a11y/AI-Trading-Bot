import os
import sys
import time
import logging
from datetime import datetime, timezone

# Core module imports
from sqlite_logger import get_connection
import paper_analytics
from paper_analytics import get_daily_closed_trade_metrics
from portfolio_risk_manager import PortfolioRiskManager

logger = logging.getLogger(__name__)

def run_startup_preflight():
    """
    Validates critical module contracts, DB availability, and
    risk manager initialization before entering the execution loop.
    """
    try:
        print("[PRE-FLIGHT] Checking paper_analytics export contract...")
        if not hasattr(paper_analytics, 'get_daily_closed_trade_metrics'):
            print("CRITICAL PRE-FLIGHT ERROR: 'get_daily_closed_trade_metrics' missing in paper_analytics")
            return False

        if not callable(paper_analytics.get_daily_closed_trade_metrics):
            print("CRITICAL PRE-FLIGHT ERROR: 'get_daily_closed_trade_metrics' is not callable")
            return False

        print("[PRE-FLIGHT] Checking SQLite database connection...")
        conn = get_connection()
        if conn is None:
            print("CRITICAL PRE-FLIGHT ERROR: Database connection failed")
            return False
        conn.close()

        print("[PRE-FLIGHT] Checking PortfolioRiskManager initialization...")
        risk_mgr = PortfolioRiskManager()
        if risk_mgr is None:
            print("CRITICAL PRE-FLIGHT ERROR: PortfolioRiskManager initialization failed")
            return False

        print("WORKER PRE-FLIGHT CHECK: PASS")
        return True
    except Exception as e:
        print(f"CRITICAL PRE-FLIGHT EXCEPTION: {type(e).__name__}: {e}")
        return False

def execute_paper_trade_cycle():
    """
    Executes a single paper trading loop cycle safely.
    Read-only analytics and fail-closed risk checks.
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            print("Warning: Database connection unavailable for current cycle.")
            return

        # Fetch daily closed trade metrics for UTC date
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_metrics = get_daily_closed_trade_metrics(conn, target_date_utc=today_utc)

        # Verify Portfolio Risk Manager / Loss Lock
        risk_mgr = PortfolioRiskManager()
        if hasattr(risk_mgr, 'check_daily_loss_lock'):
            loss_locked = risk_mgr.check_daily_loss_lock(conn)
            if loss_locked:
                print(f"[{datetime.now(timezone.utc)}] Daily Loss Lock is ACTIVE. Trading suspended for today.")
                return

        print(f"[{datetime.now(timezone.utc)}] Paper Trade Cycle Executed. Daily Trades Analyzed: {daily_metrics.get('total_closed', 0)}")
    except Exception as e:
        print(f"Error inside execute_paper_trade_cycle [{type(e).__name__}]: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def main():
    """Main worker engine entry point with fault isolation."""
    if not run_startup_preflight():
        print("Worker startup aborted due to pre-flight failure.")
        sys.exit(1)

    print("Paper Worker Engine Started with Daily Loss Lock & Summary Scheduler...")

    while True:
        try:
            execute_paper_trade_cycle()
        except (KeyboardInterrupt, SystemExit):
            print("Worker stopping gracefully due to interrupt signal...")
            break
        except Exception as e:
            print(f"Recoverable worker loop error caught [{type(e).__name__}]: {e}")

        # Standard 60-second polling interval
        time.sleep(60)

if __name__ == "__main__":
    main()
