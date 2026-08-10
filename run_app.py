"""
run_app.py - PyInstaller Wrapper Launcher for Pro-Trade AI Trading Terminal
"""
import sys
import os
import streamlit.web.cli as stcli

def main():
    # Application ki root directory locate karna
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "app.py")

    # Streamlit CLI commands pass karke server launch karna
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
