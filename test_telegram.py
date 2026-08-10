"""
test_telegram.py - Quick Test Script for Telegram Bot Integration
Version: v2.0
"""

import requests
import config

def test_telegram_connection():
    bot_token = str(config.TELEGRAM_BOT_TOKEN).strip()
    chat_id = str(config.TELEGRAM_CHAT_ID).strip()

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": "🚀 *AI Trading Bot Status*\n\nTelegram Alert Gateway successfully connected to v2.0 Dashboard!",
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ Success! Check your Telegram app for the test message.")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"⚠️ Exception: {str(e)}")

if __name__ == "__main__":
    test_telegram_connection()
