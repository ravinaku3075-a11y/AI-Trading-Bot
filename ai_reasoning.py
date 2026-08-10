"""
ai_reasoning.py - Technical Signal Reasoning Engine
Version: v1.5
Generates human-readable "Why BUY / Why SELL" explanations based on technical indicators.
"""

def generate_trade_explanation(ticker: str, signal: str, price: float, strategy: str, indicator_data: dict) -> str:
    """
    Generates a concise, structured explanation for a trade signal.
    """
    if signal == "HOLD" or not signal:
        return f"No clear trade setup detected for {ticker}. Indicators remain in neutral zone."

    rsi = indicator_data.get("rsi", 50.0)
    sma_20 = indicator_data.get("sma_20", price)
    sma_50 = indicator_data.get("sma_50", price)
    volume_trend = indicator_data.get("volume_trend", "Normal")

    reasons = []

    if signal == "BUY":
        if rsi < 35:
            reasons.append(f"RSI is oversold ({rsi:.1f}), signaling potential bullish reversal")
        elif rsi < 55:
            reasons.append(f"RSI ({rsi:.1f}) shows healthy upward momentum")

        if price > sma_20:
            reasons.append(f"Price (${price:.2f}) trading above 20 SMA (${sma_20:.2f}), confirming uptrend")

        if sma_20 > sma_50:
            reasons.append(f"20 SMA is above 50 SMA (Bullish Crossover Alignment)")

        if volume_trend == "High":
            reasons.append("Higher volume supports institutional buying interest")

        if not reasons:
            reasons.append(f"{strategy} pattern alignment triggered a high-probability entry")

        explanation = f"🟢 **WHY BUY {ticker}?**\n" + "\n".join([f"• {r}" for r in reasons])

    elif signal == "SELL":
        if rsi > 65:
            reasons.append(f"RSI is overbought ({rsi:.1f}), signaling exhaustion")
        elif rsi > 45:
            reasons.append(f"RSI ({rsi:.1f}) shows weakening momentum")

        if price < sma_20:
            reasons.append(f"Price (${price:.2f}) trading below 20 SMA (${sma_20:.2f}), confirming downtrend")

        if sma_20 < sma_50:
            reasons.append(f"20 SMA is below 50 SMA (Bearish Crossover Alignment)")

        if not reasons:
            reasons.append(f"{strategy} strategy condition met profit-taking / risk exit criteria")

        explanation = f"🔴 **WHY SELL {ticker}?**\n" + "\n".join([f"• {r}" for r in reasons])

    return explanation
