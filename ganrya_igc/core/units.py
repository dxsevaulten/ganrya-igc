# ganrya_igc/core/units.py
"""
Plan 1.9: Sistem Internasionalisasi & Aksesibilitas.
Subplan 1.9.5: Unit System Display & Conversion.
"""

from typing import Dict, Tuple


class UnitSystem:
    """Konversi dan format satuan ukuran."""

    # Konversi dari meter ke satuan lain
    _units: Dict[str, float] = {
        'm': 1.0,
        'cm': 100.0,
        'mm': 1000.0,
        'km': 0.001,
        'in': 39.37007874015748,       # 1 m = 39.3701 inci (lebih presisi)
        'ft': 3.2808398950131235,       # 1 m = 3.28084 kaki (lebih presisi)
        'yd': 1.0936132983377078,       # 1 m = 1.09361 yard
        'mi': 0.0006213711922373339,    # 1 m = 0.000621371 mil
    }

    _symbols: Dict[str, str] = {
        'm': 'm',
        'cm': 'cm',
        'mm': 'mm',
        'km': 'km',
        'in': 'in',
        'ft': 'ft',
        'yd': 'yd',
        'mi': 'mi',
    }

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Konversi nilai antar satuan."""
        if from_unit not in cls._units or to_unit not in cls._units:
            raise ValueError(f"Unit tidak dikenal: {from_unit} atau {to_unit}")
        meters = value / cls._units[from_unit]
        return meters * cls._units[to_unit]

    @classmethod
    def format(cls, value: float, unit: str = 'm', decimals: int = 2) -> str:
        """Format nilai dengan simbol satuan."""
        symbol = cls._symbols.get(unit, unit)
        if decimals >= 0:
            return f"{value:.{decimals}f} {symbol}"
        return f"{value} {symbol}"

    @classmethod
    def available_units(cls):
        """Kembalikan daftar satuan yang didukung."""
        return list(cls._units.keys())