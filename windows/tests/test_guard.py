import unittest
from guard import PresenceGuard


class PresenceGuardTests(unittest.TestCase):
    def test_absence_requires_continuous_delay(self):
        guard = PresenceGuard(delay=3)
        self.assertFalse(guard.update(0, face_present=False, idle_seconds=10))
        self.assertFalse(guard.update(2.9, face_present=False, idle_seconds=10))
        self.assertTrue(guard.update(3, face_present=False, idle_seconds=10))

    def test_face_or_activity_resets_absence(self):
        guard = PresenceGuard(delay=3)
        guard.update(0, face_present=False, idle_seconds=10)
        self.assertFalse(guard.update(2, face_present=False, idle_seconds=1))
        self.assertFalse(guard.update(4, face_present=False, idle_seconds=10))
        self.assertFalse(guard.update(5, face_present=True, idle_seconds=10))
        self.assertFalse(guard.update(6, face_present=False, idle_seconds=10))

    def test_face_releases_guard_and_reset_clears_timer(self):
        guard = PresenceGuard(delay=1)
        guard.update(0, face_present=False, idle_seconds=10)
        self.assertTrue(guard.update(1, face_present=False, idle_seconds=10))
        self.assertFalse(guard.update(2, face_present=True, idle_seconds=10))
        guard.update(3, face_present=False, idle_seconds=10)
        guard.reset()
        self.assertFalse(guard.update(10, face_present=False, idle_seconds=10))

    def test_activity_guard_can_be_disabled(self):
        guard = PresenceGuard(delay=1, activity_guard=False)
        guard.update(0, face_present=False, idle_seconds=0)
        self.assertTrue(guard.update(1, face_present=False, idle_seconds=0))


if __name__ == '__main__':
    unittest.main()

class CameraFreshnessTests(unittest.TestCase):
    def test_stale_camera_data_is_rejected(self):
        from guard import camera_is_stale
        self.assertFalse(camera_is_stale(12.9, 10, timeout=3))
        self.assertTrue(camera_is_stale(13, 10, timeout=3))
