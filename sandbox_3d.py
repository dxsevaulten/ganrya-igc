# sandbox_3d.py - Ganrya IGC Entry Point
import sys
from PyQt6.QtWidgets import QApplication
from ganrya_igc.core.app import GanryaApplication

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ganrya IGC")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Marsekeplar")
    
    window = GanryaApplication()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()