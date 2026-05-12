# ganrya_igc/core/scene_graph.py
import numpy as np
import threading
import copy
from typing import Optional, List, Dict, Any

class AABB:
    """Axis-Aligned Bounding Box."""
    def __init__(self, min_point: np.ndarray = None, max_point: np.ndarray = None):
        if min_point is None:
            self.min = np.full(3, np.inf)
        else:
            self.min = np.array(min_point, dtype=float)
        if max_point is None:
            self.max = np.full(3, -np.inf)
        else:
            self.max = np.array(max_point, dtype=float)

    def extend(self, point: np.ndarray):
        """Perluas AABB untuk mencakup titik baru."""
        self.min = np.minimum(self.min, point)
        self.max = np.maximum(self.max, point)

    def union(self, other: 'AABB') -> 'AABB':
        """Gabungkan dua AABB."""
        new = AABB()
        new.min = np.minimum(self.min, other.min)
        new.max = np.maximum(self.max, other.max)
        return new

    def center(self) -> np.ndarray:
        return (self.min + self.max) * 0.5

    def size(self) -> np.ndarray:
        return self.max - self.min

    def is_valid(self) -> bool:
        return np.any(self.min <= self.max)


class Transform:
    # ... (tidak berubah, sama seperti sebelumnya)
    def __init__(self,
                 translation: np.ndarray = np.array([0.0, 0.0, 0.0]),
                 rotation: np.ndarray = np.array([0.0, 0.0, 0.0, 1.0]),  # quaternion
                 scale: np.ndarray = np.array([1.0, 1.0, 1.0])):
        self.translation = translation.copy()
        self.rotation = rotation.copy()
        self.scale = scale.copy()

    def get_local_matrix(self) -> np.ndarray:
        S = np.diag(np.append(self.scale, 1.0))
        R = self._quaternion_to_matrix(self.rotation)
        T = np.eye(4)
        T[:3, 3] = self.translation
        return T @ R @ S

    @staticmethod
    def _quaternion_to_matrix(q: np.ndarray) -> np.ndarray:
        x, y, z, w = q[0], q[1], q[2], q[3]
        xx, yy, zz = x*x, y*y, z*z
        xy, xz, yz = x*y, x*z, y*z
        wx, wy, wz = w*x, w*y, w*z
        R = np.eye(4)
        R[0, 0] = 1 - 2*(yy + zz)
        R[0, 1] = 2*(xy - wz)
        R[0, 2] = 2*(xz + wy)
        R[1, 0] = 2*(xy + wz)
        R[1, 1] = 1 - 2*(xx + zz)
        R[1, 2] = 2*(yz - wx)
        R[2, 0] = 2*(xz - wy)
        R[2, 1] = 2*(yz + wx)
        R[2, 2] = 1 - 2*(xx + yy)
        return R

class SceneNode:
    """Node dalam scene graph dengan dukungan thread-safe."""
    
    def __init__(self, name: str, transform: Optional[Transform] = None):
        self.name = name
        self._local_transform = transform if transform is not None else Transform()
        self.parent: Optional[SceneNode] = None
        self.children: List[SceneNode] = []
        self.components: Dict[str, Any] = {}
        self.aabb: Optional[AABB] = None
        self._world_dirty = True
        self._cached_world_matrix: np.ndarray = np.eye(4)
        # --- Subplan 1.1.5: Thread-Safety ---
        self._lock = threading.RLock()  # Reentrant lock

    @property
    def local_transform(self) -> Transform:
        with self._lock:
            return self._local_transform

    @local_transform.setter
    def local_transform(self, value: Transform):
        with self._lock:
            self._local_transform = value
            self.invalidate_world()

    def invalidate_world(self):
        """Tandai node ini dan seluruh subtree sebagai dirty (thread-safe)."""
        with self._lock:
            self._world_dirty = True
            for child in self.children:
                child.invalidate_world()

    def get_world_matrix(self) -> np.ndarray:
        """Mengembalikan world matrix (thread-safe)."""
        with self._lock:
            if not self._world_dirty:
                return self._cached_world_matrix.copy()

            local = self._local_transform.get_local_matrix()
            if self.parent:
                parent_world = self.parent.get_world_matrix()
                self._cached_world_matrix = parent_world @ local
            else:
                self._cached_world_matrix = local

            self._world_dirty = False
            return self._cached_world_matrix.copy()

    def set_parent(self, parent: Optional['SceneNode']):
        """Mengatur parent dengan aman (thread-safe)."""
        with self._lock:
            if self.parent is not None:
                self.parent.children.remove(self)
            self.parent = parent
            if parent is not None:
                with parent._lock:
                    parent.children.append(self)
            self.invalidate_world()

    def get_world_position(self) -> np.ndarray:
        return self.get_world_matrix()[:3, 3]

    def add_component(self, name: str, component: Any):
        with self._lock:
            self.components[name] = component

    def get_component(self, name: str) -> Optional[Any]:
        with self._lock:
            return self.components.get(name)

    def remove_component(self, name: str):
        with self._lock:
            self.components.pop(name, None)

    def set_aabb(self, aabb: AABB):
        with self._lock:
            self.aabb = aabb

    def compute_aabb(self) -> AABB:
        with self._lock:
            mesh = self.components.get('mesh')
            if mesh and hasattr(mesh, 'vertices'):
                aabb = AABB()
                for v in mesh.vertices:
                    aabb.extend(v)
                self.aabb = aabb
                return aabb
            return AABB()

# ========== SUBPLAN 1.1.3: VISITOR PATTERN ==========
from abc import ABC, abstractmethod

class SceneVisitor(ABC):
    """Kelas dasar abstrak untuk semua visitor scene graph."""
    
    @abstractmethod
    def visit(self, node: SceneNode):
        """Dipanggil saat mengunjungi sebuah node."""
        pass
    
    def traverse(self, node: SceneNode):
        """Traversal depth-first: kunjungi node, lalu semua anaknya."""
        self.visit(node)
        for child in node.children:
            self.traverse(child)

class PrintVisitor(SceneVisitor):
    """Visitor yang mencetak nama node ke konsol (untuk debugging)."""
    
    def __init__(self):
        self.indent = 0
    
    def visit(self, node: SceneNode):
        print("  " * self.indent + f"- {node.name}")
        self.indent += 1
        # Traversal anak dilakukan oleh traverse()
        # Kita perlu mengatur indent sebelum dan sesudah
        for child in node.children:
            self.traverse(child)
        self.indent -= 1

class ComputeAABBVisitor(SceneVisitor):
    """Visitor yang menghitung ulang bounding box seluruh scene."""
    
    def __init__(self):
        self.global_aabb = AABB()
    
    def visit(self, node: SceneNode):
        # Hitung AABB lokal node jika ada mesh
        node.compute_aabb()
        if node.aabb and node.aabb.is_valid():
            # Transformasikan AABB ke world space (kira-kira)
            world = node.get_world_matrix()
            # Ambil 8 titik sudut AABB, transformasikan, lalu perluas global AABB
            corners = np.array([
                [node.aabb.min[0], node.aabb.min[1], node.aabb.min[2], 1],
                [node.aabb.min[0], node.aabb.min[1], node.aabb.max[2], 1],
                [node.aabb.min[0], node.aabb.max[1], node.aabb.min[2], 1],
                [node.aabb.min[0], node.aabb.max[1], node.aabb.max[2], 1],
                [node.aabb.max[0], node.aabb.min[1], node.aabb.min[2], 1],
                [node.aabb.max[0], node.aabb.min[1], node.aabb.max[2], 1],
                [node.aabb.max[0], node.aabb.max[1], node.aabb.min[2], 1],
                [node.aabb.max[0], node.aabb.max[1], node.aabb.max[2], 1],
            ])
            transformed = (world @ corners.T).T[:, :3]
            for p in transformed:
                self.global_aabb.extend(p)
        # Traversal anak
        for child in node.children:
            self.traverse(child)