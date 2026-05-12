# ganrya_igc/tests/test_shortcuts.py
import unittest
from ganrya_igc.core.shortcuts import ShortcutManager
from ganrya_igc.core.shortcuts import AccessibilityManager

class TestShortcutManager(unittest.TestCase):
    def setUp(self):
        self.mgr = ShortcutManager()
        self.results = []
        self.mgr.register_action("undo", lambda: self.results.append("undo"), "Ctrl+Z")
        self.mgr.register_action("redo", lambda: self.results.append("redo"), "Ctrl+Y")
        self.mgr.register_action("save", lambda: self.results.append("save"), "Ctrl+S")

    def test_default_shortcut_is_registered(self):
        self.assertEqual(self.mgr.get_shortcut("undo"), "Ctrl+Z")

    def test_execute_action(self):
        self.mgr.execute("Ctrl+Z")
        self.assertEqual(self.results, ["undo"])

    def test_execute_case_insensitive(self):
        self.mgr.execute("ctrl+z")
        self.assertEqual(self.results, ["undo"])

    def test_custom_shortcut(self):
        self.mgr.set_shortcut("undo", "Alt+U")
        self.assertEqual(self.mgr.get_shortcut("undo"), "Alt+U")
        self.mgr.execute("Alt+U")
        self.assertEqual(self.results, ["undo"])

    def test_remove_shortcut(self):
        self.mgr.remove_shortcut("undo")
        self.assertIsNone(self.mgr.get_shortcut("undo"))
        self.mgr.execute("Ctrl+Z")
        self.assertEqual(self.results, [])

    def test_export_import(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            path = f.name
        try:
            self.mgr.export_to_file(path)
            new_mgr = ShortcutManager()
            new_mgr.register_action("undo", lambda: None)
            new_mgr.register_action("save", lambda: None)
            new_mgr.import_from_file(path)
            self.assertEqual(new_mgr.get_shortcut("undo"), "Ctrl+Z")
            self.assertEqual(new_mgr.get_shortcut("save"), "Ctrl+S")
        finally:
            os.unlink(path)

class TestAccessibility(unittest.TestCase):
    def test_apply_to_label_does_not_crash(self):
        # Tanpa PyQt6 di lingkungan pengujian, panggilan harus tetap aman
        try:
            AccessibilityManager.apply_to_label(None, "test_label")
        except Exception:
            self.fail("apply_to_label raised an exception unexpectedly")

    def test_announce_does_not_crash(self):
        try:
            AccessibilityManager.announce("Halo dunia")
        except Exception:
            self.fail("announce raised an exception unexpectedly")

if __name__ == "__main__":
    unittest.main()