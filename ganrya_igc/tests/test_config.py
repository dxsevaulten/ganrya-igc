# ganrya_igc/tests/test_config.py
import unittest
import tempfile
import os
import json
import time
from ganrya_igc.core.config import Config
from ganrya_igc.core.config import ConfigSchema, ConfigValidationError
from ganrya_igc.core.config import ConfigPresetManager

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = Config({'app': {'name': 'Ganrya', 'version': '1.0'}})

    def test_default_value(self):
        self.assertEqual(self.config.get('app.name'), 'Ganrya')
        self.assertEqual(self.config.get('app.version'), '1.0')

    def test_missing_key_returns_default(self):
        self.assertEqual(self.config.get('missing.key', 42), 42)
        self.assertIsNone(self.config.get('missing.key'))

    def test_application_override(self):
        self.config.load_application(self._write_temp({'app': {'name': 'MyApp'}}))
        self.assertEqual(self.config.get('app.name'), 'MyApp')

    def test_user_override(self):
        self.config.load_application(self._write_temp({'app.name': 'AppLevel'}))
        self.config.load_user(self._write_temp({'app.name': 'UserLevel'}))
        self.assertEqual(self.config.get('app.name'), 'UserLevel')

    def test_nested_key(self):
        self.config.set_defaults({'viewport': {'width': 1920}})
        self.config.load_user(self._write_temp({'viewport': {'height': 1080}}))
        self.assertEqual(self.config.get('viewport.width'), 1920)
        self.assertEqual(self.config.get('viewport.height'), 1080)

    def test_set_and_save_user(self):
        self.config.set_user('ui.theme', 'dark')
        path = os.path.join(tempfile.mkdtemp(), 'user_config.json')
        self.config.save_user(path)
        # Muat kembali di instance baru
        config2 = Config()
        config2.load_user(path)
        self.assertEqual(config2.get('ui.theme'), 'dark')

    def _write_temp(self, data: dict) -> str:
        """Tulis dictionary ke file JSON temporary, kembalikan path-nya."""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        self.addCleanup(os.unlink, path)
        return path
    
class TestConfigSchema(unittest.TestCase):
    def setUp(self):
        self.config = Config({
            'app': {'name': 'Ganrya', 'version': '1.0'},
            'viewport': {'width': 1920, 'height': 1080}
        })
        self.schema = ConfigSchema({
            'app.name': 'str',
            'app.version': 'str',
            'viewport.width': 'int',
            'viewport.height': 'int',
        })

    def test_valid_config_passes(self):
        is_valid, errors = self.schema.validate(self.config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_invalid_type_returns_error(self):
        self.config.set_user('viewport.width', 'not_an_int')
        is_valid, errors = self.schema.validate(self.config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_missing_optional_key_is_ok(self):
        # Kunci yang tidak ada di schema tidak divalidasi
        self.config.set_user('new_feature', True)
        is_valid, _ = self.schema.validate(self.config)
        self.assertTrue(is_valid)

    def test_validate_or_raise(self):
        self.schema.validate_or_raise(self.config)  # no exception

    def test_validate_or_raise_throws_on_error(self):
        self.config.set_user('app.name', 123)
        with self.assertRaises(ConfigValidationError):
            self.schema.validate_or_raise(self.config)

class TestHotReload(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.user_path = os.path.join(self.temp_dir, 'user.json')
        # Tulis konfigurasi awal
        with open(self.user_path, 'w') as f:
            json.dump({'ui': {'theme': 'light'}}, f)
        self.config = Config()
        self.config.load_user(self.user_path)

    def tearDown(self):
        if hasattr(self.config, '_hot_reload') and self.config._hot_reload:
            self.config.disable_hot_reload()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_hot_reload_detects_change(self):
        self.config.enable_hot_reload(poll_interval=0.3)
        self.assertEqual(self.config.get('ui.theme'), 'light')
        
        # Ubah file konfigurasi
        time.sleep(0.1)
        with open(self.user_path, 'w') as f:
            json.dump({'ui': {'theme': 'dark'}}, f)
        
        # Tunggu sampai terdeteksi
        for _ in range(10):
            time.sleep(0.2)
            if self.config.get('ui.theme') == 'dark':
                break
        
        self.assertEqual(self.config.get('ui.theme'), 'dark')
        self.config.disable_hot_reload()

    def test_disable_hot_reload_stops_watching(self):
        self.config.enable_hot_reload(poll_interval=0.2)
        self.config.disable_hot_reload()
        self.assertFalse(self.config._hot_reload)

class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.preset_dir = os.path.join(self.temp_dir, 'presets')
        self.config = Config({'app': {'name': 'Ganrya'}})
        self.manager = ConfigPresetManager(self.config, self.preset_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_list_presets(self):
        self.config.set_user('ui.theme', 'dark')
        self.manager.save_preset('dark_mode')
        presets = self.manager.list_presets()
        self.assertIn('dark_mode', presets)

    def test_load_preset(self):
        self.config.set_user('ui.theme', 'light')
        self.manager.save_preset('light_mode')
        
        # Ubah konfigurasi
        self.config.set_user('ui.theme', 'blue')
        self.manager.load_preset('light_mode')
        self.assertEqual(self.config.get('ui.theme'), 'light')

    def test_delete_preset(self):
        self.manager.save_preset('temp_preset')
        self.assertIn('temp_preset', self.manager.list_presets())
        self.manager.delete_preset('temp_preset')
        self.assertNotIn('temp_preset', self.manager.list_presets())

    def test_export_import_preset(self):
        self.config.set_user('viewport.width', 2560)
        self.manager.save_preset('4k')
        
        export_path = os.path.join(self.temp_dir, 'exported_preset.json')
        self.manager.export_preset('4k', export_path)
        self.assertTrue(os.path.isfile(export_path))
        
        # Import ke manager baru
        manager2 = ConfigPresetManager(Config(), self.preset_dir)
        manager2.import_preset(export_path)
        self.assertIn('4k', manager2.list_presets())

class TestEnvironmentConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_environment_default(self):
        # Tulis config dasar
        with open(os.path.join(self.temp_dir, 'config.json'), 'w') as f:
            json.dump({'app': {'name': 'Base'}}, f)
        
        self.config.load_environment(self.temp_dir, env='production')
        self.assertEqual(self.config.get('app.name'), 'Base')
        self.assertEqual(self.config.active_environment, 'production')

    def test_environment_override(self):
        # Tulis config dasar
        with open(os.path.join(self.temp_dir, 'config.json'), 'w') as f:
            json.dump({'app': {'name': 'Base', 'debug': True}}, f)
        
        # Tulis config production (override)
        with open(os.path.join(self.temp_dir, 'config.production.json'), 'w') as f:
            json.dump({'app': {'debug': False}}, f)
        
        self.config.load_environment(self.temp_dir, env='production')
        self.assertEqual(self.config.get('app.name'), 'Base')      # dari base
        self.assertFalse(self.config.get_bool('app.debug'))       # override production

    def test_env_variable_detection(self):
        # Tulis config development
        with open(os.path.join(self.temp_dir, 'config.development.json'), 'w') as f:
            json.dump({'app': {'mode': 'dev'}}, f)
        
        # Set env variable
        os.environ['GANRYA_ENV'] = 'development'
        self.config.load_environment(self.temp_dir)
        self.assertEqual(self.config.get('app.mode'), 'dev')
        self.assertEqual(self.config.active_environment, 'development')