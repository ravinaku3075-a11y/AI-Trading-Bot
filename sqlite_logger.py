import sqlite3
import os

# Centralized Database Path Resolution (DB_PATH -> DATA_DIR/trades.db -> trades.db)
_custom_db_path = os.getenv("DB_PATH")
if _custom_db_path:
    DB_PATH = _custom_db_path
else:
    _data_dir = os.getenv("DATA_DIR")
    if _data_dir:
        DB_PATH = os.path.join(_data_dir, "trades.db")
    else:
        DB_PATH = "trades.db"

# Backward compatibility alias
DB_NAME = DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Trades Table
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

    # 2. Telegram Alerts Table
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

if __name__ == "__main__":
    init_db()