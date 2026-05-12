# engine_gui.py - Fase 3: Menu Sentuh & Hologram Interaktif
import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QCheckBox, QLabel,
                             QFileDialog, QMessageBox, QSlider, QGroupBox,
                             QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QColor, QPalette, QFont

# -------------------------------------------------------------------
# Tema Holographic ditingkatkan
# -------------------------------------------------------------------
THEME = {
    "bg_color": "rgba(10, 5, 20, 0.9)",
    "panel_bg": "rgba(20, 10, 35, 0.75)",
    "border_color": "rgba(0, 255, 255, 0.5)",
    "text_color": "#e0e0ff",
    "accent_cyan": "#00ffff",
    "accent_magenta": "#ff00ff",
    "accent_purple": "#b066ff",
    "button_bg": "rgba(0, 255, 255, 0.15)",
    "button_hover": "rgba(255, 0, 255, 0.3)",
    "glow_color": "rgba(0, 255, 255, 0.6)",
    "shadow_color": "rgba(0, 255, 255, 0.4)"
}

def apply_theme(widget):
    widget.setStyleSheet(f"""
        QMainWindow {{
            background-color: {THEME['bg_color']};
            border: 2px solid {THEME['border_color']};
            border-radius: 18px;
            padding: 12px;
        }}
        QGroupBox {{
            background-color: {THEME['panel_bg']};
            border: 1px solid {THEME['border_color']};
            border-radius: 12px;
            margin-top: 18px;
            padding: 15px;
            font-weight: bold;
            color: {THEME['text_color']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 18px;
            color: {THEME['accent_cyan']};
            font-size: 13px;
        }}
        QPushButton {{
            background-color: {THEME['button_bg']};
            border: 1px solid {THEME['border_color']};
            border-radius: 10px;
            padding: 10px 20px;
            color: {THEME['text_color']};
            font-weight: bold;
            min-width: 110px;
        }}
        QPushButton:hover {{
            background-color: {THEME['button_hover']};
            border-color: {THEME['accent_magenta']};
        }}
        QSlider::groove:horizontal {{
            background: rgba(0, 255, 255, 0.25);
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {THEME['accent_cyan']};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QCheckBox {{
            color: {THEME['text_color']};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 2px solid {THEME['border_color']};
            border-radius: 4px;
            background: rgba(0,0,0,0.3);
        }}
        QCheckBox::indicator:checked {{
            background: {THEME['accent_cyan']};
            border-color: {THEME['accent_cyan']};
        }}
    """)

# -------------------------------------------------------------------
# Tombol dengan efek glow & skala animasi
# -------------------------------------------------------------------
class GlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(THEME['shadow_color']))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['button_hover']};
                border: 2px solid {THEME['accent_magenta']};
                color: white;
                padding: 12px 24px;
                transition: 0.2s;
            }}
        """)

    def leaveEvent(self, event):
        self.setStyleSheet("")

# -------------------------------------------------------------------
# Floating Toolbar (muncul saat kursor di tepi kanan)
# -------------------------------------------------------------------
class FloatingToolbar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"background: {THEME['panel_bg']}; border-radius: 12px;")
        layout = QVBoxLayout()
        self.btn_preview = GlowButton("🔍 Preview")
        self.btn_reset = GlowButton("🔄 Reset")
        self.btn_snap = GlowButton("📸 Snap View")
        layout.addWidget(self.btn_preview)
        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_snap)
        self.setLayout(layout)
        self.setFixedSize(140, 160)
        self.hide()
        # Animasi masuk
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def show_at(self, pos):
        self.anim.setStartValue(pos + QPoint(50, 0))
        self.anim.setEndValue(pos)
        self.anim.start()
        self.show()

# -------------------------------------------------------------------
# Jendela Utama Holographic
# -------------------------------------------------------------------
class SandboxHolographicWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marsekeplar Holographic v6.0 - kicawmania_101")
        self.setGeometry(200, 200, 520, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        apply_theme(self)
        self.data = None

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        self.info_label = QLabel("Status: Menunggu data dari SketchUp...")
        self.info_label.setStyleSheet(f"color: {THEME['accent_cyan']}; font-size: 14px;")
        main_layout.addWidget(self.info_label)

        # Grup Sisi
        sides_group = QGroupBox("Dimensi Proyeksi")
        sides_layout = QHBoxLayout()
        self.side_checks = {}
        for side in ['front', 'back', 'left', 'right', 'top', 'bottom']:
            cb = QCheckBox(side.capitalize())
            cb.setChecked(True)
            self.side_checks[side] = cb
            sides_layout.addWidget(cb)
        sides_group.setLayout(sides_layout)
        main_layout.addWidget(sides_group)

        # Grup Pengaturan (dengan live preview update)
        settings_group = QGroupBox("Parameter Visual")
        settings_layout = QVBoxLayout()

        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolusi:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 10)
        self.size_slider.setValue(5)
        res_layout.addWidget(self.size_slider)
        self.size_label = QLabel("5 (Sedang)")
        res_layout.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v} (Sedang)"))
        # Live update bisa ditambahkan nanti untuk pratinjau
        settings_layout.addLayout(res_layout)

        line_layout = QHBoxLayout()
        line_layout.addWidget(QLabel("Skala Garis:"))
        self.line_slider = QSlider(Qt.Orientation.Horizontal)
        self.line_slider.setRange(1, 10)
        self.line_slider.setValue(5)
        line_layout.addWidget(self.line_slider)
        self.line_label = QLabel("5")
        line_layout.addWidget(self.line_label)
        self.line_slider.valueChanged.connect(lambda v: self.line_label.setText(str(v)))
        settings_layout.addLayout(line_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Tombol Aksi
        btn_layout = QHBoxLayout()
        self.load_btn = GlowButton("1. Muat Proyeksi")
        self.load_btn.clicked.connect(self.load_input)
        btn_layout.addWidget(self.load_btn)

        self.export_btn = GlowButton("2. Ekspor Hasil (.json)")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_result)
        btn_layout.addWidget(self.export_btn)
        main_layout.addLayout(btn_layout)

        # Tombol Terapkan ke SketchUp
        self.apply_btn = GlowButton("3. Terapkan ke SketchUp")
        self.apply_btn.setEnabled(True)  # aktif setelah data dimuat
        self.apply_btn.clicked.connect(self.apply_to_sketchup)
        btn_layout.addWidget(self.apply_btn)

        # Checkbox Auto-Import (default aktif)
        self.auto_import_cb = QCheckBox("Auto-Import saat diterapkan")
        self.auto_import_cb.setChecked(True)
        self.auto_import_cb.setStyleSheet(f"color: {THEME['text_color']};")
        main_layout.addWidget(self.auto_import_cb)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {THEME['accent_purple']};")
        main_layout.addWidget(self.status_label)

        # Color Picker Group
        color_group = QGroupBox("Warna Output")
        color_layout = QHBoxLayout()
        
        color_layout.addWidget(QLabel("Garis:"))
        self.line_color_btn = QPushButton()
        self.line_color_btn.setFixedSize(30, 30)
        self.line_color_btn.setStyleSheet("background-color: #00ffff; border: 1px solid #fff;")
        self.line_color_btn.clicked.connect(lambda: self.pick_color('line'))
        color_layout.addWidget(self.line_color_btn)
        
        color_layout.addWidget(QLabel("Isian:"))
        self.fill_color_btn = QPushButton()
        self.fill_color_btn.setFixedSize(30, 30)
        self.fill_color_btn.setStyleSheet("background-color: #ffffff; border: 1px solid #fff;")
        self.fill_color_btn.clicked.connect(lambda: self.pick_color('fill'))
        color_layout.addWidget(self.fill_color_btn)
        
        color_group.setLayout(color_layout)
        main_layout.addWidget(color_group)
        
        # Simpan warna default
        self.line_color = "#00ffff"
        self.fill_color = "#ffffff"

        # Floating Toolbar (muncul di kanan)
        self.floating = FloatingToolbar(self)

    # -------------------------------------------------------------------
    # Event kursor untuk memunculkan floating toolbar
    # -------------------------------------------------------------------

    def pick_color(self, target):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if target == 'line':
                self.line_color = hex_color
                self.line_color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #fff;")
            elif target == 'fill':
                self.fill_color = hex_color
                self.fill_color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #fff;")
    
    def apply_to_sketchup(self):
        if not self.data:
            return
        # Filter sisi
        filtered = {}
        for side, cb in self.side_checks.items():
            if cb.isChecked() and side in self.data.get('projections', {}):
                filtered[side] = self.data['projections'][side]
        if not filtered:
            QMessageBox.warning(self, "Peringatan", "Tidak ada sisi yang dipilih.")
            return

        # Simpan file hasil ke Temp
        result_path = os.path.join(os.environ.get('TEMP', '.'), 'marsekeplar_result.json')
        output = {
            'projections': filtered,
            'normals': self.data.get('normals', {}),
            'settings': {
                'resolution': self.size_slider.value(),
                'line_scale': self.line_slider.value()
            }
        }
        try:
            with open(result_path, 'w') as f:
                json.dump(output, f, indent=2)
            self.status_label.setText(f"Hasil disimpan. SketchUp akan mengimpor otomatis.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan: {e}")
            return

        # Jika auto-import dicentang, buat file lock
        if self.auto_import_cb.isChecked():
            lock_path = os.path.join(os.environ.get('TEMP', '.'), 'marsekeplar_auto_import.lock')
            with open(lock_path, 'w') as f:
                f.write('import')
        
        # Tutup GUI (opsional)
        self.close()

    def mouseMoveEvent(self, event):
        # Munculkan floating toolbar saat kursor di dekat tepi kanan
        if event.position().x() > self.width() - 60:
            pos = self.mapToGlobal(QPoint(self.width() - 160, event.position().y() - 80))
            self.floating.show_at(pos)
        super().mouseMoveEvent(event)

    def load_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Buka Data Proyeksi", "", "JSON (*.json)")
        if not path:
            return
        self._load_file(path)

    def _load_file(self, file_path):        
        try:
            with open(file_path, 'r') as f:
                self.data = json.load(f)
            sides = list(self.data.get('projections', {}).keys())
            self.info_label.setText(f"Data Holographic Dimuat: {', '.join(sides)}")
            self.export_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca data: {e}")

    def load_from_path(self, file_path):
        if os.path.exists(file_path):
            self._load_file(file_path)
        else:
            QMessageBox.warning(self, "File Tidak Ditemukan", f"File tidak ada:\n{file_path}")

    def export_result(self):
        if not self.data:
            return
        filtered = {}
        for side, cb in self.side_checks.items():
            if cb.isChecked() and side in self.data.get('projections', {}):
                filtered[side] = self.data['projections'][side]
        if not filtered:
            QMessageBox.warning(self, "Peringatan", "Tidak ada sisi yang dipilih.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil Proyeksi", "hasil_proyeksi.json", "JSON (*.json)")
        if not path:
            return
        try:
            output = {
                'projections': filtered,
                'normals': self.data.get('normals', {}),
                'settings': {
                    'resolution': self.size_slider.value(),
                    'line_scale': self.line_slider.value()
                }
            }
            with open(path, 'w') as f:
                json.dump(output, f, indent=2)
            self.status_label.setText(f"Proyeksi Holographic tersimpan di: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menyimpan: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SandboxHolographicWindow()
    window.show()
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        QTimer.singleShot(200, lambda: window.load_from_path(file_path))
    sys.exit(app.exec())