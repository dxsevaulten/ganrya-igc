# ganrya_igc/core/plugin_system.py
import importlib
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Callable, Any
import time
import threading

# ========== SUBPLAN 1.3.2: EVENT BUS ==========
EventHandler = Callable[[Any], None]

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler):
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass

    def publish(self, event_type: str, event_data: Any = None):
        for handler in self._subscribers.get(event_type, []):
            handler(event_data)

# ========== SUBPLAN 1.3.1: PLUGIN BASE ==========
class PluginBase(ABC):
    def __init__(self, manager: 'PluginManager'):
        self.manager = manager
        self._initialized = False
        self._running = False
        self.event_bus: Optional[EventBus] = None

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    def dependencies(self) -> List[str]:
        return []

    def init(self):
        self._initialized = True

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def cleanup(self):
        self._initialized = False

# ========== SUBPLAN 1.3.4: METADATA ==========
from dataclasses import dataclass, field

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)

# ========== SUBPLAN 1.3.1 & 1.3.4: PLUGIN MANAGER ==========
class PluginManager:
    def __init__(self, plugin_directory: str):
        self.plugin_directory = plugin_directory
        self.plugins: Dict[str, PluginBase] = {}
        self._loaded_modules: Dict[str, object] = {}
        self._load_order: List[str] = []
        self.event_bus = EventBus()
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
        self._api_registry: Dict[str, Any] = {}

    # --- Discovery (1.3.1 + 1.3.4) ---
    def discover_plugins(self) -> List[str]:
        """Pindai folder plugin dan kembalikan nama file plugin (tanpa .py)."""
        discovered = []
        if not os.path.isdir(self.plugin_directory):
            return discovered
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith('.py') and filename != '__init__.py':
                discovered.append(filename[:-3])
        return discovered

    def discover_plugin_metadata(self) -> Dict[str, PluginMetadata]:
        """Pindai folder plugin dan baca PLUGIN_METADATA dari setiap modul."""
        discovered = {}
        if not os.path.isdir(self.plugin_directory):
            return discovered
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    full_path = os.path.join(self.plugin_directory, filename)
                    spec = importlib.util.spec_from_file_location(module_name, full_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    if hasattr(module, 'PLUGIN_METADATA'):
                        meta = module.PLUGIN_METADATA
                        if isinstance(meta, PluginMetadata):
                            discovered[module_name] = meta
                except Exception as e:
                    print(f"PluginManager: gagal baca metadata '{module_name}': {e}")
        self._plugin_metadata = discovered
        return discovered

    # --- API Registry & Injection (1.3.4) ---
    def register_api(self, api_name: str, api_instance: Any):
        self._api_registry[api_name] = api_instance

    def inject_all_apis(self, plugin: PluginBase):
        for api_name, api_instance in self._api_registry.items():
            setattr(plugin, api_name, api_instance)

    # --- Load / Unload (1.3.1) ---
    def load_plugin(self, plugin_name: str) -> bool:
        try:
            full_path = os.path.join(self.plugin_directory, f"{plugin_name}.py")
            if not os.path.isfile(full_path):
                print(f"PluginManager: file '{full_path}' tidak ditemukan.")
                return False

            spec = importlib.util.spec_from_file_location(plugin_name, full_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)

            plugin_class = self._find_plugin_class(module, plugin_name)
            if plugin_class is None:
                print(f"PluginManager: '{plugin_name}' tidak memiliki kelas PluginBase.")
                return False

            instance = plugin_class(self)

            # Cek dependensi
            for dep in instance.dependencies:
                if dep not in self.plugins:
                    print(f"PluginManager: '{plugin_name}' butuh '{dep}' yang belum dimuat.")
                    return False

            # Pasang metadata jika ada
            if plugin_name in self._plugin_metadata:
                instance.metadata = self._plugin_metadata[plugin_name]

            # Injeksi API dan EventBus
            self.inject_all_apis(instance)
            instance.event_bus = self.event_bus

            self.plugins[plugin_name] = instance
            self._loaded_modules[plugin_name] = module
            self._load_order.append(plugin_name)

            instance.init()
            print(f"PluginManager: plugin '{plugin_name}' v{instance.version} dimuat.")
            return True

        except Exception as e:
            print(f"PluginManager: gagal memuat '{plugin_name}': {e}")
            return False

    def start_all_plugins(self):
        self.event_bus.publish('kernel:plugins:starting', {'count': len(self._load_order)})
        for name in self._load_order:
            plugin = self.plugins[name]
            if not plugin._running:
                plugin.start()
                self.event_bus.publish('plugin:started', {'name': name})
        self.event_bus.publish('kernel:plugins:started', {})

    def stop_all_plugins(self):
        self.event_bus.publish('kernel:plugins:stopping', {})
        for name in reversed(self._load_order):
            plugin = self.plugins[name]
            if plugin._running:
                plugin.stop()
                self.event_bus.publish('plugin:stopped', {'name': name})
        self.event_bus.publish('kernel:plugins:stopped', {})

    def cleanup_all_plugins(self):
        for name in reversed(self._load_order):
            plugin = self.plugins[name]
            if plugin._initialized:
                plugin.cleanup()

    def unload_all_plugins(self):
        self.stop_all_plugins()
        self.cleanup_all_plugins()
        for name in list(self.plugins.keys()):
            self.event_bus.publish('plugin:unloaded', {'name': name})
            del self.plugins[name]
            if name in sys.modules:
                del sys.modules[name]
        self._load_order.clear()
        self._loaded_modules.clear()

    def reload_plugin(self, plugin_name: str) -> bool:
        """Muat ulang plugin dengan nama tertentu (stub)."""
        if plugin_name not in self.plugins:
            return False
        # Unload lalu load ulang
        self.unload_all_plugins()  # atau lebih selektif
        return self.load_plugin(plugin_name)

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        return self.plugins.get(name)

    def _find_plugin_class(self, module, module_name: str) -> Optional[Type[PluginBase]]:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, PluginBase) and
                attr is not PluginBase):
                return attr
        return None
    
class PluginFileWatcher:
    """
    Memantau folder plugin untuk perubahan file dan memicu reload otomatis.
    """
    def __init__(self, manager: 'PluginManager', poll_interval: float = 1.0):
        self.manager = manager
        self.poll_interval = poll_interval
        self._watched_files: Dict[str, float] = {}  # filepath -> last modified time
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Mulai pemantauan di background thread."""
        if self._running:
            return
        self._running = True
        # Catat state awal semua file plugin
        for filename in os.listdir(self.manager.plugin_directory):
            if filename.endswith('.py'):
                full_path = os.path.join(self.manager.plugin_directory, filename)
                self._watched_files[full_path] = os.path.getmtime(full_path)
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        print("PluginFileWatcher: pemantauan dimulai.")
    
    def stop(self):
        """Hentikan pemantauan."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("PluginFileWatcher: pemantauan dihentikan.")
    
    def _watch_loop(self):
        while self._running:
            time.sleep(self.poll_interval)
            self._check_changes()
    
    def _check_changes(self):
        for filepath, last_mtime in list(self._watched_files.items()):
            try:
                current_mtime = os.path.getmtime(filepath)
                if current_mtime > last_mtime:
                    print(f"PluginFileWatcher: perubahan terdeteksi pada {filepath}")
                    # Reload plugin yang sesuai
                    module_name = os.path.basename(filepath)[:-3]
                    if module_name in self.manager.plugins:
                        self.manager.reload_plugin(module_name)
                    self._watched_files[filepath] = current_mtime
            except OSError:
                # File mungkin dihapus atau dipindahkan
                pass

class DevPluginManager(PluginManager):
    """PluginManager dengan dukungan hot-reload, dev mode, dan logging."""
    
    def __init__(self, plugin_directory: str):
        super().__init__(plugin_directory)
        self.dev_mode = False
        self._observer = None
        self._reload_queue: Dict[str, float] = {}
        self._polling = False
        self._file_mtimes: Dict[str, float] = {}
    
    # --- Dev Mode ---
    def enable_dev_mode(self):
        self.dev_mode = True
        self.enable_hot_reload()
        print("DevPluginManager: Dev mode enabled.")
    
    def disable_dev_mode(self):
        self.dev_mode = False
        self.disable_hot_reload()
        print("DevPluginManager: Dev mode disabled.")
    
    # --- Logging ---
    def log(self, level: str, message: str):
        """Log dengan level filtering. DEBUG hanya muncul jika dev_mode aktif."""
        if level == "DEBUG" and not self.dev_mode:
            return
        print(f"[{level}] {message}")
    
    # --- Hot Reload ---
    def enable_hot_reload(self):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class PluginFileHandler(FileSystemEventHandler):
                def __init__(self, manager):
                    self.manager = manager
                def on_modified(self, event):
                    if event.src_path.endswith('.py'):
                        name = os.path.splitext(os.path.basename(event.src_path))[0]
                        self.manager._queue_reload(name)
            
            self._observer = Observer()
            self._observer.schedule(PluginFileHandler(self), self.plugin_directory, recursive=False)
            self._observer.start()
            self.watcher = self._observer  # ← tambahkan
            print("DevPluginManager: Hot-reload enabled (watchdog).")
        except ImportError:
            print("DevPluginManager: watchdog not installed, using polling fallback.")
            self._polling = True
            self.watcher = True  # ← tambahkan (flag polling aktif)
    
    def disable_hot_reload(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._polling = False
        self.watcher = None  # ← tambahkan
    
    def _queue_reload(self, plugin_name: str):
        self._reload_queue[plugin_name] = time.time()
        print(f"DevPluginManager: Queued reload for '{plugin_name}'")
    
    def _try_reload_plugin(self, plugin_name: str):
        if plugin_name not in self._reload_queue:
            return
        last_change = self._reload_queue.pop(plugin_name)
        if time.time() - last_change < 0.4:
            self._reload_queue[plugin_name] = last_change
            return
        
        print(f"DevPluginManager: Reloading '{plugin_name}'...")
        if plugin_name in self.plugins:
            old = self.plugins[plugin_name]
            old.stop()
            old.cleanup()
        
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]
        
        success = self.load_plugin(plugin_name)
        if success:
            self.plugins[plugin_name].start()
            print(f"DevPluginManager: '{plugin_name}' reloaded and started.")
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload plugin secara manual (untuk pengujian)."""
        if plugin_name not in self.plugins:
            print(f"DevPluginManager: Plugin '{plugin_name}' tidak dimuat.")
            return False
        self._queue_reload(plugin_name)
        self._try_reload_plugin(plugin_name)
        return plugin_name in self.plugins
    
    def update(self):
        """Panggil secara periodik untuk memproses reload queue."""
        if self._polling:
            self._poll_changes()
        for name in list(self._reload_queue.keys()):
            self._try_reload_plugin(name)
    
    def _poll_changes(self):
        if not os.path.isdir(self.plugin_directory):
            return
        for fname in os.listdir(self.plugin_directory):
            if not fname.endswith('.py') or fname == '__init__.py':
                continue
            fpath = os.path.join(self.plugin_directory, fname)
            try:
                mtime = os.path.getmtime(fpath)
                name = fname[:-3]
                if name in self.plugins:
                    if name not in self._file_mtimes or mtime > self._file_mtimes[name]:
                        self._file_mtimes[name] = mtime
                        self._queue_reload(name)
            except OSError:
                pass