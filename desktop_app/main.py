import sys
import os
import webbrowser
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# System path set up
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop_app.ui.loading_screen import LoadingSplashScreen
from desktop_app.server_manager import BackendServerThread

def main():
    app = QApplication(sys.argv)

    splash = LoadingSplashScreen()
    splash.show()

    server_thread = BackendServerThread(port=8501)

    def on_server_ready(url):
        splash.update_status("Launching Dashboard...")
        # Close splash screen and open clean App UI in Browser View
        QTimer.singleShot(1000, lambda: [splash.close(), webbrowser.open(url)])

    def on_server_failed(error_msg):
        splash.update_status(f"Error: {error_msg}")

    server_thread.server_ready.connect(on_server_ready)
    server_thread.server_failed.connect(on_server_failed)
    server_thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()