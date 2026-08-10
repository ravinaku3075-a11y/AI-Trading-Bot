"""
Telegram Notification Engine for AI Trading Assistant (v1.2).

Features:
- Modular, fail-safe architecture (network errors won't crash main analysis).
- Config-based enable/disable toggle.
- Dynamic filtering to suppress false/low-confidence signals and HOLD states.
"""

import logging
from typing import List, Dict, Any
import requests

import config

logger = logging.getLogger("TelegramBot")


def send_telegram_message(message: str) -> bool:
    """
    Sends a formatted message to Telegram via API.
    Uses non-blocking try-except to ensure trading bot never crashes on network failure.
    """
    # 1. Check toggle switch from config
    if not getattr(config, "ENABLE_TELEGRAM", False):
        logger.info("Telegram notifications are currently disabled in config.py.")
        return False

    bot_token = getattr(config, "TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = getattr(config, "TELEGRAM_CHAT_ID", "").strip()

    # 2. Check credentials
    if not bot_token or not chat_id:
        logger.warning("Telegram is enabled, but BOT_TOKEN or CHAT_ID is missing in config.py.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    # 3. Fail-safe API Request
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info("Telegram alert broadcasted successfully.")
            return True
        else:
            logger.error(f"Telegram API HTTP Error ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        # Non-blocking catch: logs error silently without stopping main.py
        logger.error(f"Telegram connection failed: {e}. Bot will continue scanning uninterrupted.")
        return False


def format_high_confidence_alerts(scanner_results: List[Dict[str, Any]], active_strategy: str) -> str:
    """
    Filters scanner results and formats ONLY high-confidence BUY/SELL signals.
    Prevents notification spam on low-confidence or HOLD setups.
    """
    min_conf = getattr(config, "MIN_ALERT_CONFIDENCE", 60)

    filtered_signals = []
    for r in scanner_results:
        # Extract numerical score from "XX%" string safely
        conf_str = str(r.get("conf", "0")).replace("%", "").strip()
        try:
            raw_conf = int(conf_str)
        except ValueError:
            raw_conf = 0

        # Only pass valid BUY/SELL that cross the confidence threshold
        if r.get("signal") in ["BUY", "SELL"] and raw_conf >= min_conf:
            filtered_signals.append((r, raw_conf))

    if not filtered_signals:
        return ""  # Empty string triggers no dispatch

    msg = f"🚨 *HIGH CONFIDENCE TRADE ALERT*\n"
    msg += f"🎯 *Strategy:* `{active_strategy}` | *Min Threshold:* `{min_conf}%`\n"
    msg += "----------------------------------------\n\n"

    for row, conf_val in filtered_signals:
        msg += f"🔹 *Ticker:* `{row['ticker']}` | *Signal:* `{row['signal']}` | *Conf:* `{conf_val}%`\n"
        msg += f"  • Current Price: `${row['price']:.2f}`\n"
        msg += f"  • Viable: `{row['viable']}` | Backtest WinRate: `{row['win_rate']}`\n"
        msg += f"  • Support: `{row['support']}` | Resistance: `{row['resistance']}`\n"
        msg += f"  • Pattern: `{row['pattern']}`\n\n"

    return msg
