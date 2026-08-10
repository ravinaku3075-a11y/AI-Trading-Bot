# Professional AI Trading Assistant

A modular, educational AI-driven trading decision-support platform in Python.

## Core Capabilities
- Market Data Fetching (`yfinance`)
- Technical Indicators (RSI, SMA, EMA)
- Swing Point & Trend Analysis
- Support & Resistance Clustering
- Strategy Signal Generation (`BUY`, `SELL`, `WAIT`)
- Dynamic Risk Management & Position Sizing
- Historical Backtesting Engine (Win Rate, Total PnL, Portfolio simulation)

## Project Structure
- `main.py`: Entry point, live signal report, and backtest runner.
- `data.py`: Market data retrieval logic.
- `indicators.py`: Technical indicator calculations.
- `trend.py`: Swing high/low and trend detection.
- `levels.py`: Support/Resistance identification.
- `strategy.py`: Multi-condition signal evaluation.
- `risk.py`: Stop loss, take profit, position sizing, and R:R checks.
- `backtest.py`: Historical simulation engine over historical price action.