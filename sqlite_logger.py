import sqlite3
import os
from datetime import datetime

DB_NAME = "trades.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Trade Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Holdings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            symbol TEXT PRIMARY KEY,
            quantity INTEGER NOT NULL,
            avg_price REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def log_trade(symbol, action, quantity, price):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Insert Trade
    cursor.execute(
        "INSERT INTO trades (symbol, action, quantity, price, timestamp) VALUES (?, ?, ?, ?, ?)",
        (symbol.upper(), action.upper(), quantity, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    # Update Holdings
    cursor.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = ?", (symbol.upper(),))
    row = cursor.fetchone()

    if action.upper() == "BUY":
        if row:
            old_qty, old_avg = row
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
            cursor.execute("UPDATE holdings SET quantity = ?, avg_price = ? WHERE symbol = ?", (new_qty, new_avg, symbol.upper()))
        else:
            cursor.execute("INSERT INTO holdings (symbol, quantity, avg_price) VALUES (?, ?, ?)", (symbol.upper(), quantity, price))

    elif action.upper() == "SELL":
        if row:
            old_qty, old_avg = row
            new_qty = old_qty - quantity
            if new_qty <= 0:
                cursor.execute("DELETE FROM holdings WHERE symbol = ?", (symbol.upper(),))
            else:
                cursor.execute("UPDATE holdings SET quantity = ? WHERE symbol = ?", (new_qty, old_avg, symbol.upper()))

    conn.commit()
    conn.close()

def get_holdings():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, quantity, avg_price FROM holdings")
    rows = cursor.fetchall()
    conn.close()
    return [{"symbol": r[0], "quantity": r[1], "avg_price": r[2]} for r in rows]

def get_trade_history():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, symbol, action, quantity, price, timestamp FROM trades ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "symbol": r[1], "action": r[2], "quantity": r[3], "price": r[4], "timestamp": r[5]} for r in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
