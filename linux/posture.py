"""Posture policy (turtle neck / hunch), independent of camera and UI.

Shared spec: posture/POSTURE_SPEC.md in the repository root.
The identical file ships in windows/ and linux/ so both platforms behave
exactly the same; macOS mirrors it in PostureGuard.swift.

Inputs are plain geometry, already normalised by the caller:
  face_size  -- face width / frame width (proxy for head distance)
  center_y   -- face centre Y, normalised, positive direction = head drops
  pitch      -- optional head pitch in degrees (macOS Vision only)

No frames are stored or sent anywhere; only these numbers live in RAM.
"""
from collections import namedtuple

PostureResult = namedtuple(
    "PostureResult",
    ["status", "kinds", "warning", "just_triggered", "forward", "drop"],
)
# status: "uncalibrated" | "no_face" | "good" | "bad_pending" | "warning"
# kinds: tuple containing "turtle_neck" and/or "hunch" (may be empty)

TURTLE_NECK = "turtle_neck"
HUNCH = "hunch"


class PostureGuard:
    def __init__(self, hold_seconds=10, cooldown_seconds=60, release_seconds=3,
                 forward_threshold=0.18, forward_alone=0.28,
                 drop_threshold=0.07, drop_alone=0.12,
                 supporting_drop=0.03, supporting_forward=0.08,
                 pitch_drop_threshold=8.0, keyboard_pitch_drop=20.0):
        self.hold_seconds = hold_seconds
        self.cooldown_seconds = cooldown_seconds
        self.release_seconds = release_seconds
        self.forward_threshold = forward_threshold
        self.forward_alone = forward_alone
        self.drop_threshold = drop_threshold
        self.drop_alone = drop_alone
        self.supporting_drop = supporting_drop
        self.supporting_forward = supporting_forward
        self.pitch_drop_threshold = pitch_drop_threshold
        self.keyboard_pitch_drop = keyboard_pitch_drop

        self.baseline_size = None
        self.baseline_center_y = None
        self.baseline_pitch = None
        self._smooth_size = None
        self._smooth_center_y = None
        self._smooth_pitch = None
        self._bad_since = None
        self._good_since = None
        self._warning = False
        self._warning_kinds = ()
        self._cooldown_until = None

    # -- calibration -----------------------------------------------------
    def calibrate(self):
        """Adopt the current smoothed measurements as the good baseline.

        Returns False when no face has been measured yet, so the UI can
        tell the user to look at the camera instead of saving an empty
        baseline.
        """
        if self._smooth_size is None or self._smooth_center_y is None:
            return False
        self.baseline_size = self._smooth_size
        self.baseline_center_y = self._smooth_center_y
        self.baseline_pitch = self._smooth_pitch
        self.reset_timers()
        return True

    @property
    def is_calibrated(self):
        return self.baseline_size is not None

    def reset(self):
        self.baseline_size = None
        self.baseline_center_y = None
        self.baseline_pitch = None
        self._smooth_size = None
        self._smooth_center_y = None
        self._smooth_pitch = None
        self.reset_timers()

    def reset_timers(self):
        self._bad_since = None
        self._good_since = None
        self._warning = False
        self._warning_kinds = ()
        self._cooldown_until = None

    # -- per-frame update --------------------------------------------------
    def _smooth(self, current, value):
        if value is None:
            return current
        if current is None:
            return value
        return current * 0.70 + value * 0.30

    def update(self, now, face_present, face_size=None, center_y=None, pitch=None):
        if not face_present:
            # Away / looking elsewhere is the privacy guard's job, not ours.
            self._bad_since = None
            self._good_since = None
            return PostureResult("no_face", (), self._warning, False, 0.0, 0.0)

        self._smooth_size = self._smooth(self._smooth_size, face_size)
        self._smooth_center_y = self._smooth(self._smooth_center_y, center_y)
        self._smooth_pitch = self._smooth(self._smooth_pitch, pitch)

        if not self.is_calibrated:
            return PostureResult("uncalibrated", (), False, False, 0.0, 0.0)

        forward = (self._smooth_size / self.baseline_size - 1.0) if self.baseline_size else 0.0
        drop = self._smooth_center_y - self.baseline_center_y
        pitch_drop = 0.0
        if pitch is not None and self.baseline_pitch is not None and self._smooth_pitch is not None:
            pitch_drop = self.baseline_pitch - self._smooth_pitch

        kinds = self._classify(forward, drop, pitch_drop, pitch_available=pitch is not None)

        if kinds:
            self._good_since = None
            if self._bad_since is None:
                self._bad_since = now
            if self._warning:
                self._warning_kinds = kinds
                return PostureResult("warning", kinds, True, False, forward, drop)
            if now - self._bad_since >= self.hold_seconds:
                if self._cooldown_until is None or now >= self._cooldown_until:
                    self._warning = True
                    self._warning_kinds = kinds
                    self._cooldown_until = now + self.cooldown_seconds
                    return PostureResult("warning", kinds, True, True, forward, drop)
                return PostureResult("bad_pending", kinds, False, False, forward, drop)
            return PostureResult("bad_pending", kinds, False, False, forward, drop)

        # Good posture this frame.
        self._bad_since = None
        if self._warning:
            if self._good_since is None:
                self._good_since = now
            if now - self._good_since >= self.release_seconds:
                self._warning = False
                self._warning_kinds = ()
                self._good_since = None
                return PostureResult("good", (), False, False, forward, drop)
            return PostureResult("warning", self._warning_kinds, True, False, forward, drop)
        return PostureResult("good", (), False, False, forward, drop)

    def _classify(self, forward, drop, pitch_drop, pitch_available):
        # Looking down at a keyboard / notes is not bad posture: the head
        # pitches far down but does not push forward or sink deeply.
        if (pitch_available and pitch_drop >= self.keyboard_pitch_drop
                and forward < self.supporting_forward and drop < self.drop_alone):
            return ()

        kinds = []
        turtle = forward >= self.forward_alone or (
            forward >= self.forward_threshold
            and (drop >= self.supporting_drop or pitch_drop >= self.pitch_drop_threshold)
        )
        hunch = drop >= self.drop_alone or (
            drop >= self.drop_threshold
            and (pitch_drop >= self.pitch_drop_threshold or forward >= self.supporting_forward)
        )
        if turtle:
            kinds.append(TURTLE_NECK)
        if hunch:
            kinds.append(HUNCH)
        return tuple(kinds)
