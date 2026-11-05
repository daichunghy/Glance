import unittest

from posture import PostureGuard, TURTLE_NECK, HUNCH

BASE_SIZE = 0.30   # face width / frame width while sitting correctly
BASE_Y = 0.40      # face centre Y while sitting correctly
BASE_PITCH = 0.0


def calibrated_guard(**kwargs):
    guard = PostureGuard(**kwargs)
    guard.update(0, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=BASE_PITCH)
    assert guard.calibrate()
    return guard


def feed(guard, now, size=BASE_SIZE, y=BASE_Y, pitch=BASE_PITCH, frames=30):
    """Feed repeated identical frames so EMA smoothing converges."""
    result = None
    for i in range(frames):
        result = guard.update(now + i * 0.0, True, face_size=size, center_y=y, pitch=pitch)
    return result


class PostureGuardTests(unittest.TestCase):
    def test_uncalibrated_never_warns(self):
        guard = PostureGuard(hold_seconds=1)
        feed(guard, 0, size=BASE_SIZE * 1.5, y=BASE_Y + 0.2)
        result = feed(guard, 5, size=BASE_SIZE * 1.5, y=BASE_Y + 0.2)
        self.assertEqual(result.status, "uncalibrated")
        self.assertFalse(result.warning)

    def test_calibrate_without_face_fails(self):
        guard = PostureGuard()
        self.assertFalse(guard.calibrate())
        self.assertFalse(guard.is_calibrated)

    def test_good_posture_never_warns(self):
        guard = calibrated_guard(hold_seconds=1)
        result = feed(guard, 10)
        self.assertEqual(result.status, "good")
        self.assertFalse(result.warning)

    def test_turtle_neck_warns_only_after_hold(self):
        guard = calibrated_guard(hold_seconds=10)
        # Head ~35% closer, slightly dropped: classic turtle neck.
        feed(guard, 0, size=BASE_SIZE * 1.35, y=BASE_Y + 0.05)
        result = guard.update(9.9, True, face_size=BASE_SIZE * 1.35, center_y=BASE_Y + 0.05, pitch=BASE_PITCH)
        self.assertFalse(result.warning)
        result = guard.update(10, True, face_size=BASE_SIZE * 1.35, center_y=BASE_Y + 0.05, pitch=BASE_PITCH)
        self.assertTrue(result.warning)
        self.assertTrue(result.just_triggered)
        self.assertIn(TURTLE_NECK, result.kinds)

    def test_hunch_by_drop_alone_without_pitch(self):
        # Windows/Linux path: no pitch signal at all.
        guard = PostureGuard(hold_seconds=5)
        guard.update(0, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=None)
        self.assertTrue(guard.calibrate())
        feed(guard, 0, size=BASE_SIZE, y=BASE_Y + 0.15, pitch=None)
        result = guard.update(5, True, face_size=BASE_SIZE, center_y=BASE_Y + 0.15, pitch=None)
        self.assertTrue(result.warning)
        self.assertIn(HUNCH, result.kinds)

    def test_forward_alone_warns_without_pitch(self):
        guard = PostureGuard(hold_seconds=5)
        guard.update(0, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=None)
        guard.calibrate()
        feed(guard, 0, size=BASE_SIZE * 1.35, y=BASE_Y, pitch=None)
        result = guard.update(5, True, face_size=BASE_SIZE * 1.35, center_y=BASE_Y, pitch=None)
        self.assertTrue(result.warning)
        self.assertIn(TURTLE_NECK, result.kinds)

    def test_brief_bad_posture_does_not_warn(self):
        guard = calibrated_guard(hold_seconds=10)
        feed(guard, 0, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        guard.update(3, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=BASE_PITCH)
        result = feed(guard, 4)
        self.assertEqual(result.status, "good")
        self.assertFalse(result.warning)

    def test_no_face_resets_bad_timer(self):
        guard = calibrated_guard(hold_seconds=5)
        feed(guard, 0, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        guard.update(4, False)
        feed(guard, 4, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        result = guard.update(8, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertFalse(result.warning)

    def test_keyboard_look_down_is_not_bad_posture(self):
        guard = calibrated_guard(hold_seconds=1)
        # Pitch drops 25 degrees (looking at keyboard), head not forward.
        result = feed(guard, 10, size=BASE_SIZE, y=BASE_Y + 0.02, pitch=BASE_PITCH - 25)
        self.assertFalse(result.warning)
        self.assertEqual(result.kinds, ())

    def test_warning_clears_after_good_posture_release(self):
        guard = calibrated_guard(hold_seconds=1, release_seconds=3, cooldown_seconds=60)
        feed(guard, 0, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        result = guard.update(1, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertTrue(result.warning)
        feed(guard, 2)
        result = guard.update(4.9, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=BASE_PITCH)
        self.assertTrue(result.warning)
        result = guard.update(5, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=BASE_PITCH)
        self.assertFalse(result.warning)
        self.assertEqual(result.status, "good")

    def test_cooldown_blocks_immediate_retrigger(self):
        guard = calibrated_guard(hold_seconds=1, release_seconds=1, cooldown_seconds=60)
        feed(guard, 0, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        self.assertTrue(guard.update(1, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH).warning)
        feed(guard, 2)
        guard.update(3, True, face_size=BASE_SIZE, center_y=BASE_Y, pitch=BASE_PITCH)
        # Bad again well inside the 60s cooldown: pending, not a new warning.
        feed(guard, 4, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        result = guard.update(10, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertFalse(result.warning)
        # After cooldown expires the still-bad posture warns again.
        result = guard.update(62, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertTrue(result.warning)
        self.assertTrue(result.just_triggered)

    def test_recalibration_clears_warning(self):
        guard = calibrated_guard(hold_seconds=1)
        feed(guard, 0, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        self.assertTrue(guard.update(1, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH).warning)
        self.assertTrue(guard.calibrate())
        result = guard.update(2, True, face_size=BASE_SIZE * 1.4, center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertFalse(result.warning)


if __name__ == "__main__":
    unittest.main()
