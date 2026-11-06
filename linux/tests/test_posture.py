import unittest

from posture import PostureGuard, TURTLE_NECK, HUNCH, frame_too_dark

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



class AdaptiveBehaviourTests(unittest.TestCase):
    def _warn(self, guard, t):
        feed(guard, t, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        return guard.update(t + 1, True, face_size=BASE_SIZE * 1.4,
                            center_y=BASE_Y + 0.06, pitch=BASE_PITCH)

    def _clear(self, guard, t):
        feed(guard, t, size=BASE_SIZE, y=BASE_Y)
        return guard.update(t + 3, True, face_size=BASE_SIZE,
                            center_y=BASE_Y, pitch=BASE_PITCH)

    def test_adaptive_cooldown_grows(self):
        guard = calibrated_guard(hold_seconds=1)
        self.assertTrue(self._warn(guard, 0).just_triggered)
        self._clear(guard, 5)
        # Second warning inside the hour: cooldown is now 120s, so a bad
        # posture at trigger+70s is still pending.
        self.assertTrue(self._warn(guard, 70).just_triggered)
        self._clear(guard, 75)
        feed(guard, 141, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        result = guard.update(142, True, face_size=BASE_SIZE * 1.4,
                              center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertFalse(result.warning)
        result = guard.update(191, True, face_size=BASE_SIZE * 1.4,
                              center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertTrue(result.warning)
        self.assertTrue(result.just_triggered)

    def test_snooze_silences_then_recovers(self):
        guard = calibrated_guard(hold_seconds=1)
        guard.snooze(0, seconds=1800)
        result = guard.update(10, True, face_size=BASE_SIZE * 1.4,
                              center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertEqual(result.status, "snoozed")
        self.assertFalse(result.warning)
        feed(guard, 1801, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        result = guard.update(1802, True, face_size=BASE_SIZE * 1.4,
                              center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertTrue(result.warning)

    def test_dismiss_as_not_bad_loosens_thresholds(self):
        guard = calibrated_guard(hold_seconds=1)
        self.assertTrue(self._warn(guard, 0).just_triggered)
        factor = guard.dismiss_as_not_bad(2)
        self.assertAlmostEqual(factor, 1.10)
        result = guard.update(3, True, face_size=BASE_SIZE, center_y=BASE_Y,
                              pitch=BASE_PITCH)
        self.assertFalse(result.warning)
        # A posture that barely crossed the old forward-alone threshold
        # (0.30) no longer classifies as bad at factor 1.10 (needs 0.33).
        feed(guard, 70, size=BASE_SIZE * 1.30, y=BASE_Y)
        result = guard.update(71, True, face_size=BASE_SIZE * 1.30,
                              center_y=BASE_Y, pitch=BASE_PITCH)
        self.assertFalse(result.warning)

    def test_profile_export_import_roundtrip(self):
        guard = calibrated_guard(hold_seconds=1)
        guard.dismiss_as_not_bad(0)
        data = guard.export_profile()
        self.assertIsNotNone(data)
        fresh = PostureGuard(hold_seconds=1)
        self.assertTrue(fresh.import_profile(data))
        self.assertTrue(fresh.is_calibrated)
        self.assertAlmostEqual(fresh.baseline_size, BASE_SIZE)
        self.assertAlmostEqual(fresh.loosen_factor, 1.10)
        result = fresh.update(10, True, face_size=BASE_SIZE, center_y=BASE_Y,
                              pitch=BASE_PITCH)
        self.assertEqual(result.status, "good")

    def test_profile_import_rejects_garbage(self):
        fresh = PostureGuard()
        self.assertIsNone(fresh.export_profile())
        self.assertFalse(fresh.import_profile(None))
        self.assertFalse(fresh.import_profile({}))
        self.assertFalse(fresh.import_profile({"size": "x", "center_y": 0.4}))
        self.assertFalse(fresh.import_profile({"size": 5.0, "center_y": 0.4}))
        self.assertFalse(fresh.is_calibrated)

    def test_third_warning_in_hour_suggests_break(self):
        guard = calibrated_guard(hold_seconds=1)
        self.assertFalse(self._warn(guard, 0).suggest_break)
        self._clear(guard, 5)
        self.assertFalse(self._warn(guard, 70).suggest_break)
        self._clear(guard, 75)
        third = None
        feed(guard, 200, size=BASE_SIZE * 1.4, y=BASE_Y + 0.06)
        third = guard.update(201, True, face_size=BASE_SIZE * 1.4,
                             center_y=BASE_Y + 0.06, pitch=BASE_PITCH)
        self.assertTrue(third.just_triggered)
        self.assertTrue(third.suggest_break)
        self.assertEqual(guard.total_warnings, 3)

    def test_frame_too_dark(self):
        self.assertTrue(frame_too_dark(3.0))
        self.assertTrue(frame_too_dark(14.9))
        self.assertFalse(frame_too_dark(15.0))
        self.assertFalse(frame_too_dark(120.0))
        self.assertFalse(frame_too_dark(None))


if __name__ == "__main__":
    unittest.main()
