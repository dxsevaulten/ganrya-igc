"""
Test Window Manager
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.window_manager import WindowManager, get_window_manager, WindowInfo


class TestWindowManager:
    """Test untuk WindowManager"""
    
    def test_creation(self):
        """Test pembuatan WindowManager"""
        wm = WindowManager()
        assert wm is not None
        assert wm._embedded_windows == {}
    
    def test_factory_function(self):
        """Test factory function"""
        wm1 = get_window_manager()
        wm2 = get_window_manager()
        # Factory membuat instance baru setiap kali
        assert wm1 is not wm2
    
    def test_find_window_by_pid_mock(self):
        """Test find_window_by_pid (mock di non-Windows)"""
        wm = WindowManager()
        result = wm.find_window_by_pid(1234)
        
        # Di non-Windows, return mock
        if sys.platform != 'win32':
            assert result is not None
            assert result.pid == 1234
            assert result.title == "Mock Window"
    
    def test_embed_window_mock(self):
        """Test embed_window (mock di non-Windows)"""
        wm = WindowManager()
        
        # Mock parent widget
        class MockWidget:
            pass
        
        result = wm.embed_window(9999, MockWidget())
        
        # Di non-Windows, selalu success
        if sys.platform != 'win32':
            assert result is True
            assert wm.is_embedded(9999)
    
    def test_is_embedded(self):
        """Test pengecekan embedded status"""
        wm = WindowManager()
        
        assert wm.is_embedded(1111) is False
        
        class MockWidget:
            pass
        
        wm.embed_window(1111, MockWidget())
        assert wm.is_embedded(1111) is True
    
    def test_get_embedded_windows(self):
        """Test mendapatkan daftar embedded windows"""
        wm = WindowManager()
        
        class MockWidget:
            pass
        
        wm.embed_window(1001, MockWidget())
        wm.embed_window(1002, MockWidget())
        wm.embed_window(1003, MockWidget())
        
        embedded = wm.get_embedded_windows()
        assert len(embedded) == 3
        assert set(embedded) == {1001, 1002, 1003}
    
    def test_restore_window(self):
        """Test restore window"""
        wm = WindowManager()
        
        class MockWidget:
            pass
        
        wm.embed_window(5555, MockWidget())
        assert wm.is_embedded(5555) is True
        
        result = wm.restore_window(5555)
        assert result is True
        assert wm.is_embedded(5555) is False
    
    def test_restore_nonexistent_window(self):
        """Test restore window yang tidak ada"""
        wm = WindowManager()
        result = wm.restore_window(99999)
        assert result is False
    
    def test_cleanup(self):
        """Test cleanup semua embedded windows"""
        wm = WindowManager()
        
        class MockWidget:
            pass
        
        wm.embed_window(7001, MockWidget())
        wm.embed_window(7002, MockWidget())
        
        wm.cleanup()
        
        assert len(wm.get_embedded_windows()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
