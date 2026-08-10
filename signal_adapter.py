import datetime

def normalize_signal(raw_signal):
    if not isinstance(raw_signal, dict):
        return {
            "symbol": "UNKNOWN",
            "action": "HOLD",
            "price": None,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reason": "Invalid signal format",
            "confidence": 0.0,
            "confirmations": []
        }

    symbol = raw_signal.get("symbol", "UNKNOWN")
    action = str(raw_signal.get("action", "HOLD")).upper()
    price = raw_signal.get("price")
    reason = raw_signal.get("reason", "No reason provided")
    confidence = float(raw_signal.get("confidence", 0.0))
    confirmations = raw_signal.get("confirmations", [])

    if action not in ["BUY", "SELL", "HOLD"]:
        action = "HOLD"

    if action in ["BUY", "SELL"]:
        if price is None or not isinstance(price, (int, float)) or price <= 0:
            action = "HOLD"
            price = None

    if action == "HOLD":
        price = None

    return {
        "symbol": symbol,
        "action": action,
        "price": price,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reason": reason,
        "confidence": max(0.0, min(100.0, confidence)),
        "confirmations": confirmations if isinstance(confirmations, list) else []
    }