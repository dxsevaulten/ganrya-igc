# ganrya_igc/tests/test_resource.py
import unittest
from ganrya_igc.core.resource import RefCounted, Ref, ResourceManager
from ganrya_igc.core.resource import GPUResource, Texture, Buffer, GPUResourceManager
from ganrya_igc.core.resource import ObjectPool
from ganrya_igc.core.resource import ResourceCache, LazyLoader

class TestRefCounted(unittest.TestCase):
    def test_initial_ref_count_is_zero(self):
        obj = RefCounted()
        self.assertEqual(obj.ref_count, 0)
    
    def test_add_ref_increases_count(self):
        obj = RefCounted()
        obj.add_ref()
        self.assertEqual(obj.ref_count, 1)
        obj.add_ref()
        self.assertEqual(obj.ref_count, 2)
    
    def test_release_decreases_count(self):
        obj = RefCounted()
        obj.add_ref()
        obj.add_ref()
        obj.release()
        self.assertEqual(obj.ref_count, 1)
    
    def test_destroy_callback_called_on_zero(self):
        destroyed = []
        obj = RefCounted()
        obj._destroy_callback = lambda: destroyed.append(True)
        obj.add_ref()
        obj.release()  # count = 0, callback dipanggil
        self.assertEqual(len(destroyed), 1)


class TestRef(unittest.TestCase):
    def test_ref_adds_reference(self):
        obj = RefCounted()
        ref = Ref(obj)
        self.assertEqual(obj.ref_count, 1)
    
    def test_ref_releases_on_set_target_none(self):
        obj = RefCounted()
        ref = Ref(obj)
        ref.set_target(None)
        self.assertEqual(obj.ref_count, 0)
    
    def test_ref_switches_target(self):
        obj1 = RefCounted()
        obj2 = RefCounted()
        ref = Ref(obj1)
        self.assertEqual(obj1.ref_count, 1)
        ref.set_target(obj2)
        self.assertEqual(obj1.ref_count, 0)
        self.assertEqual(obj2.ref_count, 1)
    
    def test_context_manager(self):
        obj = RefCounted()
        with Ref(obj) as target:
            self.assertEqual(target, obj)
            self.assertEqual(obj.ref_count, 1)
        self.assertEqual(obj.ref_count, 0)


class TestResourceManager(unittest.TestCase):
    def setUp(self):
        self.rm = ResourceManager()
    
    def test_get_or_create_returns_same_resource(self):
        self.rm.register_creator('texture', lambda *a, **kw: RefCounted())
        res1 = self.rm.get_or_create('texture', 'brick.png')
        res2 = self.rm.get_or_create('texture', 'brick.png')
        self.assertIs(res1, res2)
        self.assertEqual(res1.ref_count, 2)
    
    def test_resource_removed_when_all_refs_released(self):
        self.rm.register_creator('mesh', lambda: RefCounted())
        res = self.rm.get_or_create('mesh', 'cube')
        key = 'mesh:cube'
        self.assertIn(key, self.rm._resources)
        # Lepaskan referensi
        for _ in range(res.ref_count):
            res.release()
        # Resource harus sudah dihapus
        self.assertNotIn(key, self.rm._resources)
    
    def test_get_stats(self):
        self.rm.register_creator('material', lambda *a, **kw: RefCounted())
        self.rm.get_or_create('material', 'red')
        stats = self.rm.get_stats()
        self.assertEqual(stats['total_resources'], 1)

class TestGarbageCollection(unittest.TestCase):
    def setUp(self):
        self.rm = ResourceManager()
        self.rm.register_creator('node', lambda: RefCounted())
    
    def test_detect_simple_cycle(self):
        # A -> B -> A
        a = self.rm.get_or_create('node', 'A')
        b = self.rm.get_or_create('node', 'B')
        self.rm.register_reference('node:A', 'node:B')
        self.rm.register_reference('node:B', 'node:A')
        
        cycles = self.rm.detect_cycles()
        self.assertGreater(len(cycles), 0)
    
    def test_break_cycle(self):
        a = RefCounted()
        b = RefCounted()
        a.add_dependency(b)
        b.add_dependency(a)
        self.rm._resources['node:A'] = a
        self.rm._resources['node:B'] = b
        
        cycles = self.rm.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)
        self.rm.break_cycle(cycles[0])
        # Verifikasi tidak ada siklus lagi
        self.assertEqual(len(self.rm.detect_cycles()), 0)
    
    def test_run_gc(self):
        a = RefCounted()
        b = RefCounted()
        a.add_dependency(b)
        b.add_dependency(a)
        self.rm._resources['node:A'] = a
        self.rm._resources['node:B'] = b
        
        # Jalankan GC manual (detect + break)
        cycles = self.rm.detect_cycles()
        for cycle in cycles:
            self.rm.break_cycle(cycle)
        self.assertEqual(len(self.rm.detect_cycles()), 0)

class TestCycleDetection(unittest.TestCase):
    def setUp(self):
        self.rm = ResourceManager()

    def test_detect_cycle_two_nodes(self):
        a = RefCounted()
        b = RefCounted()
        # Buat siklus A <-> B
        a.add_dependency(b)
        b.add_dependency(a)
        
        # Daftarkan secara manual agar bisa dideteksi
        self.rm._resources['a'] = a
        self.rm._resources['b'] = b
        
        cycles = self.rm.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)

    def test_no_cycle_when_no_dependencies(self):
        a = RefCounted()
        b = RefCounted()
        self.rm._resources['a'] = a
        self.rm._resources['b'] = b
        
        cycles = self.rm.detect_cycles()
        self.assertEqual(len(cycles), 0)

    def test_break_cycle(self):
        a = RefCounted()
        b = RefCounted()
        a.add_dependency(b)
        b.add_dependency(a)
        self.rm._resources['a'] = a
        self.rm._resources['b'] = b
        
        cycles = self.rm.detect_cycles()
        self.assertGreaterEqual(len(cycles), 1)
        self.rm.break_cycle(cycles[0])
        # Setelah diputus, tidak ada siklus
        self.assertEqual(len(self.rm.detect_cycles()), 0)

    def test_link_method(self):
        a = RefCounted()
        b = RefCounted()
        self.rm.link(a, b)
        self.assertIn(b, a._dependencies)
        self.assertIn(a, b._referenced_by)

class TestGPUResource(unittest.TestCase):
    def test_texture_has_default_values(self):
        tex = Texture(64, 64)
        self.assertEqual(tex.width, 64)
        self.assertEqual(tex.height, 64)
        self.assertEqual(tex.ref_count, 0)
    
    def test_buffer_has_correct_type(self):
        buf = Buffer(b'data', Buffer.VERTEX)
        self.assertEqual(buf.buffer_type, Buffer.VERTEX)
        buf2 = Buffer(b'data', Buffer.INDEX)
        self.assertEqual(buf2.buffer_type, Buffer.INDEX)
    pass

@unittest.skipUnless(False, "Memerlukan konteks OpenGL (lewati untuk saat ini)")
class TestGPUResourceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = GPUResourceManager()
    
    def test_create_texture_returns_same_on_duplicate(self):
        tex1 = self.mgr.create_texture('test_tex', 64, 64)
        tex2 = self.mgr.create_texture('test_tex', 64, 64)
        self.assertIs(tex1, tex2)
        self.assertEqual(tex1.ref_count, 2)
    
    def test_create_buffer_returns_same_on_duplicate(self):
        buf1 = self.mgr.create_buffer('test_buf', b'vertex_data')
        buf2 = self.mgr.create_buffer('test_buf', b'vertex_data')
        self.assertIs(buf1, buf2)
        self.assertEqual(buf1.ref_count, 2)
    
    def test_texture_removed_after_all_releases(self):
        tex = self.mgr.create_texture('unique_tex', 64, 64)
        self.assertIsNotNone(self.mgr.get_texture('unique_tex'))
        for _ in range(tex.ref_count):
            tex.release()
        self.assertIsNone(self.mgr.get_texture('unique_tex'))
    
    def test_cleanup_all_removes_everything(self):
        self.mgr.create_texture('t1', 64, 64)
        self.mgr.create_buffer('b1', b'data')
        self.mgr.cleanup_all()
        self.assertIsNone(self.mgr.get_texture('t1'))
        self.assertIsNone(self.mgr.get_buffer('b1'))

class TestObjectPool(unittest.TestCase):
    def setUp(self):
        # Factory: buat list kecil sebagai "objek"
        self.pool = ObjectPool(factory=lambda: [0.0, 0.0, 0.0], initial_size=4, max_size=8)
    
    def test_acquire_returns_object(self):
        obj = self.pool.acquire()
        self.assertIsNotNone(obj)
        self.assertEqual(len(obj), 3)
        self.pool.release(obj)
    
    def test_acquire_reuse_objects(self):
        obj1 = self.pool.acquire()
        id1 = id(obj1)
        self.pool.release(obj1)
        
        obj2 = self.pool.acquire()
        # Karena pool punya objek yang sudah dikembalikan, harusnya sama
        self.assertEqual(id(obj2), id1)
        self.pool.release(obj2)
    
    def test_acquire_exceeding_initial_size(self):
        objects = []
        for _ in range(10):
            obj = self.pool.acquire()
            objects.append(obj)
        # Semua objek harus berbeda
        self.assertEqual(len(set(id(o) for o in objects)), 10)
        
        # Kembalikan semua
        for obj in objects:
            self.pool.release(obj)
        # Pool tidak boleh melebihi max_size
        self.assertLessEqual(self.pool.available_count, 8)
    
    def test_reset_method_called_on_release(self):
        class Resettable:
            def __init__(self):
                self.value = 0
            def reset(self):
                self.value = 0
        
        pool = ObjectPool(factory=Resettable, initial_size=2)
        obj = pool.acquire()
        obj.value = 42
        pool.release(obj)
        # Setelah release, value harus di-reset (jika masuk kembali ke pool)
        obj2 = pool.acquire()
        self.assertEqual(obj2.value, 0)
    
    def test_available_and_borrowed_counts(self):
        self.assertEqual(self.pool.available_count, 4)
        self.assertEqual(self.pool.borrowed_count, 0)
        
        obj1 = self.pool.acquire()
        self.assertEqual(self.pool.available_count, 3)
        self.assertEqual(self.pool.borrowed_count, 1)
        
        self.pool.release(obj1)
        self.assertEqual(self.pool.available_count, 4)
        self.assertEqual(self.pool.borrowed_count, 0)

class TestResourceCache(unittest.TestCase):
    def setUp(self):
        self.cache = ResourceCache(max_size=3)

    def test_put_and_get(self):
        obj = RefCounted()
        self.cache.put("key1", obj)
        retrieved = self.cache.get("key1")
        self.assertIs(retrieved, obj)
        self.assertEqual(obj.ref_count, 2)  # satu dari put, satu dari get

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(self.cache.get("missing"))

    def test_lru_eviction(self):
        obj1 = RefCounted()
        obj2 = RefCounted()
        obj3 = RefCounted()
        obj4 = RefCounted()

        self.cache.put("a", obj1)  # a (oldest)
        self.cache.put("b", obj2)
        self.cache.put("c", obj3)  # c (newest)

        # Akses a agar menjadi MRU
        self.cache.get("a")
        self.cache.get("b")

        # Sekarang urutan: c (oldest), a, b (newest)
        # Tambahkan obj4, harusnya c yang dibuang
        self.cache.put("d", obj4)

        self.assertFalse(self.cache.contains("c"))
        self.assertTrue(self.cache.contains("a"))
        self.assertTrue(self.cache.contains("b"))
        self.assertTrue(self.cache.contains("d"))
        self.assertEqual(self.cache.size, 3)

    def test_remove(self):
        obj = RefCounted()
        self.cache.put("x", obj)
        self.cache.remove("x")
        self.assertFalse(self.cache.contains("x"))
        self.assertEqual(obj.ref_count, 0)

    def test_clear(self):
        self.cache.put("p", RefCounted())
        self.cache.put("q", RefCounted())
        self.cache.clear()
        self.assertEqual(self.cache.size, 0)


class TestLazyLoader(unittest.TestCase):
    def test_loader_called_only_once(self):
        call_count = 0
        def factory():
            nonlocal call_count
            call_count += 1
            return RefCounted()

        loader = LazyLoader(factory)
        r1 = loader.get()
        r2 = loader.get()
        self.assertEqual(call_count, 1)
        self.assertIs(r1, r2)

    def test_is_loaded(self):
        loader = LazyLoader(lambda: RefCounted())
        self.assertFalse(loader.is_loaded())
        loader.get()
        self.assertTrue(loader.is_loaded())

    def test_unload(self):
        obj = RefCounted()
        loader = LazyLoader(lambda: obj)
        loader.get()
        self.assertEqual(obj.ref_count, 1)  # loader tidak menahan ref
        loader.unload()
        self.assertEqual(obj.ref_count, 0)

    def test_reload(self):
        call_count = 0
        def factory():
            nonlocal call_count
            call_count += 1
            return RefCounted()

        loader = LazyLoader(factory)
        loader.get()
        self.assertEqual(call_count, 1)
        loader.reload()
        self.assertEqual(call_count, 2)  # loader dipanggil lagi

if __name__ == '__main__':
    unittest.main()