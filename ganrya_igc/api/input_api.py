# ganrya_igc/api/input_api.py
"""
Subplan 1.3.3: Definisi API Publik - Input API.
Interface untuk mengakses input device (mouse, keyboard).
"""

from abc import ABC, abstractmethod
from typing import Tuple


class InputAPI_v1(ABC):
    api_version = "1.0.0"
    
    @abstractmethod
    def is_key_pressed(self, key_code: int) -> bool:
        """Memeriksa apakah tombol keyboard sedang ditekan."""
        ...
    
    @abstractmethod
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Memeriksa apakah tombol mouse sedang ditekan (0=kiri, 1=kanan, 2=tengah)."""
        ...
    
    @abstractmethod
    def get_mouse_position(self) -> Tuple[float, float]:
        """Mendapatkan posisi mouse dalam koordinat layar."""
        ...
    
    @abstractmethod
    def get_mouse_delta(self) -> Tuple[float, float]:
        """Mendapatkan perubahan posisi mouse sejak frame terakhir."""
        ...
    
    @abstractmethod
    def get_mouse_wheel(self) -> float:
        """Mendapatkan nilai scroll wheel sejak frame terakhir."""
        ...