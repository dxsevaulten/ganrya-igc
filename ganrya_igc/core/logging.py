# ganrya_igc/core/logging.py
import logging
import json
import sys
import time
import threading
import os
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

# ---------- Structured Logging (1.7.1) ----------
class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': threading.current_thread().name,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry['exception'] = {
                'type': type(record.exc_info[1]).__name__,
                'message': str(record.exc_info[1]),
            }
        if hasattr(record, 'extra_data'):
            log_entry['extra'] = record.extra_data
        return json.dumps(log_entry, default=str)

class Logger:
    _instance: Optional['Logger'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_root_logger()

    def _setup_root_logger(self):
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(StructuredFormatter())
        root.handlers.clear()
        root.addHandler(console)

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def set_level(self, level: str):
        logging.getLogger().setLevel(getattr(logging, level.upper()))

    def set_file_output(self, filepath: str, level: str = 'DEBUG'):
        fh = logging.FileHandler(filepath)
        fh.setLevel(getattr(logging, level.upper()))
        fh.setFormatter(StructuredFormatter())
        logging.getLogger().addHandler(fh)

# ---------- Profiler (1.7.2) ----------
class Profiler:
    def __init__(self):
        self._timings: Dict[str, List[float]] = {}
        self._start_times: Dict[str, float] = {}
        self._memory_start: Optional[Any] = None

    def start(self, name: str):
        self._start_times[name] = time.perf_counter()

    def end(self, name: str):
        if name in self._start_times:
            elapsed = time.perf_counter() - self._start_times.pop(name)
            self._timings.setdefault(name, []).append(elapsed)

    def start_memory(self):
        import tracemalloc
        tracemalloc.start()
        self._memory_start = tracemalloc.take_snapshot()

    def end_memory(self) -> float:
        import tracemalloc
        if self._memory_start is None:
            return 0.0
        current = tracemalloc.take_snapshot()
        stats = current.compare_to(self._memory_start, 'lineno')
        total = sum(s.size_diff for s in stats)
        return total / (1024 * 1024)

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        return {
            name: {
                'avg': sum(times)/len(times),
                'min': min(times),
                'max': max(times),
                'count': len(times)
            }
            for name, times in self._timings.items() if times
        }

    def reset(self):
        self._timings.clear()
        self._start_times.clear()

# ---------- Frame Debugger (1.7.3) ----------
@dataclass
class DrawCall:
    shader_name: str
    vertex_count: int
    texture_name: str = ""
    draw_time_us: float = 0.0

class FrameCapture:
    def __init__(self, frame_number: int):
        self.frame_number = frame_number
        self.draw_calls: List[DrawCall] = []
        self.state_changes: List[str] = []
        self.timestamp: float = time.time()

    @property
    def frame_id(self) -> int:
        return self.frame_number

    @property
    def total_draws(self) -> int:
        return len(self.draw_calls)

    def add_draw_call(self, dc: DrawCall):
        self.draw_calls.append(dc)

    def to_dict(self) -> dict:
        return {
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'draw_calls': [{'shader': dc.shader_name, 'vertices': dc.vertex_count} for dc in self.draw_calls],
            'total_draw_calls': len(self.draw_calls),
            'state_changes': self.state_changes,
        }

class FrameDebugger:
    def __init__(self, max_recorded_frames: int = 100):
        self._max_frames = max(1, max_recorded_frames)  # minimal 1
        self._captures: Dict[int, FrameCapture] = {}
        self._current_capture: Optional[FrameCapture] = None
        self._current_frame_id = 0
        self._lock = threading.RLock()

    def start_capture(self):
        """Mulai merekam frame baru (alias untuk start_frame)."""
        self.start_frame()

    def start_frame(self):
        """Mulai merekam frame baru (internal)."""
        with self._lock:
            self._current_frame_id += 1
            self._current_capture = FrameCapture(self._current_frame_id)

    def begin_frame(self, frame_number: int):
        """Wrapper untuk pengujian: mulai frame dengan nomor tertentu."""
        with self._lock:
            self._current_frame_id = frame_number - 1
        self.start_frame()

    def record_draw_call(self, shader_name: str, vertex_count: int, texture_name: str = ""):
        """Catat satu draw call ke frame yang sedang direkam."""
        with self._lock:
            if self._current_capture is not None:
                dc = DrawCall(shader_name, vertex_count, texture_name)
                self._current_capture.add_draw_call(dc)

    def end_frame(self):
        """Selesaikan perekaman frame saat ini."""
        with self._lock:
            if self._current_capture is not None:
                self._captures[self._current_capture.frame_number] = self._current_capture
                self._current_capture = None
                # Hapus frame tertua hanya jika melebihi batas (ganti while dengan if)
                if len(self._captures) > self._max_frames:
                    oldest = min(self._captures.keys())
                    del self._captures[oldest]

    def get_capture(self, frame_number: int) -> Optional[FrameCapture]:
        """Ambil rekaman frame tertentu berdasarkan nomor frame."""
        with self._lock:
            return self._captures.get(frame_number)

    def get_all_captures(self) -> Dict[int, FrameCapture]:
        """Kembalikan seluruh rekaman frame."""
        with self._lock:
            return dict(self._captures)

    def get_frame_summary(self, frame_number: int) -> Optional[dict]:
        """Kembalikan ringkasan frame tertentu."""
        with self._lock:
            capture = self._captures.get(frame_number)
            return capture.to_dict() if capture else None

    def get_statistics(self) -> dict:
        """Kembalikan statistik semua frame yang direkam."""
        with self._lock:
            captures = list(self._captures.values())
            if not captures:
                return {'total_frames': 0, 'total_draw_calls': 0, 'avg_draw_calls': 0}
            total_frames = len(captures)
            total_draws = sum(c.total_draws for c in captures)
            avg = total_draws / total_frames if total_frames > 0 else 0
            return {
                'total_frames': total_frames,
                'total_draw_calls': total_draws,
                'avg_draw_calls': avg,
            }

    def export_to_file(self, filepath: str):
        """Ekspor semua rekaman frame ke file JSON."""
        with self._lock:
            data = {
                'frames': [c.to_dict() for c in self._captures.values()],
                'statistics': self.get_statistics(),
            }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def clear(self):
        """Hapus semua rekaman."""
        with self._lock:
            self._captures.clear()
            self._current_capture = None
            self._current_frame_id = 0

    def get_frame_count(self) -> int:
        """Kembalikan jumlah frame yang direkam."""
        with self._lock:
            return len(self._captures)


# ========== SUBPLAN 1.7.4: CRASH REPORTER & STACK TRACE ==========
import traceback
import os
import platform
from datetime import datetime

class CrashReporter:
    """Menangkap exception tak tertangani dan menyimpan laporan crash."""

    _instance = None

    def __new__(cls, output_dir=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, output_dir=None):
        if self._initialized:
            return
        self._initialized = True
        self.output_dir = output_dir or os.path.join(os.path.expanduser("~"), ".ganrya", "crashes")
        os.makedirs(self.output_dir, exist_ok=True)
        self._original_hook = sys.excepthook
        sys.excepthook = self._handler

    def _handler(self, exc_type, exc_value, exc_tb):
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        report = self.generate_report(exc_type, exc_value, exc_tb)
        self.save_report(report)
        self._original_hook(exc_type, exc_value, exc_tb)

    def generate_report(self, exc_type, exc_value, exc_tb):
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        return {
            'timestamp': datetime.now().isoformat(),
            'exception_type': exc_type.__name__,
            'exception_message': str(exc_value),
            'traceback': ''.join(tb_lines),
            'platform': platform.platform(),
            'python_version': sys.version,
        }

    def save_report(self, report):
        filename = f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{abs(hash(report['traceback']))}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    def restore_hook(self):
        sys.excepthook = self._original_hook

# Reset singleton untuk testing (opsional, dapat dipanggil di tearDown)
    @classmethod
    def reset_instance(cls):
        if cls._instance:
            cls._instance.restore_hook()
        cls._instance = None

# ========== SUBPLAN 1.7.5: PERFORMANCE BENCHMARK SUITE ==========
import json
import statistics

class Benchmark:
    """Mengukur performa scene standar dan membandingkan dengan baseline."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.results: Dict[str, List[float]] = {"fps": [], "load_time": [], "memory_mb": []}

    def record_fps(self, fps: float):
        self.results["fps"].append(fps)

    def record_load_time(self, seconds: float):
        self.results["load_time"].append(seconds)

    def record_memory(self, mb: float):
        self.results["memory_mb"].append(mb)

    def summary(self) -> Dict[str, Dict[str, float]]:
        s = {}
        for k, v in self.results.items():
            if v:
                s[k] = {
                    "avg": statistics.mean(v),
                    "min": min(v),
                    "max": max(v),
                    "count": len(v)
                }
        return s

    def compare_to(self, baseline: "Benchmark") -> Dict[str, str]:
        delta = {}
        for k in self.results:
            if k in baseline.results and baseline.results[k]:
                current_avg = statistics.mean(self.results[k])
                baseline_avg = statistics.mean(baseline.results[k])
                diff = ((current_avg - baseline_avg) / baseline_avg) * 100
                delta[k] = f"{diff:+.1f}%"
        return delta

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)