import sqlite3
import os

DB_NAME = "trades.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Existing Trades Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            status TEXT DEFAULT 'EXECUTED'
        )
    """)
    
    # 2. STEP 22A Persistent Telegram Alerts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_hash TEXT UNIQUE NOT NULL,
            symbol TEXT NOT NULL,
            signal_side TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('PENDING', 'SENT', 'FAILED')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# --- Alert Deduplication Helper Functions ---

def register_alert_pending(conn, alert_hash, symbol, signal_side, event_timestamp):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO telegram_alerts (alert_hash, symbol, signal_side, event_timestamp, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    """, (alert_hash, symbol, signal_side, str(event_timestamp)))
    conn.commit()

def get_alert_status(conn, alert_hash):
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM telegram_alerts WHERE alert_hash = ?", (alert_hash,))
    row = cursor.fetchone()
    return row[0] if row else None

def mark_alert_sent(conn, alert_hash):
    cursor = conn.cursor()
    cursor.execute("UPDATE telegram_alerts SET status = 'SENT', sent_at = CURRENT_TIMESTAMP WHERE alert_hash = ?", (alert_hash,))
    conn.commit()

def mark_alert_failed(conn, alert_hash):
    cursor = conn.cursor()
    cursor.execute("UPDATE telegram_alerts SET status = 'FAILED' WHERE alert_hash = ?", (alert_hash,))
    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized with trades & telegram_alerts tables.")