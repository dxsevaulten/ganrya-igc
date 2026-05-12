# ganrya_igc/core/resource.py
import threading
from typing import Optional, Callable, Dict, List, Any, Set

# ========== SUBPLAN 1.4.1: REFERENCE COUNTING ==========
class RefCounted:
    def __init__(self):
        self._ref_count = 0
        self._lock = threading.Lock()
        self._destroy_callback: Optional[Callable[[], None]] = None
        self._dependencies: Set['RefCounted'] = set()       # resource yang direfer
        self._referenced_by: Set['RefCounted'] = set()      # resource yang mereferensi ini

    def add_ref(self) -> int:
        with self._lock:
            self._ref_count += 1
            return self._ref_count

    def release(self) -> int:
        with self._lock:
            self._ref_count -= 1
            count = self._ref_count
            if count <= 0 and self._destroy_callback:
                self._destroy_callback()
            return count

    @property
    def ref_count(self) -> int:
        return self._ref_count

    def add_dependency(self, other: 'RefCounted'):
        """Catat bahwa resource ini bergantung pada 'other'."""
        with self._lock:
            self._dependencies.add(other)
            other._referenced_by.add(self)

    def remove_dependency(self, other: 'RefCounted'):
        with self._lock:
            self._dependencies.discard(other)
            other._referenced_by.discard(self)


class Ref:
    def __init__(self, target: Optional[RefCounted] = None):
        self._target: Optional[RefCounted] = None
        self.set_target(target)

    def set_target(self, target: Optional[RefCounted]):
        if self._target is not None:
            self._target.release()
        self._target = target
        if self._target is not None:
            self._target.add_ref()

    def get(self) -> Optional[RefCounted]:
        return self._target

    @property
    def target(self) -> Optional[RefCounted]:
        return self._target

    def __del__(self):
        self.set_target(None)

    def __enter__(self):
        return self._target

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.set_target(None)


# ========== SUBPLAN 1.4.2: GARBAGE COLLECTION UNTUK SIKLUS ==========
class ResourceManager:
    def __init__(self):
        self._resources: Dict[str, RefCounted] = {}
        self._lock = threading.Lock()
        self._total_memory = 0
        self._create_callbacks: Dict[str, Callable] = {}

    def register_creator(self, resource_type: str, creator: Callable):
        self._create_callbacks[resource_type] = creator

    def get_or_create(self, resource_type: str, key: str, *args, **kwargs) -> RefCounted:
        full_key = f"{resource_type}:{key}"
        with self._lock:
            if full_key in self._resources:
                resource = self._resources[full_key]
                resource.add_ref()
                return resource

        if resource_type in self._create_callbacks:
            resource = self._create_callbacks[resource_type](*args, **kwargs)
        else:
            resource = RefCounted()

        resource._destroy_callback = lambda: self._remove_resource(full_key)

        with self._lock:
            if full_key in self._resources:
                resource.release()
                return self._resources[full_key]
            self._resources[full_key] = resource
            resource.add_ref()
            return resource

    def link(self, a: RefCounted, b: RefCounted):
        """Catat bahwa resource A bergantung pada resource B."""
        a.add_dependency(b)

    def register_reference(self, key_a: str, key_b: str):
        """Buat/ambil dua resource, lalu buat dependensi A -> B."""
        res_a = self.get_or_create('node', key_a)
        res_b = self.get_or_create('node', key_b)
        self.link(res_a, res_b)

    def detect_cycles(self) -> List[List[RefCounted]]:
        """Deteksi siklus referensi sederhana di antara resource yang terdaftar."""
        visited: Set[RefCounted] = set()
        cycles: List[List[RefCounted]] = []

        def dfs(node: RefCounted, path: List[RefCounted]):
            if node in path:
                idx = path.index(node)
                cycles.append(path[idx:])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for dep in node._dependencies:
                dfs(dep, path.copy())
            path.pop()

        with self._lock:
            for resource in list(self._resources.values()):
                dfs(resource, [])

        return cycles

    def break_cycle(self, cycle: List[RefCounted]):
        """Putus siklus referensi dengan menghapus dependensi timbal balik."""
        if len(cycle) < 2:
            return
        # Putus dependensi dari elemen pertama ke elemen kedua
        a, b = cycle[0], cycle[1]
        a.remove_dependency(b)
        print(f"ResourceManager: siklus diputus antara {a} <-> {b}")

    def _remove_resource(self, full_key: str):
        with self._lock:
            if full_key in self._resources:
                resource = self._resources[full_key]
                for dep in list(resource._dependencies):
                    resource.remove_dependency(dep)
                for ref in list(resource._referenced_by):
                    ref.remove_dependency(resource)
                del self._resources[full_key]
                print(f"ResourceManager: '{full_key}' dihapus.")

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                'total_resources': len(self._resources),
                'total_memory_estimate': self._total_memory,
            }
        
# ========== SUBPLAN 1.4.3: GPU RESOURCE MANAGER ==========
class GPUResource(RefCounted):
    """Resource GPU yang memiliki handle OpenGL."""
    def __init__(self, gl_handle: int = 0):
        super().__init__()
        self.gl_handle = gl_handle
        self._uploaded = False
    
    def upload(self):
        """Upload data ke GPU. Override di subclass."""
        self._uploaded = True
    
    def destroy(self):
        """Hapus resource dari GPU. Override di subclass."""
        self._uploaded = False


class Texture(GPUResource):
    """Representasi tekstur OpenGL."""
    def __init__(self, width: int = 0, height: int = 0, data: Optional[bytes] = None,
                 format: int = 0x1908, internal_format: int = 0x1908, mipmap: bool = True):
        super().__init__()
        self.width = width
        self.height = height
        self.data = data
        self.format = format
        self.internal_format = internal_format
        self.mipmap = mipmap
    
    def upload(self):
        """Buat tekstur di GPU menggunakan PyOpenGL."""
        try:
            from OpenGL.GL import (glGenTextures, glBindTexture, glTexImage2D,
                                   GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE,
                                   glTexParameteri, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            self.gl_handle = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.gl_handle)
            if self.data:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, self.data)
                if self.mipmap:
                    from OpenGL.GL import glGenerateMipmap
                    glGenerateMipmap(GL_TEXTURE_2D)
            else:
                # Alokasi kosong
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            super().upload()
        except ImportError:
            pass
    
    def destroy(self):
        if self.gl_handle:
            try:
                from OpenGL.GL import glDeleteTextures
                glDeleteTextures([self.gl_handle])
            except ImportError:
                pass
        super().destroy()


class Buffer(GPUResource):
    """Representasi Vertex Buffer Object (VBO) atau Index Buffer (IBO)."""
    VERTEX = 0x8892
    INDEX = 0x8893
    
    def __init__(self, data: Optional[bytes] = None, buffer_type: int = VERTEX,
                 usage: int = 0x88E4):
        super().__init__()
        self.data = data
        self.buffer_type = buffer_type
        self.usage = usage
    
    def upload(self):
        try:
            from OpenGL.GL import (glGenBuffers, glBindBuffer, glBufferData,
                                   GL_STATIC_DRAW, GL_ARRAY_BUFFER,
                                   GL_ELEMENT_ARRAY_BUFFER)
            self.gl_handle = glGenBuffers(1)
            glBindBuffer(self.buffer_type, self.gl_handle)
            if self.data:
                glBufferData(self.buffer_type, self.data, GL_STATIC_DRAW)
            super().upload()
        except ImportError:
            pass
    
    def destroy(self):
        if self.gl_handle:
            try:
                from OpenGL.GL import glDeleteBuffers
                glDeleteBuffers(1, [self.gl_handle])
            except ImportError:
                pass
        super().destroy()


class GPUResourceManager:
    """Mengelola semua resource GPU, memastikan tidak ada duplikasi dan bersih saat keluar."""
    
    def __init__(self):
        self._textures: Dict[str, Texture] = {}
        self._buffers: Dict[str, Buffer] = {}
        self._lock = threading.Lock()
    
    def create_texture(self, key: str, width: int, height: int,
                       data: Optional[bytes] = None,
                       format: int = 0x1908,
                       internal_format: int = 0x1908,
                       mipmap: bool = True) -> Texture:
        with self._lock:
            if key in self._textures:
                tex = self._textures[key]
                tex.add_ref()
                return tex
            tex = Texture(width, height, data, format, internal_format, mipmap)
            tex.upload()
            tex.add_ref()
            self._textures[key] = tex
            tex._destroy_callback = lambda: self._remove_texture(key)
            return tex
    
    def create_buffer(self, key: str, data: Optional[bytes] = None,
                      buffer_type: int = Buffer.VERTEX,
                      usage: int = 0x88E4) -> Buffer:
        with self._lock:
            if key in self._buffers:
                buf = self._buffers[key]
                buf.add_ref()
                return buf
            buf = Buffer(data, buffer_type, usage)
            buf.upload()
            buf.add_ref()
            self._buffers[key] = buf
            buf._destroy_callback = lambda: self._remove_buffer(key)
            return buf
    
    def _remove_texture(self, key: str):
        with self._lock:
            if key in self._textures:
                self._textures[key].destroy()
                del self._textures[key]
                print(f"GPUResourceManager: Texture '{key}' dihapus.")
    
    def _remove_buffer(self, key: str):
        with self._lock:
            if key in self._buffers:
                self._buffers[key].destroy()
                del self._buffers[key]
                print(f"GPUResourceManager: Buffer '{key}' dihapus.")
    
    def get_texture(self, key: str) -> Optional[Texture]:
        return self._textures.get(key)
    
    def get_buffer(self, key: str) -> Optional[Buffer]:
        return self._buffers.get(key)
    
    def cleanup_all(self):
        """Hapus semua resource GPU."""
        with self._lock:
            for tex in list(self._textures.values()):
                tex.destroy()
            for buf in list(self._buffers.values()):
                buf.destroy()
            self._textures.clear()
            self._buffers.clear()
            print("GPUResourceManager: Semua resource GPU dibersihkan.")

# ========== SUBPLAN 1.4.4: MEMORY POOL & OBJECT POOL ==========

class ObjectPool:
    """
    Pool objek generik yang dapat digunakan kembali untuk menghindari
    alokasi memori berulang pada objek kecil.
    """
    
    def __init__(self, factory: Callable[[], Any], initial_size: int = 64,
                 max_size: int = 1024):
        """
        factory: fungsi tanpa argumen yang membuat objek baru.
        initial_size: jumlah objek yang dialokasikan di awal.
        max_size: jumlah maksimum objek dalam pool.
        """
        self._factory = factory
        self._max_size = max_size
        self._available: List[Any] = []
        self._borrowed: Set[int] = set()  # lacak berdasarkan id(objek)
        self._lock = threading.Lock()
        
        # Alokasikan objek awal
        for _ in range(initial_size):
            obj = factory()
            self._available.append(obj)
    
    def acquire(self) -> Any:
        """Pinjam objek dari pool. Buat baru jika pool kosong."""
        with self._lock:
            if self._available:
                obj = self._available.pop()
            else:
                obj = self._factory()
            self._borrowed.add(id(obj))
            return obj
    
    def release(self, obj: Any):
        """Kembalikan objek ke pool."""
        with self._lock:
            obj_id = id(obj)
            if obj_id not in self._borrowed:
                return  # bukan dari pool ini
            
            self._borrowed.remove(obj_id)
            
            if len(self._available) < self._max_size:
                # Reset objek jika memiliki method reset()
                if hasattr(obj, 'reset'):
                    obj.reset()
                self._available.append(obj)
    
    @property
    def available_count(self) -> int:
        return len(self._available)
    
    @property
    def borrowed_count(self) -> int:
        return len(self._borrowed)
    
    def clear(self):
        """Kosongkan pool (hati-hati, objek yang dipinjam mungkin masih dipakai)."""
        with self._lock:
            self._available.clear()
            # Jangan sentuh _borrowed — objek masih di luar

# ========== SUBPLAN 1.4.5: RESOURCE CACHE & LAZY LOADING ==========
from collections import OrderedDict

class ResourceCache:
    """
    Cache resource dengan kebijakan LRU (Least Recently Used).
    Membatasi jumlah resource yang disimpan di memori.
    """
    
    def __init__(self, max_size: int = 256):
        self._max_size = max_size
        self._cache: OrderedDict[str, RefCounted] = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[RefCounted]:
        """Ambil resource dari cache. Jika ada, pindahkan ke posisi terakhir (MRU)."""
        with self._lock:
            if key in self._cache:
                resource = self._cache.pop(key)
                self._cache[key] = resource  # pindah ke akhir (most recent)
                resource.add_ref()
                return resource
            return None
    
    def put(self, key: str, resource: RefCounted):
        """Masukkan resource ke cache. Jika penuh, buang yang paling lama tidak digunakan."""
        with self._lock:
            if key in self._cache:
                # Update: pindahkan ke akhir
                self._cache.pop(key)
            elif len(self._cache) >= self._max_size:
                # Buang yang paling lama (pertama di OrderedDict)
                oldest_key, oldest_resource = self._cache.popitem(last=False)
                oldest_resource.release()  # kurangi ref count
                print(f"ResourceCache: '{oldest_key}' dibuang dari cache (LRU).")
            
            self._cache[key] = resource
            resource.add_ref()
    
    def remove(self, key: str):
        """Hapus resource spesifik dari cache."""
        with self._lock:
            if key in self._cache:
                resource = self._cache.pop(key)
                resource.release()
    
    def clear(self):
        """Kosongkan seluruh cache."""
        with self._lock:
            for key, resource in list(self._cache.items()):
                resource.release()
            self._cache.clear()
    
    def contains(self, key: str) -> bool:
        return key in self._cache
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    @property
    def max_size(self) -> int:
        return self._max_size


class LazyLoader:
    def __init__(self, loader: Callable[[], RefCounted]):
        self._loader = loader
        self._resource: Optional[RefCounted] = None
        self._loaded = False
        self._lock = threading.Lock()

    def get(self) -> RefCounted:
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._resource = self._loader()
                    self._resource.add_ref()  # Pegang referensi
                    self._loaded = True
        return self._resource

    def is_loaded(self) -> bool:
        return self._loaded

    def unload(self):
        with self._lock:
            if self._loaded and self._resource:
                self._resource.release()
                self._resource = None
                self._loaded = False

    def reload(self):
        self.unload()
        return self.get()