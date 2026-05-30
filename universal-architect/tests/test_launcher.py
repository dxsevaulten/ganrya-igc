"""
Test Application Launcher
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.launcher import ApplicationLauncher, get_launcher, LaunchResult


class TestApplicationLauncher:
    """Test untuk ApplicationLauncher"""
    
    def test_creation(self):
        """Test pembuatan ApplicationLauncher"""
        launcher = ApplicationLauncher()
        assert launcher is not None
    
    def test_factory_function(self):
        """Test factory function"""
        launcher1 = get_launcher()
        launcher2 = get_launcher()
        assert launcher1 is not launcher2
    
    def test_launch_nonexistent_file(self):
        """Test launch file yang tidak ada"""
        launcher = ApplicationLauncher()
        result = launcher.launch('/nonexistent/path/app.exe')
        
        assert result.success is False
        assert result.pid is None
        assert 'tidak ditemukan' in result.error.lower()
    
    def test_is_process_running(self):
        """Test pengecekan proses berjalan"""
        launcher = ApplicationLauncher()
        
        # PID 1 biasanya selalu ada di sistem
        assert launcher.is_process_running(1) is True
        
        # PID yang sangat besar biasanya tidak ada
        assert launcher.is_process_running(999999999) is False
    
    def test_get_process_name(self):
        """Test mendapatkan nama proses"""
        launcher = ApplicationLauncher()
        
        # PID 1 biasanya init/system process
        name = launcher.get_process_name(1)
        assert name is not None
        assert len(name) > 0
    
    def test_terminate_nonexistent_process(self):
        """Test terminate proses yang tidak ada"""
        launcher = ApplicationLauncher()
        result = launcher.terminate_process(999999999)
        assert result is False
    
    def test_resolve_shortcut_non_windows(self):
        """Test resolve shortcut di non-Windows"""
        launcher = ApplicationLauncher()
        
        if sys.platform != 'win32':
            # Di non-Windows, .lnk return None
            result = launcher.resolve_shortcut('/path/to/file.lnk')
            assert result is None
            
            # File biasa return as-is
            result = launcher.resolve_shortcut('/path/to/file.exe')
            assert result == '/path/to/file.exe'
    
    def test_launch_result_dataclass(self):
        """Test LaunchResult dataclass"""
        result = LaunchResult(
            success=True,
            pid=1234,
            path='/test/path.exe'
        )
        
        assert result.success is True
        assert result.pid == 1234
        assert result.path == '/test/path.exe'
        assert result.error is None
        
        result_with_error = LaunchResult(
            success=False,
            pid=None,
            path='/test/path.exe',
            error='Test error'
        )
        assert result_with_error.error == 'Test error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
