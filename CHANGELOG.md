# Changelog

## [1.2.0] - Persistent Logging, Level Integration & Responsive Layout

### Added
- Integrated `logger_utils.py` for automated `trade_journal.csv` generation and persistent file logging (`trading_bot.log`).
- Hooked dynamic Support and Resistance level calculation (`levels.py`) into main execution pipeline.

### Refactored
- Synchronized SL/TP risk parameters into backtest evaluation engine (`backtest.py`).
- Auto-aligned terminal table output in `main.py` (62-character width boundary) to eliminate text wrapping across narrow CLI panes.