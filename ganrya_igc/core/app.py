# Plan 1.3: Desain Modular & Sistem Plugin
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class GanryaApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ganrya IGC - Marsekeplar 3D Sandbox")
        self.setGeometry(150, 150, 900, 600)
        self.setStyleSheet("background-color: #1a1a2e; color: #e0e0ff;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # TODO: Tambahkan viewport 3D dan komponen lainnya
        # Akan diimplementasikan di Subplan 1.1.1 - 1.1.5