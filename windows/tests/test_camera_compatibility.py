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
        cv2 = SimpleNamespace(
            CAP_DSHOW=1,
            CAP_MSMF=2,
            CAP_ANY=0,
            error=CameraError,
            VideoCapture=Mock(side_effect=[CameraError(), failed, success]),
        )
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
            "cv2": SimpleNamespace(
                data=SimpleNamespace(haarcascades="/cascade"),
                CascadeClassifier=Mock(return_value=detector),
            ),
            "os": SimpleNamespace(
                path=SimpleNamespace(
                    join=lambda *parts: "/".join(parts),
                    exists=lambda path: True,
                    dirname=lambda path: "/app",
                    abspath=lambda path: path,
                )
            ),
            "sys": SimpleNamespace(),
            "__file__": "/app/glance_windows.py",
            "open_camera": Mock(return_value=None),
            "load_face_detector": Mock(return_value=detector),
        }
        app_class = load_nodes({"App"}, ns)["App"]
        app = app_class.__new__(app_class)
        app.publish = Mock()
        app.camera_loop(7, stop, 1, 5)
        self.assertEqual(app.publish.call_count, 2)
        self.assertEqual(app.publish.call_args.args, (7, "busy", 1))
        self.assertEqual(ns["open_camera"].call_count, 2)

    def test_window_geometry_fits_small_laptop_and_high_dpi_screens(self):
        fn = load_nodes({"compute_window_geometry"}, {})["compute_window_geometry"]
        w, h, min_w, min_h = fn(1366, 768)
        self.assertLessEqual(w, 520)
        self.assertLessEqual(h, 768 - 90)
        self.assertLessEqual(min_h, h)

        w2, h2, min_w2, min_h2 = fn(1280, 720)
        self.assertLessEqual(h2, 720 - 90)
        self.assertLessEqual(min_h2, h2)
        self.assertLessEqual(min_w2, w2)

    def test_single_instance_mutex_focuses_existing_window(self):
        user32 = SimpleNamespace(
            FindWindowW=Mock(return_value=42),
            ShowWindow=Mock(),
            SetForegroundWindow=Mock(),
        )
        kernel32 = SimpleNamespace(CreateMutexW=Mock(return_value=99))
        ctypes = SimpleNamespace(set_last_error=Mock(), get_last_error=Mock(return_value=183))
        ns = {
            "_INSTANCE_MUTEX": None,
            "ctypes": ctypes,
            "kernel32": kernel32,
            "user32": user32,
        }
        fn = load_nodes({"acquire_single_instance_mutex"}, ns)["acquire_single_instance_mutex"]
        self.assertFalse(fn())
        user32.FindWindowW.assert_called_once_with(None, "Glance")
        user32.ShowWindow.assert_called_once_with(42, 9)
        user32.SetForegroundWindow.assert_called_once_with(42)

    def test_requirements_excludes_opencv_5(self):
        reqs = (SOURCE.parent / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("opencv-python==4.", reqs)
        model_path = SOURCE.parent / "models" / "haarcascade_frontalface_default.xml"
        self.assertTrue(model_path.exists())

    def test_busy_retry_does_not_shrink_watchdog_to_five_seconds(self):
        import queue
        import time

        ns = {
            "queue": queue,
            "time": SimpleNamespace(monotonic=Mock(return_value=100.0)),
            "camera_is_stale": lambda now, last, timeout: (now - last) >= timeout,
            "idle_seconds": lambda: 0,
        }
        app_class = load_nodes({"App"}, ns)["App"]
        app = app_class.__new__(app_class)
        app.events = queue.Queue()
        app.generation = 1
        app.camera_started_at = 90.0
        app.last_frame_at = 92.0
        app.camera_busy = False
        app.automatic_cover = False
        app.status = Mock()
        app.start_button = Mock()
        app.stop_camera = Mock()
        app.refresh_cover = Mock()
        app.root = Mock()

        app.events.put((1, "busy", 0))
        app.poll()
        self.assertTrue(app.camera_busy)
        app.stop_camera.assert_not_called()

        # 8 seconds later while still busy/retrying: timeout is 15s, not 5s.
        ns["time"].monotonic.return_value = 108.0
        app.poll()
        app.stop_camera.assert_not_called()

    def test_zero_frame_backend_falls_back_to_msmf_on_reopen(self):
        detector = Mock()
        detector.empty.return_value = False
        stop = Mock()
        stop.is_set.side_effect = [False] * 6 + [True]

        bad_dshow = Mock()
        bad_dshow.isOpened.return_value = True
        bad_dshow.read.return_value = (False, None)

        good_msmf = Mock()
        good_msmf.isOpened.return_value = True
        good_msmf.read.return_value = (False, None)

        ns = {
            "cv2": SimpleNamespace(
                CAP_MSMF=2,
                CAP_ANY=0,
                CAP_PROP_FRAME_WIDTH=3,
                CAP_PROP_FRAME_HEIGHT=4,
                error=RuntimeError,
                VideoCapture=Mock(return_value=good_msmf),
            ),
            "PresenceGuard": Mock(),
            "open_camera": Mock(return_value=bad_dshow),
            "load_face_detector": Mock(return_value=detector),
        }
        app_class = load_nodes({"App"}, ns)["App"]
        app = app_class.__new__(app_class)
        app.posture_guard = Mock()
        app.publish = Mock()
        app.camera_loop(1, stop, 0, 5)
        ns["cv2"].VideoCapture.assert_any_call(0, 2)
        bad_dshow.release.assert_called_once()
        good_msmf.release.assert_called_once()

    def test_switching_to_uncalibrated_camera_resets_posture_profile(self):
        app_class = load_nodes({"App"}, {})["App"]
        app = app_class.__new__(app_class)
        app._profiles = {"cameras": {"0": {"size": 0.3, "center_y": 0.4}}}
        app.posture_guard = Mock()
        app.posture_guard.import_profile.return_value = True

        app._apply_profile_for_camera(0)
        app.posture_guard.import_profile.assert_called_once()
        app.posture_guard.reset.assert_not_called()

        app._apply_profile_for_camera(1)
        app.posture_guard.reset.assert_called_once()


if __name__ == "__main__":
    unittest.main()
