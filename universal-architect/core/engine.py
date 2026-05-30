"""
Universal Digital Architect - Core Engine
Singleton pattern untuk mengelola state global aplikasi
"""

from typing import Optional, Dict, Any
import logging

class CoreEngine:
    """
    Core Engine sebagai singleton untuk mengelola:
    - State global aplikasi
    - Registry proses yang sedang berjalan
    - Konfigurasi sistem
    - Log terpusat
    """
    
    _instance: Optional['CoreEngine'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._process_registry: Dict[int, Dict[str, Any]] = {}
        self._config: Dict[str, Any] = {}
        
        # Setup logging
        self.logger = logging.getLogger('UniversalArchitect')
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def register_process(self, pid: int, app_info: Dict[str, Any]) -> None:
        """Mendaftarkan proses aplikasi ke registry"""
        self._process_registry[pid] = {
            'info': app_info,
            'status': 'running',
            'tabs': []
        }
        self.logger.info(f"Process registered: PID={pid}, Name={app_info.get('name', 'Unknown')}")
    
    def unregister_process(self, pid: int) -> None:
        """Menghapus proses dari registry"""
        if pid in self._process_registry:
            del self._process_registry[pid]
            self.logger.info(f"Process unregistered: PID={pid}")
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan informasi proses"""
        return self._process_registry.get(pid)
    
    def get_all_processes(self) -> Dict[int, Dict[str, Any]]:
        """Mendapatkan semua proses yang terdaftar"""
        return self._process_registry.copy()
    
    def update_process_status(self, pid: int, status: str) -> None:
        """Update status proses"""
        if pid in self._process_registry:
            self._process_registry[pid]['status'] = status
            self.logger.debug(f"Process {pid} status updated to: {status}")
    
    def set_config(self, key: str, value: Any) -> None:
        """Set konfigurasi"""
        self._config[key] = value
        self.logger.debug(f"Config set: {key}={value}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get konfigurasi"""
        return self._config.get(key, default)
    
    def cleanup(self) -> None:
        """Cleanup semua resource"""
        self._process_registry.clear()
        self._config.clear()
        self.logger.info("CoreEngine cleaned up")


# Singleton instance getter
def get_engine() -> CoreEngine:
    """Mendapatkan instance CoreEngine"""
    return CoreEngine()
