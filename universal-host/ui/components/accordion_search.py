"""
UI Components - Accordion Autocomplete Search
Pencarian aplikasi dengan ikon asli, nama, path lengkap, dan animasi fade-in
"""
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class AccordionAutocomplete:
    """
    Komponen pencarian dengan accordion autocomplete.
    Fitur:
    - Menampilkan ikon asli aplikasi
    - Nama dan path lengkap
    - Animasi fade-in smooth
    - Filter real-time
    - Keyboard navigation
    """
    
    def __init__(self, on_select_callback: Optional[Callable] = None):
        self.on_select_callback = on_select_callback
        self.items: List[Dict[str, Any]] = []
        self.filtered_items: List[Dict[str, Any]] = []
        self.selected_index = -1
        self.is_expanded = False
        
    def add_item(self, name: str, path: str, icon_path: Optional[str] = None, 
                 category: str = "Applications") -> None:
        """
        Menambahkan item ke daftar pencarian
        
        Args:
            name: Nama aplikasi
            path: Path lengkap aplikasi
            icon_path: Path ke ikon (opsional)
            category: Kategori item
        """
        item = {
            'name': name,
            'path': path,
            'icon_path': icon_path,
            'category': category,
            'last_used': None
        }
        self.items.append(item)
        logger.debug(f"Added search item: {name}")
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Mencari item berdasarkan query
        
        Args:
            query: Kata kunci pencarian
            
        Returns:
            List item yang cocok
        """
        if not query:
            self.filtered_items = []
            return []
        
        query_lower = query.lower()
        
        # Filter berdasarkan nama atau path
        self.filtered_items = [
            item for item in self.items
            if query_lower in item['name'].lower() or 
               query_lower in item['path'].lower()
        ]
        
        # Sort berdasarkan relevansi (nama yang starts_with lebih prioritas)
        self.filtered_items.sort(
            key=lambda x: (not x['name'].lower().startswith(query_lower), x['name'])
        )
        
        self.selected_index = -1  # Reset selection
        logger.debug(f"Search '{query}' found {len(self.filtered_items)} items")
        
        return self.filtered_items
    
    def select_next(self) -> Optional[Dict[str, Any]]:
        """Pilih item berikutnya (keyboard down arrow)"""
        if not self.filtered_items:
            return None
        
        self.selected_index = (self.selected_index + 1) % len(self.filtered_items)
        return self.filtered_items[self.selected_index]
    
    def select_previous(self) -> Optional[Dict[str, Any]]:
        """Pilih item sebelumnya (keyboard up arrow)"""
        if not self.filtered_items:
            return None
        
        self.selected_index = (self.selected_index - 1) % len(self.filtered_items)
        return self.filtered_items[self.selected_index]
    
    def get_selected(self) -> Optional[Dict[str, Any]]:
        """Mendapatkan item yang sedang dipilih"""
        if 0 <= self.selected_index < len(self.filtered_items):
            return self.filtered_items[self.selected_index]
        return None
    
    def confirm_selection(self) -> Optional[Dict[str, Any]]:
        """
        Konfirmasi pilihan (Enter key)
        
        Returns:
            Item yang dipilih
        """
        selected = self.get_selected()
        if selected and self.on_select_callback:
            self.on_select_callback(selected)
            self.collapse()
        
        return selected
    
    def expand(self) -> None:
        """Expand accordion (tampilkan hasil)"""
        self.is_expanded = True
        logger.debug("Accordion expanded")
    
    def collapse(self) -> None:
        """Collapse accordion (sembunyikan hasil)"""
        self.is_expanded = False
        self.filtered_items = []
        self.selected_index = -1
        logger.debug("Accordion collapsed")
    
    def clear(self) -> None:
        """Menghapus semua item"""
        self.items.clear()
        self.filtered_items.clear()
        self.selected_index = -1
        logger.debug("Accordion cleared")
    
    def get_suggestions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Mendapatkan saran teratas
        
        Args:
            limit: Jumlah maksimal saran
            
        Returns:
            List saran
        """
        return self.filtered_items[:limit]


# Helper function
def get_autocomplete(on_select_callback: Optional[Callable] = None) -> AccordionAutocomplete:
    """Mendapatkan instance AccordionAutocomplete"""
    return AccordionAutocomplete(on_select_callback)
