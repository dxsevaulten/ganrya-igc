"""
Universal Digital Architect - Application Launcher
Meluncurkan aplikasi dari .exe atau .lnk shortcut
"""

import os
import sys
import subprocess
from typing import Optional, Tuple
from dataclasses import dataclass
import psutil


@dataclass
class LaunchResult:
    """Hasil peluncuran aplikasi"""
    success: bool
    pid: Optional[int]
    path: str
    error: Optional[str] = None


class ApplicationLauncher:
    """
    ApplicationLauncher untuk:
    - Meluncurkan .exe langsung
    - Resolve .lnk shortcut ke target sebenarnya
    - Deteksi PID proses yang diluncurkan
    - Validasi path dan file existence
    """
    
    def __init__(self):
        self._is_windows = sys.platform == 'win32'
    
    def resolve_shortcut(self, lnk_path: str) -> Optional[str]:
        """
        Resolve .lnk shortcut ke target path sebenarnya
        Hanya berfungsi di Windows, return None di platform lain
        """
        if not self._is_windows:
            # Di non-Windows, anggap file .lnk sebagai teks biasa
            # atau return path as-is jika bukan .lnk
            if lnk_path.endswith('.lnk'):
                return None
            return lnk_path
        
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            target = shortcut.Targetpath
            return target if os.path.exists(target) else None
        except Exception as e:
            print(f"Error resolving shortcut: {e}")
            return None
    
    def launch(self, path: str, arguments: str = "") -> LaunchResult:
        """
        Meluncurkan aplikasi dari path
        Support .exe langsung dan .lnk shortcut
        """
        # Cek apakah file ada
        if not os.path.exists(path):
            return LaunchResult(
                success=False,
                pid=None,
                path=path,
                error=f"File tidak ditemukan: {path}"
            )
        
        # Resolve jika .lnk shortcut
        actual_path = path
        if path.endswith('.lnk'):
            resolved = self.resolve_shortcut(path)
            if resolved is None:
                return LaunchResult(
                    success=False,
                    pid=None,
                    path=path,
                    error="Gagal resolve shortcut .lnk"
                )
            actual_path = resolved
        
        # Validasi file executable
        if not os.path.isfile(actual_path):
            return LaunchResult(
                success=False,
                pid=None,
                path=path,
                error="Path bukan file executable"
            )
        
        try:
            # Launch proses
            cmd = [actual_path]
            if arguments:
                cmd.extend(arguments.split())
            
            process = subprocess.Popen(cmd)
            pid = process.pid
            
            # Tunggu sebentar untuk memastikan proses berjalan
            import time
            time.sleep(0.5)
            
            # Cek apakah proses masih berjalan
            if psutil.pid_exists(pid):
                return LaunchResult(
                    success=True,
                    pid=pid,
                    path=actual_path
                )
            else:
                return LaunchResult(
                    success=False,
                    pid=None,
                    path=actual_path,
                    error="Proses langsung keluar setelah diluncurkan"
                )
                
        except Exception as e:
            return LaunchResult(
                success=False,
                pid=None,
                path=actual_path,
                error=f"Error meluncurkan aplikasi: {str(e)}"
            )
    
    def get_process_name(self, pid: int) -> Optional[str]:
        """Mendapatkan nama proses dari PID"""
        try:
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def is_process_running(self, pid: int) -> bool:
        """Cek apakah proses masih berjalan"""
        return psutil.pid_exists(pid)
    
    def terminate_process(self, pid: int) -> bool:
        """Menghentikan proses"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False


def get_launcher() -> ApplicationLauncher:
    """Factory function untuk mendapatkan ApplicationLauncher instance"""
    return ApplicationLauncher()
