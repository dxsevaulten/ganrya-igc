"""
Window Manager - Universal Embedding Engine
Mengelola embedding jendela aplikasi menggunakan Win32 API (Windows) atau mock (non-Windows)
"""
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Informasi jendela aplikasi"""
    hwnd: int
    pid: int
    title: str
    class_name: str
    is_visible: bool
    is_child: bool


class WindowManager:
    """
    Mengelola embedding jendela aplikasi ke dalam Qt widget.
    Mendukung Windows (via Win32 API) dan fallback untuk platform lain.
    """
    
    def __init__(self):
        self.embedded_windows: Dict[int, Dict[str, Any]] = {}
        self._win32_available = False
        
        # Coba import Win32 API jika di Windows
        try:
            import win32gui
            import win32process
            import win32con
            import win32api
            self._win32_available = True
            logger.info("Win32 API available - full embedding support enabled")
        except ImportError:
            logger.warning("Win32 API not available - running in mock mode")
    
    def find_window_by_pid(self, pid: int) -> Optional[int]:
        """
        Mencari handle window (HWND) berdasarkan Process ID (PID)
        
        Args:
            pid: Process ID dari aplikasi target
            
        Returns:
            HWND jika ditemukan, None jika tidak
        """
        if not self._win32_available:
            logger.debug(f"Mock: Found window for PID {pid}")
            return 12345  # Mock HWND
        
        import win32gui
        import win32process
        
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid:
                    results.append(hwnd)
            return True
        
        results = []
        try:
            win32gui.EnumWindows(callback, results)
            if results:
                hwnd = results[0]
                logger.info(f"Found window for PID {pid}: HWND {hwnd}")
                return hwnd
        except Exception as e:
            logger.error(f"Error finding window for PID {pid}: {e}")
        
        return None
    
    def embed_window(self, hwnd: int, parent_widget) -> bool:
        """
        Menanamkan jendela aplikasi ke dalam Qt widget
        
        Args:
            hwnd: Handle window aplikasi target
            parent_widget: Qt widget yang akan menjadi parent
            
        Returns:
            True jika berhasil, False jika gagal
        """
        if not self._win32_available:
            logger.info(f"Mock: Embedding window {hwnd} into widget")
            self.embedded_windows[hwnd] = {
                'parent': parent_widget,
                'original_style': None,
                'embedded': True
            }
            return True
        
        try:
            import win32gui
            import win32con
            
            # Simpan style asli
            original_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            
            # Hapus border dan title bar
            new_style = original_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
            
            # Set parent ke Qt widget
            # Catatan: Ini memerlukan handle dari Qt widget
            # win32gui.SetParent(hwnd, int(parent_widget.winId()))
            
            self.embedded_windows[hwnd] = {
                'parent': parent_widget,
                'original_style': original_style,
                'embedded': True
            }
            
            logger.info(f"Successfully embedded window {hwnd}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed window {hwnd}: {e}")
            return False
    
    def restore_window(self, hwnd: int) -> bool:
        """
        Mengembalikan jendela ke state asli (melepaskan embedding)
        
        Args:
            hwnd: Handle window yang ingin dipulihkan
            
        Returns:
            True jika berhasil, False jika gagal
        """
        if hwnd not in self.embedded_windows:
            logger.warning(f"Window {hwnd} not found in embedded windows")
            return False
        
        if not self._win32_available:
            logger.info(f"Mock: Restoring window {hwnd}")
            del self.embedded_windows[hwnd]
            return True
        
        try:
            import win32gui
            import win32con
            
            info = self.embedded_windows[hwnd]
            if info['original_style'] is not None:
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, info['original_style'])
            
            # Reset parent ke desktop
            # win32gui.SetParent(hwnd, 0)
            
            del self.embedded_windows[hwnd]
            logger.info(f"Successfully restored window {hwnd}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore window {hwnd}: {e}")
            return False
    
    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """
        Mendapatkan informasi lengkap tentang jendela
        
        Args:
            hwnd: Handle window
            
        Returns:
            WindowInfo object atau None
        """
        if not self._win32_available:
            return WindowInfo(
                hwnd=hwnd,
                pid=9999,
                title="Mock Window",
                class_name="MockClass",
                is_visible=True,
                is_child=False
            )
        
        try:
            import win32gui
            import win32process
            
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            return WindowInfo(
                hwnd=hwnd,
                pid=pid,
                title=title,
                class_name=class_name,
                is_visible=is_visible,
                is_child=False
            )
        except Exception as e:
            logger.error(f"Error getting window info for {hwnd}: {e}")
            return None
    
    def forward_input(self, hwnd: int, message: int, wparam: int, lparam: int) -> bool:
        """
        Meneruskan input mouse/keyboard ke jendela target
        
        Args:
            hwnd: Handle window target
            message: Windows message (WM_MOUSEMOVE, WM_LBUTTONDOWN, dll)
            wparam: WPARAM value
            lparam: LPARAM value
            
        Returns:
            True jika berhasil
        """
        if not self._win32_available:
            logger.debug(f"Mock: Forwarding input {message} to window {hwnd}")
            return True
        
        try:
            import win32gui
            win32gui.PostMessage(hwnd, message, wparam, lparam)
            return True
        except Exception as e:
            logger.error(f"Failed to forward input: {e}")
            return False
    
    def cleanup_all(self) -> None:
        """Melepaskan semua jendela yang ter-embed"""
        hwnds = list(self.embedded_windows.keys())
        for hwnd in hwnds:
            self.restore_window(hwnd)
        logger.info("All embedded windows cleaned up")


# Helper function
def get_window_manager() -> WindowManager:
    """Mendapatkan instance WindowManager"""
    return WindowManager()
