import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class ConfigAndAutostartTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'glance_windows.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        
        # Extract standalone functions
        func_names = {'load_config', 'save_config', 'get_launch_command', 'set_windows_autostart', 'get_windows_autostart'}
        funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in func_names]
        
        self.namespace = {
            'os': SimpleNamespace(
                path=SimpleNamespace(
                    join=lambda *args: "/".join(args),
                    exists=lambda path: False,
                    dirname=lambda path: "dir",
                    abspath=lambda path: "/abs/path/glance_windows.py",
                ),
                makedirs=Mock(),
                environ={},
                expanduser=lambda path: "/home/user"
            ),
            'sys': SimpleNamespace(platform='win32', executable='/usr/bin/python3', frozen=False),
            'json': SimpleNamespace(load=Mock(), dump=Mock()),
            'CONFIG_PATH': '/test/config.json',
            'CONFIG_DIR': '/test',
            '__file__': '/abs/path/glance_windows.py'
        }
        module = ast.Module(body=funcs, type_ignores=[])
        exec(compile(module, str(source), 'exec'), self.namespace)

    def test_default_config_values(self):
        load_config = self.namespace['load_config']
        cfg = load_config()
        self.assertEqual(cfg['camera'], 0)
        self.assertEqual(cfg['delay'], 5)
        self.assertEqual(cfg['opacity'], 90)
        self.assertTrue(cfg['activity'])
        self.assertFalse(cfg['autostart'])
        self.assertFalse(cfg['auto_camera'])
        self.assertTrue(cfg['minimize_on_close'])

    def test_launch_command_frozen_vs_script(self):
        get_launch_command = self.namespace['get_launch_command']
        
        # Test script mode
        cmd = get_launch_command()
        self.assertIn('--startup', cmd)
        self.assertIn('glance_windows.py', cmd)
        
        # Test frozen exe mode
        self.namespace['sys'].frozen = True
        self.namespace['sys'].executable = 'C:\\Program Files\\Glance\\Glance.exe'
        cmd_frozen = get_launch_command()
        self.assertEqual(cmd_frozen, '"C:\\Program Files\\Glance\\Glance.exe" --startup')


if __name__ == '__main__':
    unittest.main()
