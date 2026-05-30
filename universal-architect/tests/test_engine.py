"""
Test Core Engine
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import CoreEngine, get_engine


class TestCoreEngine:
    """Test untuk CoreEngine"""
    
    def test_singleton_pattern(self):
        """Test bahwa CoreEngine mengikuti singleton pattern"""
        engine1 = CoreEngine()
        engine2 = CoreEngine()
        assert engine1 is engine2
    
    def test_get_engine_factory(self):
        """Test factory function get_engine"""
        engine = get_engine()
        assert isinstance(engine, CoreEngine)
        assert engine is get_engine()
    
    def test_register_process(self):
        """Test registrasi proses"""
        engine = CoreEngine()
        engine.register_process(1234, {'name': 'TestApp', 'path': '/test/path.exe'})
        
        info = engine.get_process_info(1234)
        assert info is not None
        assert info['info']['name'] == 'TestApp'
        assert info['status'] == 'running'
    
    def test_unregister_process(self):
        """Test unregister proses"""
        engine = CoreEngine()
        engine.register_process(5678, {'name': 'TempApp'})
        assert engine.get_process_info(5678) is not None
        
        engine.unregister_process(5678)
        assert engine.get_process_info(5678) is None
    
    def test_update_process_status(self):
        """Test update status proses"""
        engine = CoreEngine()
        engine.register_process(9999, {'name': 'StatusApp'})
        
        engine.update_process_status(9999, 'paused')
        info = engine.get_process_info(9999)
        assert info['status'] == 'paused'
    
    def test_config_management(self):
        """Test manajemen konfigurasi"""
        engine = CoreEngine()
        
        engine.set_config('theme', 'dark')
        assert engine.get_config('theme') == 'dark'
        
        assert engine.get_config('nonexistent', 'default') == 'default'
    
    def test_get_all_processes(self):
        """Test mendapatkan semua proses"""
        engine = CoreEngine()
        engine.cleanup()  # Reset dulu
        
        engine.register_process(1111, {'name': 'App1'})
        engine.register_process(2222, {'name': 'App2'})
        
        all_procs = engine.get_all_processes()
        assert len(all_procs) == 2
        assert 1111 in all_procs
        assert 2222 in all_procs
    
    def test_cleanup(self):
        """Test cleanup"""
        engine = CoreEngine()
        engine.register_process(3333, {'name': 'CleanupApp'})
        
        engine.cleanup()
        assert len(engine.get_all_processes()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
