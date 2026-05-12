# ganrya_igc/core/ecs.py
"""
Plan 1.2: Arsitektur Berbasis Komponen (ECS).
Subplan 1.2.1: Dekomposisi Objek — Entity sebagai ID, Component sebagai data murni.
"""

from typing import Dict, Type, TypeVar, Optional, List

# Type alias untuk ID Entity (cukup integer)
EntityId = int

T = TypeVar('T', bound='Component')


class Component:
    """Kelas dasar untuk semua komponen. Hanya berisi data, tidak ada logika."""
    pass


class Entity:
    """
    Entity hanyalah sebuah ID dengan koleksi komponen.
    Tidak ada logika game/behaviour di sini.
    """
    _next_id: EntityId = 0

    def __init__(self):
        self.id: EntityId = Entity._next_id
        Entity._next_id += 1
        self._components: Dict[Type[Component], Component] = {}
        self._name: str = f"Entity_{self.id}"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def add_component(self, component: Component):
        """Tambahkan sebuah komponen. Hanya satu instance per tipe."""
        self._components[type(component)] = component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """Ambil komponen berdasarkan tipe."""
        return self._components.get(component_type)  # type: ignore

    def has_component(self, component_type: Type[Component]) -> bool:
        return component_type in self._components

    def remove_component(self, component_type: Type[Component]):
        self._components.pop(component_type, None)

    def get_all_components(self) -> List[Component]:
        return list(self._components.values())


# ----------------------------------------------------------------------
# Beberapa contoh komponen untuk pengujian & penggunaan awal
# ----------------------------------------------------------------------
class TransformComponent(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class MeshComponent(Component):
    def __init__(self, vertices: List = None, faces: List = None):
        self.vertices = vertices if vertices is not None else []
        self.faces = faces if faces is not None else []


class MaterialComponent(Component):
    def __init__(self, color: tuple = (255, 255, 255, 255)):
        self.color = color

# ========== SUBPLAN 1.2.2: SYSTEM UNTUK LOGIKA ==========
from abc import ABC, abstractmethod
from typing import Set, List

class System(ABC):
    """Kelas dasar untuk semua System. Berisi logika yang beroperasi pada entity."""
    
    def __init__(self, required_components: Set[Type[Component]]):
        """
        required_components: tipe-tipe komponen yang harus dimiliki entity
        agar diproses oleh system ini.
        """
        self.required_components = required_components
        self.entities: List[Entity] = []
    
    def can_process(self, entity: Entity) -> bool:
        """Cek apakah entity memiliki semua komponen yang diperlukan."""
        return all(entity.has_component(ct) for ct in self.required_components)
    
    def add_entity(self, entity: Entity):
        """Tambahkan entity ke daftar jika memenuhi syarat."""
        if self.can_process(entity) and entity not in self.entities:
            self.entities.append(entity)
    
    def remove_entity(self, entity: Entity):
        """Hapus entity dari daftar."""
        if entity in self.entities:
            self.entities.remove(entity)
    
    @abstractmethod
    def update(self, delta_time: float):
        """Dipanggil setiap frame. delta_time dalam detik."""
        ...


class SystemManager:
    """Mengelola semua System dan entities di dunia ECS."""
    
    def __init__(self):
        self.systems: List[System] = []
        self.entities: List[Entity] = []
    
    def add_system(self, system: System):
        self.systems.append(system)
        # Daftarkan entity yang sudah ada ke system baru
        for entity in self.entities:
            system.add_entity(entity)
    
    def add_entity(self, entity: Entity):
        self.entities.append(entity)
        for system in self.systems:
            system.add_entity(entity)
    
    def remove_entity(self, entity: Entity):
        if entity in self.entities:
            self.entities.remove(entity)
        for system in self.systems:
            system.remove_entity(entity)
    
    def update(self, delta_time: float):
        """Jalankan semua system satu kali."""
        for system in self.systems:
            system.update(delta_time)

# ========== SUBPLAN 1.2.3: DATA-ORIENTED DESIGN ==========
import numpy as np
from typing import Dict, Type, Set, List, Optional

class ComponentStore:
    """
    Menyimpan semua komponen dalam array NumPy per tipe.
    Structure of Arrays (SoA) untuk akses memori yang efisien.
    """
    def __init__(self):
        # Tipe komponen -> array NumPy
        self._arrays: Dict[Type[Component], np.ndarray] = {}
        # Tipe komponen -> mapping entity_id ke index di array
        self._entity_index: Dict[Type[Component], Dict[EntityId, int]] = {}
        # Tipe komponen -> list index yang kosong (dari entity yang dihapus)
        self._free_slots: Dict[Type[Component], List[int]] = {}
        # Konfigurasi: jumlah komponen yang dialokasikan sekaligus saat array penuh
        self._chunk_size = 1024

    def _ensure_array(self, component_type: Type[Component]):
        """Pastikan array untuk tipe komponen sudah ada."""
        if component_type not in self._arrays:
            self._arrays[component_type] = np.empty((self._chunk_size,), dtype=object)
            self._entity_index[component_type] = {}
            self._free_slots[component_type] = []

    def add_component(self, entity_id: EntityId, component: Component):
        """Tambahkan komponen untuk entity tertentu."""
        self._ensure_array(type(component))
        ct = type(component)
        if entity_id in self._entity_index[ct]:
            # Sudah ada, timpa
            idx = self._entity_index[ct][entity_id]
            self._arrays[ct][idx] = component
        elif self._free_slots[ct]:
            # Gunakan slot kosong
            idx = self._free_slots[ct].pop()
            self._arrays[ct][idx] = component
            self._entity_index[ct][entity_id] = idx
        else:
            # Tambah ke akhir, perbesar array jika perlu
            idx = len(self._entity_index[ct])
            if idx >= len(self._arrays[ct]):
                self._arrays[ct] = np.resize(self._arrays[ct], len(self._arrays[ct]) + self._chunk_size)
            self._arrays[ct][idx] = component
            self._entity_index[ct][entity_id] = idx

    def get_component(self, entity_id: EntityId, component_type: Type[T]) -> Optional[T]:
        """Ambil komponen entity."""
        if component_type not in self._entity_index:
            return None
        idx = self._entity_index[component_type].get(entity_id)
        if idx is None:
            return None
        return self._arrays[component_type][idx]

    def remove_component(self, entity_id: EntityId, component_type: Type[Component]):
        """Hapus komponen entity."""
        if component_type not in self._entity_index:
            return
        if entity_id in self._entity_index[component_type]:
            idx = self._entity_index[component_type].pop(entity_id)
            self._arrays[component_type][idx] = None  # bersihkan referensi
            self._free_slots[component_type].append(idx)

    def has_component(self, entity_id: EntityId, component_type: Type[Component]) -> bool:
        if component_type not in self._entity_index:
            return False
        return entity_id in self._entity_index[component_type]

    def get_all_entities_with(self, component_type: Type[Component]) -> List[EntityId]:
        """Kembalikan daftar entity_id yang memiliki komponen ini."""
        if component_type not in self._entity_index:
            return []
        return list(self._entity_index[component_type].keys())

    def get_all_component_arrays(self, component_types: Set[Type[Component]]) -> Optional[List[np.ndarray]]:
        """Untuk akses SoA: kembalikan beberapa array komponen yang dijamin paralel."""
        result = []
        indices = None
        for ct in component_types:
            if ct not in self._entity_index:
                return None
            ids = set(self._entity_index[ct].keys())
            if indices is None:
                indices = ids
            else:
                indices = indices.intersection(ids)
            if not indices:
                return None
        
        # Untuk sekarang, kembalikan array per tipe (tidak di-slice paralel dulu)
        for ct in component_types:
            result.append(self._arrays[ct])
        return result


class EntityDOD(Entity):
    """Entity yang menggunakan ComponentStore untuk penyimpanan data."""
    def __init__(self, store: ComponentStore):
        super().__init__()
        self.store = store

    def add_component(self, component: Component):
        self.store.add_component(self.id, component)

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        return self.store.get_component(self.id, component_type)

    def has_component(self, component_type: Type[Component]) -> bool:
        return self.store.has_component(self.id, component_type)

    def remove_component(self, component_type: Type[Component]):
        self.store.remove_component(self.id, component_type)


class SystemDOD(System):
    """System yang bekerja dengan ComponentStore."""
    def __init__(self, required_components: Set[Type[Component]]):
        super().__init__(required_components)
        self.store: Optional[ComponentStore] = None
        self._entity_ids: List[EntityId] = []

    def bind_store(self, store: ComponentStore):
        self.store = store

    def refresh_entities(self):
        """Sinkronkan ulang daftar entity yang memenuhi syarat dari store."""
        if not self.store:
            return
        ids = None
        for ct in self.required_components:
            entity_ids = set(self.store.get_all_entities_with(ct))
            if ids is None:
                ids = entity_ids
            else:
                ids = ids.intersection(entity_ids)
        self._entity_ids = list(ids) if ids else []

    def update(self, delta_time: float):
        # Diimplementasikan oleh subclass
        pass

# ========== SUBPLAN 1.2.4: EVENT-DRIVEN COMMUNICATION ==========
from typing import Callable, Dict, List, Any

# Type alias untuk callback event
EventHandler = Callable[[Any], None]


class EventBus:
    """Sistem event-driven untuk komunikasi antar System secara loosely-coupled."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """Daftarkan handler untuk event_type tertentu."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Hapus handler dari event_type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event_type: str, event_data: Any = None):
        """Kirim event ke semua handler yang subscribed."""
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            handler(event_data)


class SystemManagerDOD(SystemManager):
    """SystemManager dengan dukungan EventBus."""
    
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
        self._entity_created_handlers: List[EventHandler] = []
        self._entity_destroyed_handlers: List[EventHandler] = []
    
    def add_entity(self, entity: Entity):
        super().add_entity(entity)
        self.event_bus.publish('entity_created', {'entity': entity})
    
    def remove_entity(self, entity: Entity):
        super().remove_entity(entity)
        self.event_bus.publish('entity_destroyed', {'entity': entity})


class SystemWithEvents(System):
    """System yang dapat berinteraksi dengan EventBus."""
    
    def __init__(self, required_components: Set[Type[Component]]):
        super().__init__(required_components)
        self.event_bus: Optional[EventBus] = None
    
    def bind_event_bus(self, event_bus: EventBus):
        """Hubungkan system ke EventBus."""
        self.event_bus = event_bus
        self.on_bind()
    
    def publish_event(self, event_type: str, data: Any = None):
        """Helper untuk publish event (jika event_bus tersedia)."""
        if self.event_bus:
            self.event_bus.publish(event_type, data)
    
    def on_bind(self):
        """Override di subclass untuk subscribe ke event."""
        pass

# ========== SUBPLAN 1.2.5: ARCHETYPE-BASED STORAGE ==========

class ArchetypeStorage:
    """
    Menyimpan entity dalam chunk kontigu berdasarkan kombinasi komponen (archetype).
    Entity dengan set komponen yang sama akan disimpan bersama dalam array terstruktur.
    """
    
    def __init__(self, chunk_size: int = 256):
        self.chunk_size = chunk_size
        # Archetype key (frozenset of component types) -> list of chunks
        self._chunks: Dict[frozenset, List[np.ndarray]] = {}
        # Archetype key -> daftar indeks kosong dalam chunk
        self._free_slots: Dict[frozenset, List[tuple]] = {}
        # Entity ID -> (archetype_key, chunk_index, slot_index)
        self._entity_location: Dict[EntityId, tuple] = {}
    
    def _get_archetype_key(self, entity: Entity) -> frozenset:
        """Dapatkan archetype key dari entity (set tipe komponen yang dimilikinya)."""
        return frozenset(type(c) for c in entity.get_all_components())
    
    def add_entity(self, entity: Entity):
        """Tambahkan entity ke storage berdasarkan archetype-nya."""
        key = self._get_archetype_key(entity)
        
        # Cek ruang kosong dulu
        if key in self._free_slots and self._free_slots[key]:
            chunk_idx, slot_idx = self._free_slots[key].pop()
        else:
            # Perlu chunk baru atau slot di akhir
            if key not in self._chunks:
                self._chunks[key] = [np.empty(self.chunk_size, dtype=object)]
                self._free_slots[key] = []
                chunk_idx, slot_idx = 0, 0
            else:
                # Cari slot kosong di chunk terakhir
                last_chunk = self._chunks[key][-1]
                filled = sum(1 for x in last_chunk if x is not None)
                if filled < self.chunk_size:
                    chunk_idx = len(self._chunks[key]) - 1
                    slot_idx = filled
                else:
                    # Buat chunk baru
                    self._chunks[key].append(np.empty(self.chunk_size, dtype=object))
                    chunk_idx = len(self._chunks[key]) - 1
                    slot_idx = 0
        
        # Simpan entity
        self._chunks[key][chunk_idx][slot_idx] = entity
        self._entity_location[entity.id] = (key, chunk_idx, slot_idx)
    
    def remove_entity(self, entity: Entity):
        """Hapus entity dari storage."""
        if entity.id not in self._entity_location:
            return
        
        key, chunk_idx, slot_idx = self._entity_location.pop(entity.id)
        self._chunks[key][chunk_idx][slot_idx] = None
        self._free_slots[key].append((chunk_idx, slot_idx))
    
    def get_entities_by_archetype(self, component_types: Set[Type[Component]]) -> List[Entity]:
        """Ambil semua entity yang memiliki persis set komponen tertentu."""
        key = frozenset(component_types)
        if key not in self._chunks:
            return []
        result = []
        for chunk in self._chunks[key]:
            for entity in chunk:
                if entity is not None:
                    result.append(entity)
        return result
    
    def get_all_entities_with(self, component_type: Type[Component]) -> List[Entity]:
        """Ambil semua entity yang memiliki komponen tertentu (semua archetypes)."""
        result = []
        for key, chunks in self._chunks.items():
            if component_type in key:
                for chunk in chunks:
                    for entity in chunk:
                        if entity is not None:
                            result.append(entity)
        return result
    
    def get_entity(self, entity_id: EntityId) -> Optional[Entity]:
        """Ambil entity berdasarkan ID."""
        if entity_id not in self._entity_location:
            return None
        key, chunk_idx, slot_idx = self._entity_location[entity_id]
        return self._chunks[key][chunk_idx][slot_idx]
    
    def count_entities(self, component_type: Optional[Type[Component]] = None) -> int:
        """Hitung jumlah entity (opsional: filter per tipe komponen)."""
        if component_type is None:
            return sum(1 for key in self._chunks for chunk in self._chunks[key] for e in chunk if e is not None)
        return len(self.get_all_entities_with(component_type))