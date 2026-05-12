# ganrya_igc/tests/test_concurrency.py
import unittest
import time
from ganrya_igc.core.concurrency import WorkerThread, WorkerPool
from ganrya_igc.core.concurrency import AsyncTask, AsyncTaskManager
from ganrya_igc.core.concurrency import (
    ThreadSafeList, ThreadSafeDict, RWLockDict, ConcurrentQueue
)
import queue as std_queue
from ganrya_igc.core.concurrency import DoubleBuffer, FrameSyncManager
from ganrya_igc.core.concurrency import TaskGraph

class TestWorkerThread(unittest.TestCase):
    def setUp(self):
        self.worker = WorkerThread()
        self.worker.start()

    def tearDown(self):
        self.worker.stop()

    def test_submit_and_get_result(self):
        tid = self.worker.submit(lambda x: x * 2, 21)
        result = self.worker.get_result(tid)
        self.assertEqual(result, 42)

    def test_multiple_tasks(self):
        t1 = self.worker.submit(lambda: "hello")
        t2 = self.worker.submit(lambda: "world")
        r1 = self.worker.get_result(t1)
        r2 = self.worker.get_result(t2)
        self.assertEqual(r1, "hello")
        self.assertEqual(r2, "world")

    def test_exception_propagates(self):
        def bad():
            raise ValueError("oops")
        tid = self.worker.submit(bad)
        with self.assertRaises(ValueError):
            self.worker.get_result(tid)


class TestWorkerPool(unittest.TestCase):
    def setUp(self):
        self.pool = WorkerPool(2)

    def tearDown(self):
        self.pool.shutdown()

    def test_submit_to_different_workers(self):
        t1 = self.pool.submit(0, lambda: "worker0")   # indeks 0
        t2 = self.pool.submit(1, lambda: "worker1")   # indeks 1
        r1 = self.pool.get_result(t1)
        r2 = self.pool.get_result(t2)
        self.assertEqual(r1, "worker0")
        self.assertEqual(r2, "worker1")

class TestAsyncTask(unittest.TestCase):
    def test_set_and_get_result(self):
        task = AsyncTask()
        task.set_result(42)
        self.assertTrue(task.done())
        self.assertEqual(task.result(), 42)

    def test_exception_propagates(self):
        task = AsyncTask()
        task.set_exception(ValueError("test"))
        with self.assertRaises(ValueError):
            task.result()

    def test_callback_called(self):
        results = []
        task = AsyncTask()
        task.add_done_callback(lambda t: results.append(t.result()))
        task.set_result(99)
        self.assertEqual(results, [99])


class TestAsyncTaskManager(unittest.TestCase):
    def setUp(self):
        self.mgr = AsyncTaskManager(2)

    def tearDown(self):
        self.mgr.shutdown()

    def test_submit_and_get_result(self):
        t = self.mgr.submit(lambda: "hello")
        self.assertEqual(t.result(timeout=5.0), "hello")

    def test_submit_multiple(self):
        t1 = self.mgr.submit(lambda: 1)
        t2 = self.mgr.submit(lambda: 2)
        self.assertEqual(t1.result(), 1)
        self.assertEqual(t2.result(), 2)

class TestThreadSafeDataStructures(unittest.TestCase):
    def test_thread_safe_list(self):
        ts_list = ThreadSafeList([1, 2, 3])
        ts_list.append(4)
        self.assertEqual(len(ts_list), 4)
        self.assertEqual(ts_list.get(3), 4)
        ts_list.remove(2)
        self.assertEqual(len(ts_list), 3)
        self.assertEqual(list(ts_list), [1, 3, 4])

    def test_thread_safe_dict(self):
        ts_dict = ThreadSafeDict()
        ts_dict.set('a', 1)
        ts_dict.set('b', 2)
        self.assertEqual(ts_dict.get('a'), 1)
        self.assertEqual(ts_dict.pop('b'), 2)
        self.assertIsNone(ts_dict.get('b'))

    def test_rwlock_dict(self):
        rw_dict = RWLockDict()
        rw_dict.set('x', 10)
        rw_dict.set('y', 20)
        self.assertEqual(rw_dict.get('x'), 10)
        self.assertEqual(rw_dict.get('y'), 20)
        self.assertIn('x', rw_dict.keys())

    def test_concurrent_queue(self):
        q = ConcurrentQueue()
        q.put('first')
        q.put('second')
        self.assertEqual(q.get(timeout=1.0), 'first')
        self.assertEqual(q.get(timeout=1.0), 'second')
        with self.assertRaises(std_queue.Empty):
            q.get(timeout=0.1)

    def test_concurrent_queue_drain(self):
        q = ConcurrentQueue()
        q.put(1)
        q.put(2)
        q.put(3)
        items = q.drain()
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(len(q), 0)

class TestDoubleBuffer(unittest.TestCase):
    def test_swap_exchanges_buffers(self):
        buf = DoubleBuffer(0)
        buf.next = 42
        self.assertEqual(buf.current, 0)  # belum ditukar
        buf.swap()
        self.assertEqual(buf.current, 42)  # sekarang menjadi 42

    def test_next_can_be_modified_in_place(self):
        buf = DoubleBuffer([1, 2, 3])
        next_list = buf.next
        next_list.append(4)
        buf.next = next_list
        buf.swap()
        self.assertEqual(buf.current, [1, 2, 3, 4])


class TestFrameSyncManager(unittest.TestCase):
    def test_swap_all(self):
        mgr = FrameSyncManager()
        a = mgr.create_buffer("a", "old_a")
        b = mgr.create_buffer("b", "old_b")
        a.next = "new_a"
        b.next = "new_b"
        mgr.swap_all()
        self.assertEqual(a.current, "new_a")
        self.assertEqual(b.current, "new_b")

class TestTaskGraph(unittest.TestCase):
    def setUp(self):
        self.pool = WorkerPool(4)
        self.graph = TaskGraph(self.pool)

    def tearDown(self):
        self.pool.shutdown()

    def test_simple_sequence(self):
        self.graph.add_task("a", lambda _: 1)
        self.graph.add_task("b", lambda _: 2, depends_on=["a"])
        self.graph.add_task("c", lambda res: res["a"] + res["b"], depends_on=["b"])
        results = self.graph.run()
        self.assertEqual(results["a"], 1)
        self.assertEqual(results["b"], 2)
        self.assertEqual(results["c"], 3)

    def test_parallel_branches(self):
        self.graph.add_task("root", lambda _: 0)
        self.graph.add_task("left", lambda _: 1, depends_on=["root"])
        self.graph.add_task("right", lambda _: 2, depends_on=["root"])
        self.graph.add_task("merge", lambda res: res["left"] + res["right"], depends_on=["left", "right"])
        results = self.graph.run()
        self.assertEqual(results["merge"], 3)

    def test_missing_dependency_raises(self):
        with self.assertRaises(ValueError):
            self.graph.add_task("bad", lambda _: 1, depends_on=["ghost"])