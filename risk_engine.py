"""
risk_engine.py - Advanced Institutional Risk Management Engine
Version: 2.2 (Hardened & Audit Validated)
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

try:
    import config
except ImportError:
    config = None

# Logging Setup (Console + File Handler)
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "risk_engine.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] RiskEngine: %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RiskEngine")


class AdvancedRiskEngine:
    def __init__(self):
        self.account_balance = getattr(config, 'ACCOUNT_BALANCE', 10000.0) if config else 10000.0
        self.risk_per_trade_pct = getattr(config, 'DEFAULT_RISK_PER_TRADE_PCT', 1.0) if config else 1.0
        self.risk_reward_ratio = getattr(config, 'RISK_REWARD_RATIO', 2.0) if config else 2.0
        self.max_daily_loss_pct = getattr(config, 'MAX_DAILY_LOSS_PCT', 3.0) if config else 3.0
        self.max_open_trades = getattr(config, 'MAX_OPEN_TRADES', 3) if config else 3

    def calculate_atr(self, df: pd.DataFrame, period: Optional[int] = None) -> float:
        """Calculates Average True Range (ATR) with safe fallback."""
        if period is None:
            period = getattr(config, 'ATR_PERIOD', 14) if config else 14

        try:
            if df is None or df.empty or 'Close' not in df.columns or len(df) < 2:
                logger.warning("Empty or insufficient DataFrame for ATR calculation. Using default percentage fallback.")
                return 1.5

            if len(df) < period + 1:
                return float(max(0.01, df['Close'].dropna().iloc[-1] * 0.015))

            df_copy = df.copy()
            if 'High' in df_copy.columns and 'Low' in df_copy.columns:
                tr1 = df_copy['High'] - df_copy['Low']
                tr2 = abs(df_copy['High'] - df_copy['Close'].shift(1))
                tr3 = abs(df_copy['Low'] - df_copy['Close'].shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            else:
                tr = abs(df_copy['Close'].diff())

            atr_val = tr.rolling(window=period).mean().iloc[-1]
            if np.isnan(atr_val) or atr_val <= 0:
                return float(max(0.01, df_copy['Close'].dropna().iloc[-1] * 0.015))

            return float(atr_val)

        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return 1.5

    def check_volatility_filter(self, current_price: float, atr: float) -> Tuple[bool, str]:
        """Validates volatility limits to avoid low-liquidity or slippage risk."""
        if current_price <= 0:
            return False, "Invalid price (<= 0) provided for volatility check."

        min_thresh = getattr(config, 'VOLATILITY_MIN_THRESHOLD', 0.5) if config else 0.5
        max_thresh = getattr(config, 'VOLATILITY_MAX_THRESHOLD', 5.0) if config else 5.0

        atr_pct = (atr / current_price) * 100
        if atr_pct < min_thresh:
            return False, f"Volatility too low ({atr_pct:.2f}% ATR). Market rangebound."
        if atr_pct > max_thresh:
            return False, f"Volatility too high ({atr_pct:.2f}% ATR). High risk of slippage."

        return True, f"Volatility optimal ({atr_pct:.2f}% ATR)."

    def calculate_sl_tp(
        self, entry_price: float, side: str, atr: float, rr_ratio: Optional[float] = None
    ) -> Tuple[float, float]:
        """Calculates ATR-based Stop Loss and Take Profit levels."""
        if entry_price <= 0:
            return 0.01, 0.01

        ratio = rr_ratio if rr_ratio is not None else self.risk_reward_ratio
        sl_multiplier = getattr(config, 'ATR_SL_MULTIPLIER', 1.5) if config else 1.5

        sl_dist = atr * sl_multiplier
        tp_dist = sl_dist * ratio

        if side.upper() in ["BUY", "LONG"]:
            stop_loss = max(0.01, round(entry_price - sl_dist, 2))
            take_profit = max(0.01, round(entry_price + tp_dist, 2))
        else:
            stop_loss = max(0.01, round(entry_price + sl_dist, 2))
            take_profit = max(0.01, round(entry_price - tp_dist, 2))

        return stop_loss, take_profit

    def calculate_position_size(
        self, entry_price: float, stop_loss: float, confidence_score: float = 100.0
    ) -> int:
        """Calculates optimal share count based on risk parameters."""
        try:
            risk_per_share = abs(entry_price - stop_loss)
            if risk_per_share <= 0:
                return 1

            base_risk_dollars = self.account_balance * (self.risk_per_trade_pct / 100.0)
            confidence_weight = max(0.5, min(1.0, confidence_score / 100.0))
            adjusted_risk_dollars = base_risk_dollars * confidence_weight

            qty = int(adjusted_risk_dollars / risk_per_share)
            return max(1, qty)
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 1

    def evaluate_trade_risk(
        self,
        ticker: str,
        side: str,
        entry_price: float,
        df: pd.DataFrame,
        active_positions_count: int,
        daily_pnl: float,
        ai_confidence: float = 80.0
    ) -> Dict[str, Any]:
        """Main Risk Assessment Gatekeeper Function."""
        ticker = str(ticker).upper().strip()

        if active_positions_count >= self.max_open_trades:
            return {
                "Approved": False,
                "Reason": f"Max open trades limit reached ({active_positions_count}/{self.max_open_trades})."
            }

        max_allowed_loss = -(self.account_balance * (self.max_daily_loss_pct / 100.0))
        if daily_pnl <= max_allowed_loss:
            return {
                "Approved": False,
                "Reason": f"Daily Circuit Breaker Triggered! P&L (${daily_pnl:.2f}) hit limit (${max_allowed_loss:.2f})."
            }

        atr = self.calculate_atr(df)
        vol_ok, vol_msg = self.check_volatility_filter(entry_price, atr)
        if not vol_ok:
            return {"Approved": False, "Reason": vol_msg}

        sl, tp = self.calculate_sl_tp(entry_price, side, atr)
        qty = self.calculate_position_size(entry_price, sl, ai_confidence)

        return {
            "Approved": True,
            "Reason": "Trade passed all risk validation checks.",
            "ATR": round(atr, 2),
            "StopLoss": sl,
            "TakeProfit": tp,
            "Quantity": qty,
            "RiskAmount": round(abs(entry_price - sl) * qty, 2),
            "RiskRewardRatio": f"1:{self.risk_reward_ratio}"
        }


# Singleton Instance
risk_engine = AdvancedRiskEngine()


if __name__ == "__main__":
    print("--- TESTING RISK ENGINE V2.2 ---")
    dummy_data = pd.DataFrame({"High": [130, 132, 131], "Low": [128, 129, 127], "Close": [129, 131, 128]})
    assessment = risk_engine.evaluate_trade_risk(
        ticker="NVDA", side="BUY", entry_price=128.0, df=dummy_data, active_positions_count=1, daily_pnl=50.0
    )
    print(f"Risk Approval: {assessment['Approved']} | Reason: {assessment['Reason']}")
