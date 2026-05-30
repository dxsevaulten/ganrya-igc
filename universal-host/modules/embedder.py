"""
Embedder Module - Dynamic Embedding Matrix
Mengelola embedding jendela aplikasi ke dalam Qt widget dengan fitur lengkap
"""
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingSession:
    """Sesi embedding untuk satu aplikasi"""
    pid: int
    hwnd: Optional[int]
    tab_id: int
    app_name: str
    app_path: str
    embedded_at: datetime = field(default_factory=datetime.now)
    is_responsive: bool = True
    child_windows: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pid': self.pid,
            'hwnd': self.hwnd,
            'tab_id': self.tab_id,
            'app_name': self.app_name,
            'app_path': self.app_path,
            'embedded_at': self.embedded_at.isoformat(),
            'is_responsive': self.is_responsive,
            'child_windows': self.child_windows
        }


class EmbeddingManager:
    """
    Mengelola semua sesi embedding aktif.
    Fitur:
    - Multi-tab embedding
    - Deteksi proses anak (Enscape, V-Ray, dll.)
    - Monitoring responsivitas
    - Auto-cleanup saat crash
    """
    
    def __init__(self, window_manager):
        self.window_manager = window_manager
        self.sessions: Dict[int, EmbeddingSession] = {}
        self.tab_to_session: Dict[int, int] = {}  # tab_id -> pid mapping
        self._responsiveness_callbacks: list[Callable] = []
        
    def create_embedding(self, pid: int, app_name: str, app_path: str, 
                         tab_id: int) -> Optional[EmbeddingSession]:
        """
        Membuat sesi embedding baru untuk aplikasi
        
        Args:
            pid: Process ID aplikasi
            app_name: Nama aplikasi
            app_path: Path aplikasi
            tab_id: ID tab di UI
            
        Returns:
            EmbeddingSession jika berhasil, None jika gagal
        """
        try:
            # Cari window handle dari PID
            hwnd = self.window_manager.find_window_by_pid(pid)
            
            if hwnd is None:
                logger.warning(f"No window found for PID {pid}")
                # Tetap buat session tanpa hwnd (untuk aplikasi yang butuh waktu load)
            
            session = EmbeddingSession(
                pid=pid,
                hwnd=hwnd,
                tab_id=tab_id,
                app_name=app_name,
                app_path=app_path
            )
            
            self.sessions[pid] = session
            self.tab_to_session[tab_id] = pid
            
            logger.info(f"Created embedding session: {app_name} (PID: {pid}, Tab: {tab_id})")
            
            # Jika hwnd ditemukan, langsung embed
            if hwnd:
                self._perform_embedding(hwnd, tab_id)
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to create embedding for {app_name}: {e}")
            return None
    
    def _perform_embedding(self, hwnd: int, tab_id: int) -> bool:
        """Melakukan embedding window ke tab"""
        # Diimplementasikan nanti dengan Qt widget actual
        # Untuk sekarang, panggil window_manager.embed_window
        success = self.window_manager.embed_window(hwnd, None)  # parent_widget akan di-set dari UI
        
        if success:
            logger.info(f"Successfully embedded window {hwnd} into tab {tab_id}")
        else:
            logger.error(f"Failed to embed window {hwnd} into tab {tab_id}")
        
        return success
    
    def detect_child_processes(self, parent_pid: int) -> list[int]:
        """
        Mendeteksi proses anak dari parent PID
        Berguna untuk mendeteksi Enscape, V-Ray, dll.
        
        Args:
            parent_pid: PID proses parent
            
        Returns:
            List PID proses anak
        """
        try:
            import psutil
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            child_pids = [child.pid for child in children]
            
            if child_pids:
                logger.info(f"Detected {len(child_pids)} child processes for PID {parent_pid}")
                
                # Update session dengan child windows info
                if parent_pid in self.sessions:
                    self.sessions[parent_pid].child_windows = child_pids
            
            return child_pids
            
        except ImportError:
            logger.warning("psutil not available, cannot detect child processes")
            return []
        except Exception as e:
            logger.error(f"Error detecting child processes: {e}")
            return []
    
    def check_responsiveness(self, pid: int) -> bool:
        """
        Mengecek apakah aplikasi masih responsif
        
        Args:
            pid: Process ID
            
        Returns:
            True jika responsif, False jika tidak/hang
        """
        if pid not in self.sessions:
            return False
        
        try:
            import psutil
            process = psutil.Process(pid)
            
            # Cek status proses
            if process.status() == psutil.STATUS_ZOMBIE:
                self.sessions[pid].is_responsive = False
                return False
            
            # Cek apakah window responding (Windows only)
            if self.sessions[pid].hwnd and self.window_manager._win32_available:
                # Implementasi lebih lanjut bisa menggunakan IsHungAppWindow
                pass
            
            self.sessions[pid].is_responsive = True
            return True
            
        except Exception as e:
            logger.error(f"Error checking responsiveness for PID {pid}: {e}")
            self.sessions[pid].is_responsive = False
            return False
    
    def update_hwnd(self, pid: int, hwnd: int) -> None:
        """Update HWND untuk sesi yang sudah ada"""
        if pid in self.sessions:
            old_hwnd = self.sessions[pid].hwnd
            self.sessions[pid].hwnd = hwnd
            
            if old_hwnd and old_hwnd != hwnd:
                # Restore old window dulu
                self.window_manager.restore_window(old_hwnd)
            
            # Embed dengan hwnd baru
            if hwnd:
                self._perform_embedding(hwnd, self.sessions[pid].tab_id)
            
            logger.info(f"Updated HWND for PID {pid}: {old_hwnd} -> {hwnd}")
    
    def get_session_by_tab(self, tab_id: int) -> Optional[EmbeddingSession]:
        """Mendapatkan sesi berdasarkan tab_id"""
        pid = self.tab_to_session.get(tab_id)
        if pid:
            return self.sessions.get(pid)
        return None
    
    def get_session_by_pid(self, pid: int) -> Optional[EmbeddingSession]:
        """Mendapatkan sesi berdasarkan PID"""
        return self.sessions.get(pid)
    
    def remove_embedding(self, pid: int) -> bool:
        """
        Menghapus embedding dan cleanup
        
        Args:
            pid: Process ID yang ingin di-remove
            
        Returns:
            True jika berhasil
        """
        if pid not in self.sessions:
            return False
        
        session = self.sessions[pid]
        
        # Restore window jika ada
        if session.hwnd:
            self.window_manager.restore_window(session.hwnd)
        
        # Hapus dari registry
        del self.sessions[pid]
        if session.tab_id in self.tab_to_session:
            del self.tab_to_session[session.tab_id]
        
        logger.info(f"Removed embedding session for PID {pid}")
        return True
    
    def get_all_sessions(self) -> list[EmbeddingSession]:
        """Mendapatkan semua sesi aktif"""
        return list(self.sessions.values())
    
    def cleanup_all(self) -> None:
        """Cleanup semua sesi embedding"""
        pids = list(self.sessions.keys())
        for pid in pids:
            self.remove_embedding(pid)
        logger.info("All embedding sessions cleaned up")


# Helper function
def get_embedder(window_manager) -> EmbeddingManager:
    """Mendapatkan instance EmbeddingManager"""
    return EmbeddingManager(window_manager)
