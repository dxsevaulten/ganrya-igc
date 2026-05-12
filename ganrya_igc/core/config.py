# ganrya_igc/core/config.py
"""
Plan 1.6: Sistem Konfigurasi & Preferensi.
Subplan 1.6.1: Hierarchical Configuration System.
"""

import json
import os
from typing import Any, Dict, Optional
import threading
import time

class Config:
    def __init__(self, defaults: Optional[Dict[str, Any]] = None):
        # defaults bisa flat {'a.b': 1} atau nested {'a': {'b': 1}}
        self._defaults = {}
        self._application = {}
        self._user = {}
        if defaults:
            self.set_defaults(defaults)

    def set_defaults(self, defaults: Dict[str, Any]):
        """Simpan default sebagai nested dict."""
        self._defaults = self._flatten_to_nested(defaults)

    def load_application(self, filepath: str):
        data = self._load_json(filepath)
        self._application = self._flatten_to_nested(data)

    def enable_hot_reload(self, poll_interval: float = 1.0):
        """
        Aktifkan pemantauan perubahan file user config.
        Jika file berubah, otomatis dimuat ulang.
        """
        if not hasattr(self, '_user_filepath'):
            raise RuntimeError("Panggil load_user() dulu sebelum enable_hot_reload()")
        
        self._hot_reload = True
        self._poll_interval = poll_interval
        
        def watch():
            last_mtime = os.path.getmtime(self._user_filepath) if os.path.isfile(self._user_filepath) else 0
            while getattr(self, '_hot_reload', False):
                time.sleep(poll_interval)
                if not os.path.isfile(self._user_filepath):
                    continue
                current_mtime = os.path.getmtime(self._user_filepath)
                if current_mtime > last_mtime:
                    print(f"Config: mendeteksi perubahan pada '{self._user_filepath}', memuat ulang...")
                    self.load_user(self._user_filepath)
                    last_mtime = current_mtime
        
        self._watch_thread = threading.Thread(target=watch, daemon=True)
        self._watch_thread.start()
        print(f"Config: hot-reload aktif untuk '{self._user_filepath}' (polling setiap {poll_interval}s)")

    def disable_hot_reload(self):
        """Nonaktifkan pemantauan perubahan."""
        self._hot_reload = False
        if hasattr(self, '_watch_thread'):
            self._watch_thread.join(timeout=2)
        print("Config: hot-reload dinonaktifkan")

    def load_user(self, filepath: str):
        """Muat konfigurasi pengguna dan simpan path untuk hot-reload."""
        self._user_filepath = filepath
        data = self._load_json(filepath)
        self._user = self._flatten_to_nested(data)

    def set_user(self, key: str, value: Any):
        """Set nilai user dengan dukungan kunci bertitik."""
        parts = key.split('.')
        target = self._user
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

    def apply_user_override(self, overrides: Dict[str, Any]):
        """Terapkan override manual (misal dari command line)."""
        self._user.update(overrides)

    # ----- Baca Nilai -----
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('.')
        # Cari di user
        val = self._get_from_dict(self._user, parts)
        if val is not None:
            return val
        # Cari di application
        val = self._get_from_dict(self._application, parts)
        if val is not None:
            return val
        # Cari di defaults
        val = self._get_from_dict(self._defaults, parts)
        return val if val is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self.get(key, default))

    def get_float(self, key: str, default: float = 0.0) -> float:
        return float(self.get(key, default))

    def get_str(self, key: str, default: str = '') -> str:
        return str(self.get(key, default))

    # ----- Tulis & Simpan -----
    def set_user(self, key: str, value: Any):
        """Tulis nilai ke konfigurasi pengguna (in-memory)."""
        parts = key.split('.')
        target = self._user
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    def save_user(self, filepath: str):
        """Simpan konfigurasi pengguna ke file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._user, f, indent=2)

    def as_dict(self) -> Dict[str, Any]:
        """Kembalikan seluruh konfigurasi sebagai dictionary (gabungan semua sumber)."""
        result = self._defaults.copy()
        self._deep_update(result, self._application)
        self._deep_update(result, self._user)
        return result

    # ----- Bantuan Internal -----
    @staticmethod
    def _load_json(filepath: str) -> Dict[str, Any]:
        if not os.path.isfile(filepath):
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _get_from_dict(data: Dict[str, Any], parts: list) -> Any:
        current = data
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    @staticmethod
    def _deep_update(base: dict, override: dict):
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                Config._deep_update(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _flatten_to_nested(data: Dict[str, Any]) -> dict:
        """Konversi flat dict dengan kunci bertitik menjadi nested dict."""
        nested = {}
        for key, value in data.items():
            parts = key.split('.')
            target = nested
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
        return nested
    
    def load_environment(self, base_dir: str, env: str = None):
        """
        Muat konfigurasi berdasarkan environment.
        Mencari file: {base_dir}/config.json (default) dan
                       {base_dir}/config.{env}.json (environment-specific).
        Environment dibaca dari ENV atau parameter.
        """
        if env is None:
            env = os.environ.get('GANRYA_ENV', 'development')
        
        # Muat konfigurasi dasar
        base_path = os.path.join(base_dir, 'config.json')
        if os.path.isfile(base_path):
            self.load_application(base_path)
        
        # Muat konfigurasi environment-specific (override)
        env_path = os.path.join(base_dir, f'config.{env}.json')
        if os.path.isfile(env_path):
            env_data = self._load_json(env_path)
            self._deep_update(self._application, self._flatten_to_nested(env_data))
            print(f"Config: environment '{env}' dimuat dari {env_path}")
        else:
            print(f"Config: environment '{env}' (tidak ada file khusus)")
        
        self._active_environment = env

    @property
    def active_environment(self) -> str:
        """Kembalikan environment yang sedang aktif."""
        return getattr(self, '_active_environment', 'development')
    
# ========== SUBPLAN 1.6.2: SCHEMA VALIDATION ==========

from typing import Tuple, List, Union, get_type_hints, get_origin


class ConfigValidationError(Exception):
    """Exception yang dilempar saat validasi konfigurasi gagal."""
    def __init__(self, key: str, expected: str, actual: Any):
        self.key = key
        self.expected = expected
        self.actual = actual
        super().__init__(f"Konfigurasi '{key}': diharapkan {expected}, dapat {type(actual).__name__} = {actual}")


class ConfigSchema:
    """
    Validasi schema untuk konfigurasi.
    Mendefinisikan tipe yang diharapkan untuk setiap kunci.
    """
    
    # Registri tipe yang didukung
    TYPE_MAP = {
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
    }
    
    def __init__(self, schema: Dict[str, str] = None):
        """
        schema: dictionary yang memetakan kunci ke tipe yang diharapkan.
        Contoh: {'app.name': 'str', 'app.version': 'str', 'viewport.width': 'int'}
        """
        self._schema = schema or {}
    
    def add_field(self, key: str, expected_type: str):
        self._schema[key] = expected_type
    
    def validate(self, config: Config) -> Tuple[bool, List[str]]:
        """
        Validasi konfigurasi terhadap schema.
        Mengembalikan (is_valid, list_of_errors).
        """
        errors = []
        for key, expected_type in self._schema.items():
            value = config.get(key)
            if value is None:
                continue  # opsional
            
            if not self._check_type(value, expected_type):
                errors.append(
                    f"'{key}': diharapkan {expected_type}, dapat {type(value).__name__}"
                )
        return len(errors) == 0, errors
    
    def validate_or_raise(self, config: Config):
        """Validasi dan lempar exception jika gagal."""
        is_valid, errors = self.validate(config)
        if not is_valid:
            raise ConfigValidationError(
                'schema', 'valid configuration', '; '.join(errors)
            )
    
    def _check_type(self, value: Any, expected: str) -> bool:
        """Periksa apakah tipe nilai sesuai dengan yang diharapkan."""
        if expected == 'int':
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected == 'float':
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected == 'str':
            return isinstance(value, str)
        elif expected == 'bool':
            return isinstance(value, bool)
        elif expected == 'list':
            return isinstance(value, list)
        elif expected == 'dict':
            return isinstance(value, dict)
        return True  # type unknown, skip
    
# ========== SUBPLAN 1.6.4: USER PRESETS & PROFILES ==========

class ConfigPresetManager:
    """
    Mengelola preset konfigurasi. Setiap preset adalah dictionary
    yang dapat disimpan, dimuat, dan diterapkan ke Config.
    """

    def __init__(self, config: Config, preset_dir: str):
        self.config = config
        self.preset_dir = preset_dir
        os.makedirs(preset_dir, exist_ok=True)

    def list_presets(self) -> list:
        """Kembalikan daftar nama preset yang tersedia (tanpa ekstensi)."""
        if not os.path.isdir(self.preset_dir):
            return []
        return [
            f[:-5] for f in os.listdir(self.preset_dir)
            if f.endswith('.json')
        ]

    def save_preset(self, name: str):
        """Simpan konfigurasi pengguna saat ini sebagai preset."""
        filepath = os.path.join(self.preset_dir, f"{name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.config._user, f, indent=2)
        print(f"Preset '{name}' disimpan ke {filepath}")

    def load_preset(self, name: str):
        """Muat preset dan terapkan sebagai konfigurasi pengguna."""
        filepath = os.path.join(self.preset_dir, f"{name}.json")
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Preset '{name}' tidak ditemukan")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.config._user = self.config._flatten_to_nested(json.load(f))
        print(f"Preset '{name}' dimuat")

    def delete_preset(self, name: str):
        """Hapus preset berdasarkan nama."""
        filepath = os.path.join(self.preset_dir, f"{name}.json")
        if os.path.isfile(filepath):
            os.remove(filepath)
            print(f"Preset '{name}' dihapus")

    def export_preset(self, name: str, export_path: str):
        """Ekspor preset ke file .json eksternal."""
        filepath = os.path.join(self.preset_dir, f"{name}.json")
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Preset '{name}' tidak ditemukan")
        import shutil
        shutil.copy(filepath, export_path)
        print(f"Preset '{name}' diekspor ke {export_path}")

    def import_preset(self, import_path: str):
        """Impor preset dari file .json eksternal."""
        if not os.path.isfile(import_path):
            raise FileNotFoundError(f"File '{import_path}' tidak ditemukan")
        name = os.path.splitext(os.path.basename(import_path))[0]
        dest = os.path.join(self.preset_dir, f"{name}.json")
        import shutil
        shutil.copy(import_path, dest)
        print(f"Preset '{name}' diimpor dari {import_path}")