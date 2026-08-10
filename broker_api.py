"""
broker_api.py - Institutional Paper Trading Broker Core
"""
import pandas as pd
from typing import List, Dict, Any

class PaperBroker:
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []

    def execute_order(self, ticker: str, side: str, price: float, quantity: int) -> bool:
        if quantity <= 0 or price <= 0:
            return False

        cost = price * quantity

        if side.upper() == "BUY":
            # Allow trade execution in paper trading
            if ticker in self.positions:
                self.positions[ticker]['Quantity'] += quantity
                self.positions[ticker]['Cost'] += cost
            else:
                self.positions[ticker] = {
                    'Ticker': ticker,
                    'Quantity': quantity,
                    'EntryPrice': price,
                    'Cost': cost,
                    'P&L ($)': 0.0
                }

            self.trade_history.append({
                'Ticker': ticker,
                'Side': 'BUY',
                'Price': price,
                'Quantity': quantity,
                'Status': 'FILLED'
            })
            return True

        elif side.upper() == "SELL":
            if ticker in self.positions:
                qty_held = self.positions[ticker]['Quantity']
                sell_qty = min(quantity, qty_held)
                self.positions[ticker]['Quantity'] -= sell_qty

                if self.positions[ticker]['Quantity'] <= 0:
                    del self.positions[ticker]

                self.trade_history.append({
                    'Ticker': ticker,
                    'Side': 'SELL',
                    'Price': price,
                    'Quantity': sell_qty,
                    'Status': 'FILLED'
                })
                return True
            else:
                # Allow simulated short-selling / sell execution for testing
                self.trade_history.append({
                    'Ticker': ticker,
                    'Side': 'SELL',
                    'Price': price,
                    'Quantity': quantity,
                    'Status': 'FILLED'
                })
                return True

        return False

    def get_positions(self) -> List[Dict[str, Any]]:
        return list(self.positions.values())

    def get_trade_history(self) -> List[Dict[str, Any]]:
        return self.trade_history

broker = PaperBroker()
