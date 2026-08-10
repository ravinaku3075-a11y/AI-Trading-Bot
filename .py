[1mdiff --git a/paper_analytics.py b/paper_analytics.py[m
[1mindex 41ae622..a5a3a5f 100644[m
[1m--- a/paper_analytics.py[m
[1m+++ b/paper_analytics.py[m
[36m@@ -1,51 +1,71 @@[m
 import sqlite3[m
[31m-from datetime import datetime, timezone[m
[31m-[m
[31m-def get_daily_closed_trade_metrics(conn, target_date_utc=None):[m
[31m-    if not target_date_utc:[m
[31m-        target_date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")[m
 [m
[32m+[m[32mdef get_enhanced_paper_analytics(conn):[m
     cursor = conn.cursor()[m
[31m-    # Query closed trades for the specified UTC date[m
     cursor.execute("""[m
[31m-        SELECT price, quantity, action, status [m
[32m+[m[32m        SELECT symbol, action, price, quantity, status, timestamp[m[41m [m
         FROM trades [m
[31m-        WHERE DATE(timestamp) = ? AND status = 'EXECUTED'[m
[31m-    """, (target_date_utc,))[m
[31m-    [m
[32m+[m[32m        WHERE status = 'EXECUTED'[m
[32m+[m[32m        ORDER BY id ASC[m
[32m+[m[32m    """)[m
     rows = cursor.fetchall()[m
[31m-    [m
[32m+[m
[32m+[m[32m    if not rows:[m
[32m+[m[32m        return {[m
[32m+[m[32m            "total_closed_trades": 0,[m
[32m+[m[32m            "winning_trades": 0,[m
[32m+[m[32m            "losing_trades": 0,[m
[32m+[m[32m            "breakeven_trades": 0,[m
[32m+[m[32m            "total_realized_pnl": 0.0,[m
[32m+[m[32m            "win_rate_pct": 0.0,[m
[32m+[m[32m            "average_win": 0.0,[m
[32m+[m[32m            "average_loss": 0.0,[m
[32m+[m[32m            "largest_win": 0.0,[m
[32m+[m[32m            "largest_loss": 0.0,[m
[32m+[m[32m            "profit_factor": "NO_LOSSES",[m
[32m+[m[32m            "max_realized_drawdown_pct": 0.0,[m
[32m+[m[32m            "max_consecutive_losses": 0,[m
[32m+[m[32m            "per_symbol_performance": {}[m
[32m+[m[32m        }[m
[32m+[m
     total_closed = len(rows)[m
[31m-    winning = 0[m
[31m-    losing = 0[m
[31m-    breakeven = 0[m
[31m-    daily_pnl = 0.0[m
[32m+[m[32m    wins = 0[m
[32m+[m[32m    losses = 0[m
[32m+[m[32m    breakevens = 0[m
[32m+[m[32m    gross_profit = 0.0[m
[32m+[m[32m    gross_loss = 0.0[m
[32m+[m[32m    total_pnl = 0.0[m
 [m
[32m+[m[32m    # Calculate metrics[m
     for row in rows:[m
[31m-        price, qty, action, status = row[m
[31m-        # Simulated PnL calculation baseline for closed records[m
[31m-        trade_pnl = price * qty if action == 'SELL' else -price * qty[m
[31m-        daily_pnl += trade_pnl[m
[31m-        [m
[31m-        if trade_pnl > 0:[m
[31m-            winning += 1[m
[31m-        elif trade_pnl < 0:[m
[31m-            losing += 1[m
[32m+[m[32m        # Simulated PnL check for executed trades[m
[32m+[m[32m        pnl = row[2] * row[3] if row[1] == 'SELL' else 0.0[m
[32m+[m[32m        total_pnl += pnl[m
[32m+[m[32m        if pnl > 0:[m
[32m+[m[32m            wins += 1[m
[32m+[m[32m            gross_profit += pnl[m
[32m+[m[32m        elif pnl < 0:[m
[32m+[m[32m            losses += 1[m
[32m+[m[32m            gross_loss += abs(pnl)[m
         else:[m
[31m-            breakeven += 1[m
[32m+[m[32m            breakevens += 1[m
 [m
[31m-    win_rate = (winning / total_closed * 100.0) if total_closed > 0 else 0.0[m
[31m-    [m
[31m-    # Safe return calculation baseline[m
[31m-    return_pct = 0.0  # Safe default when portfolio starting baseline is uninitialized[m
[32m+[m[32m    win_rate = (wins / total_closed * 100.0) if total_closed > 0 else 0.0[m
[32m+[m[32m    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else "NO_LOSSES"[m
 [m
     return {[m
[31m-        "date": target_date_utc,[m
         "total_closed_trades": total_closed,[m
[31m-        "winning_trades": winning,[m
[31m-        "losing_trades": losing,[m
[31m-        "breakeven_trades": breakeven,[m
[31m-        "daily_realized_pnl": daily_pnl,[m
[31m-        "daily_win_rate_pct": round(win_rate, 2),[m
[31m-        "daily_realized_return_pct": round(return_pct, 2)[m
[32m+[m[32m        "winning_trades": wins,[m
[32m+[m[32m        "losing_trades": losses,[m
[32m+[m[32m        "breakeven_trades": breakevens,[m
[32m+[m[32m        "total_realized_pnl": total_pnl,[m
[32m+[m[32m        "win_rate_pct": win_rate,[m
[32m+[m[32m        "average_win": (gross_profit / wins) if wins > 0 else 0.0,[m
[32m+[m[32m        "average_loss": (gross_loss / losses) if losses > 0 else 0.0,[m
[32m+[m[32m        "largest_win": gross_profit,[m
[32m+[m[32m        "largest_loss": gross_loss,[m
[32m+[m[32m        "profit_factor": profit_factor,[m
[32m+[m[32m        "max_realized_drawdown_pct": 0.0,[m
[32m+[m[32m        "max_consecutive_losses": 0,[m
[32m+[m[32m        "per_symbol_performance": {}[m
     }[m
\ No newline at end of file[m
