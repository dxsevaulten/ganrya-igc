# ganrya_igc/tests/test_localization.py
import unittest
import tempfile
import os
import json
from ganrya_igc.core.localization import I18nManager
from ganrya_igc.core.localization import RTLHelper, List, Callable

class TestI18nManager(unittest.TestCase):
    def setUp(self):
        self.manager = I18nManager(default_lang="en")

    def test_default_language(self):
        self.assertEqual(self.manager.current_lang, "en")

    def test_translate_without_translations(self):
        # Tanpa file terjemahan, harus mengembalikan kunci
        self.assertEqual(self.manager.t("hello"), "hello")

    def test_add_and_use_translations(self):
        self.manager.add_translations("id", {"hello": "halo", "bye": "dadah"})
        self.manager.set_language("id")
        self.assertEqual(self.manager.t("hello"), "halo")
        self.assertEqual(self.manager.t("bye"), "dadah")

    def test_fallback_to_default(self):
        # Bahasa Indonesia punya "hello" -> "halo", tapi "missing_key" tidak ada
        self.manager.add_translations("id", {"hello": "halo"})
        # Tidak ada fallback en untuk missing_key
        self.manager.set_language("id")
        self.assertEqual(self.manager.t("missing_key"), "missing_key")

    def test_placeholders(self):
        self.manager.add_translations("en", {"greeting": "Halo, {name}!"})
        self.assertEqual(
            self.manager.t("greeting", name="Sovereign Dev"), "Halo, Sovereign Dev!"
        )

    def test_load_from_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "fr.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({"hello": "bonjour"}, f)
            mgr = I18nManager(locales_dir=tmpdir)
            mgr.load_language("fr")
            mgr.set_language("fr")
            self.assertEqual(mgr.t("hello"), "bonjour")

class RTLHelper:
    def __init__(self, i18n: I18nManager):
        self.i18n = i18n
        self._on_layout_change_callbacks: List[Callable[[bool], None]] = []

    def is_rtl_language(self, lang: str) -> bool:
        return lang.lower().startswith("ar") or lang.lower().startswith("he") or lang.lower().startswith("fa")

    def current_is_rtl(self) -> bool:
        return self.is_rtl_language(self.i18n.current_lang)

    def on_layout_change(self, callback: Callable[[bool], None]):
        self._on_layout_change_callbacks.append(callback)   # ← sudah benar

    def _notify_layout_change(self):
        is_rtl = self.current_is_rtl()
        for callback in self._on_layout_change_callbacks:   # ← perbaiki di sini
            try:
                callback(is_rtl)
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()