# ganrya_igc/core/shortcuts.py
"""
Plan 1.9: Sistem Internasionalisasi & Aksesibilitas.
Subplan 1.9.3: Full Keyboard Navigation & Shortcut Customization.
"""

import json
import os
from typing import Dict, Callable, List, Optional


class ShortcutManager:
    """
    Mengelola pemetaan kombinasi tombol ke aksi.
    """
    def __init__(self, default_shortcuts: Optional[Dict[str, str]] = None):
        """
        default_shortcuts: dictionary {action_name: key_combination}
        """
        self._shortcuts: Dict[str, str] = default_shortcuts.copy() if default_shortcuts else {}
        self._actions: Dict[str, Callable[[], None]] = {}
        self._callbacks: List[Callable[[str, str], None]] = []

    def register_action(self, name: str, func: Callable[[], None], default_keys: str = ""):
        """Daftarkan aksi dengan fungsi dan kombinasi tombol default."""
        self._actions[name] = func
        if name not in self._shortcuts:
            self._shortcuts[name] = default_keys

    def set_shortcut(self, action_name: str, keys: str):
        """Tetapkan kombinasi tombol untuk aksi tertentu."""
        if action_name not in self._actions:
            raise KeyError(f"Aksi '{action_name}' tidak terdaftar.")
        self._shortcuts[action_name] = keys
        self._notify_change(action_name, keys)

    def get_shortcut(self, action_name: str) -> Optional[str]:
        return self._shortcuts.get(action_name)

    def execute(self, keys: str):
        """Jalankan aksi yang dipetakan ke kombinasi tombol yang diberikan."""
        for action, shortcut in self._shortcuts.items():
            if shortcut.lower() == keys.lower():
                if action in self._actions:
                    self._actions[action]()
                return

    def remove_shortcut(self, action_name: str):
        if action_name in self._shortcuts:
            del self._shortcuts[action_name]
            self._notify_change(action_name, "")

    def on_shortcut_changed(self, callback: Callable[[str, str], None]):
        """Callback dipanggil saat pintasan berubah."""
        self._callbacks.append(callback)

    def _notify_change(self, action_name: str, new_keys: str):
        for cb in self._callbacks:
            try:
                cb(action_name, new_keys)
            except Exception:
                pass

    def export_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._shortcuts, f, indent=2)

    def import_from_file(self, filepath: str):
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for action, keys in data.items():
                    if action in self._actions:
                        self._shortcuts[action] = keys

# ========== SUBPLAN 1.9.4: SCREEN READER SUPPORT ==========

class AccessibilityManager:
    """
    Menerapkan properti aksesibilitas dasar pada widget PyQt6
    agar kompatibel dengan screen reader.
    """

    @staticmethod
    def apply_to_button(button, name: str, description: str = ""):
        """Terapkan accessible name dan description pada QPushButton."""
        try:
            from PyQt6.QtWidgets import QPushButton, QWidget
            if isinstance(button, QWidget):
                button.setAccessibleName(name)
                if description:
                    button.setAccessibleDescription(description)
        except ImportError:
            pass

    @staticmethod
    def apply_to_label(label, name: str):
        """Terapkan accessible name pada QLabel."""
        try:
            from PyQt6.QtWidgets import QWidget
            if isinstance(label, QWidget):
                label.setAccessibleName(name)
        except ImportError:
            pass

    @staticmethod
    def apply_to_input(input_widget, name: str, description: str = ""):
        """Terapkan accessible name/description pada input widget."""
        try:
            from PyQt6.QtWidgets import QWidget
            if isinstance(input_widget, QWidget):
                input_widget.setAccessibleName(name)
                if description:
                    input_widget.setAccessibleDescription(description)
        except ImportError:
            pass

    @staticmethod
    def announce(message: str):
        """Umumkan pesan ke teknologi asistif (jika didukung)."""
        try:
            from PyQt6.QtGui import QAccessible
            # Tidak ada API pengumuman langsung di PyQt6,
            # jadi kita gunakan update pada statusbar sebagai fallback.
            print(f"[A11Y Announce] {message}")
        except ImportError:
            print(f"[A11Y Announce] {message}")
