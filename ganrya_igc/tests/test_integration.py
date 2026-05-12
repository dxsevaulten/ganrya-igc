# ganrya_igc/tests/test_integration.py
"""
Integration tests untuk Ganrya IGC.
Menguji interaksi antar modul inti (SceneGraph, ECS, Resource, Config).
"""

import unittest
import tempfile
import os
import numpy as np
from ganrya_igc.core.scene_graph import SceneNode, Transform, AABB, PrintVisitor
from ganrya_igc.core.ecs import Entity, TransformComponent, SystemManager
from ganrya_igc.core.resource import ResourceManager, RefCounted
from ganrya_igc.core.config import Config


class TestSceneGraphIntegration(unittest.TestCase):
    """Integrasi: SceneNode + Transform + AABB."""

    def test_create_hierarchy_and_compute_world_aabb(self):
        root = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(root)

        # Atur transformasi
        root.local_transform.translation = np.array([10.0, 0.0, 0.0])
        child.local_transform.translation = np.array([5.0, 0.0, 0.0])

        # Hitung posisi dunia
        world_pos = child.get_world_position()
        np.testing.assert_array_almost_equal(world_pos, [15.0, 0.0, 0.0])

    def test_aabb_union_across_nodes(self):
        root = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(root)

        root.aabb = AABB(np.array([0,0,0]), np.array([2,2,2]))
        child.aabb = AABB(np.array([3,0,0]), np.array([5,2,2]))

        visitor = ...  # Gunakan ComputeAABBVisitor jika ada
        combined = root.aabb.union(child.aabb)
        np.testing.assert_array_almost_equal(combined.min, [0,0,0])
        np.testing.assert_array_almost_equal(combined.max, [5,2,2])


class TestECSResourceIntegration(unittest.TestCase):
    """Integrasi: ECS + ResourceManager."""

    def test_entity_with_transform_and_resource(self):
        entity = Entity()
        entity.add_component(TransformComponent(1.0, 2.0, 3.0))

        rm = ResourceManager()
        rm.register_creator('mesh', lambda *a, **kw: RefCounted())
        mesh = rm.get_or_create('mesh', 'cube')

        self.assertIsNotNone(entity.get_component(TransformComponent))
        self.assertIsNotNone(mesh)
        self.assertEqual(mesh.ref_count, 1)


class TestConfigSceneIntegration(unittest.TestCase):
    """Integrasi: Config + SceneGraph."""

    def test_config_controls_scene_parameters(self):
        config = Config({'scene.offset': 5.0})
        offset = config.get('scene.offset')

        node = SceneNode("origin")
        node.local_transform.translation = np.array([offset, 0.0, 0.0])
        np.testing.assert_array_almost_equal(
            node.local_transform.translation, [5.0, 0.0, 0.0]
        )


class TestFullWorkflow(unittest.TestCase):
    """Simulasi workflow lengkap: buat scene, konfigurasi, serialisasi."""

    def test_create_scene_serialize_and_deserialize(self):
        # 1. Buat scene
        root = SceneNode("root")
        child = SceneNode("child")
        child.set_parent(root)
        child.local_transform.translation = np.array([1.0, 2.0, 3.0])

        # 2. Konfigurasi
        cfg = Config({'export.format': 'json'})
        fmt = cfg.get('export.format')
        self.assertEqual(fmt, 'json')

        # 3. Serialisasi
        from ganrya_igc.core.serialization import SceneSerializer
        serializer = SceneSerializer()
        raw = serializer.serialize_scene(root)

        # 4. Deserialisasi
        restored = serializer.deserialize_scene(raw)
        self.assertEqual(restored.name, "root")
        self.assertEqual(len(restored.children), 1)
        np.testing.assert_array_almost_equal(
            restored.children[0].local_transform.translation,
            [1.0, 2.0, 3.0]
        )


if __name__ == '__main__':
    unittest.main()