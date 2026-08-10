import sys
import os
import subprocess
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal

class BackendServerThread(QThread):
    server_ready = pyqtSignal(str)
    server_failed = pyqtSignal(str)

    def __init__(self, port=8501):
        super().__init__()
        self.port = port
        self.url = f"http://127.0.0.1:{self.port}"
        self.process = None

    def run(self):
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            app_script = os.path.join(project_root, "app.py")

            cmd = [
                sys.executable, "-m", "streamlit", "run", app_script,
                "--server.port", str(self.port),
                "--server.address", "127.0.0.1",
                "--server.headless", "true",
                "--global.developmentMode", "false"
            ]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            max_retries = 25
            for _ in range(max_retries):
                try:
                    res = requests.get(self.url, timeout=1)
                    if res.status_code == 200:
                        self.server_ready.emit(self.url)
                        return
                except Exception:
                    time.sleep(1)

            self.server_failed.emit("Streamlit backend timeout after 25s")

        except Exception as e:
            self.server_failed.emit(str(e))

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass