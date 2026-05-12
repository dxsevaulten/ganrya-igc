import unittest
import json
import sys
import tempfile
import os
import logging
import time
from ganrya_igc.core.logging import (
    Logger, StructuredFormatter, FrameDebugger, DrawCall,
    Profiler, CrashReporter
)
from ganrya_igc.core.logging import Benchmark

class TestStructuredFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = StructuredFormatter()

    def test_format_basic_log(self):
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='test.py',
            lineno=42, msg='Hello World', args=(), exc_info=None
        )
        data = json.loads(self.formatter.format(record))
        self.assertEqual(data['level'], 'INFO')
        self.assertEqual(data['message'], 'Hello World')

    def test_format_with_exception(self):
        try:
            raise ValueError("Oops")
        except ValueError:
            record = logging.LogRecord(
                name='test', level=logging.ERROR, pathname='', lineno=0,
                msg='Error', args=(), exc_info=sys.exc_info()
            )
        data = json.loads(self.formatter.format(record))
        self.assertEqual(data['exception']['type'], 'ValueError')


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.logger = Logger()

    def test_singleton(self):
        self.assertIs(self.logger, Logger())

    def test_get_logger(self):
        log = self.logger.get_logger('test.log')
        self.assertEqual(log.name, 'test.log')

    def test_set_level(self):
        self.logger.set_level('ERROR')
        log = self.logger.get_logger('x')
        self.assertFalse(log.isEnabledFor(logging.INFO))
        self.logger.set_level('DEBUG')

    def test_file_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'out.log')
            self.logger.set_file_output(path)
            self.logger.get_logger('f').info('test')
            # tutup handler
            root = logging.getLogger()
            for h in root.handlers[:]:
                if isinstance(h, logging.FileHandler):
                    h.close()
                    root.removeHandler(h)
            self.assertTrue(os.path.exists(path))


class TestProfiler(unittest.TestCase):
    def setUp(self):
        self.p = Profiler()

    def test_basic(self):
        self.p.start('x')
        time.sleep(0.005)
        self.p.end('x')
        self.assertIn('x', self.p.get_stats())

    def test_reset(self):
        self.p.start('x')
        self.p.end('x')
        self.p.reset()
        self.assertEqual(len(self.p.get_stats()), 0)


class TestFrameDebugger(unittest.TestCase):
    def setUp(self):
        self.debugger = FrameDebugger(max_recorded_frames=5)

    def test_capture_and_retrieve(self):
        self.debugger.start_capture()
        self.debugger.begin_frame(1)
        self.debugger.record_draw_call("shader1", 100)
        self.debugger.end_frame()
        cap = self.debugger.get_capture(1)
        self.assertIsNotNone(cap)
        self.assertEqual(len(cap.draw_calls), 1)

    def test_clear(self):
        self.debugger.start_capture()
        self.debugger.begin_frame(1)
        self.debugger.record_draw_call("test", 5)
        self.debugger.end_frame()
        self.debugger.clear()
        self.assertEqual(self.debugger.get_frame_count(), 0)

    def test_export(self):
        self.debugger.start_capture()
        self.debugger.begin_frame(1)
        self.debugger.record_draw_call("test", 5)
        self.debugger.end_frame()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "export.json")
            self.debugger.export_to_file(path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                data = json.load(f)
            self.assertEqual(len(data['frames']), 1)


class TestCrashReporter(unittest.TestCase):
    def setUp(self):
        # Reset singleton agar test bersih
        CrashReporter.reset_instance()
        self.tmp = tempfile.mkdtemp()
        self.reporter = CrashReporter(output_dir=self.tmp)

    def tearDown(self):
        self.reporter.restore_hook()
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)
        CrashReporter.reset_instance()

    def test_generate_report(self):
        try:
            raise RuntimeError("Test crash")
        except RuntimeError:
            report = self.reporter.generate_report(*sys.exc_info())
        self.assertEqual(report['exception_type'], 'RuntimeError')
        self.assertIn('traceback', report)

    def test_save_and_read(self):
        try:
            raise ValueError("Save test")
        except ValueError:
            report = self.reporter.generate_report(*sys.exc_info())
        self.reporter.save_report(report)
        files = os.listdir(self.tmp)
        self.assertTrue(any(f.startswith('crash_') for f in files))

class TestBenchmark(unittest.TestCase):
    def test_record_and_summary(self):
        b = Benchmark("test")
        b.record_fps(60)
        b.record_fps(58)
        b.record_load_time(1.2)
        s = b.summary()
        self.assertAlmostEqual(s["fps"]["avg"], 59.0)
        self.assertEqual(s["load_time"]["count"], 1)

    def test_compare(self):
        old = Benchmark("old")
        old.record_fps(50)
        new = Benchmark("new")
        new.record_fps(55)
        delta = new.compare_to(old)
        self.assertIn("fps", delta)
        self.assertIn("+10.0%", delta["fps"])
