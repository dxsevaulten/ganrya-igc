# ganrya_igc/api/ui_api.py
"""
Subplan 1.3.3: Definisi API Publik - UI API.
Interface untuk membuat dan mengelola elemen UI dalam viewport.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class UIAPI_v1(ABC):
    api_version = "1.0.0"
    
    @abstractmethod
    def add_menu(self, menu_name: str) -> Any:
        """Menambahkan menu ke menu bar viewport."""
        ...
    
    @abstractmethod
    def add_menu_item(self, menu: Any, item_name: str, callback: Callable[[], None]) -> Any:
        """Menambahkan item ke menu."""
        ...
    
    @abstractmethod
    def show_message_box(self, title: str, message: str) -> None:
        """Menampilkan dialog pesan."""
        ...
    
    @abstractmethod
    def show_open_file_dialog(self, title: str, filter_str: str) -> Optional[str]:
        """Menampilkan dialog buka file, mengembalikan path atau None."""
        ...
    
    @abstractmethod
    def show_save_file_dialog(self, title: str, filter_str: str) -> Optional[str]:
        """Menampilkan dialog simpan file, mengembalikan path atau None."""
        ...
    
    @abstractmethod
    def set_status_message(self, message: str, timeout: int = 5000) -> None:
        """Menampilkan pesan di status bar viewport."""
        ...