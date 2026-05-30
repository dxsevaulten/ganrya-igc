# Universal Host

**Menjadi Arsitek Digital Universal** — Platform untuk menanamkan, mendekode, dan mereplikasi aplikasi desktop dari berbagai era.

## 🌌 Visi

"Membangun jembatan antara masa lalu, masa kini, dan masa depan perangkat lunak, menciptakan ekosistem di mana tidak ada aplikasi yang benar-benar punah."

## ✨ Fitur Utama

### Fase 0-1: Universal Host (✅ Complete)
- **Universal Launcher**: Jalankan aplikasi .exe, .lnk dari berbagai era
- **Window Embedding**: Tanamkan jendela aplikasi ke dalam tab modern
- **Multi-Tab Management**: Kelola banyak aplikasi dalam satu workspace
- **Auto-Detect Child Processes**: Deteksi Enscape, V-Ray, dll.
- **Glassmorphism UI**: Loading overlay dengan animasi modern
- **Real-Time Logging**: Monitor semua aktivitas (F2 toggle)
- **Smart Search**: Accordion autocomplete dengan ikon asli

### Fase 2+: Decoding & Replika (Coming Soon)
- **Interaction Recording**: Rekam aksi dan konversi ke kode Python
- **Visual Logic Editor**: Edit logika aplikasi replika
- **One-Click Deploy**: Build installer mandiri (.exe)
- **Plugin Framework**: Ekstensi universal untuk semua aplikasi

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Windows 10/11 (recommended untuk full features)

### Installation

```bash
# Clone atau navigate ke direktori proyek
cd universal-host

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run main application
python main.py
```

## 📁 Struktur Proyek

```
universal-host/
├── main.py                 # Entry point
├── MASTER_PLAN.md          # Roadmap lengkap
├── README.md               # Dokumentasi ini
├── requirements.txt        # Dependencies
├── core/
│   ├── engine.py           # Core Engine (singleton)
│   └── window_manager.py   # Win32 API embedding
├── modules/
│   ├── launcher.py         # Application launcher
│   ├── embedder.py         # Embedding manager
│   └── tab_manager.py      # Multi-tab system
├── ui/
│   ├── main_window.py      # Main window integrator
│   └── components/
│       ├── loading_overlay.py
│       ├── accordion_search.py
│       └── log_panel.py
├── utils/
│   └── helpers.py          # Utility functions
└── tests/                  # Test suite
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=.
```

## 🎯 Target Pengguna

1. **Arsitek & Desainer 3D**: Integrasikan SketchUp, Blender, AutoCAD dalam satu viewport
2. **Developer**: Selamatkan software jadul, integrasikan ke pipeline modern
3. **Gamers**: Jalankan game lama di Windows 11 tanpa masalah kompatibilitas
4. **IT Professionals**: Kelola banyak aplikasi secara terpusat
5. **Edukator**: Ajarkan sejarah software, laboratorium rekayasa balik

## 🛠️ Teknologi

- **GUI**: PyQt6
- **Windows API**: pywin32
- **Process Management**: psutil
- **Image Processing**: Pillow
- **Testing**: pytest

## 📊 Status Pengembangan

| Fase | Status | Deskripsi |
|------|--------|-----------|
| Fase 0 | ✅ Complete | Iron Foundation - Core engine & utilities |
| Fase 1 | ✅ Complete | Universal Host - UI & embedding system |
| Fase 2 | 🔄 Pending | Decoder Core - Interaction recording |
| Fase 3 | ⏳ Future | Replika Suite - Visual editor & deploy |
| Fase 4 | ⏳ Future | Global Ecosystem - i18n & marketplace |

## 🤝 Kontribusi

Kami menyambut kontribusi! Silakan baca MASTER_PLAN.md untuk roadmap lengkap.

## 📄 Lisensi

[TODO: Tentukan lisensi]

---

**Universal Host** - Tidak ada aplikasi yang punah.
