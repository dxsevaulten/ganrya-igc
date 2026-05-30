"""
Core Engine - The Heart of Universal Host
Singleton pattern untuk mengelola state global aplikasi
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CoreEngine:
    """
    Singleton Core Engine yang mengelola:
    - State global aplikasi
    - Registry proses yang sedang berjalan
    - Log sistem terpusat
    - Konfigurasi global
    """
    
    _instance: Optional['CoreEngine'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'CoreEngine':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.process_registry: Dict[int, Dict[str, Any]] = {}
            self.active_tabs: Dict[int, Any] = {}
            self.config: Dict[str, Any] = {
                'auto_detect_child_processes': True,
                'enable_loading_overlay': True,
                'log_level': 'INFO',
                'theme': 'system'
            }
            self._setup_logging()
            self._initialized = True
            logger.info("Core Engine initialized")
    
    def _setup_logging(self):
        """Setup logging system terpusat"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('universal_host.log')
            ]
        )
    
    def register_process(self, pid: int, name: str, path: str, hwnd: Optional[int] = None) -> None:
        """Mendaftarkan proses yang sedang dijalankan"""
        self.process_registry[pid] = {
            'name': name,
            'path': path,
            'hwnd': hwnd,
            'started_at': datetime.now(),
            'status': 'running'
        }
        logger.info(f"Process registered: {name} (PID: {pid})")
    
    def unregister_process(self, pid: int) -> None:
        """Menghapus proses dari registry"""
        if pid in self.process_registry:
            del self.process_registry[pid]
            logger.info(f"Process unregistered: PID {pid}")
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Mengambil informasi proses"""
        return self.process_registry.get(pid)
    
    def update_process_hwnd(self, pid: int, hwnd: int) -> None:
        """Update handle window untuk proses"""
        if pid in self.process_registry:
            self.process_registry[pid]['hwnd'] = hwnd
            logger.debug(f"Updated HWND for PID {pid}: {hwnd}")
    
    def add_active_tab(self, tab_id: int, widget: Any) -> None:
        """Menambahkan tab aktif"""
        self.active_tabs[tab_id] = widget
    
    def remove_active_tab(self, tab_id: int) -> None:
        """Menghapus tab aktif"""
        if tab_id in self.active_tabs:
            del self.active_tabs[tab_id]
    
    def get_config(self, key: str) -> Any:
        """Mengambil nilai konfigurasi"""
        return self.config.get(key)
    
    def set_config(self, key: str, value: Any) -> None:
        """Mengatur nilai konfigurasi"""
        self.config[key] = value
        logger.debug(f"Config updated: {key} = {value}")
    
    def shutdown(self) -> None:
        """Shutdown engine dengan aman"""
        logger.info("Shutting down Core Engine...")
        # Cleanup semua proses yang terdaftar jika diperlukan
        self.process_registry.clear()
        self.active_tabs.clear()
        logger.info("Core Engine shutdown complete")


# Helper untuk mendapatkan instance
def get_engine() -> CoreEngine:
    """Mendapatkan instance Core Engine"""
    return CoreEngine()
