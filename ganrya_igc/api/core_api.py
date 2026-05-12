# ganrya_igc/api/core_api.py
"""
Subplan 1.3.3: Definisi API Publik - Core API.
Interface untuk mengakses scene graph, ECS world, dan event bus.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Type
import numpy as np


class CoreAPI_v1(ABC):
    """API inti versi 1.0 - kontrak untuk plugin."""
    
    api_version = "1.0.0"
    
    # --- Scene Graph ---
    @abstractmethod
    def get_root_node(self) -> Any:
        """Mengembalikan root node dari scene graph."""
        ...
    
    @abstractmethod
    def create_node(self, name: str, parent: Optional[Any] = None) -> Any:
        """Membuat node baru dalam scene graph."""
        ...
    
    @abstractmethod
    def remove_node(self, node: Any) -> None:
        """Menghapus node dari scene graph."""
        ...
    
    @abstractmethod
    def get_node_by_name(self, name: str) -> Optional[Any]:
        """Mencari node berdasarkan nama."""
        ...
    
    # --- ECS World ---
    @abstractmethod
    def create_entity(self) -> Any:
        """Membuat entity baru di ECS world."""
        ...
    
    @abstractmethod
    def add_component(self, entity: Any, component: Any) -> None:
        """Menambahkan komponen ke entity."""
        ...
    
    @abstractmethod
    def get_component(self, entity: Any, component_type: Type) -> Optional[Any]:
        """Mengambil komponen dari entity."""
        ...
    
    @abstractmethod
    def remove_entity(self, entity: Any) -> None:
        """Menghapus entity dari ECS world."""
        ...
    
    # --- Event Bus ---
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Berlangganan ke event."""
        ...
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Berhenti berlangganan event."""
        ...
    
    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Mempublikasikan event."""
        ...
    
    # --- Utilitas ---
    @abstractmethod
    def get_delta_time(self) -> float:
        """Mendapatkan delta time frame saat ini."""
        ...
    
    @abstractmethod
    def get_frame_count(self) -> int:
        """Mendapatkan nomor frame saat ini."""
        ...