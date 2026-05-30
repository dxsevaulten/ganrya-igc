"""
Tab Manager - Neural Tab Management System
Mengelola tab UI dengan fitur auto-detect, always-on-top, dan cleanup aman
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TabInfo:
    """Informasi tab"""
    tab_id: int
    title: str
    process_name: str
    pid: Optional[int]
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False
    has_unsaved_changes: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tab_id': self.tab_id,
            'title': self.title,
            'process_name': self.process_name,
            'pid': self.pid,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'has_unsaved_changes': self.has_unsaved_changes
        }


class TabManager:
    """
    Mengelola sistem multi-tab untuk aplikasi yang di-embed.
    Fitur:
    - Auto-create tab untuk setiap jendela baru
    - Label dinamis berdasarkan nama proses
    - Always-on-top saat tab diklik
    - Safe close dengan cleanup
    """
    
    def __init__(self):
        self.tabs: Dict[int, TabInfo] = {}
        self.active_tab_id: Optional[int] = None
        self._next_tab_id: int = 1
        self._tab_widgets: Dict[int, Any] = {}  # tab_id -> Qt widget mapping
        
    def create_tab(self, title: str, process_name: str, 
                   pid: Optional[int] = None) -> int:
        """
        Membuat tab baru
        
        Args:
            title: Judul tab
            process_name: Nama proses (untuk label)
            pid: Process ID (opsional)
            
        Returns:
            tab_id dari tab yang dibuat
        """
        tab_id = self._next_tab_id
        self._next_tab_id += 1
        
        tab_info = TabInfo(
            tab_id=tab_id,
            title=title,
            process_name=process_name,
            pid=pid
        )
        
        self.tabs[tab_id] = tab_info
        logger.info(f"Created tab {tab_id}: {title} (Process: {process_name})")
        
        return tab_id
    
    def activate_tab(self, tab_id: int) -> bool:
        """
        Mengaktifkan tab dan set always-on-top jika perlu
        
        Args:
            tab_id: ID tab yang ingin diaktifkan
            
        Returns:
            True jika berhasil
        """
        if tab_id not in self.tabs:
            logger.warning(f"Tab {tab_id} not found")
            return False
        
        # Deactivate tab sebelumnya
        if self.active_tab_id and self.active_tab_id in self.tabs:
            self.tabs[self.active_tab_id].is_active = False
        
        # Activate tab baru
        self.tabs[tab_id].is_active = True
        self.active_tab_id = tab_id
        
        logger.debug(f"Activated tab {tab_id}: {self.tabs[tab_id].title}")
        
        # Trigger always-on-top untuk window yang di-embed
        self._apply_always_on_top(tab_id)
        
        return True
    
    def _apply_always_on_top(self, tab_id: int) -> None:
        """Menerapkan always-on-top untuk window di tab"""
        # Implementasi akan dipanggil dari UI layer
        logger.debug(f"Apply always-on-top for tab {tab_id}")
    
    def update_tab_title(self, tab_id: int, new_title: str) -> bool:
        """
        Update judul tab
        
        Args:
            tab_id: ID tab
            new_title: Judul baru
            
        Returns:
            True jika berhasil
        """
        if tab_id not in self.tabs:
            return False
        
        old_title = self.tabs[tab_id].title
        self.tabs[tab_id].title = new_title
        
        logger.debug(f"Updated tab {tab_id} title: {old_title} -> {new_title}")
        return True
    
    def update_tab_from_process(self, tab_id: int, process_name: str) -> bool:
        """
        Update informasi tab dari data proses actual
        
        Args:
            tab_id: ID tab
            process_name: Nama proses actual
            
        Returns:
            True jika berhasil
        """
        if tab_id not in self.tabs:
            return False
        
        self.tabs[tab_id].process_name = process_name
        
        # Auto-update title jika masih default
        if self.tabs[tab_id].title.startswith("Tab"):
            self.tabs[tab_id].title = process_name
        
        return True
    
    def mark_unsaved(self, tab_id: int, has_unsaved: bool = True) -> bool:
        """
        Menandai tab memiliki perubahan yang belum disimpan
        
        Args:
            tab_id: ID tab
            has_unsaved: Status unsaved changes
            
        Returns:
            True jika berhasil
        """
        if tab_id not in self.tabs:
            return False
        
        self.tabs[tab_id].has_unsaved_changes = has_unsaved
        logger.debug(f"Tab {tab_id} unsaved changes: {has_unsaved}")
        return True
    
    def get_tab(self, tab_id: int) -> Optional[TabInfo]:
        """Mendapatkan informasi tab"""
        return self.tabs.get(tab_id)
    
    def get_active_tab(self) -> Optional[TabInfo]:
        """Mendapatkan tab yang sedang aktif"""
        if self.active_tab_id:
            return self.tabs.get(self.active_tab_id)
        return None
    
    def get_all_tabs(self) -> List[TabInfo]:
        """Mendapatkan semua tab"""
        return list(self.tabs.values())
    
    def remove_tab(self, tab_id: int, force: bool = False) -> bool:
        """
        Menghapus tab dengan safe cleanup
        
        Args:
            tab_id: ID tab yang akan dihapus
            force: Paksa hapus tanpa konfirmasi unsaved changes
            
        Returns:
            True jika berhasil dihapus
        """
        if tab_id not in self.tabs:
            logger.warning(f"Tab {tab_id} not found")
            return False
        
        tab = self.tabs[tab_id]
        
        # Cek unsaved changes
        if tab.has_unsaved_changes and not force:
            logger.warning(f"Tab {tab_id} has unsaved changes")
            # Di UI actual, tampilkan dialog konfirmasi di sini
            return False
        
        # Cleanup widget jika ada
        if tab_id in self._tab_widgets:
            del self._tab_widgets[tab_id]
        
        # Hapus tab
        del self.tabs[tab_id]
        
        # Jika tab yang dihapus adalah active, pilih tab lain
        if self.active_tab_id == tab_id:
            self.active_tab_id = None
            # Pilih tab pertama yang tersedia
            remaining_tabs = list(self.tabs.keys())
            if remaining_tabs:
                self.activate_tab(remaining_tabs[0])
        
        logger.info(f"Removed tab {tab_id}: {tab.title}")
        return True
    
    def register_widget(self, tab_id: int, widget: Any) -> None:
        """Mendaftarkan Qt widget untuk tab"""
        self._tab_widgets[tab_id] = widget
        logger.debug(f"Registered widget for tab {tab_id}")
    
    def get_widget(self, tab_id: int) -> Optional[Any]:
        """Mendapatkan Qt widget untuk tab"""
        return self._tab_widgets.get(tab_id)
    
    def close_all_tabs(self, force: bool = False) -> int:
        """
        Menutup semua tab
        
        Args:
            force: Paksa tutup tanpa konfirmasi
            
        Returns:
            Jumlah tab yang ditutup
        """
        tab_ids = list(self.tabs.keys())
        closed_count = 0
        
        for tab_id in tab_ids:
            if self.remove_tab(tab_id, force=force):
                closed_count += 1
        
        logger.info(f"Closed {closed_count} tabs")
        return closed_count
    
    def get_tab_count(self) -> int:
        """Mendapatkan jumlah tab aktif"""
        return len(self.tabs)


# Helper function
def get_tab_manager() -> TabManager:
    """Mendapatkan instance TabManager"""
    return TabManager()
