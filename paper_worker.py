import os
import time
import hashlib
import requests
from datetime import datetime, timezone

from sqlite_logger import (
    get_connection,
    init_db,
    register_alert_pending,
    get_alert_status,
    mark_alert_sent,
    mark_alert_failed
)
from paper_analytics import get_daily_closed_trade_metrics
from portfolio_risk_manager import PortfolioRiskManager

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

risk_manager = PortfolioRiskManager(max_daily_loss_pct=50.0)

def generate_alert_hash(alert_type, identifier):
    raw = f"{alert_type}_{identifier}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def check_and_send_daily_summary(conn):
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_hash = generate_alert_hash("DAILY_SUMMARY", today_utc)
    
    status = get_alert_status(conn, summary_hash)
    if status == 'SENT':
        return False  # Already sent for today

    metrics = get_daily_closed_trade_metrics(conn, today_utc)
    
    msg = (
        f"📊 *DAILY TRADING SUMMARY ({today_utc} UTC)*\n"
        f"----------------------------------------\n"
        f"• *Closed Trades:* {metrics['total_closed_trades']}\n"
        f"• *Wins:* {metrics['winning_trades']} | *Losses:* {metrics['losing_trades']} | *Breakeven:* {metrics['breakeven_trades']}\n"
        f"• *Realized PnL:* ${metrics['daily_realized_pnl']:.2f}\n"
        f"• *Win Rate:* {metrics['daily_win_rate_pct']}%\n"
        f"• *Return:* {metrics['daily_realized_return_pct']}%"
    )

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Daily Summary] Missing Telegram credentials. Skipping dispatch.")
        return False

    register_alert_pending(conn, summary_hash, "SUMMARY", "DAILY", today_utc)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            mark_alert_sent(conn, summary_hash)
            print("[Daily Summary] Sent successfully.")
            return True
        else:
            mark_alert_failed(conn, summary_hash)
            return False
    except Exception as e:
        mark_alert_failed(conn, summary_hash)
        return False

def execute_paper_trade_cycle():
    conn = get_connection()
    symbol = "NVDA"
    action = "BUY"
    price = 150.00
    quantity = 1

    # Validate Risk & Daily Loss Lock
    passed, reason = risk_manager.validate_order_risk(conn, symbol, action, price, quantity)
    if not passed:
        print(f"[Risk Blocked] Order rejected: {reason}")
        check_and_send_daily_summary(conn)
        conn.close()
        return

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trades (symbol, action, price, quantity) VALUES (?, ?, ?, ?)",
        (symbol, action, price, quantity)
    )
    conn.commit()
    print(f"[Paper Trade Executed] Logged {action} {quantity} x {symbol} @ ${price}")

    check_and_send_daily_summary(conn)
    conn.close()

def main():
    init_db()
    print("Paper Worker Engine Started with Daily Loss Lock & Summary Scheduler...")
    while True:
        try:
            execute_paper_trade_cycle()
        except Exception as e:
            print(f"Error in worker loop: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()