import os
import sys
import time
import threading
import webbrowser

def run_streamlit_backend():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        script_path = os.path.join(base_dir, "run_streamlit.py")
        
        from streamlit.web import bootstrap

        flag_options = {
            "server.port": 8501,
            "server.headless": True,
            "global.developmentMode": False,
            "browser.gatherUsageStats": False
        }
        
        # Internal Streamlit bootstrap runner
        bootstrap.run(script_path, is_hello=False, args=[], flag_options=flag_options)
    except Exception as e:
        print(f"Streamlit Backend Exception: {e}")

if __name__ == "__main__":
    # Start Streamlit in daemon thread
    backend_thread = threading.Thread(target=run_streamlit_backend, daemon=True)
    backend_thread.start()

    # Give server time to bind port 8501
    time.sleep(3)
    
    # Auto launch browser
    webbrowser.open("http://localhost:8501")

    # Keep executable alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()