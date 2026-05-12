# ganrya_igc/core/serialization.py
"""
Plan 1.5: Serialisasi & Deserialisasi.
Subplan 1.5.1: Binary vs. Text Serialization.
"""

import json
import struct
import os
from abc import ABC, abstractmethod
from typing import Any, Optional


class Serializer(ABC):
    """Interface abstrak untuk serializer."""
    
    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """Mengubah objek Python menjadi byte string."""
        ...
    
    @abstractmethod
    def deserialize(self, raw: bytes) -> Any:
        """Mengembalikan objek Python dari byte string."""
        ...

    def serialize_to_file(self, data: Any, filepath: str):
        """Serialisasi dan tulis ke file."""
        with open(filepath, 'wb') as f:
            f.write(self.serialize(data))

    def deserialize_from_file(self, filepath: str) -> Any:
        """Baca dari file dan deserialisasi."""
        with open(filepath, 'rb') as f:
            return self.deserialize(f.read())


class JSONSerializer(Serializer):
    """Serialisasi berbasis teks (JSON)."""
    
    def __init__(self, indent: Optional[int] = None):
        self.indent = indent
    
    def serialize(self, data: Any) -> bytes:
        json_str = json.dumps(data, indent=self.indent, default=str)
        return json_str.encode('utf-8')
    
    def deserialize(self, raw: bytes) -> Any:
        return json.loads(raw.decode('utf-8'))


class BinarySerializer(Serializer):
    """Serialisasi biner menggunakan MessagePack jika tersedia, atau fallback ke pickle."""
    
    def __init__(self):
        self._use_msgpack = False
        try:
            import msgpack
            self._msgpack = msgpack
            self._use_msgpack = True
        except ImportError:
            import pickle
            self._pickle = pickle
    
    def serialize(self, data: Any) -> bytes:
        if self._use_msgpack:
            return self._msgpack.packb(data)
        return self._pickle.dumps(data)
    
    def deserialize(self, raw: bytes) -> Any:
        if self._use_msgpack:
            return self._msgpack.unpackb(raw)
        return self._pickle.loads(raw)


class SceneSerializer:
    """
    Serializer khusus untuk scene graph.
    Mendukung serialisasi rekursif node dan komponen.
    """
    
    def __init__(self, serializer: Serializer = None):
        self.serializer = serializer or JSONSerializer(indent=2)
    
    def serialize_node(self, node) -> dict:
        """Serialize satu SceneNode ke dictionary."""
        data = {
            'name': node.name,
            'translation': node.local_transform.translation.tolist(),
            'rotation': node.local_transform.rotation.tolist(),
            'scale': node.local_transform.scale.tolist(),
            'components': {},
            'children': [self.serialize_node(child) for child in node.children]
        }
        # Serialize komponen sederhana
        for comp_name, comp in node.components.items():
            data['components'][comp_name] = str(type(comp).__name__)
        return data
    
    def serialize_scene(self, root_node) -> bytes:
        """Serialize seluruh scene dari root node."""
        scene_data = self.serialize_node(root_node)
        return self.serializer.serialize(scene_data)
    
    def deserialize_scene(self, raw: bytes):
        """
        Deserialize scene ke dalam SceneNode.
        Mengembalikan tuple (root_node, list_of_all_nodes).
        """
        scene_data = self.serializer.deserialize(raw)
        return self._deserialize_node(scene_data, None)
    
    def _deserialize_node(self, data: dict, parent):
        """Rekursif membangun SceneNode dari dictionary."""
        from ganrya_igc.core.scene_graph import SceneNode, Transform
        import numpy as np
        
        node = SceneNode(data['name'])
        node.local_transform = Transform(
            translation=np.array(data['translation']),
            rotation=np.array(data['rotation']),
            scale=np.array(data['scale'])
        )
        if parent:
            node.set_parent(parent)
        
        for child_data in data.get('children', []):
            self._deserialize_node(child_data, node)
        
        return node
    
# ========== SUBPLAN 1.5.2: FORMAT CONTAINER (GLTF/GLB & CUSTOM) ==========
import base64
import zipfile
import io
from typing import Dict, Tuple, List


class GLTFExporter:
    """Mengekspor scene graph ke format GLTF 2.0 (JSON + binary opsional)."""
    
    def __init__(self):
        self._buffer_data = bytearray()
        self._buffer_views: List[Dict] = []
        self._accessors: List[Dict] = []
        self._meshes: List[Dict] = []
        self._nodes: List[Dict] = []
        self._node_index_map: Dict[int, int] = {}  # id(node) -> indeks di glTF
    
    def export_scene(self, root_node) -> Dict:
        """Mengembalikan dictionary GLTF (format .gltf)."""
        self._reset()
        self._add_node_recursive(root_node)
        
        gltf = {
            'asset': {'version': '2.0', 'generator': 'Ganrya IGC'},
            'scenes': [{'nodes': [0]}],
            'nodes': self._nodes,
            'meshes': self._meshes if self._meshes else None,
        }
        if self._buffer_data:
            gltf['buffers'] = [{
                'uri': 'data:application/octet-stream;base64,' + 
                       base64.b64encode(self._buffer_data).decode('ascii'),
                'byteLength': len(self._buffer_data)
            }]
            gltf['bufferViews'] = self._buffer_views
            gltf['accessors'] = self._accessors
        return gltf
    
    def export_glb(self, root_node) -> bytes:
        """Mengembalikan binary GLB (format .glb)."""
        gltf = self.export_scene(root_node)
        gltf_json = json.dumps(gltf).encode('utf-8')
        # Padding untuk alignment 4-byte
        while len(gltf_json) % 4:
            gltf_json += b' '
        
        bin_data = bytes(self._buffer_data)
        while len(bin_data) % 4:
            bin_data += b'\x00'
        
        # GLB header
        header = struct.pack('<I', 0x46546C67)  # magic 'glTF'
        header += struct.pack('<I', 2)           # version 2
        total_length = 12 + 8 + len(gltf_json) + 8 + len(bin_data)
        header += struct.pack('<I', total_length)
        
        # JSON chunk
        json_chunk = struct.pack('<I', len(gltf_json))
        json_chunk += struct.pack('<I', 0x4E4F534A)  # 'JSON'
        json_chunk += gltf_json
        
        # Binary chunk
        bin_chunk = struct.pack('<I', len(bin_data))
        bin_chunk += struct.pack('<I', 0x004E4942)  # 'BIN\0'
        bin_chunk += bin_data
        
        return header + json_chunk + bin_chunk
    
    def _reset(self):
        self._buffer_data = bytearray()
        self._buffer_views = []
        self._accessors = []
        self._meshes = []
        self._nodes = []
        self._node_index_map = {}
    
    def _add_node_recursive(self, node, parent_idx: int = -1):
        node_idx = len(self._nodes)
        self._node_index_map[id(node)] = node_idx
        
        gltf_node = {
            'name': node.name,
            'translation': node.local_transform.translation.tolist(),
            'rotation': node.local_transform.rotation.tolist(),
            'scale': node.local_transform.scale.tolist(),
        }
        if node.children:
            gltf_node['children'] = []
        
        self._nodes.append(gltf_node)
        
        if parent_idx >= 0:
            if 'children' not in self._nodes[parent_idx]:
                self._nodes[parent_idx]['children'] = []
            self._nodes[parent_idx]['children'].append(node_idx)
        
        # Rekursif ke anak
        for child in node.children:
            self._add_node_recursive(child, node_idx)


class CustomProjectSerializer:
    """
    Serialisasi proyek custom (.msp) berbasis ZIP.
    Berisi scene graph (JSON), material, dan aset.
    """
    
    @staticmethod
    def save_project(root_node, filepath: str, metadata: Dict = None):
        """Simpan proyek ke file .msp (ZIP)."""
        serializer = SceneSerializer(JSONSerializer(indent=2))
        scene_data = serializer.serialize_node(root_node)
        
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Scene graph
            zf.writestr('scene.json', json.dumps(scene_data, indent=2))
            # Metadata
            if metadata:
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            # Versi
            zf.writestr('version.txt', '1.0.0')
    
    @staticmethod
    def load_project(filepath: str) -> Tuple[any, Optional[Dict]]:
        """Muat proyek dari file .msp, kembalikan (root_node, metadata)."""
        with zipfile.ZipFile(filepath, 'r') as zf:
            scene_raw = zf.read('scene.json')
            metadata = None
            if 'metadata.json' in zf.namelist():
                metadata = json.loads(zf.read('metadata.json'))
        
        serializer = SceneSerializer(JSONSerializer())
        root_node = serializer.deserialize_scene(scene_raw)
        return root_node, metadata
    
# ========== SUBPLAN 1.5.3: VERSION-TOLERANT LOADING ==========

class VersionMigrator:
    """
    Menangani migrasi data scene dari versi lama ke versi saat ini.
    Setiap fungsi migrasi menerima dictionary data scene dan mengembalikan
    dictionary yang telah dimutakhirkan.
    """
    
    CURRENT_VERSION = "1.0.0"
    
    def __init__(self):
        # Daftar migrasi: versi_lama -> fungsi_migrasi
        self._migrations = {
            "0.9.0": self._migrate_0_9_0_to_1_0_0,
        }
    
    def migrate(self, scene_data: dict, from_version: str) -> dict:
        """Jalankan rantai migrasi dari from_version ke CURRENT_VERSION."""
        data = scene_data.copy()
        # Urutkan versi secara semantik dan jalankan migrasi satu per satu
        sorted_versions = sorted(self._migrations.keys())
        for version in sorted_versions:
            if from_version < version <= self.CURRENT_VERSION:
                data = self._migrations[version](data)
                data['version'] = version
        data['version'] = self.CURRENT_VERSION
        return data
    
    def _migrate_0_9_0_to_1_0_0(self, data: dict) -> dict:
        """Contoh migrasi: menambahkan field 'scale' jika belum ada."""
        def add_scale(node: dict):
            if 'scale' not in node:
                node['scale'] = [1.0, 1.0, 1.0]
            for child in node.get('children', []):
                add_scale(child)
        
        if 'scene' in data:
            add_scale(data['scene'])
        return data


class SceneSerializer:
    """SceneSerializer dengan dukungan version-tolerant loading."""
    
    CURRENT_VERSION = "1.0.0"
    
    def __init__(self, serializer: Serializer = None):
        self.serializer = serializer or JSONSerializer(indent=2)
        self.migrator = VersionMigrator()
    
    def serialize_node(self, node) -> dict:
        data = {
            'name': node.name,
            'translation': node.local_transform.translation.tolist(),
            'rotation': node.local_transform.rotation.tolist(),
            'scale': node.local_transform.scale.tolist(),
            'components': {},
            'children': [self.serialize_node(child) for child in node.children]
        }
        for comp_name, comp in node.components.items():
            data['components'][comp_name] = str(type(comp).__name__)
        return data
    
    def serialize_scene(self, root_node) -> bytes:
        scene_data = {
            'version': self.CURRENT_VERSION,
            'scene': self.serialize_node(root_node)
        }
        return self.serializer.serialize(scene_data)
    
    def deserialize_scene(self, raw: bytes):
        """Deserialize dengan dukungan migrasi versi."""
        scene_data = self.serializer.deserialize(raw)
        
        # Deteksi versi
        version = scene_data.get('version', '0.9.0')
        if version != self.CURRENT_VERSION:
            print(f"SceneSerializer: migrasi dari v{version} ke v{self.CURRENT_VERSION}")
            scene_data = self.migrator.migrate(scene_data, version)
        
        # Ekstrak node root
        root_data = scene_data.get('scene', scene_data)
        return self._deserialize_node(root_data, None)
    
    def _deserialize_node(self, data: dict, parent):
        from ganrya_igc.core.scene_graph import SceneNode, Transform
        import numpy as np
        
        node = SceneNode(data['name'])
        node.local_transform = Transform(
            translation=np.array(data.get('translation', [0, 0, 0])),
            rotation=np.array(data.get('rotation', [0, 0, 0, 1])),
            scale=np.array(data.get('scale', [1, 1, 1]))
        )
        if parent:
            node.set_parent(parent)
        
        for child_data in data.get('children', []):
            self._deserialize_node(child_data, node)
        
        return node
    
# ========== SUBPLAN 1.5.4: INCREMENTAL SAVING & AUTOSAVE ==========
import time
import threading
from typing import Any, Optional, Callable


class AutosaveManager:
    """
    Mengelola autosave periodik.
    Berjalan di thread terpisah dan memanggil callback save dengan interval tertentu.
    """

    def __init__(self,
                 save_callback: Callable[[], None],
                 interval_seconds: float = 300.0,  # 5 menit
                 max_backups: int = 5):
        self.save_callback = save_callback
        self.interval = interval_seconds
        self.max_backups = max_backups
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._lock = threading.Lock()
        self.save_count = 0

    def start(self):
        """Mulai autosave periodik."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._schedule_next()

    def stop(self):
        """Hentikan autosave."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None

    def _schedule_next(self):
        """Jadwalkan autosave berikutnya."""
        if not self._running:
            return
        self._timer = threading.Timer(self.interval, self._on_tick)
        self._timer.daemon = True
        self._timer.start()

    def _on_tick(self):
        """Dipanggil saat timer autosave tercapai."""
        print(f"AutosaveManager: menjalankan autosave #{self.save_count + 1}...")
        try:
            self.save_callback()
            self.save_count += 1
        except Exception as e:
            print(f"AutosaveManager: gagal autosave: {e}")
        finally:
            self._schedule_next()

    def force_save(self):
        """Paksa autosave sekarang juga."""
        print("AutosaveManager: force save...")
        try:
            self.save_callback()
            self.save_count += 1
        except Exception as e:
            print(f"AutosaveManager: force save gagal: {e}")

class IncrementalSaver:
    """Menyimpan file dengan backup berputar (rotating backups) dan serialisasi node."""
    
    def __init__(self, filepath: str, max_backups: int = 3):
        self.filepath = filepath
        self.max_backups = max_backups
    
    def save(self, data: str):
        """Simpan string mentah ke file (untuk teks generik)."""
        self._rotate_backups()
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(data)
    
    def save_node(self, node):
        """Simpan SceneNode ke file dengan serialisasi JSON."""
        serializer = SceneSerializer(JSONSerializer(indent=2))
        scene_data = {
            'version': SceneSerializer.CURRENT_VERSION,
            'scene': serializer.serialize_node(node)
        }
        json_str = json.dumps(scene_data, indent=2)
        self._rotate_backups()
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    def load_node(self):
        """Muat SceneNode dari file yang disimpan dengan save_node()."""
        if not os.path.exists(self.filepath):
            return None
        serializer = SceneSerializer(JSONSerializer())
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return serializer.deserialize_scene(f.read().encode('utf-8'))
    
    def _rotate_backups(self):
        """Putar backup: .bak2 <- .bak1 <- .bak <- file utama."""
        for i in range(self.max_backups - 1, 0, -1):
            src = f"{self.filepath}.bak{i}"
            dst = f"{self.filepath}.bak{i+1}"
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
        
        if os.path.exists(self.filepath):
            bak1 = f"{self.filepath}.bak1"
            if os.path.exists(bak1):
                os.remove(bak1)
            os.rename(self.filepath, bak1)