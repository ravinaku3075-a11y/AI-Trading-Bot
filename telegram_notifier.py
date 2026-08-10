"""
telegram_notifier.py - Telegram Alert System
Version: 2.2 (Hardened & Audit Validated)
Sends formatted trade notifications and exit alerts to Telegram channel/chat.
"""

import os
import re
import logging
import requests

# Try loading config securely
try:
    import config
except ImportError:
    config = None

# Logging Setup (Console + File Handler)
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_notifier.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] TelegramNotifier: %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TelegramNotifier")


def escape_markdown(text: str) -> str:
    """Escapes Telegram Markdown special characters to prevent API parsing crashes."""
    if not text:
        return ""
    # Characters that corrupt Markdown formatting if unescaped in text mode
    escape_chars = r'_*[`'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))


class TelegramNotifier:
    def __init__(self):
        self.bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', '') if config else ''
        self.chat_id = getattr(config, 'TELEGRAM_CHAT_ID', '') if config else ''
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message: str) -> bool:
        """Core delivery method with error handling and timeout protection."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Bot token or Chat ID missing in config.py. Skipping Telegram alert.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            res_data = response.json()

            if response.status_code == 200 and res_data.get("ok"):
                logger.info("Telegram message delivered successfully.")
                return True
            else:
                logger.error(f"Telegram API Error response: {res_data}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Telegram API request timed out (5s limit).")
            return False
        except Exception as e:
            logger.exception(f"Failed to send Telegram message: {e}")
            return False

    def send_trade_alert(self, action: str, ticker: str, price: float, quantity: float = 1.0) -> bool:
        """Sends basic formatted trade notification."""
        action_clean = action.upper()
        emoji = "🟢" if action_clean == "BUY" else "🔴"

        message = (
            f"{emoji} *TRADE ALERT: {action_clean}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"• *Asset:* {escape_markdown(ticker)}\n"
            f"• *Price:* ${price:.2f}\n"
            f"• *Quantity:* {quantity}\n"
            f"• *Status:* Executed"
        )
        return self.send_message(message)


# Singleton Instance
telegram_notifier = TelegramNotifier()


# --- MODULE LEVEL WRAPPERS FOR PAPER TRADING ENGINE ---

def send_trade_open_alert(ticker: str, action: str, price: float, sl: float, tp: float, strategy: str, timestamp: str) -> bool:
    """Wrapper used by Paper Trading Engine on position opening."""
    action_clean = action.upper()
    emoji = "🟢" if action_clean == "BUY" else "🔴"

    message = (
        f"{emoji} *PAPER TRADE OPENED: {action_clean}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• *Asset:* {escape_markdown(ticker)}\n"
        f"• *Entry Price:* ${price:.2f}\n"
        f"• *Stop Loss:* ${sl:.2f}\n"
        f"• *Take Profit:* ${tp:.2f}\n"
        f"• *Strategy:* {escape_markdown(strategy)}\n"
        f"• *Time:* {timestamp}"
    )
    return telegram_notifier.send_message(message)


def send_trade_closed_alert(ticker: str, result_reason: str, profit: float, portfolio_val: float, win_rate: float) -> bool:
    """Wrapper used by Paper Trading Engine on position closing."""
    pnl_emoji = "🎉 🚀" if profit >= 0 else "🛑 📉"
    pnl_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"

    message = (
        f"{pnl_emoji} *TRADE CLOSED: {escape_markdown(ticker)}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• *Reason:* {escape_markdown(result_reason)}\n"
        f"• *Trade PnL:* {pnl_str}\n"
        f"• *Portfolio Value:* ${portfolio_val:.2f}\n"
        f"• *Win Rate:* {win_rate}%"
    )
    return telegram_notifier.send_message(message)


if __name__ == "__main__":
    print("--- TESTING TELEGRAM NOTIFIER V2.2 ---")
    res = telegram_notifier.send_trade_alert("BUY", "NVDA", 125.50, quantity=2)
    print(f"Delivery Status: {res}")
