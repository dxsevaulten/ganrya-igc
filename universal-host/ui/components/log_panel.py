"""
UI Components - Real-Time Log Panel
Panel log untuk memantau semua aktivitas mesin secara real-time (F2 toggle)
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class LogEntry:
    """Entri log individual"""
    
    def __init__(self, timestamp: datetime, level: str, message: str, 
                 source: str = ""):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.source = source
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'source': self.source
        }
    
    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.level}: {self.message}"


class LogPanel:
    """
    Panel log real-time dengan fitur:
    - Streaming log entry
    - Filter berdasarkan level
    - Search functionality
    - Auto-scroll
    - Export log
    """
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.entries: deque[LogEntry] = deque(maxlen=max_entries)
        self.is_visible = False
        self.filter_level = "DEBUG"  # Minimum level yang ditampilkan
        self._search_query = ""
        
        # Setup custom handler untuk menangkap log
        self._setup_handler()
    
    def _setup_handler(self) -> None:
        """Setup logging handler khusus untuk panel"""
        class PanelHandler(logging.Handler):
            def __init__(self, panel):
                super().__init__()
                self.panel = panel
            
            def emit(self, record):
                msg = self.format(record)
                self.panel.add_entry(
                    level=record.levelname,
                    message=msg,
                    source=record.name
                )
        
        handler = PanelHandler(self)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        # Add handler ke root logger
        logging.getLogger().addHandler(handler)
        logger.info("Log panel handler initialized")
    
    def add_entry(self, level: str, message: str, source: str = "") -> None:
        """
        Menambahkan entri log
        
        Args:
            level: Level log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Pesan log
            source: Sumber log (nama modul)
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source or "Unknown"
        )
        self.entries.append(entry)
        
        # Debug log untuk tracking
        if level == "ERROR":
            logger.error(f"Log entry added: {message}")
    
    def get_entries(self, limit: Optional[int] = None) -> List[LogEntry]:
        """
        Mendapatkan entri log
        
        Args:
            limit: Jumlah maksimal entri yang dikembalikan
            
        Returns:
            List LogEntry
        """
        entries_list = list(self.entries)
        
        # Apply filter level
        level_priority = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4
        }
        
        min_priority = level_priority.get(self.filter_level, 0)
        filtered = [
            e for e in entries_list 
            if level_priority.get(e.level, 0) >= min_priority
        ]
        
        # Apply search query jika ada
        if self._search_query:
            query_lower = self._search_query.lower()
            filtered = [
                e for e in filtered 
                if query_lower in e.message.lower() or query_lower in e.source.lower()
            ]
        
        if limit:
            return filtered[-limit:]
        
        return filtered
    
    def clear(self) -> None:
        """Menghapus semua entri log"""
        self.entries.clear()
        logger.info("Log panel cleared")
    
    def set_filter(self, level: str) -> None:
        """
        Set filter level minimum
        
        Args:
            level: Level minimum (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level in valid_levels:
            self.filter_level = level
            logger.debug(f"Log filter set to: {level}")
        else:
            logger.warning(f"Invalid log level: {level}")
    
    def set_search(self, query: str) -> None:
        """
        Set search query
        
        Args:
            query: Kata kunci pencarian
        """
        self._search_query = query
        logger.debug(f"Log search query: {query}")
    
    def toggle_visibility(self) -> bool:
        """
        Toggle visibilitas panel
        
        Returns:
            Status visibilitas baru
        """
        self.is_visible = not self.is_visible
        status = "shown" if self.is_visible else "hidden"
        logger.debug(f"Log panel {status}")
        return self.is_visible
    
    def show(self) -> None:
        """Menampilkan panel"""
        self.is_visible = True
    
    def hide(self) -> None:
        """Menyembunyikan panel"""
        self.is_visible = False
    
    def export_logs(self, filepath: str) -> bool:
        """
        Export log ke file
        
        Args:
            filepath: Path file tujuan
            
        Returns:
            True jika berhasil
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("UNIVERSAL HOST - LOG EXPORT\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                
                for entry in self.entries:
                    f.write(str(entry) + "\n")
            
            logger.info(f"Logs exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Mendapatkan statistik log
        
        Returns:
            Dict dengan statistik
        """
        stats = {
            'total_entries': len(self.entries),
            'debug_count': sum(1 for e in self.entries if e.level == 'DEBUG'),
            'info_count': sum(1 for e in self.entries if e.level == 'INFO'),
            'warning_count': sum(1 for e in self.entries if e.level == 'WARNING'),
            'error_count': sum(1 for e in self.entries if e.level == 'ERROR'),
            'critical_count': sum(1 for e in self.entries if e.level == 'CRITICAL')
        }
        return stats


# Helper function
def get_log_panel(max_entries: int = 1000) -> LogPanel:
    """Mendapatkan instance LogPanel"""
    return LogPanel(max_entries)
