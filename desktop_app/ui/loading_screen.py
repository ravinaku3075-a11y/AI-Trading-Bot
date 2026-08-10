import sys
import os
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette

class LoadingSplashScreen(QSplashScreen):
    """
    Custom splash screen that displays initial loading status 
    before launching the main PyQt WebEngine window.
    """
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setFixedSize(450, 280)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Background styling
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(24, 28, 36))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Layout container
        container = QWidget(self)
        container.setGeometry(0, 0, 450, 280)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 40, 30, 40)

        # Title Label
        self.title_label = QLabel("AI Trading Terminal v2.2", container)
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #00E676;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Status Label
        self.status_label = QLabel("Starting Streamlit Backend Services...", container)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #B0BEC5;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar(container)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #37474F;
                border-radius: 5px;
                background-color: #1E232A;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00E676;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def update_status(self, message: str):
        """Updates the splash screen loading status text."""
        self.status_label.setText(message)

    def finish(self, main_window):
        """Closes splash screen when main UI window loads."""
        super().finish(main_window)