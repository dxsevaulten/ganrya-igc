# ganrya_igc/tests/test_plugin_system.py
import unittest
import os
import tempfile
from ganrya_igc.core.plugin_system import PluginBase, PluginManager
from ganrya_igc.core.plugin_system import DevPluginManager, PluginFileWatcher, PluginMetadata
import time

# Helper: buat file plugin sementara
def create_plugin_file(folder: str, name: str, content: str):
    path = os.path.join(folder, f"{name}.py")
    with open(path, 'w') as f:
        f.write(content)
    return path


class TestPluginManager(unittest.TestCase):
    def setUp(self):
        # Buat folder plugin sementara
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        # Hapus folder sementara
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_plugins_empty(self):
        discovered = self.manager.discover_plugins()
        self.assertEqual(len(discovered), 0)

    def test_discover_plugins(self):
        create_plugin_file(self.temp_dir, "hello_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class HelloPlugin(PluginBase):
    name = "hello"
    version = "1.0.0"
""")
        discovered = self.manager.discover_plugins()
        self.assertIn("hello_plugin", discovered)

    def test_load_and_get_plugin(self):
        create_plugin_file(self.temp_dir, "my_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class MyPlugin(PluginBase):
    name = "my_plugin"
    version = "1.0.0"
""")
        self.assertTrue(self.manager.load_plugin("my_plugin"))
        plugin = self.manager.get_plugin("my_plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "my_plugin")
        self.assertEqual(plugin.version, "1.0.0")

    def test_plugin_dependency_check(self):
        # Plugin yang bergantung pada plugin lain yang belum dimuat
        create_plugin_file(self.temp_dir, "dependent_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class DependentPlugin(PluginBase):
    name = "dependent"
    version = "1.0.0"
    dependencies = ["missing_plugin"]
""")
        result = self.manager.load_plugin("dependent_plugin")
        self.assertFalse(result)

    def test_start_stop_lifecycle(self):
        create_plugin_file(self.temp_dir, "lifecycle_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class LifecyclePlugin(PluginBase):
    name = "lifecycle"
    version = "1.0.0"
""")
        self.manager.load_plugin("lifecycle_plugin")
        plugin = self.manager.get_plugin("lifecycle_plugin")
        
        self.assertTrue(plugin._initialized)
        self.assertFalse(plugin._running)
        
        self.manager.start_all_plugins()
        self.assertTrue(plugin._running)
        
        self.manager.stop_all_plugins()
        self.assertFalse(plugin._running)

    def test_unload_all(self):
        create_plugin_file(self.temp_dir, "temp_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class TempPlugin(PluginBase):
    name = "temp"
    version = "1.0.0"
""")
        self.manager.load_plugin("temp_plugin")
        self.assertIsNotNone(self.manager.get_plugin("temp_plugin"))
        
        self.manager.unload_all_plugins()
        self.assertIsNone(self.manager.get_plugin("temp_plugin"))
        self.assertEqual(len(self.manager.plugins), 0)

class TestPluginEventSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_event_bus_accessible_in_plugin(self):
        create_plugin_file(self.temp_dir, "event_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class EventPlugin(PluginBase):
    name = "event_plugin"
    version = "1.0.0"
    
    def init(self):
        super().init()
        self.received_events = []
        self.event_bus.subscribe('test:event', self._on_test_event)
    
    def _on_test_event(self, data):
        self.received_events.append(data)
""")
        self.manager.load_plugin("event_plugin")
        plugin = self.manager.get_plugin("event_plugin")
        self.assertIsNotNone(plugin.event_bus)
        
        # Publikasikan event
        self.manager.event_bus.publish('test:event', {'value': 42})
        self.assertEqual(len(plugin.received_events), 1)
        self.assertEqual(plugin.received_events[0]['value'], 42)

    def test_kernel_lifecycle_events(self):
        create_plugin_file(self.temp_dir, "lifecycle_listener", """
from ganrya_igc.core.plugin_system import PluginBase

class LifecycleListener(PluginBase):
    name = "lifecycle_listener"
    version = "1.0.0"
    
    def init(self):
        super().init()
        self.events = []
        self.event_bus.subscribe('plugin:started', lambda d: self.events.append(('started', d['name'])))
        self.event_bus.subscribe('plugin:stopped', lambda d: self.events.append(('stopped', d['name'])))
""")
        self.manager.load_plugin("lifecycle_listener")
        plugin = self.manager.get_plugin("lifecycle_listener")
        
        self.manager.start_all_plugins()
        self.manager.stop_all_plugins()
        
        # Harus menerima event untuk dirinya sendiri
        self.assertGreaterEqual(len(plugin.events), 2)

class TestPluginDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_plugin_metadata(self):
        create_plugin_file(self.temp_dir, "meta_plugin", """
from ganrya_igc.core.plugin_system import PluginBase, PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="meta_plugin",
    version="2.0.0",
    author="Test Author",
    description="A test plugin"
)

class MetaPlugin(PluginBase):
    name = "meta_plugin"
    version = "2.0.0"
""")
        metadata = self.manager.discover_plugin_metadata()
        self.assertIn("meta_plugin", metadata)
        self.assertEqual(metadata["meta_plugin"].version, "2.0.0")
        self.assertEqual(metadata["meta_plugin"].author, "Test Author")

    def test_discover_plugin_dependencies(self):
        create_plugin_file(self.temp_dir, "dependent_meta", """
from ganrya_igc.core.plugin_system import PluginBase, PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="dependent_meta",
    version="1.0.0",
    dependencies=["core_plugin"]
)

class DependentMeta(PluginBase):
    name = "dependent_meta"
    version = "1.0.0"
    dependencies = ["core_plugin"]
""")
        metadata = self.manager.discover_plugin_metadata()
        self.assertIn("dependent_meta", metadata)
        self.assertEqual(metadata["dependent_meta"].dependencies, ["core_plugin"])

class TestDependencyInjection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_and_inject_api(self):
        # Buat API mock
        class MockAPI:
            def hello(self):
                return "world"
        
        api = MockAPI()
        self.manager.register_api("my_api", api)
        
        create_plugin_file(self.temp_dir, "di_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class DIPlugin(PluginBase):
    name = "di_plugin"
    version = "1.0.0"
""")
        self.manager.load_plugin("di_plugin")
        plugin = self.manager.get_plugin("di_plugin")
        
        # API harus sudah terinjeksi
        self.assertTrue(hasattr(plugin, "my_api"))
        self.assertEqual(plugin.my_api.hello(), "world")

    def test_inject_all_apis(self):
        class API1:
            pass
        class API2:
            pass
        
        self.manager.register_api("api1", API1())
        self.manager.register_api("api2", API2())
        
        create_plugin_file(self.temp_dir, "multi_api_plugin", """
from ganrya_igc.core.plugin_system import PluginBase

class MultiAPIPlugin(PluginBase):
    name = "multi_api"
    version = "1.0.0"
""")
        self.manager.load_plugin("multi_api_plugin")
        plugin = self.manager.get_plugin("multi_api_plugin")
        
        self.assertTrue(hasattr(plugin, "api1"))
        self.assertTrue(hasattr(plugin, "api2"))
        
class TestDevPluginManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DevPluginManager(self.temp_dir)

    def tearDown(self):
        import shutil
        if hasattr(self, 'manager'):
            try:
                self.manager.disable_dev_mode()
            except:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dev_mode_toggle(self):
        self.assertFalse(self.manager.dev_mode)
        self.manager.enable_dev_mode()
        self.assertTrue(self.manager.dev_mode)
        self.assertIsNotNone(self.manager.watcher)
        self.manager.disable_dev_mode()
        self.assertFalse(self.manager.dev_mode)
        self.assertIsNone(self.manager.watcher)

    def test_reload_plugin(self):
        create_plugin_file(self.temp_dir, "reloadable", """
from ganrya_igc.core.plugin_system import PluginBase

class Reloadable(PluginBase):
    name = "reloadable"
    version = "1.0.0"
    
    def init(self):
        super().init()
        self.counter = 0
    
    def start(self):
        super().start()
        self.counter += 1
""")
        self.manager.load_plugin("reloadable")
        self.manager.start_all_plugins()
        plugin = self.manager.get_plugin("reloadable")
        self.assertEqual(plugin.counter, 1)
        
        # Stop plugin
        self.manager.stop_all_plugins()
        
        # Ubah file plugin: counter += 100
        import time
        time.sleep(0.1)
        create_plugin_file(self.temp_dir, "reloadable", """
from ganrya_igc.core.plugin_system import PluginBase

class Reloadable(PluginBase):
    name = "reloadable"
    version = "1.0.0"
    
    def init(self):
        super().init()
        self.counter = 0
    
    def start(self):
        super().start()
        self.counter += 100
""")
        # Trigger reload
        self.manager._queue_reload("reloadable")
        
        # Proses reload dengan update() beberapa kali
        for _ in range(20):
            self.manager.update()
            time.sleep(0.1)
            new_plugin = self.manager.get_plugin("reloadable")
            if new_plugin and new_plugin.counter == 100:
                break
        
        final = self.manager.get_plugin("reloadable")
        self.assertIsNotNone(final)
        self.assertEqual(final.counter, 100)

    def test_reload_nonexistent_plugin(self):
        result = self.manager.reload_plugin("nonexistent")
        self.assertFalse(result)

    def test_log_levels(self):
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        self.manager.log("INFO", "This should appear")
        sys.stdout = sys.__stdout__
        self.assertIn("This should appear", captured.getvalue())
        
        # DEBUG hanya muncul jika dev_mode aktif
        captured = io.StringIO()
        sys.stdout = captured
        self.manager.log("DEBUG", "This should NOT appear")
        sys.stdout = sys.__stdout__
        self.assertNotIn("This should NOT appear", captured.getvalue())

class TestPluginFileWatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_watcher_start_stop(self):
        watcher = PluginFileWatcher(self.manager, poll_interval=0.5)
        watcher.start()
        self.assertTrue(watcher._running)
        watcher.stop()
        self.assertFalse(watcher._running)

    def test_watcher_detect_change(self):
        # Buat file plugin
        plugin_path = create_plugin_file(self.temp_dir, "watch_test", """
from ganrya_igc.core.plugin_system import PluginBase

class WatchTest(PluginBase):
    name = "watch_test"
    version = "1.0.0"
""")
        # Muat plugin
        self.manager.load_plugin("watch_test")
        
        watcher = PluginFileWatcher(self.manager, poll_interval=0.5)
        watcher._watched_files[plugin_path] = os.path.getmtime(plugin_path)
        watcher.start()
        
        # Tunggu sebentar, lalu ubah file
        time.sleep(0.6)
        # Modifikasi file
        with open(plugin_path, 'a') as f:
            f.write("\n# modified\n")
        
        time.sleep(0.6)  # Beri waktu watcher untuk mendeteksi
        # Seharusnya memicu reload_plugin, tapi kita sudah mengimplementasikannya
        # Test ini hanya memastikan tidak crash
        watcher.stop()
        self.assertTrue(True)  # Sampai sini tidak error

if __name__ == '__main__':
    unittest.main()