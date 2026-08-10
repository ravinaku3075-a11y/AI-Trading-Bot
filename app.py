import streamlit as st
import importlib
import time
import os
import gc
from datetime import datetime

# Core Modules Import
import auto_coder
import code_review_engine
import performance_optimizer
import security_scanner
import auto_testing_engine
import self_improvement_engine
import ai_architect_engine
import project_manager
import ai_supervisor

# Dynamic Import Handling for Autonomous Developer
try:
    import agent_developer
    importlib.reload(agent_developer)
except Exception:
    agent_developer = None

# Dynamic Reloading
importlib.reload(auto_coder)
importlib.reload(project_manager)
importlib.reload(self_improvement_engine)
importlib.reload(ai_architect_engine)
importlib.reload(ai_supervisor)

st.set_page_config(
    page_title="AI Trading & Desktop Assistant v2.5",
    page_icon="⚡",
    layout="wide"
)

# Safe Dynamic Imports
import portfolio_viewer
import backtesting_engine
import reasoning_engine
import voice_assistant
import sqlite_logger

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def sanitize_user_input(prompt: str) -> str:
    if not prompt:
        return ""
    clean_text = prompt.replace("<script>", "").replace("</script>", "").strip()
    return clean_text[:500]

def get_yfinance():
    import yfinance as yf
    return yf

def get_pandas():
    import pandas as pd
    return pd

def get_requests():
    import requests
    return requests

def render_interactive_candlestick(symbol: str):
    try:
        import plotly.graph_objects as go
        yf = get_yfinance()
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        
        if df.empty:
            st.warning(f"No chart data found for {symbol}")
            return

        pd = get_pandas()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        )])
        
        fig.update_layout(
            title=f"📊 Interactive Candlestick Chart: {symbol}",
            yaxis_title="Stock Price (₹)",
            xaxis_title="Date",
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Chart Render Error: {str(e)}")

try:
    import pattern_engine
    TechnicalPatternEngine = getattr(pattern_engine, 'TechnicalPatternEngine', None)
except Exception:
    TechnicalPatternEngine = None

# Sidebar Navigation
st.sidebar.title("🎮 Terminal Navigation")
tab_choice = st.sidebar.radio(
    "Select Interface Tab:",
    [
        "Dashboard", 
        "⚡ Autonomous AI Developer v3",
        "🕵️ AI Supervisor",
        "👑 AI Project Manager",
        "🤖 AI Auto-Coder", 
        "🧐 AI Code Review", 
        "⚡ Performance Optimizer", 
        "🛡️ Security Scanner",
        "🧪 AI Auto Testing",
        "🧠 AI Self Improvement",
        "🏗️ AI Architect",
        "Pattern Engine", 
        "Portfolio Viewer", 
        "Backtester", 
        "Telegram Notifier", 
        "AI Reasoning"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("⚡ Groq AI Engine")

if GROQ_API_KEY:
    st.sidebar.success("🟢 Groq AI API: Connected Safely")
else:
    st.sidebar.warning("⚠️ Groq API Key Missing in Environment")

# ---------------------------------------------------------
# INTENT ROUTER & AI LOGIC
# ---------------------------------------------------------
def detect_intent_and_respond(prompt: str) -> dict:
    text = prompt.strip()
    words = text.upper().split()
    lower_text = text.lower()

    stock_tickers = ["RELIANCE", "TCS", "INFY", "NVDA", "AAPL", "TSLA", "TATAMOTORS", "HDFCBANK"]
    has_ticker = any(".NS" in w or w in stock_tickers for w in words)
    ticker_found = "RELIANCE.NS"
    for w in words:
        if ".NS" in w or w in stock_tickers:
            ticker_found = w if ".NS" in w or w in ["NVDA", "AAPL", "TSLA"] else f"{w}.NS"
            break

    if ("BUY" in words or "SELL" in words or "KHAREEDO" in words or "BECHO" in words) and has_ticker:
        return {"intent": "EXECUTION", "symbol": ticker_found, "raw": text}

    if any(k in lower_text for k in ["portfolio", "holdings", "mere trades", "pnl"]):
        return {"intent": "PORTFOLIO", "raw": text}

    if any(k in lower_text for k in ["backtest", "strategy test", "historical performance"]):
        return {"intent": "BACKTEST", "symbol": ticker_found, "raw": text}

    if has_ticker or any(k in lower_text for k in ["analysis", "chart", "technical", "target", "stoploss", "rsi", "macd"]):
        return {"intent": "TRADING_ANALYSIS", "symbol": ticker_found, "raw": text}

    return {"intent": "GENERAL_CHAT", "raw": text}

def get_general_chat_response(prompt: str) -> str:
    req = get_requests()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are an AI Personal Desktop Assistant for Ravi. Answer in simple, friendly Hindi/Hinglish in 2-3 short sentences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        res = req.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
        return f"Groq Error ({res.status_code}): API Issue"
    except Exception as e:
        return f"Network Error: {str(e)}"

# ---------------------------------------------------------
# 1. DASHBOARD TAB
# ---------------------------------------------------------
if tab_choice == "Dashboard":
    st.title("⚡ AI Trading & Desktop Assistant v2.5")
    st.caption("Auto-Intent Routing: General AI Chat | Technical Trading Engine | Live Candlestick Charts | Voice Response")
    st.divider()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💬 Chat with AI Assistant")

        mic_available = False
        if hasattr(voice_assistant, 'is_mic_available'):
            try:
                mic_available = voice_assistant.is_mic_available()
            except Exception:
                mic_available = False

        if not mic_available:
            st.info("No microphone detected. Chat box me type karke Enter dabayein.")

        raw_user_prompt = st.chat_input("Sawal ya Command likhein aur Enter dabayein...")

        if raw_user_prompt:
            user_prompt = sanitize_user_input(raw_user_prompt)
            st.session_state["active_cmd"] = user_prompt
            
            route_info = detect_intent_and_respond(user_prompt)
            intent = route_info['intent']

            if intent == "GENERAL_CHAT":
                reply = get_general_chat_response(user_prompt)
            elif intent == "EXECUTION":
                sym = route_info['symbol']
                words = user_prompt.upper().split()
                action = "BUY" if ("BUY" in words or "KHAREEDO" in words) else "SELL"
                try:
                    yf = get_yfinance()
                    price = float(yf.Ticker(sym).history(period="1d")['Close'].iloc[-1])
                    sqlite_logger.log_trade(sym, action, 10, price)
                    reply = f"✅ Trade Executed: {action} 10 shares of {sym} at ₹{price:.2f}"
                except Exception as e:
                    reply = f"Execution Error: {str(e)}"
            elif intent == "TRADING_ANALYSIS":
                sym = route_info['symbol']
                analysis = reasoning_engine.generate_ai_reasoning(sym)
                if analysis and "error" not in analysis:
                    reply = f"Target: {analysis['symbol']} | Decision: {analysis['action']} | Price: ₹{analysis['last_price']}"
                else:
                    reply = f"'{sym}' ka data nahi mil saka."
            else:
                reply = "Command received."

            st.session_state["messages"].append({"role": "user", "content": user_prompt})
            st.session_state["messages"].append({"role": "assistant", "content": reply})

        for msg in reversed(st.session_state["messages"]):
            st.chat_message(msg["role"]).write(msg["content"])

    with col2:
        st.subheader("🎧 AI Active Response & Visual Analytics")
        
        if 'active_cmd' in st.session_state and st.session_state['active_cmd']:
            raw_input = st.session_state['active_cmd']
            route_info = detect_intent_and_respond(raw_input)
            intent = route_info['intent']

            if intent == "GENERAL_CHAT":
                st.markdown("### 🟢 Category: **Groq Super Fast AI**")
                reply = get_general_chat_response(raw_input)
                st.info(reply)
                
                if hasattr(voice_assistant, 'text_to_speech_hindi'):
                    audio_file = voice_assistant.text_to_speech_hindi(reply)
                    if audio_file:
                        st.audio(audio_file, autoplay=True)

            elif intent == "EXECUTION":
                st.markdown("### 📈 Category: **Order Execution Engine**")
                sym = route_info['symbol']
                words = raw_input.upper().split()
                action = "BUY" if ("BUY" in words or "KHAREEDO" in words) else "SELL"
                try:
                    yf = get_yfinance()
                    price = float(yf.Ticker(sym).history(period="1d")['Close'].iloc[-1])
                    sqlite_logger.log_trade(sym, action, 10, price)
                    msg = f"Trade Executed: {action} 10 shares of {sym} at ₹{price:.2f}"
                    st.success(f"✅ {msg}")
                    render_interactive_candlestick(sym)
                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")

            elif intent == "TRADING_ANALYSIS":
                st.markdown("### 📈 Category: **Trading Reasoning & Chart Engine**")
                sym = route_info['symbol']
                with st.spinner(f"Analyzing market data and generating chart for {sym}..."):
                    analysis = reasoning_engine.generate_ai_reasoning(sym)
                    if analysis and "error" not in analysis:
                        st.markdown(f"### Target: **{analysis['symbol']}**")
                        st.markdown(f"### Decision: :{analysis['color']}[**{analysis['action']}**] (Confidence: {analysis['confidence']})")
                        st.write(f"**Current Price:** ₹{analysis['last_price']}")
                        
                        render_interactive_candlestick(sym)

                        st.subheader("📌 Technical Reasons (Hindi):")
                        for reason in analysis['reasons']:
                            st.write(f"• {reason}")
                        
                        if hasattr(voice_assistant, 'text_to_speech_hindi'):
                            text_speech = f"{analysis['symbol']} par hamara decision {analysis['action']} hai. Confidence level {analysis['confidence']} hai."
                            audio_file = voice_assistant.text_to_speech_hindi(text_speech)
                            if audio_file:
                                st.audio(audio_file, autoplay=True)
                    else:
                        st.error(f"'{sym}' ka data nahi mila. Sahi symbol daalein.")

            elif intent == "PORTFOLIO":
                st.markdown("### 📊 Category: **Portfolio & Holdings**")
                st.info("Portfolio dekhne ke liye left sidebar se 'Portfolio Viewer' tab par jayein.")

            elif intent == "BACKTEST":
                st.markdown("### 🔄 Category: **Strategy Backtesting**")
                st.info("Backtesting chalane ke liye left sidebar se 'Backtester' tab par jayein.")

        else:
            st.info("Niche chat box me stock symbol (e.g. RELIANCE) likhein aur Enter dabayein.")

# ---------------------------------------------------------
# 2. AUTONOMOUS AI DEVELOPER V3 (MULTI-FILE & SELF-HEAL)
# ---------------------------------------------------------
elif tab_choice == "⚡ Autonomous AI Developer v3":
    st.header("⚡ Autonomous AI Developer v3 (Enterprise Mode)")
    st.caption("Multi-File Concurrent Editing | Smart Self-Healing Debugger | Dry Run Preview | Full Zip Backup | Audit Logs")
    st.divider()

    if agent_developer is None:
        try:
            import agent_developer
        except Exception:
            pass

    col_dev1, col_dev2 = st.columns([2, 1])

    with col_dev1:
        st.subheader("1. Multi-File Selection & Instructions")
        selected_files = st.multiselect(
            "Select Target Files to Modify (Multiple Allowed):",
            ["reasoning_engine.py", "portfolio_viewer.py", "backtesting_engine.py", "agent_developer.py", "app.py"],
            default=["reasoning_engine.py"]
        )

        user_instruction = st.text_area(
            "Write Instruction for AI Developer:",
            placeholder="e.g., Is feature ko in sabhi selected files me synced aur updated handle kar do.",
            height=100
        )

        if st.button("🔍 Run Multi-File Dry Run & Self-Heal Check", type="secondary"):
            if user_instruction.strip() and selected_files:
                with st.spinner("Executing Multi-File Dry Run & Smart Self-Healing Check..."):
                    dry_res = agent_developer.perform_multi_file_dry_run(selected_files, user_instruction)
                    if dry_res["success"]:
                        st.session_state["multi_dry_run_data"] = dry_res
                        st.success("✅ Multi-File Dry Run & Self-Healed Drafts Ready!")
                    else:
                        st.error(dry_res["error"])
            else:
                st.warning("Kam se kam ek file chunne aur instruction likhein.")

        # Multi-File Diff Preview & Approval
        if "multi_dry_run_data" in st.session_state and st.session_state["multi_dry_run_data"]:
            m_data = st.session_state["multi_dry_run_data"]
            st.divider()
            st.subheader("2. Multi-File Preview & Impact Analysis")

            for plan in m_data["files_plan"]:
                st.markdown(f"### 📄 Target: `{plan['target_file']}`")
                if plan.get("self_healed"):
                    st.info("🧠 **Smart Self-Heal Triggered:** AI detected syntax issue on 1st draft and automatically auto-fixed code!")

                c1, c2 = st.columns(2)
                c1.metric("Lines Added", f"+{plan['lines_added']}")
                c2.metric("Lines Deleted", f"-{plan['lines_deleted']}")

                with st.expander(f"View Line Diff for {plan['target_file']}", expanded=True):
                    st.code(plan["diff_text"], language="diff")

            col_app1, col_app2 = st.columns([1, 1])
            with col_app1:
                if st.button("✅ Approve & Write All Files", type="primary"):
                    with st.spinner("Backing up full project & applying multi-file write..."):
                        write_res = agent_developer.apply_multi_file_approved_update(m_data)
                        if write_res["success"]:
                            st.success(write_res["msg"])
                            st.info(f"📦 Full Zip Backup: `{os.path.basename(write_res['full_backup'])}`")
                            st.session_state["multi_dry_run_data"] = None
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(write_res["msg"])

            with col_app2:
                if st.button("❌ Cancel Change"):
                    st.session_state["multi_dry_run_data"] = None
                    st.warning("Multi-file modification cancelled.")
                    st.rerun()

    with col_dev2:
        st.subheader("🧠 v3 Enterprise Powers")
        st.markdown("""
        - **Multi-File Engine:** Edit multiple files concurrently.
        - **Smart Self-Healing:** Auto-fixes code if syntax check fails.
        - **Full Zip Backup:** Whole project backed up before write.
        - **Multi-File Rollback:** If any file fails, ALL files revert.
        - **Scope Sandbox:** Outside project access strictly blocked.
        """)

        st.divider()
        st.subheader("📋 Execution Audit Logs")
        logs = agent_developer.get_execution_logs() if agent_developer else []
        if logs:
            for l in logs[:5]:
                status_icon = "🟢" if "Success" in l["status"] else "🔴"
                st.markdown(f"**{status_icon} {l['timestamp']}** - `{l['status']}`")
                st.caption(f"Prompt: {l['prompt']}")
                st.caption(f"Files: {', '.join(l['files_modified'])}")
                st.markdown("---")
        else:
            st.caption("No execution logs found.")

# ---------------------------------------------------------
# OTHER TABS LOGIC
# ---------------------------------------------------------
elif tab_choice == "🕵️ AI Supervisor":
    st.header("🕵️ AI Supervisor Control Engine")
    ai_supervisor.start_supervisor()
    if st.button("▶ Queue Full Autonomous Cycle"):
        ai_supervisor.trigger_full_autonomous_cycle()
        st.success("Queued!")
    logs = ai_supervisor.get_supervisor_logs()
    for entry in logs[:10]:
        st.write(f"{entry['timestamp']} | {entry['task']} | {entry['status']}")

elif tab_choice == "👑 AI Project Manager":
    st.header("👑 AI Project Manager")
    metrics = project_manager.run_full_inspection() if st.button("Run Inspection") else None
    if metrics:
        st.metric("Project Health", f"{metrics['project_health']}%")

elif tab_choice == "🤖 AI Auto-Coder":
    st.header("🤖 AI Auto-Coder")
    if st.button("🔍 Scan Project"):
        st.session_state["proposed_fixes"] = auto_coder.analyze_and_propose_fixes()

elif tab_choice == "🧐 AI Code Review":
    st.header("🧐 AI Code Review")
    if st.button("🔍 Run Code Review"):
        res = code_review_engine.run_code_review()
        st.json(res)

elif tab_choice == "⚡ Performance Optimizer":
    st.header("⚡ Performance Optimizer")
    if st.button("🚀 Audit Performance"):
        st.json(performance_optimizer.run_performance_audit())

elif tab_choice == "🛡️ Security Scanner":
    st.header("🛡️ Security Scanner")
    if st.button("🛡️ Audit Security"):
        st.json(security_scanner.run_security_scan())

elif tab_choice == "🧪 AI Auto Testing":
    st.header("🧪 Auto Testing")
    if st.button("🧪 Execute Tests"):
        st.json(auto_testing_engine.run_full_test_suite())

elif tab_choice == "🧠 AI Self Improvement":
    st.header("🧠 Self Improvement")
    if st.button("🔍 Daily Scan"):
        st.json(self_improvement_engine.run_daily_project_scan())

elif tab_choice == "🏗️ AI Architect":
    st.header("🏗️ AI Architect")
    st.code(ai_architect_engine.generate_mermaid_architecture_diagram(), language="mermaid")

elif tab_choice == "Pattern Engine":
    st.header("Pattern Engine")

elif tab_choice == "Portfolio Viewer":
    portfolio_viewer.render_portfolio_tab()

elif tab_choice == "Backtester":
    backtesting_engine.render_backtester_tab()

elif tab_choice == "Telegram Notifier":
    st.header("Telegram Notifier")

elif tab_choice == "AI Reasoning":
    st.header("AI Reasoning")

gc.collect()
