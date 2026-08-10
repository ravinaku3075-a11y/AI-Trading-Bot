"""
config.py - Centralized Configuration Management
"""

# General Terminal & Broker Config
APP_TITLE = "Pro-Trade AI Trading Terminal"
APP_ICON = "⚡"
PAPER_TRADING_MODE = True
WATCHLIST = ["NVDA", "AAPL", "MSFT", "TSLA", "AMD"]

# Advanced Risk Engine Configurations
ACCOUNT_BALANCE = 10000.0          # Starting Account Capital ($)
DEFAULT_RISK_PER_TRADE_PCT = 1.0  # Risk 1.0% per trade
RISK_REWARD_RATIO = 2.0           # Default 1:2 R:R Ratio

# ATR Volatility Parameters
ATR_PERIOD = 14                   # Rolling ATR Window
ATR_SL_MULTIPLIER = 1.5           # SL = Entry - (ATR * 1.5)

# Portfolio Circuit Breakers
MAX_DAILY_LOSS_PCT = 3.0          # Halt if daily loss >= 3%
MAX_OPEN_TRADES = 3               # Max active positions

# Volatility Filter Thresholds
VOLATILITY_MIN_THRESHOLD = 0.5
VOLATILITY_MAX_THRESHOLD = 5.0

# AI & Pattern Thresholds
AI_CONFIDENCE_THRESHOLD_HIGH = 75.0
AI_CONFIDENCE_THRESHOLD_MEDIUM = 50.0

# UI Theme Colors
THEME_BG_DARK = "#0E1117"
THEME_SIDEBAR_BG = "#131722"
THEME_CARD_BG = "#1E222D"
THEME_ACCENT_CYAN = "#00F0FF"
THEME_ACCENT_GREEN = "#00FF88"
THEME_ACCENT_RED = "#FF4B4B"
THEME_BORDER_COLOR = "#2A2E39"
