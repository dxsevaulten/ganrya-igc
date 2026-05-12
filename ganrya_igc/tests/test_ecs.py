# ganrya_igc/tests/test_ecs.py
import unittest
from ganrya_igc.core.ecs import (
    Entity, Component,
    TransformComponent, MeshComponent, MaterialComponent
)
from ganrya_igc.core.ecs import System, SystemManager
from typing import Set, Type
from ganrya_igc.core.ecs import EventBus, SystemManagerDOD, SystemWithEvents
from ganrya_igc.core.ecs import ArchetypeStorage

# --- Di dalam file, tambahkan class test baru ---
class MockMovementSystem(System):
    def __init__(self):
        super().__init__(required_components={TransformComponent})
        self.updated_count = 0
    
    def update(self, delta_time: float):
        for entity in self.entities:
            transform = entity.get_component(TransformComponent)
            transform.x += 1.0 * delta_time
            self.updated_count += 1

class MockRenderSystem(System):
    def __init__(self):
        super().__init__(required_components={MeshComponent, MaterialComponent})
        self.rendered = []
    
    def update(self, delta_time: float):
        for entity in self.entities:
            mesh = entity.get_component(MeshComponent)
            mat = entity.get_component(MaterialComponent)
            self.rendered.append((mesh, mat))


class TestSystem(unittest.TestCase):
    def test_system_can_process_entity(self):
        system = MockMovementSystem()
        entity = Entity()
        # Belum punya TransformComponent
        self.assertFalse(system.can_process(entity))
        entity.add_component(TransformComponent())
        self.assertTrue(system.can_process(entity))
    
    def test_system_updates_only_relevant_entities(self):
        system = MockMovementSystem()
        mngr = SystemManager()
        mngr.add_system(system)
        
        e1 = Entity()
        e1.add_component(TransformComponent())
        e2 = Entity()  # tidak punya TransformComponent
        e3 = Entity()
        e3.add_component(TransformComponent())
        
        mngr.add_entity(e1)
        mngr.add_entity(e2)
        mngr.add_entity(e3)
        
        mngr.update(2.0)  # delta_time = 2 detik
        # Hanya e1 dan e3 yang diproses
        self.assertEqual(len(system.entities), 2)
        self.assertIn(e1, system.entities)
        self.assertIn(e3, system.entities)
        self.assertEqual(system.updated_count, 2)

    def test_systemmanager_add_remove_entities(self):
        mngr = SystemManager()
        system = MockMovementSystem()
        mngr.add_system(system)
        
        entity = Entity()
        entity.add_component(TransformComponent())
        mngr.add_entity(entity)
        self.assertIn(entity, system.entities)
        
        mngr.remove_entity(entity)
        self.assertNotIn(entity, system.entities)

    def test_multiple_systems_run_independently(self):
        move = MockMovementSystem()
        render = MockRenderSystem()
        mngr = SystemManager()
        mngr.add_system(move)
        mngr.add_system(render)
        
        e = Entity()
        e.add_component(TransformComponent())
        e.add_component(MeshComponent())
        e.add_component(MaterialComponent(color=(255, 0, 0, 255)))
        mngr.add_entity(e)
        
        mngr.update(1.0)
        # Movement system harus memperbarui
        self.assertEqual(move.updated_count, 1)
        # Render system harus merender
        self.assertEqual(len(render.rendered), 1)
        # Transformasi entity berubah
        self.assertAlmostEqual(e.get_component(TransformComponent).x, 1.0)

    def test_late_added_system_gets_existing_entities(self):
        mngr = SystemManager()
        entity = Entity()
        entity.add_component(TransformComponent())
        mngr.add_entity(entity)
        
        # System ditambahkan setelah entity
        system = MockMovementSystem()
        mngr.add_system(system)
        self.assertIn(entity, system.entities)

class TestEntity(unittest.TestCase):
    def test_entity_has_unique_id(self):
        e1 = Entity()
        e2 = Entity()
        self.assertNotEqual(e1.id, e2.id)

    def test_add_and_get_component(self):
        e = Entity()
        transform = TransformComponent(1.0, 2.0, 3.0)
        e.add_component(transform)
        retrieved = e.get_component(TransformComponent)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.x, 1.0)

    def test_has_component(self):
        e = Entity()
        self.assertFalse(e.has_component(TransformComponent))
        e.add_component(TransformComponent())
        self.assertTrue(e.has_component(TransformComponent))

    def test_remove_component(self):
        e = Entity()
        e.add_component(TransformComponent())
        e.remove_component(TransformComponent)
        self.assertFalse(e.has_component(TransformComponent))
        self.assertIsNone(e.get_component(TransformComponent))

    def test_overwrite_component(self):
        e = Entity()
        t1 = TransformComponent(1.0, 0.0, 0.0)
        t2 = TransformComponent(2.0, 0.0, 0.0)
        e.add_component(t1)
        e.add_component(t2)
        retrieved = e.get_component(TransformComponent)
        self.assertEqual(retrieved.x, 2.0)

    def test_multiple_component_types(self):
        e = Entity()
        e.add_component(TransformComponent())
        e.add_component(MeshComponent())
        e.add_component(MaterialComponent(color=(0, 255, 0, 255)))
        self.assertTrue(e.has_component(TransformComponent))
        self.assertTrue(e.has_component(MeshComponent))
        self.assertTrue(e.has_component(MaterialComponent))

    def test_entity_name(self):
        e = Entity()
        e.name = "Player"
        self.assertEqual(e.name, "Player")

# Di bagian atas, tambahkan import
from ganrya_igc.core.ecs import ComponentStore, EntityDOD, SystemDOD

class TestComponentStore(unittest.TestCase):
    def setUp(self):
        self.store = ComponentStore()
        self.entity = EntityDOD(self.store)
    
    def test_add_and_get_component(self):
        transform = TransformComponent(5.0, 0.0, 0.0)
        self.entity.add_component(transform)
        retrieved = self.entity.get_component(TransformComponent)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.x, 5.0)
    
    def test_remove_component(self):
        self.entity.add_component(TransformComponent())
        self.entity.remove_component(TransformComponent)
        self.assertIsNone(self.entity.get_component(TransformComponent))
        self.assertFalse(self.entity.has_component(TransformComponent))
    
    def test_get_all_entities_with(self):
        e1 = EntityDOD(self.store)
        e2 = EntityDOD(self.store)
        e1.add_component(TransformComponent(1,0,0))
        e2.add_component(TransformComponent(2,0,0))
        ids = self.store.get_all_entities_with(TransformComponent)
        self.assertIn(e1.id, ids)
        self.assertIn(e2.id, ids)
    
    def test_store_reuse_slots(self):
        # Tambah, hapus, tambah lagi — harus menggunakan kembali indeks
        e1 = EntityDOD(self.store)
        e1.add_component(TransformComponent())
        e1.remove_component(TransformComponent)
        e2 = EntityDOD(self.store)
        e2.add_component(TransformComponent())
        # e2 seharusnya bisa menggunakan slot yang sama dengan e1
        retrieved = e2.get_component(TransformComponent)
        self.assertIsNotNone(retrieved)

class TestEventBus(unittest.TestCase):
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        def handler(data):
            received.append(data)
        
        bus.subscribe('test_event', handler)
        bus.publish('test_event', {'value': 42})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['value'], 42)
    
    def test_unsubscribe(self):
        bus = EventBus()
        received = []
        def handler(data):
            received.append(data)
        
        bus.subscribe('test', handler)
        bus.unsubscribe('test', handler)
        bus.publish('test', {'x': 1})
        self.assertEqual(len(received), 0)
    
    def test_multiple_subscribers(self):
        bus = EventBus()
        count = [0]
        def h1(data): count[0] += 1
        def h2(data): count[0] += 1
        bus.subscribe('e', h1)
        bus.subscribe('e', h2)
        bus.publish('e')
        self.assertEqual(count[0], 2)

class TestSystemEvents(unittest.TestCase):
    def test_systemmanager_dod_publishes_entity_events(self):
        mngr = SystemManagerDOD()
        events = []
        mngr.event_bus.subscribe('entity_created', lambda d: events.append(('created', d['entity'])))
        mngr.event_bus.subscribe('entity_destroyed', lambda d: events.append(('destroyed', d['entity'])))
        
        entity = Entity()
        entity.add_component(TransformComponent())
        mngr.add_entity(entity)
        mngr.remove_entity(entity)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0][0], 'created')
        self.assertEqual(events[1][0], 'destroyed')

    def test_system_with_events_publish_and_subscribe(self):
        mngr = SystemManagerDOD()
        received = []
        
        class PublisherSystem(SystemWithEvents):
            def __init__(self):
                super().__init__(required_components={TransformComponent})
            def on_bind(self):
                pass  # akan publish saat update
            def update(self, delta_time: float):
                self.publish_event('custom_event', {'dt': delta_time})
        
        pub_sys = PublisherSystem()
        mngr.add_system(pub_sys)
        pub_sys.bind_event_bus(mngr.event_bus)
        mngr.event_bus.subscribe('custom_event', lambda d: received.append(d['dt']))
        
        mngr.update(0.16)
        self.assertEqual(len(received), 1)
        self.assertAlmostEqual(received[0], 0.16)

class TestArchetypeStorage(unittest.TestCase):
    def setUp(self):
        self.storage = ArchetypeStorage(chunk_size=4)  # chunk kecil untuk pengujian
    
    def test_add_and_retrieve_entity(self):
        entity = Entity()
        entity.add_component(TransformComponent(1, 2, 3))
        self.storage.add_entity(entity)
        
        retrieved = self.storage.get_entity(entity.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get_component(TransformComponent).x, 1)
    
    def test_remove_entity(self):
        entity = Entity()
        entity.add_component(TransformComponent())
        self.storage.add_entity(entity)
        self.storage.remove_entity(entity)
        self.assertIsNone(self.storage.get_entity(entity.id))
    
    def test_entities_same_archetype_stored_together(self):
        e1 = Entity()
        e1.add_component(TransformComponent())
        e2 = Entity()
        e2.add_component(TransformComponent())
        self.storage.add_entity(e1)
        self.storage.add_entity(e2)
        
        entities = self.storage.get_entities_by_archetype({TransformComponent})
        self.assertIn(e1, entities)
        self.assertIn(e2, entities)
    
    def test_different_archetypes_separated(self):
        e1 = Entity()
        e1.add_component(TransformComponent())
        e2 = Entity()
        e2.add_component(TransformComponent())
        e2.add_component(MeshComponent())
        self.storage.add_entity(e1)
        self.storage.add_entity(e2)
        
        # e1 dan e2 memiliki archetype berbeda
        entities_transform_only = self.storage.get_entities_by_archetype({TransformComponent})
        entities_both = self.storage.get_entities_by_archetype({TransformComponent, MeshComponent})
        self.assertIn(e1, entities_transform_only)
        self.assertIn(e2, entities_both)
    
    def test_chunk_overflow(self):
        # chunk_size = 4, tambah 5 entity
        entities = []
        for i in range(5):
            e = Entity()
            e.add_component(TransformComponent(float(i), 0, 0))
            self.storage.add_entity(e)
            entities.append(e)
        
        # Semua harus dapat ditemukan
        for e in entities:
            self.assertIsNotNone(self.storage.get_entity(e.id))
    
    def test_get_all_entities_with_component(self):
        e1 = Entity()
        e1.add_component(TransformComponent())
        e2 = Entity()
        e2.add_component(TransformComponent())
        e2.add_component(MeshComponent())
        self.storage.add_entity(e1)
        self.storage.add_entity(e2)
        
        with_transform = self.storage.get_all_entities_with(TransformComponent)
        self.assertEqual(len(with_transform), 2)
        self.assertIn(e1, with_transform)
        self.assertIn(e2, with_transform)
    
    def test_count_entities(self):
        self.assertEqual(self.storage.count_entities(), 0)
        e = Entity()
        e.add_component(TransformComponent())
        self.storage.add_entity(e)
        self.assertEqual(self.storage.count_entities(), 1)
        self.assertEqual(self.storage.count_entities(TransformComponent), 1)
        self.assertEqual(self.storage.count_entities(MeshComponent), 0)
    
    def test_reuse_slots_after_removal(self):
        e1 = Entity()
        e1.add_component(TransformComponent())
        self.storage.add_entity(e1)
        self.storage.remove_entity(e1)
        
        e2 = Entity()
        e2.add_component(TransformComponent())
        self.storage.add_entity(e2)  # harusnya menggunakan slot bekas e1
        
        retrieved = self.storage.get_entity(e2.id)
        self.assertIsNotNone(retrieved)

if __name__ == '__main__':
    unittest.main()