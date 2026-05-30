"""
Launcher Module - Universal Application Launcher
Meluncurkan aplikasi dari .exe, .lnk, atau shortcut lainnya
"""
import os
import subprocess
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LaunchResult:
    """Hasil peluncuran aplikasi"""
    success: bool
    pid: Optional[int]
    path: str
    error: Optional[str] = None


class ApplicationLauncher:
    """
    Meluncurkan aplikasi desktop dengan berbagai format:
    - .exe (executable langsung)
    - .lnk (Windows shortcut)
    - Path direktori (mencari executable default)
    """
    
    def __init__(self):
        self.launched_processes: Dict[int, LaunchResult] = {}
    
    def resolve_path(self, path: str) -> str:
        """
        Menyelesaikan path, termasuk resolving .lnk shortcuts
        
        Args:
            path: Path ke aplikasi (.exe, .lnk, atau direktori)
            
        Returns:
            Path absolut yang sudah di-resolve
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Path tidak ditemukan: {path}")
        
        # Jika .lnk shortcut (Windows)
        if path_obj.suffix.lower() == '.lnk':
            return self._resolve_lnk(path_obj)
        
        # Jika direktori, cari executable umum
        if path_obj.is_dir():
            return self._find_executable_in_dir(path_obj)
        
        return str(path_obj.absolute())
    
    def _resolve_lnk(self, lnk_path: Path) -> str:
        """
        Resolve Windows .lnk shortcut ke target sebenarnya
        
        Args:
            lnk_path: Path ke file .lnk
            
        Returns:
            Path target dari shortcut
        """
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(lnk_path))
            target = shortcut.Targetpath
            logger.debug(f"Resolved .lnk: {lnk_path} -> {target}")
            return target
        except ImportError:
            logger.warning("win32com tidak tersedia, menggunakan path .lnk langsung")
            return str(lnk_path)
        except Exception as e:
            logger.error(f"Gagal resolve .lnk {lnk_path}: {e}")
            return str(lnk_path)
    
    def _find_executable_in_dir(self, dir_path: Path) -> str:
        """
        Mencari executable default dalam direktori
        
        Args:
            dir_path: Path direktori
            
        Returns:
            Path ke executable pertama yang ditemukan
        """
        # Prioritas executable
        priorities = ['main.exe', 'app.exe', 'start.exe', 'launch.exe']
        
        for exe_name in priorities:
            exe_path = dir_path / exe_name
            if exe_path.exists():
                logger.debug(f"Found executable in dir: {exe_path}")
                return str(exe_path)
        
        # Cari .exe pertama
        for exe_file in dir_path.glob('*.exe'):
            logger.debug(f"Found first .exe in dir: {exe_file}")
            return str(exe_file)
        
        raise FileNotFoundError(f"Tidak ada executable ditemukan di {dir_path}")
    
    def launch(self, path: str, arguments: Optional[str] = None, 
               working_dir: Optional[str] = None) -> LaunchResult:
        """
        Meluncurkan aplikasi
        
        Args:
            path: Path ke aplikasi
            arguments: Argument command line (opsional)
            working_dir: Direktori kerja (opsional, default: folder aplikasi)
            
        Returns:
            LaunchResult dengan status dan PID
        """
        try:
            # Resolve path
            resolved_path = self.resolve_path(path)
            logger.info(f"Launching application: {resolved_path}")
            
            # Siapkan command
            cmd = [resolved_path]
            if arguments:
                cmd.extend(arguments.split())
            
            # Tentukan working directory
            if working_dir is None:
                working_dir = str(Path(resolved_path).parent)
            
            # Launch proses
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            pid = process.pid
            result = LaunchResult(
                success=True,
                pid=pid,
                path=resolved_path
            )
            
            self.launched_processes[pid] = result
            logger.info(f"Application launched successfully: PID {pid}")
            
            return result
            
        except FileNotFoundError as e:
            logger.error(f"Launch failed - File not found: {e}")
            return LaunchResult(success=False, pid=None, path=path, error=str(e))
        except PermissionError as e:
            logger.error(f"Launch failed - Permission denied: {e}")
            return LaunchResult(success=False, pid=None, path=path, error=f"Permission denied: {e}")
        except Exception as e:
            logger.error(f"Launch failed - Unexpected error: {e}")
            return LaunchResult(success=False, pid=None, path=path, error=str(e))
    
    def get_process_info(self, pid: int) -> Optional[LaunchResult]:
        """Mengambil informasi proses yang diluncurkan"""
        return self.launched_processes.get(pid)
    
    def is_process_running(self, pid: int) -> bool:
        """Cek apakah proses masih berjalan"""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback sederhana
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def terminate_process(self, pid: int) -> bool:
        """
        Menghentikan proses yang diluncurkan
        
        Args:
            pid: Process ID
            
        Returns:
            True jika berhasil dihentikan
        """
        try:
            import psutil
            process = psutil.Process(pid)
            process.terminate()
            logger.info(f"Process {pid} terminated")
            return True
        except Exception as e:
            logger.error(f"Failed to terminate process {pid}: {e}")
            return False
    
    def cleanup_all(self) -> None:
        """Menghentikan semua proses yang diluncurkan"""
        for pid in list(self.launched_processes.keys()):
            self.terminate_process(pid)
        self.launched_processes.clear()
        logger.info("All launched processes cleaned up")


# Helper function
def get_launcher() -> ApplicationLauncher:
    """Mendapatkan instance ApplicationLauncher"""
    return ApplicationLauncher()
