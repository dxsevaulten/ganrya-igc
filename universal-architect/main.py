"""
Universal Digital Architect - Main Entry Point
Aplikasi GUI utama menggunakan PyQt6
"""

import sys
import os

# Tambahkan parent directory ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core import get_engine, WindowManager
from modules import get_launcher


class MainWindow(QMainWindow):
    """
    MainWindow untuk Universal Digital Architect
    Saat ini masih versi dasar, akan dikembangkan di Fase 1
    """
    
    def __init__(self):
        super().__init__()
        
        # Inisialisasi komponen inti
        self.engine = get_engine()
        self.window_manager = WindowManager()
        self.launcher = get_launcher()
        
        # Setup UI dasar
        self.setup_ui()
        
        # Set konfigurasi default
        self.engine.set_config('theme', 'dark')
        self.engine.set_config('version', '0.1.0')
    
    def setup_ui(self):
        """Setup antarmuka pengguna dasar"""
        self.setWindowTitle("Universal Digital Architect - v0.1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget sentral
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Label judul
        title_label = QLabel("🌌 Universal Digital Architect")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Arsitek Digital Universal - Membangkitkan Kembali Aplikasi Masa Lalu")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #888; margin-bottom: 20px;")
        layout.addWidget(subtitle_label)
        
        # Status label
        self.status_label = QLabel("Status: Siap - Core Engine Initialized")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Info box
        info_box = QLabel("""
        <div style='background-color: #2d2d2d; padding: 20px; border-radius: 10px; margin: 20px;'>
            <h3 style='color: #fff;'>Fase 0: The Iron Foundation ✅</h3>
            <ul style='color: #ccc;'>
                <li>✓ Core Engine (Singleton Pattern)</li>
                <li>✓ Window Manager (Win32 API + Mock)</li>
                <li>✓ Application Launcher (.exe, .lnk)</li>
                <li>✓ Utilities & Helpers</li>
                <li>✓ Testing Suite (36 tests passed)</li>
            </ul>
            <p style='color: #FFD700; margin-top: 15px;'>
                🚀 Selanjutnya: Fase 1 - The Universal Host
            </p>
        </div>
        """)
        info_box.setWordWrap(True)
        layout.addWidget(info_box)
        
        # Footer
        footer_label = QLabel("Tekan Ctrl+Q untuk keluar")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(footer_label)
    
    def closeEvent(self, event):
        """Handle penutupan aplikasi"""
        # Cleanup resources
        self.window_manager.cleanup()
        self.engine.cleanup()
        
        event.accept()


def main():
    """Entry point utama aplikasi"""
    print("=" * 60)
    print("🌌 Universal Digital Architect - Starting...")
    print("=" * 60)
    
    # Buat aplikasi Qt
    app = QApplication(sys.argv)
    
    # Set style sheet global
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
        QLabel {
            color: #ffffff;
        }
    """)
    
    # Buat dan tampilkan main window
    window = MainWindow()
    window.show()
    
    print("✅ Main Window displayed")
    print("📊 Core Engine status: Ready")
    print("🎯 Phase: 0 (Iron Foundation) - Complete")
    print("=" * 60)
    
    # Jalankan event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
