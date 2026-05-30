# 🌌 Universal Digital Architect

**Arsitek Digital Universal** — Platform untuk menanamkan, mendekode, dan merekonstruksi aplikasi desktop dari berbagai era menjadi Aplikasi Replika yang hidup, modern, dan mandiri.

## 🚀 Visi

"Menjadi Arsitek Digital Universal—sebuah platform yang tidak hanya mampu menanamkan dan menjalankan aplikasi desktop apa pun dari berbagai era, tetapi juga mendekode, merekonstruksi, dan membangkitkan kembali fungsionalitasnya sebagai Aplikasi Replika yang hidup."

## 📋 Fitur Utama

### Fase 0: The Iron Foundation ✅
- **Core Engine**: Singleton pattern untuk state management
- **Window Manager**: Embedding jendela dengan Win32 API
- **Application Launcher**: Support .exe dan .lnk shortcut
- **Utilities**: Helper functions untuk icon extraction, path formatting, dll

### Fase 1: The Universal Host (Dalam Pengembangan)
- Multi-tab embedding system
- Dynamic window detection
- Input forwarding
- Loading overlay dengan animasi
- Accordion autocomplete search
- Real-time log panel

### Fase 2-4 (Coming Soon)
- Decoder Core (Misi 5)
- Replika Suite (Misi 6)
- Global Ecosystem (Misi 7)

## 🏗️ Struktur Proyek

```
universal-architect/
├── main.py              # Entry point
├── MASTER_PLAN.md       # Roadmap lengkap
├── requirements.txt     # Dependencies
├── core/                # Inti sistem
│   ├── engine.py        # Core Engine (singleton)
│   └── window_manager.py # Window embedding
├── modules/             # Modul fungsional
│   └── launcher.py      # App launcher
├── utils/               # Utilities
│   └── helpers.py       # Helper functions
└── tests/               # Testing suite
    ├── test_engine.py
    ├── test_window_manager.py
    ├── test_launcher.py
    └── test_helpers.py
```

## 🔧 Instalasi

### Prasyarat
- Python 3.8+
- Windows 10/11 (untuk fitur penuh Win32 API)
- Atau Linux/macOS (dengan mode mock untuk testing)

### Langkah Instalasi

```bash
# Clone atau download repository
cd universal-architect

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🧪 Testing

```bash
# Jalankan semua test
pytest

# Jalankan dengan coverage
pytest --cov=. --cov-report=html

# Jalankan test spesifik
pytest tests/test_engine.py -v
```

## 🎯 Cara Penggunaan (Contoh Dasar)

```python
from core import get_engine, WindowManager
from modules import get_launcher

# Inisialisasi engine
engine = get_engine()

# Launch aplikasi
launcher = get_launcher()
result = launcher.launch('C:/Path/To/App.exe')

if result.success:
    print(f"Aplikasi diluncurkan dengan PID: {result.pid}")
    
    # Register ke engine
    engine.register_process(result.pid, {
        'name': 'MyApp',
        'path': result.path
    })
    
    # Embed window (Windows only)
    wm = WindowManager()
    window_info = wm.find_window_by_pid(result.pid)
    
    if window_info:
        print(f"Jendela ditemukan: {window_info.title}")
        # wm.embed_window(window_info.hwnd, qt_widget)
```

## 📖 Dokumentasi Lengkap

Lihat [MASTER_PLAN.md](MASTER_PLAN.md) untuk roadmap detail dan arsitektur lengkap.

## 🤝 Kontribusi

Kami menyambut kontribusi! Silakan:
1. Fork repository
2. Buat branch fitur (`git checkout -b feature/amazing-feature`)
3. Commit perubahan (`git commit -m 'Add amazing feature'`)
4. Push ke branch (`git push origin feature/amazing-feature`)
5. Buat Pull Request

## 📄 Lisensi

Proyek ini dibuat dengan visi open-source untuk melestarikan dan membangkitkan kembali aplikasi-aplikasi bersejarah.

## 🌟 Pengakuan

Terima kasih kepada semua kontributor dan pendukung visi "Tidak ada aplikasi yang punah".

---

**Dibangun dengan ❤️ untuk masa depan perangkat lunak**
