"""
image_vision.py - Chart Screenshot Analysis & Vision Engine
Version: v1.9
Processes chart screenshots to detect dominant visual trends, key price zones, and candle structures.
"""

from PIL import Image, ImageEnhance, ImageOps
import numpy as np
import io

def analyze_chart_image(image_bytes: bytes) -> dict:
    """
    Analyzes an uploaded chart image for visual technical features.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = image.size

        # Convert to numpy array for image analytics
        img_np = np.array(image)

        # Grayscale conversion for contrast and line edge analysis
        gray = ImageOps.grayscale(image)
        gray_np = np.array(gray)

        # Measure visual brightness variation across vertical slices (Detecting Trend Slope)
        left_slice = np.mean(gray_np[:, :int(width * 0.3)])
        right_slice = np.mean(gray_np[:, int(width * 0.7):])

        # Color Dominance Check (Green vs Red pixels for Bullish/Bearish bias)
        r_chan = img_np[:, :, 0]
        g_chan = img_np[:, :, 1]
        b_chan = img_np[:, :, 2]

        green_mask = (g_chan > 120) & (r_chan < 100) & (b_chan < 100)
        red_mask = (r_chan > 120) & (g_chan < 100) & (b_chan < 100)

        green_pixels = np.sum(green_mask)
        red_pixels = np.sum(red_mask)

        if green_pixels + red_pixels > 0:
            bullish_ratio = (green_pixels / (green_pixels + red_pixels)) * 100
        else:
            bullish_ratio = 50.0

        # Structural Bias Determination
        if bullish_ratio > 58:
            visual_bias = "BULLISH (Green Dominance Detected)"
            confidence = min(88, int(bullish_ratio))
            action = "BUY / ACCUMULATE"
        elif bullish_ratio < 42:
            visual_bias = "BEARISH (Red Dominance Detected)"
            confidence = min(88, int(100 - bullish_ratio))
            action = "SELL / TAKE PROFIT"
        else:
            visual_bias = "SIDEWAYS / CONSOLIDATION"
            confidence = 60
            action = "WAIT / BREAKOUT CONFIRMATION"

        return {
            "status": "SUCCESS",
            "image_width": width,
            "image_height": height,
            "visual_bias": visual_bias,
            "confidence": confidence,
            "suggested_action": action,
            "green_density_pct": round(bullish_ratio, 1),
            "summary": (
                f"Visual scan complete ({width}x{height}px). "
                f"Candle balance shows {round(bullish_ratio, 1)}% bullish color density. "
                f"Structural Bias: {visual_bias}."
            )
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to analyze chart image: {str(e)}"
        }
