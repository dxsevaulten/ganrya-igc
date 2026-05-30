"""
Universal Digital Architect - Helper Functions
Fungsi-fungsi utilitas untuk berbagai keperluan
"""

import os
import sys
from typing import Optional, Tuple
from pathlib import Path


def is_valid_executable(path: str) -> bool:
    """
    Cek apakah path adalah file executable yang valid
    Support .exe di Windows, dan executable bit di Linux/Mac
    """
    if not os.path.exists(path):
        return False
    
    if not os.path.isfile(path):
        return False
    
    # Cek extension
    valid_extensions = ['.exe', '.bat', '.cmd']
    ext = os.path.splitext(path)[1].lower()
    
    if sys.platform == 'win32':
        return ext in valid_extensions
    else:
        # Di Unix-like, cek execute permission
        if ext in valid_extensions:
            return True
        # Atau file dengan execute bit
        return os.access(path, os.X_OK)


def format_path(path: str, max_length: int = 50) -> str:
    """
    Format path untuk display, truncate jika terlalu panjang
    Contoh: "C:/Program Files/App/app.exe" -> ".../App/app.exe"
    """
    if len(path) <= max_length:
        return path
    
    # Coba truncate dari tengah
    parts = Path(path).parts
    if len(parts) > 2:
        # Ambil 2 bagian terakhir dan truncate sisanya
        last_parts = parts[-2:]
        truncated = "/".join(last_parts)
        
        if len(truncated) < max_length - 5:
            return f".../{truncated}"
    
    # Fallback: truncate dari awal
    return f"...{path[-(max_length-3):]}"


def extract_icon(path: str, size: Tuple[int, int] = (32, 32)) -> Optional[object]:
    """
    Ekstrak ikon dari file executable
    Return PIL Image atau None jika gagal
    
    Note: Implementasi penuh memerlukan pywin32 di Windows
    atau library khusus di platform lain.
    Ini adalah versi mock/skeleton.
    """
    try:
        from PIL import Image
        
        # Mock icon untuk sekarang
        # Implementasi lengkap akan ditambahkan nanti
        # Menggunakan icon default
        icon_size = min(size[0], size[1])
        
        # Buat placeholder icon berwarna abu-abu
        img = Image.new('RGBA', (icon_size, icon_size), (128, 128, 128, 255))
        
        # Gambar lingkaran sederhana sebagai placeholder
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        margin = 4
        draw.ellipse(
            [margin, margin, icon_size - margin, icon_size - margin],
            fill=(200, 200, 200, 255),
            outline=(100, 100, 100, 255)
        )
        
        return img
        
    except ImportError:
        return None
    except Exception as e:
        print(f"Error extracting icon: {e}")
        return None


def get_file_info(path: str) -> dict:
    """
    Mendapatkan informasi file (nama, ukuran, tanggal modifikasi)
    """
    if not os.path.exists(path):
        return {}
    
    stat = os.stat(path)
    return {
        'name': os.path.basename(path),
        'size': stat.st_size,
        'modified': stat.st_mtime,
        'extension': os.path.splitext(path)[1].lower()
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename untuk menghapus karakter ilegal
    """
    illegal_chars = '<>:"/\\|?*'
    result = filename
    for char in illegal_chars:
        result = result.replace(char, '_')
    return result.strip()


def ensure_directory(path: str) -> bool:
    """
    Pastikan direktori ada, buat jika belum
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False
