"""
Logger & Journaling Utility Module for AI Trading Assistant.

Manages automated CSV trade journaling and persistent execution logging.
"""

import os
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any

LOG_FILE = "trading_bot.log"
JOURNAL_FILE = "trade_journal.csv"

def setup_persistent_logging() -> None:
    """Configures file and console logging outputs."""
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

def save_to_journal(results: List[Dict[str, Any]]) -> None:
    """
    Saves scanner results into a persistent CSV trade journal file.
    """
    file_exists = os.path.isfile(JOURNAL_FILE)
    fieldnames = ["timestamp", "ticker", "price", "trend", "signal", "viable", "win_rate", "pattern"]

    try:
        with open(JOURNAL_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for row in results:
                writer.writerow({
                    "timestamp": now_str,
                    "ticker": row.get("ticker", ""),
                    "price": row.get("price", 0.0),
                    "trend": row.get("trend", ""),
                    "signal": row.get("signal", ""),
                    "viable": row.get("viable", ""),
                    "win_rate": row.get("win_rate", ""),
                    "pattern": row.get("pattern", "")
                })
        print(f"\n[Journal] Scan results appended to '{JOURNAL_FILE}'.")
    except Exception as e:
        print(f"\n[Journal Error] Failed to write journal: {e}")
