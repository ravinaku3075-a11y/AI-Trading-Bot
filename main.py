"""
main.py - Technical Indicator Based Strategy Loop
"""
import time
import random
from broker_api import broker
import config

# Simple Moving Average (SMA) tracking window
price_history = {ticker: [150.0] * 5 for ticker in config.WATCHLIST}

def get_sma(ticker: str) -> float:
    prices = price_history[ticker]
    return sum(prices) / len(prices)

def run_trading_bot():
    print("🚀 Starting Technical Strategy Bot Loop...")
    print(f"Paper Trading Mode: {config.PAPER_TRADING_MODE}")
    print("Press Ctrl+C to stop the bot anytime.\n")

    while True:
        try:
            ticker = random.choice(config.WATCHLIST)

            # Simulated current market price calculation
            last_price = price_history[ticker][-1]
            change = random.uniform(-3.0, 3.0)
            current_price = round(max(10.0, last_price + change), 2)

            # History update
            price_history[ticker].append(current_price)
            price_history[ticker].pop(0)

            sma = round(get_sma(ticker), 2)

            # Technical Strategy Logic (SMA Crossover)
            if current_price > sma:
                action = "BUY"
                reason = f"Price (${current_price}) > SMA (${sma})"
            else:
                action = "SELL"
                reason = f"Price (${current_price}) <= SMA (${sma})"

            print(f"[SMA Strategy] {ticker}: {reason} -> Signal: {action}")

            # Order Execution
            broker.execute_order(ticker=ticker, action=action, price=current_price, quantity=1)

            print("⏳ Waiting 15 seconds for next check...\n")
            time.sleep(15)

        except KeyboardInterrupt:
            print("\n🛑 Trading Bot Stopped by User.")
            break
        except Exception as e:
            print(f"❌ Error in trading loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_trading_bot()
