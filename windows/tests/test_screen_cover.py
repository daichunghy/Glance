import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


def load_screen_cover(user32, window, set_style=None, last_error=0):
    source = Path(__file__).resolve().parents[1] / 'glance_windows.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ScreenCover')
    module = ast.Module(body=[cls], type_ignores=[])
    namespace = {
        'tk': SimpleNamespace(Toplevel=lambda root: window),
        'user32': user32,
        'wintypes': SimpleNamespace(HWND=lambda value: value),
        'get_style': Mock(return_value=0),
        'set_style': set_style or Mock(return_value=0),
        'ctypes': SimpleNamespace(set_last_error=Mock(), get_last_error=Mock(return_value=last_error)),
    }
    exec(compile(module, str(source), 'exec'), namespace)
    return namespace['ScreenCover'](object())


class ScreenCoverTests(unittest.TestCase):
    def test_position_failure_is_not_reported_as_success(self):
        user32 = SimpleNamespace(GetSystemMetrics=Mock(side_effect=lambda i: {76: 0, 77: 0, 78: 1920, 79: 1080}[i]),
                                 GetParent=Mock(return_value=1), SetWindowPos=Mock(return_value=0))
        window = Mock()
        window.winfo_id.return_value = 2
        cover = load_screen_cover(user32, window)
        with self.assertRaises(OSError):
            cover.update(True, 90)
        self.assertIsNone(cover.bounds)

    def test_style_failure_does_not_leave_an_input_blocking_cover(self):
        user32 = SimpleNamespace(GetSystemMetrics=Mock(side_effect=lambda i: {76: 0, 77: 0, 78: 1920, 79: 1080}[i]),
                                 GetParent=Mock(return_value=1), SetWindowPos=Mock(return_value=1))
        window = Mock()
        window.winfo_id.return_value = 2
        cover = load_screen_cover(user32, window, set_style=Mock(return_value=0), last_error=5)
        with self.assertRaises(OSError):
            cover.update(True, 90)
        window.withdraw.assert_called()
        user32.SetWindowPos.assert_not_called()

    def test_successful_position_is_cached(self):
        user32 = SimpleNamespace(GetSystemMetrics=Mock(side_effect=lambda i: {76: -1920, 77: 0, 78: 3840, 79: 1080}[i]),
                                 GetParent=Mock(return_value=1), SetWindowPos=Mock(return_value=1))
        window = Mock()
        window.winfo_id.return_value = 2
        cover = load_screen_cover(user32, window)
        cover.update(True, 90)
        cover.update(True, 90)
        self.assertEqual(cover.bounds, (-1920, 0, 3840, 1080))
        self.assertEqual(user32.SetWindowPos.call_count, 1)

class AppOverlayFailureTests(unittest.TestCase):
    def test_overlay_error_stops_automatic_guard_and_warns_user(self):
        source = Path(__file__).resolve().parents[1] / 'glance_windows.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'App')
        namespace = {}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(source), 'exec'), namespace)
        app = namespace['App'].__new__(namespace['App'])
        app.root = Mock()
        app.cover = Mock()
        app.cover.update.side_effect = OSError('SetWindowPos failed')
        app.opacity = Mock()
        app.opacity.get.return_value = 90
        app.status = Mock()
        app.start_button = Mock()
        app.manual_button = Mock()
        app.stop_event = Mock()
        app.manual = False
        app.automatic_cover = True
        app.controls_topmost = False
        app.camera_started_at = 1
        app.last_frame_at = 2
        app.generation = 3
        app.refresh_cover()
        self.assertFalse(app.automatic_cover)
        app.stop_event.set.assert_called_once()
        self.assertIn('không', app.status.set.call_args.args[0].lower())
