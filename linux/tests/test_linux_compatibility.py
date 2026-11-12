import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[1] / "glance_linux.py"


def load_nodes(names, namespace):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if getattr(node, "name", None) in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


class LinuxCompatibilityTests(unittest.TestCase):
    def test_open_camera_skips_metadata_nodes_and_probes_next_device(self):
        class CameraError(Exception):
            pass

        metadata_node = Mock()
        metadata_node.isOpened.return_value = True
        metadata_node.read.return_value = (False, None)

        working_cam = Mock()
        working_cam.isOpened.return_value = True
        working_cam.read.return_value = (True, object())

        cv2 = SimpleNamespace(
            CAP_V4L2=200,
            CAP_ANY=0,
            error=CameraError,
            VideoCapture=Mock(side_effect=[metadata_node, CameraError(), working_cam]),
        )
        open_camera = load_nodes({"open_camera"}, {"cv2": cv2})["open_camera"]
        result = open_camera(0, probe_indices=(0, 1))
        self.assertIs(result, working_cam)
        metadata_node.release.assert_called_once()

    def test_requirements_excludes_opencv_5_and_model_exists(self):
        reqs = (SOURCE.parent / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("<5", reqs)
        self.assertTrue((SOURCE.parent / "models" / "haarcascade_frontalface_default.xml").exists())

    @unittest.skipUnless(importlib.util.find_spec("cv2"), "OpenCV is not installed")
    def test_bundled_model_loads_from_memory(self):
        import os
        import cv2
        import numpy as np

        ns = {"os": os, "sys": SimpleNamespace(), "cv2": cv2, "__file__": str(SOURCE)}
        detector = load_nodes({"load_face_detector"}, ns)["load_face_detector"]()
        self.assertFalse(detector.empty())
        self.assertEqual(len(detector.detectMultiScale(np.zeros((64, 64), dtype=np.uint8))), 0)

    def test_overlay_stays_hidden_when_inactive(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        overlay_cls = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "GlanceOverlay"
        )
        init_src = ast.unparse(
            next(n for n in overlay_cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        )
        paint_src = ast.unparse(
            next(n for n in overlay_cls.body if isinstance(n, ast.FunctionDef) and n.name == "paintEvent")
        )
        self.assertIn("self.hide()", init_src)
        self.assertNotIn("self.show()", init_src)
        self.assertIn("WindowDoesNotAcceptFocus", init_src)
        self.assertIn("w - start_x", paint_src)

    def test_dark_frame_clears_protection_and_panel_is_not_qdialog(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertIn("class FallbackControlPanel(QWidget)", src)
        tree = ast.parse(src)
        ctrl_cls = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "GlanceLinuxController"
        )
        worker_src = ast.unparse(
            next(n for n in ctrl_cls.body if isinstance(n, ast.FunctionDef) and n.name == "camera_worker")
        )
        self.assertIn('update_protection.emit(\'none\', 0.0)', worker_src)
        self.assertIn("camera_ready.emit()", worker_src)


if __name__ == "__main__":
    unittest.main()
