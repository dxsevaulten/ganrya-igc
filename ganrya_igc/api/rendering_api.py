# ganrya_igc/api/rendering_api.py
"""
Subplan 1.3.3: Definisi API Publik - Rendering API.
Interface untuk mengakses renderer, material, dan shader.
"""

from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional


class RenderingAPI_v1(ABC):
    api_version = "1.0.0"
    
    @abstractmethod
    def set_clear_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        """Mengatur warna background viewport."""
        ...
    
    @abstractmethod
    def create_material(self, name: str, color: Tuple[float, float, float, float]) -> Any:
        """Membuat material baru dengan warna solid."""
        ...
    
    @abstractmethod
    def apply_material(self, node: Any, material: Any) -> None:
        """Menerapkan material ke node."""
        ...
    
    @abstractmethod
    def set_ambient_light(self, color: Tuple[float, float, float], intensity: float = 1.0) -> None:
        """Mengatur pencahayaan ambient."""
        ...
    
    @abstractmethod
    def create_directional_light(self, direction: Tuple[float, float, float],
                                 color: Tuple[float, float, float],
                                 intensity: float = 1.0) -> Any:
        """Membuat directional light."""
        ...
    
    @abstractmethod
    def toggle_wireframe(self, enabled: bool) -> None:
        """Mengaktifkan/menonaktifkan mode wireframe."""
        ...
    
    @abstractmethod
    def take_screenshot(self, filepath: str) -> bool:
        """Mengambil screenshot viewport ke file."""
        ...