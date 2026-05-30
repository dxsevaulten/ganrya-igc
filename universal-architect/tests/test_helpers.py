"""
Test Helper Functions
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    is_valid_executable,
    format_path,
    extract_icon,
    get_file_info,
    sanitize_filename,
    ensure_directory
)


class TestHelpers:
    """Test untuk helper functions"""
    
    def test_is_valid_executable_nonexistent(self):
        """Test file yang tidak ada"""
        assert is_valid_executable('/nonexistent/file.exe') is False
    
    def test_is_valid_executable_directory(self):
        """Test direktori (bukan file)"""
        assert is_valid_executable('/tmp') is False
    
    def test_format_path_short(self):
        """Test format path pendek"""
        path = "C:/App/app.exe"
        result = format_path(path)
        assert result == path
    
    def test_format_path_long(self):
        """Test format path panjang"""
        path = "C:/Program Files/Application Name/Subfolder/deep/nested/app.exe"
        result = format_path(path, max_length=30)
        assert len(result) <= 30
        assert result.startswith('...')
    
    def test_extract_icon(self):
        """Test extract icon"""
        icon = extract_icon('/fake/path.exe', size=(32, 32))
        
        # Icon bisa None jika PIL tidak tersedia, atau Image object
        if icon is not None:
            assert hasattr(icon, 'size')
            assert icon.size[0] == 32
            assert icon.size[1] == 32
    
    def test_get_file_info_nonexistent(self):
        """Test info file yang tidak ada"""
        info = get_file_info('/nonexistent/file.txt')
        assert info == {}
    
    def test_get_file_info_existing(self):
        """Test info file yang ada"""
        # Buat file temporary
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"test content")
        
        try:
            info = get_file_info(temp_path)
            assert 'name' in info
            assert 'size' in info
            assert info['size'] > 0
            assert 'extension' in info
        finally:
            os.unlink(temp_path)
    
    def test_sanitize_filename(self):
        """Test sanitasi filename"""
        dirty = "file<with>illegal:chars?.txt"
        clean = sanitize_filename(dirty)
        
        assert '<' not in clean
        assert '>' not in clean
        assert ':' not in clean
        assert '?' not in clean
        assert clean.endswith('.txt')
    
    def test_sanitize_filename_clean(self):
        """Test sanitasi filename yang sudah bersih"""
        clean = "normal_file.txt"
        result = sanitize_filename(clean)
        assert result == clean
    
    def test_ensure_directory(self):
        """Test pembuatan direktori"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, 'new', 'nested', 'dir')
            result = ensure_directory(new_dir)
            
            assert result is True
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_ensure_directory_existing(self):
        """Test ensure_directory pada folder yang sudah ada"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory(tmpdir)
            assert result is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
