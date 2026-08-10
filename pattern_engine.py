import pandas as pd
import numpy as np

class TechnicalPatternEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def calculate_indicators(self):
        """
        Calculates RSI, MACD, Moving Averages (EMA), and Bollinger Bands.
        """
        df = self.df

        # Ensure single level columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']

        # 1. Exponential Moving Averages (EMA)
        df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
        df['EMA_50'] = close.ewm(span=50, adjust=False).mean()

        # 2. RSI (14 period)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 3. MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # 4. Bollinger Bands
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        df['BB_Upper'] = sma_20 + (std_20 * 2)
        df['BB_Lower'] = sma_20 - (std_20 * 2)

        self.df = df
        return df

    def detect_patterns(self):
        """
        Detects technical signals like Bullish Crossover, Overbought/Oversold RSI, etc.
        """
        if 'RSI' not in self.df.columns:
            self.calculate_indicators()

        df = self.df
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        patterns = []

        # RSI Checks
        if latest['RSI'] > 70:
            patterns.append(f"⚠️ RSI Overbought ({latest['RSI']:.1f}) - Pullback Risk")
        elif latest['RSI'] < 30:
            patterns.append(f"🟢 RSI Oversold ({latest['RSI']:.1f}) - Potential Reversal Buy")
        else:
            patterns.append(f"ℹ️ RSI Neutral ({latest['RSI']:.1f})")

        # EMA Crossover
        if prev['EMA_20'] <= prev['EMA_50'] and latest['EMA_20'] > latest['EMA_50']:
            patterns.append("🚀 Bullish Golden Crossover (20-EMA crossed above 50-EMA)")
        elif prev['EMA_20'] >= prev['EMA_50'] and latest['EMA_20'] < latest['EMA_50']:
            patterns.append("🔻 Bearish Death Crossover (20-EMA crossed below 50-EMA)")

        # Bollinger Band Breakouts
        if latest['Close'] > latest['BB_Upper']:
            patterns.append("🔥 Upper Bollinger Band Breakout (Strong Momentum)")
        elif latest['Close'] < latest['BB_Lower']:
            patterns.append("❄️ Lower Bollinger Band Breakdown")

        return patterns


if __name__ == "__main__":
    print("Technical Pattern Engine initialized successfully.")
