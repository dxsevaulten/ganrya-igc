"""
Helper Functions - Utility utilities untuk Universal Host
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_file_extension(path: str) -> str:
    """
    Mendapatkan ekstensi file dari path
    
    Args:
        path: Path file
        
    Returns:
        Ekstensi file (tanpa titik), lowercase
    """
    return Path(path).suffix.lower().lstrip('.')


def is_executable(path: str) -> bool:
    """
    Cek apakah file adalah executable
    
    Args:
        path: Path file
        
    Returns:
        True jika executable
    """
    ext = get_file_extension(path)
    executable_extensions = ['exe', 'bat', 'cmd', 'com', 'msi']
    
    if os.name == 'nt':  # Windows
        return ext in executable_extensions
    else:  # Linux/Mac
        # Cek execute permission
        return os.access(path, os.X_OK) or ext in executable_extensions


def is_shortcut(path: str) -> bool:
    """
    Cek apakah file adalah shortcut
    
    Args:
        path: Path file
        
    Returns:
        True jika shortcut
    """
    ext = get_file_extension(path)
    shortcut_extensions = ['lnk', 'url', 'desktop']
    return ext in shortcut_extensions


def format_size(size_bytes: int) -> str:
    """
    Format ukuran file ke human-readable format
    
    Args:
        size_bytes: Ukuran dalam bytes
        
    Returns:
        String ukuran yang diformat (KB, MB, GB)
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename untuk keamanan
    
    Args:
        filename: Nama file asli
        
    Returns:
        Nama file yang sudah disanitize
    """
    # Karakter yang tidak diperbolehkan
    invalid_chars = '<>:"/\\|?*'
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Hapus leading/trailing spaces dan dots
    sanitized = sanitized.strip(' .')
    
    # Limit panjang
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized if sanitized else "unnamed"


def get_process_name_from_path(path: str) -> str:
    """
    Ekstrak nama proses dari path
    
    Args:
        path: Path lengkap aplikasi
        
    Returns:
        Nama proses (tanpa ekstensi)
    """
    name = Path(path).stem
    return name


def ensure_directory(path: str) -> bool:
    """
    Pastikan direktori ada, buat jika belum
    
    Args:
        path: Path direktori
        
    Returns:
        True jika berhasil
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def get_app_data_dir(app_name: str = "UniversalHost") -> str:
    """
    Mendapatkan direktori data aplikasi
    
    Args:
        app_name: Nama aplikasi
        
    Returns:
        Path ke direktori data
    """
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', str(Path.home()))
    elif os.name == 'posix':  # Linux/Mac
        base = str(Path.home())
    else:
        base = str(Path.home())
    
    data_dir = Path(base) / f".{app_name.lower()}"
    ensure_directory(str(data_dir))
    
    return str(data_dir)


def validate_path(path: str, must_exist: bool = True) -> bool:
    """
    Validasi path
    
    Args:
        path: Path yang divalidasi
        must_exist: Harus ada atau tidak
        
    Returns:
        True jika valid
    """
    if not path:
        return False
    
    path_obj = Path(path)
    
    if must_exist:
        return path_obj.exists()
    
    # Cek parent directory ada
    return path_obj.parent.exists()


def safe_remove_file(path: str) -> bool:
    """
    Hapus file dengan aman
    
    Args:
        path: Path file
        
    Returns:
        True jika berhasil dihapus
    """
    try:
        if Path(path).exists():
            Path(path).unlink()
            logger.debug(f"File removed: {path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to remove file {path}: {e}")
        return False


# Konstanta utilitas
SUPPORTED_EXTENSIONS = {
    'executable': ['exe', 'bat', 'cmd', 'com', 'msi'],
    'shortcut': ['lnk', 'url', 'desktop'],
    'config': ['ini', 'cfg', 'conf', 'yaml', 'json', 'toml'],
    'log': ['log', 'txt']
}
