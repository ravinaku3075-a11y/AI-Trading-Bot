@echo off
title AI Trading Terminal
cd /d "%~dp0"
call venv\Scripts\activate.bat
start "" "http://localhost:8501"
python -m streamlit run run_streamlit.py --server.port=8501 --server.headless=true
pause