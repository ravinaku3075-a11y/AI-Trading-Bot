import time
import logging
from paper_trading import PaperTradingEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_once():
    """Ek single iteration/tick execution ke liye."""
    try:
        # PaperTradingEngine apne andar risk controls automatic handle karta hai
        engine = PaperTradingEngine()
        logging.info("Checking market tick & executing paper strategy...")
        if hasattr(engine, 'process_market_tick'):
            engine.process_market_tick()
        elif hasattr(engine, 'run_tick'):
            engine.run_tick()
        else:
            logging.info("Paper engine is active and ready.")
    except Exception as e:
        logging.error(f"Error in worker iteration: {e}")

def run_forever(poll_interval=60):
    """24/7 background continuous loop execution."""
    logging.info(f"Starting 24/7 Paper Trading Worker (Poll Interval: {poll_interval}s)...")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logging.info("Worker stopped manually.")
            break
        except Exception as e:
            logging.error(f"Unexpected loop error: {e}")
        time.sleep(poll_interval)

if __name__ == "__main__":
    run_forever()