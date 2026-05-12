# ganrya_igc/tests/test_units.py
import unittest
from ganrya_igc.core.units import UnitSystem


class TestUnitSystem(unittest.TestCase):
    def test_convert_m_to_cm(self):
        result = UnitSystem.convert(1.0, 'm', 'cm')
        self.assertAlmostEqual(result, 100.0)

    def test_convert_ft_to_in(self):
        result = UnitSystem.convert(1.0, 'ft', 'in')
        self.assertAlmostEqual(result, 12.0)

    def test_convert_same_unit(self):
        result = UnitSystem.convert(5.0, 'm', 'm')
        self.assertAlmostEqual(result, 5.0)

    def test_invalid_unit_raises(self):
        with self.assertRaises(ValueError):
            UnitSystem.convert(1.0, 'lightyear', 'm')

    def test_format_with_decimals(self):
        self.assertEqual(UnitSystem.format(1.2345, 'm', 2), "1.23 m")

    def test_available_units(self):
        units = UnitSystem.available_units()
        self.assertIn('m', units)
        self.assertIn('ft', units)
        self.assertIn('mm', units)


if __name__ == "__main__":
    unittest.main()