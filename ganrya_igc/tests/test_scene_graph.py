import unittest
import numpy as np
from ganrya_igc.core.scene_graph import Transform, SceneNode, AABB, PrintVisitor, ComputeAABBVisitor
import threading
import time

class TestThreadSafety(unittest.TestCase):
    def test_concurrent_reads(self):
        """Beberapa thread membaca world matrix secara bersamaan tidak boleh error."""
        root = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(root)
        
        errors = []
        def reader():
            try:
                for _ in range(100):
                    _ = root.get_world_matrix()
                    _ = child.get_world_position()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
    
    def test_write_during_read(self):
        """Penulisan transformasi selama pembacaan tidak boleh corrupt data."""
        parent = SceneNode("parent")
        child = SceneNode("child")
        child.set_parent(parent)
        
        errors = []
        def writer():
            for i in range(50):
                parent.local_transform = Transform(translation=np.array([float(i), 0, 0]))
                time.sleep(0.001)
        
        def reader():
            for _ in range(50):
                _ = child.get_world_matrix()
                time.sleep(0.002)
        
        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        # Tidak ada assertion; jika tidak crash, test lolos

class TestAABB(unittest.TestCase):
    def test_empty_aabb(self):
        aabb = AABB()
        self.assertFalse(aabb.is_valid())
    
    def test_extend(self):
        aabb = AABB()
        aabb.extend(np.array([1.0, 2.0, 3.0]))
        aabb.extend(np.array([-1.0, 5.0, 0.0]))
        np.testing.assert_array_almost_equal(aabb.min, [-1.0, 2.0, 0.0])
        np.testing.assert_array_almost_equal(aabb.max, [1.0, 5.0, 3.0])
        self.assertTrue(aabb.is_valid())
    
    def test_union(self):
        a1 = AABB(np.array([0,0,0]), np.array([1,1,1]))
        a2 = AABB(np.array([-1,-1,-1]), np.array([0,0,0]))
        u = a1.union(a2)
        np.testing.assert_array_almost_equal(u.min, [-1,-1,-1])
        np.testing.assert_array_almost_equal(u.max, [1,1,1])


class TestSceneNodeComponents(unittest.TestCase):
    def test_add_and_get_component(self):
        node = SceneNode("test")
        mesh = object()  # placeholder
        node.add_component('mesh', mesh)
        self.assertIs(node.get_component('mesh'), mesh)
        self.assertIsNone(node.get_component('material'))
    
    def test_remove_component(self):
        node = SceneNode("test")
        node.add_component('mesh', object())
        node.remove_component('mesh')
        self.assertIsNone(node.get_component('mesh'))
    
    def test_reparenting_removes_from_old_parent(self):
        parent1 = SceneNode("p1")
        parent2 = SceneNode("p2")
        child = SceneNode("c")
        child.set_parent(parent1)
        self.assertIn(child, parent1.children)
        child.set_parent(parent2)
        self.assertNotIn(child, parent1.children)
        self.assertIn(child, parent2.children)
    
    def test_compute_aabb_no_mesh(self):
        node = SceneNode("n")
        aabb = node.compute_aabb()
        self.assertFalse(aabb.is_valid())
    
    def test_compute_aabb_with_mesh(self):
        # Buat mesh dummy dengan vertices
        class DummyMesh:
            def __init__(self, verts):
                self.vertices = verts
        mesh = DummyMesh([np.array([0,0,0]), np.array([1,2,3])])
        node = SceneNode("n")
        node.add_component('mesh', mesh)
        aabb = node.compute_aabb()
        self.assertTrue(aabb.is_valid())
        np.testing.assert_array_almost_equal(aabb.min, [0,0,0])
        np.testing.assert_array_almost_equal(aabb.max, [1,2,3])

class TestVisitorPattern(unittest.TestCase):
    def test_print_visitor(self):
        """Cek bahwa PrintVisitor bisa berjalan tanpa error."""
        root = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(root)
        grandchild = SceneNode("grandchild")
        grandchild.set_parent(child)
        
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        visitor = PrintVisitor()
        visitor.traverse(root)
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn("root", output)
        self.assertIn("child", output)
        self.assertIn("grandchild", output)

    def test_compute_aabb_visitor(self):
        """Cek bahwa ComputeAABBVisitor menghitung AABB global dengan benar."""
        class DummyMesh:
            def __init__(self, verts):
                self.vertices = verts
        # Node 1: kubus di origin
        mesh1 = DummyMesh([np.array([0,0,0]), np.array([1,1,1])])
        node1 = SceneNode("node1")
        node1.add_component('mesh', mesh1)
        # Node 2: kubus di (2,0,0)
        mesh2 = DummyMesh([np.array([2,0,0]), np.array([3,1,1])])
        node2 = SceneNode("node2")
        node2.add_component('mesh', mesh2)
        node2.set_parent(node1)  # child dari node1
        
        visitor = ComputeAABBVisitor()
        visitor.traverse(node1)
        global_aabb = visitor.global_aabb
        self.assertTrue(global_aabb.is_valid())
        # AABB global harus mencakup kedua kubus
        np.testing.assert_array_almost_equal(global_aabb.min, [0,0,0])
        np.testing.assert_array_almost_equal(global_aabb.max, [3,1,1])

class TestDirtyFlag(unittest.TestCase):
    def test_cache_returns_same_values(self):
        node = SceneNode("n")
        wm1 = node.get_world_matrix()
        wm2 = node.get_world_matrix()
        # Nilai harus sama, meskipun objek berbeda (karena thread-safe copy)
        np.testing.assert_array_almost_equal(wm1, wm2)

    def test_parent_change_invalidates_cache(self):
        parent = SceneNode("parent")
        child = SceneNode("child")
        child.set_parent(parent)
        wm1 = child.get_world_matrix()

        # Ubah transformasi parent melalui setter
        parent.local_transform = Transform(translation=np.array([10.0, 0.0, 0.0]))
        wm2 = child.get_world_matrix()
        # Harus berbeda karena parent berubah
        self.assertFalse(np.array_equal(wm1, wm2))

    def test_setter_invalidates_cache(self):
        node = SceneNode("n")
        wm1 = node.get_world_matrix()
        # Ubah lewat setter
        new_t = Transform(translation=np.array([1.0, 2.0, 3.0]))
        node.local_transform = new_t
        wm2 = node.get_world_matrix()
        self.assertFalse(np.array_equal(wm1, wm2))

    def test_child_invalidates_when_parent_dirty(self):
        parent = SceneNode("p")
        child = SceneNode("c")
        child.set_parent(parent)
        wm_child = child.get_world_matrix()
        self.assertTrue(child._world_dirty == False)

        parent.invalidate_world()
        self.assertTrue(child._world_dirty == True)

# Gabung dengan test sebelumnya
if __name__ == '__main__':
    unittest.main()