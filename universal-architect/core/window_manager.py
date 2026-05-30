"""
Universal Digital Architect - Window Manager
Mengelola embedding jendela aplikasi menggunakan Win32 API (Windows) atau mock (non-Windows)
"""

import sys
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class WindowInfo:
    """Informasi jendela"""
    hwnd: int
    title: str
    pid: int
    class_name: str


class WindowManager:
    """
    WindowManager untuk:
    - Mendeteksi jendela aplikasi
    - Embedding jendela ke widget Qt
    - Menghilangkan border dan title bar
    - Forwarding input
    """
    
    def __init__(self):
        self._embedded_windows = {}
        self._is_windows = sys.platform == 'win32'
        
        if self._is_windows:
            try:
                import win32gui
                import win32con
                import win32process
                self._win32_available = True
            except ImportError:
                self._win32_available = False
        else:
            self._win32_available = False
    
    def find_window_by_pid(self, pid: int) -> Optional[WindowInfo]:
        """Mencari jendela utama berdasarkan PID"""
        if not self._is_windows or not self._win32_available:
            # Mock untuk non-Windows
            return WindowInfo(hwnd=12345, title="Mock Window", pid=pid, class_name="MockClass")
        
        import win32gui
        import win32process
        
        def enum_callback(hwnd, results):
            try:
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    if title:  # Hanya jendela dengan title
                        results.append((hwnd, title, class_name))
            except Exception:
                pass
            return True
        
        windows = []
        win32gui.EnumWindows(enum_callback, windows)
        
        if windows:
            # Ambil jendela pertama yang cocok
            hwnd, title, class_name = windows[0]
            return WindowInfo(hwnd=hwnd, title=title, pid=pid, class_name=class_name)
        
        return None
    
    def embed_window(self, hwnd: int, parent_widget) -> bool:
        """
        Embed jendela aplikasi ke widget Qt
        Menggunakan SetParent untuk menanamkan jendela
        """
        if not self._is_windows or not self._win32_available:
            # Mock untuk non-Windows
            self._embedded_windows[hwnd] = {
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
            
            # Hapus WS_BORDER dan WS_CAPTION
            new_style = original_style & ~win32con.WS_BORDER & ~win32con.WS_CAPTION
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
            
            # Set parent ke widget Qt
            from PyQt6.QtWidgets import QWidget
            if isinstance(parent_widget, QWidget):
                # Gunakan win32gui.SetParent
                win32gui.SetParent(hwnd, int(parent_widget.winId()))
                
                # Resize untuk mengisi parent
                self.resize_window_to_parent(hwnd, parent_widget)
                
                self._embedded_windows[hwnd] = {
                    'parent': parent_widget,
                    'original_style': original_style,
                    'embedded': True
                }
                return True
            
        except Exception as e:
            print(f"Error embedding window: {e}")
            return False
        
        return False
    
    def resize_window_to_parent(self, hwnd: int, parent_widget) -> None:
        """Resize jendela embedded agar sesuai dengan parent"""
        if not self._is_windows or not self._win32_available:
            return
        
        try:
            import win32gui
            import win32con
            
            # Dapatkan ukuran parent
            from PyQt6.QtWidgets import QWidget
            if isinstance(parent_widget, QWidget):
                rect = parent_widget.rect()
                width = rect.width()
                height = rect.height()
                
                # Set posisi dan ukuran
                win32gui.MoveWindow(hwnd, 0, 0, width, height, True)
                
        except Exception as e:
            print(f"Error resizing window: {e}")
    
    def restore_window(self, hwnd: int) -> bool:
        """Restore jendela ke state asli (lepas dari embedding)"""
        if hwnd not in self._embedded_windows:
            return False
        
        if not self._is_windows or not self._win32_available:
            del self._embedded_windows[hwnd]
            return True
        
        try:
            import win32gui
            
            info = self._embedded_windows[hwnd]
            if info['original_style'] is not None:
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, info['original_style'])
            
            # Reset parent ke desktop
            win32gui.SetParent(hwnd, 0)
            
            del self._embedded_windows[hwnd]
            return True
            
        except Exception as e:
            print(f"Error restoring window: {e}")
            return False
    
    def get_embedded_windows(self) -> List[int]:
        """Mendapatkan daftar semua jendela yang sedang embedded"""
        return list(self._embedded_windows.keys())
    
    def is_embedded(self, hwnd: int) -> bool:
        """Cek apakah jendela sedang embedded"""
        return hwnd in self._embedded_windows
    
    def cleanup(self) -> None:
        """Cleanup semua embedded windows"""
        for hwnd in list(self._embedded_windows.keys()):
            self.restore_window(hwnd)


def get_window_manager() -> WindowManager:
    """Factory function untuk mendapatkan WindowManager instance"""
    return WindowManager()
