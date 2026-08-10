import sys
import os
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl

class MainWindow(QMainWindow):
    def __init__(self, server_url="http://127.0.0.1:8501"):
        super().__init__()
        self.server_url = server_url

        self.setWindowTitle("AI Trading Terminal v2.2")
        self.resize(1280, 800)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        
        # Enable JavaScript & Local Content
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        self.web_view.setUrl(QUrl(self.server_url))
        layout.addWidget(self.web_view)

    def load_url(self, url: str):
        self.server_url = url
        self.web_view.setUrl(QUrl(url))