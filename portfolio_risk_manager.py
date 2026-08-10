import sqlite3
from datetime import datetime, timezone

class PortfolioRiskManager:
    def __init__(self, max_daily_loss_pct=2.0, max_position_size=100):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_position_size = max_position_size

    def check_daily_loss_lock(self, conn):
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(price * quantity) 
            FROM trades 
            WHERE DATE(timestamp) = ? AND action = 'SELL' AND status = 'EXECUTED'
        """, (today_utc,))
        realized_sell = cursor.fetchone()[0] or 0.0

        cursor.execute("""
            SELECT SUM(price * quantity) 
            FROM trades 
            WHERE DATE(timestamp) = ? AND action = 'BUY' AND status = 'EXECUTED'
        """, (today_utc,))
        realized_buy = cursor.fetchone()[0] or 0.0

        realized_pnl = realized_sell - realized_buy

        # Check if loss limit exceeded
        if realized_pnl < 0 and abs(realized_pnl) >= self.max_daily_loss_pct:
            return True, realized_pnl  # Lock active
        return False, realized_pnl

    def validate_order_risk(self, conn, symbol, action, price, quantity):
        is_locked, realized_pnl = self.check_daily_loss_lock(conn)

        # Risk-reducing SELL orders remain allowed during daily loss lock
        if is_locked and action.upper() == 'BUY':
            return False, f"Daily Loss Lock active (Realized PnL: ${realized_pnl:.2f}). BUY orders blocked."

        if quantity > self.max_position_size:
            return False, f"Order quantity {quantity} exceeds max limit {self.max_position_size}."

        return True, "Order risk checks passed."