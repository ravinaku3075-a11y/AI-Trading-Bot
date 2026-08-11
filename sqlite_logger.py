import os
import sqlite3

DB_NAME = os.getenv("DB_PATH", "trades.db")
DB_PATH = DB_NAME

def get_connection():
    """
    Returns a connection to the SQLite database.
    Ensures parent directory exists before creating/connecting to the database file.
    """
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """
    Initializes the database schema if tables do not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            action TEXT,
            price REAL,
            quantity REAL,
            status TEXT,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_side TEXT,
            status TEXT,
            event_timestamp TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS closed_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            pnl REAL,
            close_time TEXT
        )
    """)

    conn.commit()
    conn.close()