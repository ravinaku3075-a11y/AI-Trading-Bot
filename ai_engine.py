"""
ai_engine.py - AI Trading Analysis & Confidence Engine
Generates confidence scores and signal rationale for active assets.
"""
# Lazy loaded inside methods

class AITradingEngine:
    def __init__(self):
        pass

    def analyze_signal(self, df, ticker: str) -> dict:
        """
        Analyzes recent price action and SMA levels to generate signal,
        confidence score, and trade rationale.
        """
        import pandas as pd
        import numpy as np
        if len(df) < 20:
            return {
                "Signal": "NEUTRAL",
                "Confidence": 50,
                "Reasoning": "Insufficient data points for AI quantitative analysis."
            }

        data = df.copy()
        data['SMA_5'] = data['Close'].rolling(5).mean()
        data['SMA_20'] = data['Close'].rolling(20).mean()

        latest_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        latest_sma5 = data['SMA_5'].iloc[-1]
        latest_sma20 = data['SMA_20'].iloc[-1]

        # Momentum calculation
        pct_change = ((latest_close - prev_close) / prev_close) * 100
        volatility = data['Close'].pct_change().std() * 100

        # Signal Rules & Confidence Scoring
        if latest_sma5 > latest_sma20 and latest_close > latest_sma5:
            signal = "STRONG BUY"
            base_score = 75
            momentum_bonus = min(15, max(0, pct_change * 5))
            vol_penalty = min(10, volatility)
            confidence = min(95, int(base_score + momentum_bonus - vol_penalty))
            reasoning = (
                f"Bullish alignment detected for {ticker}. Fast SMA (5) is trading above Slow SMA (20), "
                f"with price breaking out above short-term momentum levels (+{pct_change:.2f}% shift)."
            )
        elif latest_sma5 < latest_sma20 and latest_close < latest_sma5:
            signal = "STRONG SELL"
            base_score = 75
            momentum_bonus = min(15, max(0, abs(pct_change) * 5))
            vol_penalty = min(10, volatility)
            confidence = min(95, int(base_score + momentum_bonus - vol_penalty))
            reasoning = (
                f"Bearish breakdown detected for {ticker}. Fast SMA (5) has crossed below Slow SMA (20), "
                f"accompanied by downward price momentum ({pct_change:.2f}% shift)."
            )
        else:
            signal = "HOLD / NEUTRAL"
            confidence = 50
            reasoning = (
                f"Consolidation pattern for {ticker}. Fast and Slow moving averages are converging "
                f"without a clear directional trend break."
            )

        return {
            "Ticker": ticker,
            "Signal": signal,
            "Confidence": confidence,
            "Reasoning": reasoning,
            "Volatility_Risk": round(volatility, 2)
        }

ai_analyzer = AITradingEngine()

