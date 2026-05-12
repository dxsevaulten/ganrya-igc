# ganrya_igc/core/concurrency.py
"""
Plan 1.8: Manajemen Thread & Concurrency.
Subplan 1.8.1: Simple Worker Threads.
"""

import threading
import queue
import traceback
import time
from typing import Callable, Any, Optional, List, Dict


class WorkerThread(threading.Thread):
    """Thread sederhana yang menjalankan antrean tugas (FIFO)."""

    def __init__(self, name: str = "Worker"):
        super().__init__(daemon=True, name=name)
        self._queue: queue.Queue[Optional[Callable]] = queue.Queue()
        self._running = True
        self._results: Dict[int, Any] = {}
        self._result_lock = threading.Lock()
        self._task_counter = 0

    def run(self):
        while self._running:
            try:
                task = self._queue.get(timeout=0.5)
                if task is None:  # sinyal berhenti
                    break
                task_id, func, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    with self._result_lock:
                        self._results[task_id] = result
                except Exception as e:
                    with self._result_lock:
                        self._results[task_id] = e
            except queue.Empty:
                continue
            except Exception:
                traceback.print_exc()

    def submit(self, func: Callable, *args, **kwargs) -> int:
        """Kembalikan task_id untuk mengambil hasil nanti."""
        with self._result_lock:
            task_id = self._task_counter
            self._task_counter += 1
        self._queue.put((task_id, func, args, kwargs))
        return task_id

    def get_result(self, task_id: int, timeout: float = 10.0) -> Optional[Any]:
        """Ambil hasil tugas, blocking sampai tersedia atau timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._result_lock:
                if task_id in self._results:
                    result = self._results.pop(task_id)
                    if isinstance(result, Exception):
                        raise result
                    return result
            time.sleep(0.01)
        return None  # timeout

    def stop(self):
        self._running = False
        self._queue.put(None)
        self.join(timeout=2.0)


class WorkerPool:
    def __init__(self, num_workers: int = 4):
        self.workers = [WorkerThread(name=f"Worker-{i}") for i in range(num_workers)]
        for w in self.workers:
            w.start()

    def submit(self, worker_index: int, func: Callable, *args, **kwargs) -> int:
        """Kirim tugas ke pekerja tertentu (indeks 0-based)."""
        if worker_index < 0 or worker_index >= len(self.workers):
            raise IndexError(f"worker_index {worker_index} di luar rentang 0-{len(self.workers)-1}")
        return self.workers[worker_index].submit(func, *args, **kwargs)

    def get_result(self, task_id: int, timeout: float = 10.0) -> Optional[Any]:
        """Ambil hasil dari pekerja mana pun yang memilikinya."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            for w in self.workers:
                res = w.get_result(task_id, timeout=0.1)  # beri waktu sedikit
                if res is not None:
                    return res
            time.sleep(0.01)
        return None

    def shutdown(self):
        for w in self.workers:
            w.stop()

# ========== SUBPLAN 1.8.2: ASYNCHRONOUS TASK MANAGER ==========
from typing import List, Callable, Any, Optional, Dict
import threading

class AsyncTask:
    """Representasi tugas asinkron yang akan menghasilkan nilai di masa depan."""

    def __init__(self):
        self._done = False
        self._result = None
        self._exception = None
        self._lock = threading.Lock()
        self._callbacks: List[Callable[['AsyncTask'], None]] = []

    def set_result(self, value: Any):
        with self._lock:
            self._result = value
            self._done = True
        self._fire_callbacks()

    def set_exception(self, exc: Exception):
        with self._lock:
            self._exception = exc
            self._done = True
        self._fire_callbacks()

    def result(self, timeout: float = None) -> Any:
        """Ambil hasil, blocking jika belum selesai."""
        deadline = time.time() + timeout if timeout else float('inf')
        while time.time() < deadline:
            with self._lock:
                if self._done:
                    if self._exception:
                        raise self._exception
                    return self._result
            time.sleep(0.01)
        raise TimeoutError("AsyncTask timeout")

    def done(self) -> bool:
        with self._lock:
            return self._done

    def add_done_callback(self, fn: Callable[['AsyncTask'], None]):
        with self._lock:
            if self._done:
                fn(self)
            else:
                self._callbacks.append(fn)

    def _fire_callbacks(self):
        for fn in self._callbacks:
            try:
                fn(self)
            except Exception:
                pass


class AsyncTaskManager:
    """Mengelola WorkerPool dan menyediakan antarmuka submit asinkron (AsyncTask)."""

    def __init__(self, num_workers: int = 4):
        self._pool = WorkerPool(num_workers)

    def submit(self, func: Callable, *args, **kwargs) -> AsyncTask:
        """Kirim tugas, kembalikan AsyncTask."""
        task = AsyncTask()

        def wrapped():
            try:
                result = func(*args, **kwargs)
                task.set_result(result)
            except Exception as e:
                task.set_exception(e)

        # Sebarkan tugas ke worker dengan round-robin sederhana
        worker_idx = hash(task) % len(self._pool.workers)
        self._pool.submit(worker_idx, wrapped)
        return task

    def shutdown(self):
        self._pool.shutdown()

# ========== SUBPLAN 1.8.3: THREAD-SAFE DATA STRUCTURES ==========
import threading
from typing import List, Dict, Any, Optional, Iterator

class ThreadSafeList:
    """List sederhana yang aman untuk akses multi‑thread."""

    def __init__(self, initial: Optional[List[Any]] = None):
        self._list = initial[:] if initial else []
        self._lock = threading.Lock()

    def append(self, item):
        with self._lock:
            self._list.append(item)

    def get(self, index: int):
        with self._lock:
            if 0 <= index < len(self._list):
                return self._list[index]
            raise IndexError("list index out of range")

    def remove(self, item):
        with self._lock:
            self._list.remove(item)

    def __len__(self) -> int:
        with self._lock:
            return len(self._list)

    def __iter__(self) -> Iterator:
        with self._lock:
            return iter(list(self._list))

    def copy(self) -> List[Any]:
        with self._lock:
            return self._list[:]


class ThreadSafeDict:
    """Dictionary yang aman untuk akses multi‑thread."""

    def __init__(self):
        self._dict: Dict[Any, Any] = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            self._dict[key] = value

    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)

    def pop(self, key, default=None):
        with self._lock:
            return self._dict.pop(key, default)

    def keys(self) -> List[Any]:
        with self._lock:
            return list(self._dict.keys())

    def __len__(self) -> int:
        with self._lock:
            return len(self._dict)


class RWLock:
    """Read‑Write Lock sederhana."""
    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._lock = threading.Lock()
        self._read_cond = threading.Condition(self._lock)
        self._write_cond = threading.Condition(self._lock)

    def acquire_read(self):
        with self._lock:
            while self._writers > 0:
                self._read_cond.wait()
            self._readers += 1

    def release_read(self):
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_cond.notify()

    def acquire_write(self):
        with self._lock:
            while self._readers > 0 or self._writers > 0:
                self._write_cond.wait()
            self._writers = 1

    def release_write(self):
        with self._lock:
            self._writers = 0
            self._read_cond.notify_all()
            self._write_cond.notify()


class RWLockDict:
    """Dictionary yang menggunakan Read‑Write Lock untuk performa lebih baik."""

    def __init__(self):
        self._dict: Dict[Any, Any] = {}
        self._rwlock = RWLock()

    def get(self, key, default=None):
        self._rwlock.acquire_read()
        try:
            return self._dict.get(key, default)
        finally:
            self._rwlock.release_read()

    def set(self, key, value):
        self._rwlock.acquire_write()
        try:
            self._dict[key] = value
        finally:
            self._rwlock.release_write()

    def pop(self, key, default=None):
        self._rwlock.acquire_write()
        try:
            return self._dict.pop(key, default)
        finally:
            self._rwlock.release_write()

    def keys(self) -> List[Any]:
        self._rwlock.acquire_read()
        try:
            return list(self._dict.keys())
        finally:
            self._rwlock.release_read()


class ConcurrentQueue:
    """Antrean aman‑thread sederhana (FIFO)."""

    def __init__(self):
        self._queue: List[Any] = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def put(self, item):
        with self._cond:
            self._queue.append(item)
            self._cond.notify()

    def get(self, timeout: float = None) -> Any:
        deadline = time.time() + timeout if timeout else float('inf')
        with self._cond:
            while not self._queue:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise queue.Empty()
                self._cond.wait(timeout=remaining)
            return self._queue.pop(0)

    def drain(self) -> List[Any]:
        """Kembalikan semua item dan kosongkan antrean."""
        with self._cond:
            items = self._queue[:]
            self._queue.clear()
            return items

    def __len__(self):
        with self._cond:
            return len(self._queue)
        
# ========== SUBPLAN 1.8.4: FRAME SYNCHRONIZATION ==========
import copy

class DoubleBuffer:
    """Buffer ganda untuk memisahkan baca dan tulis antar frame."""

    def __init__(self, initial_value: Any = None):
        self._current = initial_value
        self._next = copy.deepcopy(initial_value) if initial_value is not None else None
        self._lock = threading.Lock()

    @property
    def current(self) -> Any:
        """Baca data terkini (untuk thread render)."""
        with self._lock:
            return self._current

    @property
    def next(self) -> Any:
        """Akses buffer berikutnya (untuk diisi oleh thread lain)."""
        with self._lock:
            return self._next

    @next.setter
    def next(self, value: Any):
        with self._lock:
            self._next = value

    def swap(self):
        """Tukar buffer, memindahkan 'next' menjadi 'current' (panggil di awal frame)."""
        with self._lock:
            self._current, self._next = self._next, self._current


class FrameSyncManager:
    """Mengelola banyak DoubleBuffer dan menukarnya sekaligus."""

    def __init__(self):
        self._buffers: Dict[str, DoubleBuffer] = {}
        self._lock = threading.Lock()

    def create_buffer(self, name: str, initial_value: Any = None) -> DoubleBuffer:
        with self._lock:
            buf = DoubleBuffer(initial_value)
            self._buffers[name] = buf
            return buf

    def get_buffer(self, name: str) -> DoubleBuffer:
        with self._lock:
            return self._buffers[name]

    def swap_all(self):
        """Tukar semua buffer (panggil di awal frame)."""
        with self._lock:
            for buf in self._buffers.values():
                buf.swap()

# ========== SUBPLAN 1.8.5: TASK DEPENDENCY GRAPH ==========
from typing import Dict, Set, List, Tuple, Optional
from collections import deque

class TaskGraph:
    """Graf tugas berarah (DAG) yang dapat dijalankan paralel."""

    def __init__(self, worker_pool: WorkerPool):
        self._pool = worker_pool
        self._tasks: Dict[str, Callable] = {}          # nama -> fungsi
        self._deps: Dict[str, Set[str]] = {}           # nama -> dependensi
        self._results: Dict[str, Any] = {}

    def add_task(self, name: str, func: Callable, depends_on: List[str] = None):
        depends_on = depends_on or []
        for dep in depends_on:
            if dep not in self._tasks:
                raise ValueError(f"Dependensi '{dep}' tidak dikenal untuk tugas '{name}'")
        self._tasks[name] = func
        self._deps[name] = set(depends_on)

    def run(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Jalankan semua tugas sesuai urutan dependensi. Kembalikan hasil."""
        remaining = set(self._tasks.keys())
        in_progress: Dict[str, int] = {}  # nama -> task_id
        ready = deque()

        deadline = time.time() + timeout

        while remaining or in_progress:
            # Cari tugas yang semua dependensinya sudah selesai
            for name in list(remaining):
                if self._deps[name].issubset(self._results.keys()):
                    ready.append(name)
                    remaining.remove(name)

            # Kirim tugas yang siap ke worker pool
            while ready and len(in_progress) < len(self._pool.workers):
                name = ready.popleft()
                func = self._tasks[name]
                # Tangkap hasil dengan closure
                def make_runner(task_name, task_func):
                    def runner():
                        return task_func(self._results)
                    return runner
                try:
                    tid = self._pool.submit(len(in_progress), make_runner(name, func))
                    in_progress[name] = tid
                except Exception:
                    # fallback: jalankan sinkron
                    self._results[name] = func(self._results)
                    ready.appendleft(name)

            # Periksa tugas yang sudah selesai
            done = []
            for name, tid in list(in_progress.items()):
                res = self._pool.get_result(tid, timeout=0.1)
                if res is not None:
                    self._results[name] = res
                    done.append(name)
            for name in done:
                del in_progress[name]

            if time.time() > deadline:
                raise TimeoutError(f"TaskGraph timeout. Sisa: {remaining}, Proses: {list(in_progress.keys())}")
            time.sleep(0.01)

        return self._results