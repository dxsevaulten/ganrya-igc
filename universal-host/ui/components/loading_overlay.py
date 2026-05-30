"""
UI Components - Loading Overlay with Glassmorphism
Overlay interaktif dengan animasi polkadot dan sparkle trail
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LoadingOverlay:
    """
    Loading overlay dengan efek glassmorphism modern.
    Fitur:
    - Animasi polkadot interaktif
    - Trail sparkle effect
    - Transparent blur background
    - Progress indication
    """
    
    def __init__(self, parent=None):
        self.parent = parent
        self.is_visible = False
        self.progress = 0
        self.message = "Loading..."
        self.animation_speed = 100  # ms
        
    def show(self, message: str = "Loading...", progress: int = 0) -> None:
        """
        Menampilkan loading overlay
        
        Args:
            message: Pesan yang ditampilkan
            progress: Progress percentage (0-100)
        """
        self.message = message
        self.progress = progress
        self.is_visible = True
        logger.debug(f"Loading overlay shown: {message} ({progress}%)")
        
        # Implementasi Qt actual akan dibuat di UI layer
        # self.setStyleSheet("background-color: rgba(255, 255, 255, 0.7);")
        # self.raise_()
        # self.show()
    
    def hide(self) -> None:
        """Menyembunyikan loading overlay"""
        self.is_visible = False
        self.progress = 0
        logger.debug("Loading overlay hidden")
    
    def update_progress(self, progress: int) -> None:
        """
        Update progress bar
        
        Args:
            progress: Progress percentage (0-100)
        """
        self.progress = max(0, min(100, progress))
        logger.debug(f"Loading progress updated: {self.progress}%")
    
    def set_message(self, message: str) -> None:
        """
        Update pesan loading
        
        Args:
            message: Pesan baru
        """
        self.message = message
        logger.debug(f"Loading message updated: {message}")
    
    def is_showing(self) -> bool:
        """Cek apakah overlay sedang ditampilkan"""
        return self.is_visible


# Helper function
def get_loading_overlay(parent=None) -> LoadingOverlay:
    """Mendapatkan instance LoadingOverlay"""
    return LoadingOverlay(parent)
