# ganrya_igc/tests/test_visual.py
"""
Subplan 1.10.3: Visual Regression Testing.
Kerangka kerja untuk membandingkan gambar referensi (golden images).
"""

import unittest
import numpy as np
import tempfile
import os
from PIL import Image


class VisualRegressionTest:
    """Membantu pengujian regresi visual dengan membandingkan gambar."""

    def __init__(self, baseline_dir: str = "baselines", threshold: float = 0.01):
        self.baseline_dir = baseline_dir
        self.threshold = threshold  # persentase piksel yang boleh berbeda

    def _image_to_array(self, img: Image.Image) -> np.ndarray:
        return np.array(img.convert("RGB"), dtype=np.float32)

    def _save_baseline(self, name: str, img: Image.Image):
        os.makedirs(self.baseline_dir, exist_ok=True)
        img.save(os.path.join(self.baseline_dir, f"{name}.png"))

    def _load_baseline(self, name: str) -> Image.Image:
        path = os.path.join(self.baseline_dir, f"{name}.png")
        if not os.path.exists(path):
            return None
        return Image.open(path)

    def assert_images_equal(self, name: str, current: Image.Image,
                            update_baseline: bool = False):
        """Bandingkan gambar saat ini dengan baseline. Jika tidak ada, simpan sebagai baseline."""
        baseline = self._load_baseline(name)
        if baseline is None or update_baseline:
            self._save_baseline(name, current)
            return

        current_arr = self._image_to_array(current)
        baseline_arr = self._image_to_array(baseline)

        if current_arr.shape != baseline_arr.shape:
            raise AssertionError(
                f"Ukuran gambar berbeda: {current_arr.shape} vs {baseline_arr.shape}"
            )

        diff = np.abs(current_arr - baseline_arr)
        diff_pixels = np.sum(diff > 10) / diff.size  # toleransi 10 per kanal
        if diff_pixels > self.threshold:
            raise AssertionError(
                f"Gambar berbeda {diff_pixels:.2%} (threshold {self.threshold:.2%})"
            )


class TestVisualRegression(unittest.TestCase):
    """Pengujian logika perbandingan visual dengan array mock."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.vr = VisualRegressionTest(baseline_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_image(self, color=(255, 0, 0), size=(100, 100)) -> Image.Image:
        return Image.new("RGB", size, color)

    def test_identical_images_pass(self):
        img = self._make_image((0, 255, 0))
        self.vr.assert_images_equal("test_green", img)  # simpan baseline
        self.vr.assert_images_equal("test_green", img)  # harus lulus

    def test_different_images_fail(self):
        baseline = self._make_image((0, 0, 255))
        self.vr.assert_images_equal("test_blue", baseline)
        different = self._make_image((255, 0, 0))
        with self.assertRaises(AssertionError):
            self.vr.assert_images_equal("test_blue", different)

    def test_size_mismatch_fails(self):
        self.vr.assert_images_equal("size", self._make_image(size=(50, 50)))
        with self.assertRaises(AssertionError):
            self.vr.assert_images_equal("size", self._make_image(size=(100, 100)))


if __name__ == "__main__":
    unittest.main()