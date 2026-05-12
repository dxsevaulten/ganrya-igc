# ganrya_igc/tests/test_serialization.py
import unittest
from ganrya_igc.core.serialization import GLTFExporter, CustomProjectSerializer
import tempfile
import os
import numpy as np
from ganrya_igc.core.serialization import (
    JSONSerializer, BinarySerializer, SceneSerializer
)
from ganrya_igc.core.scene_graph import SceneNode, Transform
import time
from ganrya_igc.core.serialization import AutosaveManager, IncrementalSaver, CustomProjectSerializer

class TestJSONSerializer(unittest.TestCase):
    def setUp(self):
        self.serializer = JSONSerializer()
    
    def test_roundtrip_dict(self):
        data = {'key': 'value', 'number': 42, 'list': [1, 2, 3]}
        raw = self.serializer.serialize(data)
        result = self.serializer.deserialize(raw)
        self.assertEqual(result, data)
    
    def test_roundtrip_nested(self):
        data = {'name': 'root', 'children': [{'name': 'child1'}, {'name': 'child2'}]}
        raw = self.serializer.serialize(data)
        result = self.serializer.deserialize(raw)
        self.assertEqual(len(result['children']), 2)
    
    def test_file_roundtrip(self):
        data = {'test': True, 'value': 3.14}
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            path = f.name
        try:
            self.serializer.serialize_to_file(data, path)
            result = self.serializer.deserialize_from_file(path)
            self.assertEqual(result, data)
        finally:
            os.unlink(path)


class TestBinarySerializer(unittest.TestCase):
    def setUp(self):
        self.serializer = BinarySerializer()
    
    def test_roundtrip_dict(self):
        data = {'key': 'value', 'number': 42}
        raw = self.serializer.serialize(data)
        result = self.serializer.deserialize(raw)
        self.assertEqual(result, data)
    
    def test_roundtrip_large_data(self):
        data = {'vertices': [[1.0, 2.0, 3.0] for _ in range(100)]}
        raw = self.serializer.serialize(data)
        result = self.serializer.deserialize(raw)
        self.assertEqual(len(result['vertices']), 100)


class TestSceneSerializer(unittest.TestCase):
    def setUp(self):
        self.serializer = SceneSerializer()
    
    def test_serialize_single_node(self):
        node = SceneNode("root")
        node.local_transform.translation = np.array([1.0, 2.0, 3.0])
        raw = self.serializer.serialize_scene(node)
        self.assertIsInstance(raw, bytes)
        self.assertGreater(len(raw), 0)
    
    def test_deserialize_single_node(self):
        node = SceneNode("root")
        node.local_transform.translation = np.array([4.0, 5.0, 6.0])
        raw = self.serializer.serialize_scene(node)
        restored = self.serializer.deserialize_scene(raw)
        self.assertEqual(restored.name, "root")
        np.testing.assert_array_almost_equal(
            restored.local_transform.translation, [4.0, 5.0, 6.0]
        )
    
    def test_serialize_hierarchy(self):
        parent = SceneNode("parent")
        child = SceneNode("child")
        child.set_parent(parent)
        
        raw = self.serializer.serialize_scene(parent)
        restored = self.serializer.deserialize_scene(raw)
        self.assertEqual(len(restored.children), 1)
        self.assertEqual(restored.children[0].name, "child")

class TestGLTFExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = GLTFExporter()
    
    def test_export_empty_node(self):
        node = SceneNode("test")
        gltf = self.exporter.export_scene(node)
        self.assertEqual(gltf['asset']['version'], '2.0')
        self.assertIn('nodes', gltf)
        self.assertEqual(len(gltf['nodes']), 1)
        self.assertEqual(gltf['nodes'][0]['name'], 'test')
    
    def test_export_hierarchy(self):
        parent = SceneNode("parent")
        child = SceneNode("child")
        child.set_parent(parent)
        
        gltf = self.exporter.export_scene(parent)
        self.assertEqual(len(gltf['nodes']), 2)
        # Parent (indeks 0) memiliki child di indeks 1
        self.assertIn(1, gltf['nodes'][0].get('children', []))
    
    def test_export_glb_returns_bytes(self):
        node = SceneNode("root")
        glb = self.exporter.export_glb(node)
        self.assertIsInstance(glb, bytes)
        self.assertGreater(len(glb), 0)
        # Cek magic header
        self.assertEqual(glb[:4], b'glTF')

class TestCustomProjectSerializer(unittest.TestCase):
    def setUp(self):
        self.node = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(self.node)
    
    def test_save_and_load_project(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.msp') as f:
            path = f.name
        try:
            CustomProjectSerializer.save_project(self.node, path, {'author': 'test'})
            root, meta = CustomProjectSerializer.load_project(path)
            self.assertEqual(root.name, 'root')
            self.assertEqual(len(root.children), 1)
            self.assertEqual(meta['author'], 'test')
        finally:
            os.unlink(path)

class TestVersionMigration(unittest.TestCase):
    def setUp(self):
        self.serializer = SceneSerializer()
    
    def test_migrate_old_version_adds_scale(self):
        # Data scene versi 0.9.0 tanpa field 'scale'
        old_data = {
            'version': '0.9.0',
            'scene': {
                'name': 'root',
                'translation': [1, 2, 3],
                'rotation': [0, 0, 0, 1],
                'children': [
                    {
                        'name': 'child',
                        'translation': [4, 5, 6],
                        'rotation': [0, 0, 0, 1],
                        'children': []
                    }
                ],
                'components': {}
            }
        }
        raw = JSONSerializer().serialize(old_data)
        root = self.serializer.deserialize_scene(raw)
        
        # Root dan child harus memiliki scale default [1, 1, 1]
        np.testing.assert_array_almost_equal(root.local_transform.scale, [1, 1, 1])
        self.assertEqual(len(root.children), 1)
        np.testing.assert_array_almost_equal(
            root.children[0].local_transform.scale, [1, 1, 1]
        )
    
    def test_current_version_unchanged(self):
        # Data versi saat ini harus melalui migrasi tanpa perubahan
        node = SceneNode("root")
        raw = self.serializer.serialize_scene(node)
        root = self.serializer.deserialize_scene(raw)
        self.assertEqual(root.name, "root")

class TestAutosaveManager(unittest.TestCase):
    def setUp(self):
        self.saved = []
        self.manager = AutosaveManager(
            save_callback=lambda: self.saved.append(time.time()),
            interval_seconds=0.1  # interval pendek untuk pengujian
        )

    def tearDown(self):
        self.manager.stop()

    def test_autosave_starts_and_saves(self):
        self.manager.start()
        time.sleep(0.35)  # cukup untuk 2-3 kali autosave
        self.manager.stop()
        self.assertGreaterEqual(len(self.saved), 2)

    def test_force_save(self):
        self.manager.start()
        self.manager.force_save()
        self.manager.stop()
        self.assertGreaterEqual(len(self.saved), 1)

    def test_stop_prevents_further_saves(self):
        self.manager.start()
        time.sleep(0.15)
        self.manager.stop()
        count_before = len(self.saved)
        time.sleep(0.2)
        self.assertEqual(len(self.saved), count_before)

class TestIncrementalSaver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.filepath = os.path.join(self.temp_dir, "test_scene.json")
        self.saver = IncrementalSaver(self.filepath, max_backups=2)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_creates_file(self):
        node = SceneNode("root")
        self.saver.save_node(node)
        self.assertTrue(os.path.exists(self.filepath))
    
    def test_save_and_load_node(self):
        node = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(node)
        self.saver.save_node(node)
        
        restored = self.saver.load_node()
        self.assertEqual(restored.name, "root")
        self.assertEqual(len(restored.children), 1)
        self.assertEqual(restored.children[0].name, "child")
    
    def test_save_rotates_backups(self):
        node1 = SceneNode("v1")
        node2 = SceneNode("v2")
        node3 = SceneNode("v3")
        
        self.saver.save_node(node1)
        self.saver.save_node(node2)
        self.saver.save_node(node3)
        
        # File utama harus berisi "v3"
        restored = self.saver.load_node()
        self.assertEqual(restored.name, "v3")
        
        # .bak1 harus berisi "v2"
        self.assertTrue(os.path.exists(f"{self.filepath}.bak1"))
    
    def test_autosave_triggers_on_change(self):
        # Verifikasi autosave bisa dipanggil berkali-kali tanpa error
        node = SceneNode("test")
        self.saver.save_node(node)
        self.saver.save_node(node)  # simpan lagi
        self.assertTrue(os.path.exists(self.filepath))

if __name__ == '__main__':
    unittest.main()