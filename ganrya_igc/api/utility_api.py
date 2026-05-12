# ganrya_igc/api/utility_api.py
"""
Subplan 1.3.3: Definisi API Publik - Utility API.
Fungsi-fungsi bantuan untuk matematika 3D, serialisasi, dan logging.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import numpy as np


class UtilityAPI_v1(ABC):
    api_version = "1.0.0"
    
    @abstractmethod
    def log(self, level: str, message: str) -> None:
        """Mencatat pesan log (level: 'debug', 'info', 'warning', 'error')."""
        ...
    
    @abstractmethod
    def load_texture(self, filepath: str) -> Optional[Any]:
        """Memuat tekstur dari file."""
        ...
    
    @abstractmethod
    def create_transform(self, translation: np.ndarray = None,
                         rotation: np.ndarray = None,
                         scale: np.ndarray = None) -> Any:
        """Membuat objek Transform baru."""
        ...
    
    @abstractmethod
    def serialize_node(self, node: Any) -> dict:
        """Menserialisasi node ke dictionary."""
        ...
    
    @abstractmethod
    def deserialize_node(self, data: dict) -> Any:
        """Membuat node dari dictionary."""
        ...