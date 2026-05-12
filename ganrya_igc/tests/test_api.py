# ganrya_igc/tests/test_api.py
import unittest
from ganrya_igc.api.core_api import CoreAPI_v1
from ganrya_igc.api.rendering_api import RenderingAPI_v1
from ganrya_igc.api.input_api import InputAPI_v1
from ganrya_igc.api.ui_api import UIAPI_v1
from ganrya_igc.api.utility_api import UtilityAPI_v1


class MockCoreAPI(CoreAPI_v1):
    """Implementasi mock untuk pengujian."""
    def __init__(self):
        self.nodes = []
        self.entities = []
        self.events = {}
    
    def get_root_node(self): return None
    def create_node(self, name, parent=None):
        node = {'name': name, 'parent': parent}
        self.nodes.append(node)
        return node
    def remove_node(self, node): self.nodes.remove(node)
    def get_node_by_name(self, name):
        for n in self.nodes:
            if n['name'] == name:
                return n
        return None
    def create_entity(self):
        e = {'id': len(self.entities)}
        self.entities.append(e)
        return e
    def add_component(self, entity, component): entity['comp'] = component
    def get_component(self, entity, component_type): return entity.get('comp')
    def remove_entity(self, entity): self.entities.remove(entity)
    def subscribe(self, event_type, handler):
        self.events.setdefault(event_type, []).append(handler)
    def unsubscribe(self, event_type, handler):
        if event_type in self.events:
            self.events[event_type].remove(handler)
    def publish(self, event_type, data=None):
        for h in self.events.get(event_type, []):
            h(data)
    def get_delta_time(self): return 0.016
    def get_frame_count(self): return 42


class TestCoreAPI(unittest.TestCase):
    def setUp(self):
        self.api = MockCoreAPI()
    
    def test_create_and_get_node(self):
        node = self.api.create_node("TestNode")
        self.assertIsNotNone(node)
        found = self.api.get_node_by_name("TestNode")
        self.assertEqual(found, node)
    
    def test_entity_lifecycle(self):
        entity = self.api.create_entity()
        self.api.add_component(entity, "transform")
        self.assertEqual(self.api.get_component(entity, str), "transform")
        self.api.remove_entity(entity)
        self.assertNotIn(entity, self.api.entities)
    
    def test_event_subscribe_publish(self):
        received = []
        self.api.subscribe('test', lambda d: received.append(d))
        self.api.publish('test', {'value': 99})
        self.assertEqual(received[0]['value'], 99)
    
    def test_get_delta_time(self):
        self.assertAlmostEqual(self.api.get_delta_time(), 0.016)
    
    def test_all_apis_have_version(self):
        """Pastikan setiap API mendeklarasikan versi."""
        self.assertTrue(hasattr(CoreAPI_v1, 'api_version'))
        self.assertTrue(hasattr(RenderingAPI_v1, 'api_version'))
        self.assertTrue(hasattr(InputAPI_v1, 'api_version'))
        self.assertTrue(hasattr(UIAPI_v1, 'api_version'))
        self.assertTrue(hasattr(UtilityAPI_v1, 'api_version'))


class MockRenderingAPI(RenderingAPI_v1):
    """Mock untuk pengujian RenderingAPI."""
    def __init__(self):
        self.clear_color = (0, 0, 0, 1)
        self.materials = []
    
    def set_clear_color(self, r, g, b, a=1.0): self.clear_color = (r, g, b, a)
    def create_material(self, name, color):
        mat = {'name': name, 'color': color}
        self.materials.append(mat)
        return mat
    def apply_material(self, node, material): node['material'] = material
    def set_ambient_light(self, color, intensity=1.0): pass
    def create_directional_light(self, direction, color, intensity=1.0): return {}
    def toggle_wireframe(self, enabled): pass
    def take_screenshot(self, filepath): return True


class TestRenderingAPI(unittest.TestCase):
    def test_set_clear_color(self):
        api = MockRenderingAPI()
        api.set_clear_color(0.5, 0.2, 0.8)
        self.assertEqual(api.clear_color, (0.5, 0.2, 0.8, 1.0))


if __name__ == '__main__':
    unittest.main()