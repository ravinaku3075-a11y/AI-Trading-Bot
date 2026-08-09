import streamlit as st
import yfinance as yf
import pandas as pd

def calculate_market_sentiment_score(symbol: str):
    """
    Fetches real-time market data via yfinance, calculates market sentiment score.
    """
    try:
        symbol = symbol.strip().upper()
        # Fixed period from '3m' to valid yfinance parameter '3mo'
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)

        if df.empty:
            return {"error": f"'{symbol}' ke liye koi data nahi mila. Symbol sahi check karein."}

        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        if len(close) < 20:
            return {"error": "Technical analysis ke liye kam se kam 20 din ka data zaruri hai."}

        last_price = float(close.iloc[-1])

        # 1. Moving Averages
        ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])

        # 2. RSI Calculation (14-period)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        # Sentiment Score Calculation
        sentiment_score = 0

        # Price vs EMA 20
        if last_price > ema_20:
            sentiment_score += 15
        else:
            sentiment_score -= 15

        # EMA Crossover
        if ema_20 > ema_50:
            sentiment_score += 20
        else:
            sentiment_score -= 20

        # RSI Evaluation
        if 45 <= rsi <= 65:
            sentiment_score += 15
        elif rsi < 35:
            sentiment_score += 10
        elif rsi > 70:
            sentiment_score -= 15

        # Bound score between 10% and 95%
        sentiment_score = max(10, min(95, sentiment_score))

        return {
            "symbol": symbol,
            "sentiment_score": f"{sentiment_score}%",
            "last_price": f"₹{last_price:.2f}",
            "ema_20": f"₹{ema_20:.2f}",
            "ema_50": f"₹{ema_50:.2f}",
            "rsi": f"{rsi:.1f}"
        }

    except Exception as e:
        return {"error": f"AI Reasoning processing error: {str(e)}"}


def main():
    st.title("AI Reasoning Engine")
    symbol = st.text_input("Enter stock symbol (e.g. RELIANCE.NS):")
    if st.button("Generate AI Reasoning"):
        result = generate_ai_reasoning(symbol)
        if "error" in result:
            st.error(result["error"])
        else:
            st.write(f"**{result['symbol']}**")
            st.write(f"**Action:** {result['action']} ({result['color']})")
            st.write(f"**Confidence:** {result['confidence']}")
            st.write(f"**Last Price:** {result['last_price']}")
            st.write(f"**Reasons:**")
            for reason in result['reasons']:
                st.write(reason)

    if st.button("Check Price Break"):
        result = check_price_break(symbol)
        if "error" in result:
            st.error(result["error"])
        else:
            st.write(f"**{result['symbol']}**")
            st.write(f"**Alert:** {result['alert']}")

    if st.button("Calculate Market Sentiment Score"):
        result = calculate_market_sentiment_score(symbol)
        if "error" in result:
            st.error(result["error"])
        else:
            st.write(f"**{result['symbol']}**")
            st.write(f"**Sentiment Score:** {result['sentiment_score']}")
            st.write(f"**Last Price:** {result['last_price']}")
            st.write(f"**20-day EMA:** {result['ema_20']}")
            st.write(f"**50-day EMA:** {result['ema_50']}")
            st.write(f"**RSI:** {result['rsi']}")

if __name__ == "__main__":
    main()

# portfolio_viewer.py
import streamlit as st
import yfinance as yf
import pandas as pd

def display_sentiment_score(symbol: str):
    """
    Fetches real-time market data via yfinance, displays market sentiment score.
    """
    try:
        symbol = symbol.strip().upper()
        # Fixed period from '3m' to valid yfinance parameter '3mo'
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)

        if df.empty:
            return {"error": f"'{symbol}' ke liye koi data nahi mila. Symbol sahi check karein."}

        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        if len(close) < 20:
            return {"error": "Technical analysis ke liye kam se kam 20 din ka data zaruri hai."}

        last_price = float(close.iloc[-1])

        # 1. Moving Averages
        ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])

        # 2. RSI Calculation (14-period)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        # Sentiment Score Calculation
        sentiment_score = 0

        # Price vs EMA 20
        if last_price > ema_20:
            sentiment_score += 15
        else:
            sentiment_score -= 15

        # EMA Crossover
        if ema_20 > ema_50:
            sentiment_score += 20
        else:
            sentiment_score -= 20

        # RSI Evaluation
        if 45 <= rsi <= 65:
            sentiment_score += 15
        elif rsi < 35:
            sentiment_score += 10
        elif rsi > 70:
            sentiment_score -= 15

        # Bound score between 10% and 95%
        sentiment_score = max(10, min(95, sentiment_score))

        return {
            "symbol": symbol,
            "sentiment_score": f"{sentiment_score}%",
            "last_price": f"₹{last_price:.2f}",
            "ema_20": f"₹{ema_20:.2f}",
            "ema_50": f"₹{ema_50:.2f}",
            "rsi": f"{rsi:.1f}"
        }

    except Exception as e:
        return {"error": f"AI Reasoning processing error: {str(e)}"}


def main():
    st.title("Portfolio Viewer")
    symbol = st.text_input("Enter stock symbol (e.g. RELIANCE.NS):")
    if st.button("Display Sentiment Score"):
        result = display_sentiment_score(symbol)
        if "error" in result:
            st.error(result["error"])
        else:
            st.write(f"**{result['symbol']}**")
            st.write(f"**Sentiment Score:** {result['sentiment_score']}")
            st.write(f"**Last Price:** {result['last_price']}")
            st.write(f"**20-day EMA:** {result['ema_20']}")
            st.write(f"**50-day EMA:** {result['ema_50']}")
            st.write(f"**RSI:** {result['rsi']}")

if __name__ == "__main__":
    main()

# Autonomous Smart Patch
def check_price_break_alert(symbol: str, price: float, support: float, resistance: float) -> dict:
    """Analyzes support and resistance breakout for reasoning_engine.py"""
    if price >= resistance:
        return {'alert': 'RESISTANCE_BREAKOUT', 'symbol': symbol, 'price': price}
    elif price <= support:
        return {'alert': 'SUPPORT_BREAKDOWN', 'symbol': symbol, 'price': price}
    return {'alert': 'RANGE_BOUND', 'symbol': symbol, 'price': price}
