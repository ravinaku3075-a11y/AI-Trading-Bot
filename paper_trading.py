import os
import sqlite3
import pandas as pd
from datetime import datetime
import numpy as np

from portfolio_risk_manager import PortfolioRiskManager
import paper_analytics
from sqlite_logger import DB_PATH
CSV_PATH = "trade_journal.csv"

def load_paper_trade_records():
    """
    Loads paper trade records with SQLite as primary source and CSV fallback.
    Read-only retrieval to ensure zero state mutation.
    """
    records = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            df_sql = pd.read_sql_query("SELECT * FROM trades", conn)
            conn.close()
            if not df_sql.empty:
                return df_sql.to_dict(orient="records")
        except Exception:
            pass

    if os.path.exists(CSV_PATH):
        try:
            df_csv = pd.read_csv(CSV_PATH)
            if not df_csv.empty:
                return df_csv.to_dict(orient="records")
        except Exception:
            pass

    return records

class PaperTradingEngine:
    def __init__(self, initial_cash: float = 10000.0, risk_limits: dict = None):
        self.cash = float(initial_cash)
        self.positions = {}  # {symbol: {"quantity": float, "entry_price": float, "total_cost": float, "entry_commission": float}}
        self.risk_limits = risk_limits or {
            "max_symbol_exposure_pct": 25.0,
            "max_portfolio_exposure_pct": 80.0,
            "max_daily_loss_pct": 5.0,
            "max_realized_drawdown_pct": 15.0
        }

    def _build_portfolio_state(self, current_order_symbol: str, current_order_price: float, current_prices: dict = None) -> dict:
        """
        Builds portfolio state snapshot for risk manager.
        - Reads self.cash and self.positions without mutation.
        - NEVER uses entry_price as a fallback market price.
        - Obtains daily realized P&L and realized drawdown via paper_analytics.py.
        """
        price_map = {}
        if current_prices and isinstance(current_prices, dict):
            for k, v in current_prices.items():
                try:
                    vf = float(v)
                    if vf > 0 and np.isfinite(vf):
                        price_map[str(k).upper()] = vf
                except (ValueError, TypeError):
                    pass

        # Always ensure incoming order symbol uses the provided current_order_price
        if current_order_symbol and current_order_price > 0 and np.isfinite(current_order_price):
            price_map[str(current_order_symbol).upper()] = float(current_order_price)

        # Derive analytics metrics (daily realized P&L and realized drawdown)
        daily_realized_pnl = 0.0
        realized_drawdown_pct = 0.0

        try:
            records = load_paper_trade_records()
            res = analyze_paper_trades(records)
            if res.get("success", False):
                metrics = res.get("metrics", {})
                realized_drawdown_pct = float(metrics.get("max_drawdown_pct", 0.0))
                
                # Derive current day realized P&L
                closed_trades = res.get("closed_trades", [])
                today_iso = datetime.utcnow().strftime("%Y-%m-%d")
                for ct in closed_trades:
                    ts = str(ct.get("timestamp", ""))
                    if ts.startswith(today_iso):
                        daily_realized_pnl += float(ct.get("net_pnl", 0.0))
        except Exception:
            pass

        return {
            "available_cash": self.cash,
            "open_positions": self.positions,
            "daily_realized_pnl": daily_realized_pnl,
            "realized_drawdown_pct": realized_drawdown_pct,
            "current_prices": price_map
        }

    def get_portfolio_risk_snapshot(self, current_prices: dict = None) -> dict:
        """
        Pure read-only portfolio risk snapshot generator.
        - Zero order execution
        - Zero cash/position/risk_limits mutation
        - Zero SQLite/CSV writes
        - NEVER uses entry_price as mark price fallback
        """
        price_map = {}
        if current_prices and isinstance(current_prices, dict):
            for k, v in current_prices.items():
                try:
                    vf = float(v)
                    if vf > 0 and np.isfinite(vf):
                        price_map[str(k).upper()] = vf
                except (ValueError, TypeError):
                    pass

        # Check missing mark prices for open positions
        missing_price_symbols = []
        if isinstance(self.positions, dict):
            for sym, pos in self.positions.items():
                if isinstance(pos, dict) and float(pos.get("quantity", 0.0)) > 0:
                    sym_upper = str(sym).upper()
                    if sym_upper not in price_map:
                        missing_price_symbols.append(sym_upper)

        # Derive analytics metrics
        daily_realized_pnl = 0.0
        realized_drawdown_pct = 0.0
        try:
            records = load_paper_trade_records()
            res = analyze_paper_trades(records)
            if res.get("success", False):
                metrics = res.get("metrics", {})
                realized_drawdown_pct = float(metrics.get("max_drawdown_pct", 0.0))
                closed_trades = res.get("closed_trades", [])
                today_iso = datetime.utcnow().strftime("%Y-%m-%d")
                
                # Fallback calculation for closed trade drawdown
                cum_pnl = 0.0
                peak_pnl = 0.0
                max_dd_val = 0.0
                for ct in closed_trades:
                    p = float(ct.get("net_pnl", ct.get("pnl", 0.0)))
                    cum_pnl += p
                    if cum_pnl > peak_pnl:
                        peak_pnl = cum_pnl
                    dd = peak_pnl - cum_pnl
                    if dd > max_dd_val:
                        max_dd_val = dd
                    
                    ts = str(ct.get("timestamp", ""))
                    if ts.startswith(today_iso):
                        daily_realized_pnl += p
                
                # If analytics returned 0 max_drawdown_pct, calculate from closed trades relative to initial/peak equity
                if realized_drawdown_pct == 0.0 and max_dd_val > 0:
                    base_capital = self.cash + (peak_pnl - cum_pnl)
                    if base_capital > 0:
                        realized_drawdown_pct = (max_dd_val / base_capital) * 100.0
        except Exception:
            pass

        limits = dict(self.risk_limits)
        max_sym_limit = float(limits.get("max_symbol_exposure_pct", 25.0))
        max_port_limit = float(limits.get("max_portfolio_exposure_pct", 80.0))
        max_daily_loss_pct = float(limits.get("max_daily_loss_pct", 5.0))
        max_drawdown_limit = float(limits.get("max_realized_drawdown_pct", 15.0))

        if missing_price_symbols:
            return {
                "status": "DATA_UNAVAILABLE",
                "current_cash": self.cash,
                "total_portfolio_equity": None,
                "total_open_position_value": None,
                "total_portfolio_exposure_pct": None,
                "per_symbol_exposure": {},
                "daily_realized_pnl": daily_realized_pnl,
                "realized_drawdown_pct": realized_drawdown_pct,
                "risk_limits": limits,
                "missing_price_symbols": sorted(missing_price_symbols)
            }

        total_open_val = 0.0
        per_symbol_exp = {}
        if isinstance(self.positions, dict):
            for sym, pos in self.positions.items():
                if not isinstance(pos, dict):
                    continue
                qty = float(pos.get("quantity", 0.0))
                if qty <= 0:
                    continue
                sym_upper = str(sym).upper()
                mark_p = price_map[sym_upper]
                val = qty * mark_p
                total_open_val += val
                per_symbol_exp[sym_upper] = val

        total_equity = self.cash + total_open_val
        if total_equity <= 0 or not np.isfinite(total_equity):
            return {
                "status": "DATA_UNAVAILABLE",
                "current_cash": self.cash,
                "total_portfolio_equity": total_equity,
                "total_open_position_value": total_open_val,
                "total_portfolio_exposure_pct": None,
                "per_symbol_exposure": {},
                "daily_realized_pnl": daily_realized_pnl,
                "realized_drawdown_pct": realized_drawdown_pct,
                "risk_limits": limits,
                "missing_price_symbols": []
            }

        total_port_exp_pct = (total_open_val / total_equity) * 100.0
        per_symbol_exp_pct = {k: (v / total_equity) * 100.0 for k, v in per_symbol_exp.items()}

        status = "SAFE"
        max_daily_loss_amount = (max_daily_loss_pct / 100.0) * total_equity

        # Daily Loss Priority Evaluation
        if daily_realized_pnl < 0:
            loss_amt = abs(daily_realized_pnl)
            if loss_amt >= max_daily_loss_amount:
                status = "LIMIT_REACHED"
            elif loss_amt >= 0.8 * max_daily_loss_amount:
                status = "WARNING"

        # Drawdown Evaluation
        if status != "LIMIT_REACHED":
            if realized_drawdown_pct >= max_drawdown_limit:
                status = "LIMIT_REACHED"
            elif realized_drawdown_pct >= 0.8 * max_drawdown_limit and status != "WARNING":
                status = "WARNING"

        # Exposure Evaluation
        if status != "LIMIT_REACHED":
            if total_port_exp_pct >= max_port_limit or any(v >= max_sym_limit for v in per_symbol_exp_pct.values()):
                status = "LIMIT_REACHED"
            elif (total_port_exp_pct >= 0.8 * max_port_limit or any(v >= 0.8 * max_sym_limit for v in per_symbol_exp_pct.values())) and status != "WARNING":
                status = "WARNING"

        return {
            "status": status,
            "current_cash": self.cash,
            "total_portfolio_equity": total_equity,
            "total_open_position_value": total_open_val,
            "total_portfolio_exposure_pct": total_port_exp_pct,
            "per_symbol_exposure": per_symbol_exp_pct,
            "daily_realized_pnl": daily_realized_pnl,
            "realized_drawdown_pct": realized_drawdown_pct,
            "risk_limits": limits,
            "missing_price_symbols": []
        }

    def execute_order(self, symbol: str, side: str, price: float, quantity: float, timestamp: str = None, current_prices: dict = None) -> dict:
        """
        Executes a paper trading order after passing basic validation AND portfolio risk checks.
        Zero state mutation / persistence occurs if order is rejected.
        """
        # 1. Basic Parameter Validation
        if not symbol or not isinstance(symbol, str):
            return {"success": False, "status": "ERROR", "reason": ["Invalid or missing symbol."]}

        symbol = symbol.upper()
        side = str(side).upper()

        try:
            price = float(price)
            quantity = float(quantity)
        except (ValueError, TypeError):
            return {"success": False, "status": "ERROR", "reason": ["Non-numeric price or quantity."]}

        if price <= 0 or quantity <= 0 or not np.isfinite(price) or not np.isfinite(quantity):
            return {"success": False, "status": "ERROR", "reason": ["Price and quantity must be positive finite numbers."]}

        if side not in ["BUY", "SELL"]:
            return {"success": False, "status": "ERROR", "reason": [f"Unsupported side '{side}'."]}

        # 2. Oversized SELL Check
        held_qty = float(self.positions.get(symbol, {}).get("quantity", 0.0))
        if side == "SELL" and quantity > held_qty + 1e-8:
            return {"success": False, "status": "ERROR", "reason": [f"Cannot SELL quantity ({quantity}) greater than held position ({held_qty})."]}

        # 3. Portfolio Risk Validation (BEFORE ANY STATE MUTATION OR LOGGING)
        order_request = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity
        }
        
        portfolio_state = self._build_portfolio_state(
            current_order_symbol=symbol,
            current_order_price=price,
            current_prices=current_prices
        )

        risk_res = validate_portfolio_risk(order_request, portfolio_state, self.risk_limits)
        if not risk_res.get("allowed", False):
            return {
                "success": False,
                "status": risk_res.get("status", "BLOCKED"),
                "reason": risk_res.get("reasons", ["Blocked by portfolio risk manager."]),
                "metrics": risk_res.get("metrics", {})
            }

        # 4. Order Execution & State Mutation (ONLY PERFORMED WHEN APPROVED)
        ts_str = timestamp or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        order_value = price * quantity

        if side == "BUY":
            self.cash -= order_value
            if symbol in self.positions:
                cur_qty = self.positions[symbol]["quantity"]
                cur_cost = self.positions[symbol]["total_cost"]
                new_qty = cur_qty + quantity
                new_cost = cur_cost + order_value
                self.positions[symbol] = {
                    "quantity": new_qty,
                    "entry_price": new_cost / new_qty,
                    "total_cost": new_cost,
                    "entry_commission": 0.0
                }
            else:
                self.positions[symbol] = {
                    "quantity": quantity,
                    "entry_price": price,
                    "total_cost": order_value,
                    "entry_commission": 0.0
                }
        elif side == "SELL":
            self.cash += order_value
            rem_qty = held_qty - quantity
            if rem_qty <= 1e-8:
                del self.positions[symbol]
            else:
                self.positions[symbol]["quantity"] = rem_qty
                self.positions[symbol]["total_cost"] = rem_qty * self.positions[symbol]["entry_price"]

        # 5. Persistence Logging (ONLY FOR EXECUTED TRADES)
        self._log_trade(symbol, side, price, quantity, ts_str)

        return {
            "success": True,
            "status": "EXECUTED",
            "reason": ["Order executed successfully."],
            "trade": {
                "symbol": symbol,
                "side": side,
                "price": price,
                "quantity": quantity,
                "timestamp": ts_str
            }
        }

    def _log_trade(self, symbol: str, side: str, price: float, quantity: float, timestamp: str):
        """Internal helper to write executed trades to SQLite and CSV."""
        record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "commission": 0.0,
            "pnl": 0.0
        }
        
        # Write to SQLite
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    side TEXT,
                    price REAL,
                    quantity REAL,
                    commission REAL,
                    timestamp TEXT,
                    pnl REAL
                )
            """)
            cursor.execute("""
                INSERT INTO trades (symbol, side, price, quantity, commission, timestamp, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, side, price, quantity, 0.0, timestamp, 0.0))
            conn.commit()
            conn.close()
        except Exception:
            pass

        # Write to CSV
        try:
            file_exists = os.path.exists(CSV_PATH)
            df = pd.DataFrame([record])
            df.to_csv(CSV_PATH, mode="a", header=not file_exists, index=False)
        except Exception:
            pass