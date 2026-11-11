import ast
import importlib.util
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[1] / "glance_windows.py"


def load_nodes(names, namespace):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if getattr(node, "name", None) in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace


class CameraCompatibilityTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("cv2"), "OpenCV is not installed")
    def test_bundled_model_loads_and_processes_an_image(self):
        import os
        import cv2
        import numpy as np

        ns = {"os": os, "sys": SimpleNamespace(), "cv2": cv2, "__file__": str(SOURCE)}
        detector = load_nodes({"load_face_detector"}, ns)["load_face_detector"]()
        self.assertFalse(detector.empty())
        self.assertEqual(len(detector.detectMultiScale(np.zeros((64, 64), dtype=np.uint8))), 0)

        with tempfile.TemporaryDirectory(prefix="Glance-người-dùng-") as folder:
            model_dir = Path(folder) / "models"
            model_dir.mkdir()
            shutil.copy(SOURCE.parent / "models" / "haarcascade_frontalface_default.xml", model_dir)
            ns["__file__"] = str(Path(folder) / "glance_windows.py")
            self.assertFalse(ns["load_face_detector"]().empty())

    def test_falls_back_when_directshow_raises_and_releases_failed_device(self):
        class CameraError(Exception):
            pass

        failed = Mock()
        failed.isOpened.return_value = False
        success = Mock()
        success.isOpened.return_value = True
        cv2 = SimpleNamespace(CAP_DSHOW=1, CAP_MSMF=2, CAP_ANY=0, error=CameraError,
                              VideoCapture=Mock(side_effect=[CameraError(), failed, success]))
        open_camera = load_nodes({"open_camera"}, {"cv2": cv2})["open_camera"]
        self.assertIs(open_camera(1), success)
        self.assertEqual(cv2.VideoCapture.call_args_list[0].args, (1, 1))
        self.assertEqual(cv2.VideoCapture.call_args_list[1].args, (1, 2))
        self.assertEqual(cv2.VideoCapture.call_args_list[2].args, (1, 0))
        failed.release.assert_called_once()

    def test_unavailable_camera_retries_and_reports_each_attempt(self):
        detector = Mock()
        detector.empty.return_value = False
        stop = Mock()
        stop.is_set.return_value = False
        stop.wait.side_effect = [False, True]
        ns = {
            "cv2": SimpleNamespace(data=SimpleNamespace(haarcascades="/cascade"),
                                   CascadeClassifier=Mock(return_value=detector)),
            "os": SimpleNamespace(path=SimpleNamespace(join=lambda *parts: "/".join(parts),
                                  exists=lambda path: True, dirname=lambda path: "/app",
                                  abspath=lambda path: path)),
            "sys": SimpleNamespace(), "__file__": "/app/glance_windows.py",
            "open_camera": Mock(return_value=None), "load_face_detector": Mock(return_value=detector),
        }
        app_class = load_nodes({"App"}, ns)["App"]
        app = app_class.__new__(app_class)
        app.publish = Mock()
        app.camera_loop(7, stop, 1, 5)
        self.assertEqual(app.publish.call_count, 2)
        self.assertEqual(app.publish.call_args.args, (7, "busy", 1))
        self.assertEqual(ns["open_camera"].call_count, 2)


if __name__ == "__main__":
    unittest.main()
