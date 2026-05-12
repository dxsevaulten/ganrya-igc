# ganrya_igc/core/localization.py
"""
Plan 1.9: Sistem Internasionalisasi & Aksesibilitas.
Subplan 1.9.1: String Externalization & Localization Framework.
"""

import json
import os
from typing import Dict, Optional


class I18nManager:
    """
    Manajer internasionalisasi sederhana.
    Memuat file terjemahan JSON dan menyediakan akses berdasarkan kunci.
    """

    def __init__(self, default_lang: str = "en", locales_dir: str = "locales"):
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.locales_dir = locales_dir
        self._translations: Dict[str, Dict[str, str]] = {}  # lang -> {key: text}
        self._fallback = "en"
        self._rtl_helper: Optional[RTLHelper] = None  # akan di-set nanti

    def load_language(self, lang: str, filepath: Optional[str] = None):
        """
        Muat file terjemahan untuk bahasa tertentu.
        Jika filepath tidak diberikan, cari di locales_dir/lang.json.
        """
        if filepath is None:
            filepath = os.path.join(self.locales_dir, f"{lang}.json")
        if os.path.isfile(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self._translations[lang] = json.load(f)

    def set_language(self, lang: str):
        if lang in self._translations or lang == self.default_lang:
            self.current_lang = lang
        else:
            self.current_lang = self.default_lang
        # Beri tahu RTLHelper jika ada perubahan
        if self._rtl_helper:
            self._rtl_helper._notify_layout_change()

    def translate(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """
        Ambil string terjemahan berdasarkan kunci.
        Jika tidak ditemukan, kembalikan kunci itu sendiri.
        Mendukung format placeholders dengan **kwargs.
        """
        lang = lang or self.current_lang
        text = None
        if lang in self._translations:
            text = self._translations[lang].get(key)
        if text is None and self._fallback in self._translations:
            text = self._translations[self._fallback].get(key)
        if text is None:
            text = key
        if kwargs:
            return text.format(**kwargs)
        return text

    t = translate  # alias pendek

    def add_translations(self, lang: str, translations: Dict[str, str]):
        """Tambahkan terjemahan langsung dari dictionary."""
        if lang not in self._translations:
            self._translations[lang] = {}
        self._translations[lang].update(translations)

# ========== SUBPLAN 1.9.2: UI LAYOUT MIRRORING (RTL) ==========
from typing import List, Callable

class RTLHelper:
    """
    Membantu mengelola arah layout untuk mendukung bahasa RTL (Arab, Ibrani, dll.).
    """

    # Daftar kode bahasa yang menggunakan arah RTL
    RTL_LANGUAGES = {"ar", "he", "fa", "ur", "yi", "dv", "ps", "sd"}

    def __init__(self, i18n_manager: I18nManager):
        self.i18n = i18n_manager
        self._on_layout_change_callbacks: List[Callable[[bool], None]] = []
        # Daftarkan callback untuk mendeteksi perubahan bahasa
        # (Kita perlu menambahkan hook di I18nManager.set_language nanti)

    @staticmethod
    def is_rtl(lang_code: str) -> bool:
        """Periksa apakah kode bahasa menggunakan arah RTL."""
        return lang_code in RTLHelper.RTL_LANGUAGES

    def current_is_rtl(self) -> bool:
        """Apakah bahasa yang sedang aktif adalah RTL?"""
        return self.is_rtl(self.i18n.current_lang)

    def apply_to_widget(self, widget):
        """Terapkan arah layout RTL/LTR ke widget PyQt6."""
        from PyQt6.QtCore import Qt
        try:
            if self.current_is_rtl():
                widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        except ImportError:
            pass

    def on_layout_change(self, callback: Callable[[bool], None]):
        """Daftarkan callback yang dipanggil saat arah layout berubah."""
        self._on_layout_change_calls.append(callback)

    def _notify_layout_change(self):
        """Panggil semua callback yang terdaftar."""
        is_rtl = self.current_is_rtl()
        for callback in self._on_layout_change_calls:
            callback(is_rtl)
