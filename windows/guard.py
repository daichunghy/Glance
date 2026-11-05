"""Presence policy, independent of the camera and Windows UI."""


class PresenceGuard:
    def __init__(self, delay=3, activity_guard=True):
        self.delay = delay
        self.activity_guard = activity_guard
        self.absent_since = None

    def reset(self):
        self.absent_since = None

    def update(self, now, face_present, idle_seconds):
        if face_present or (self.activity_guard and idle_seconds < 2.5):
            self.reset()
            return False
        if self.absent_since is None:
            self.absent_since = now
        return now - self.absent_since >= self.delay


def camera_is_stale(now, last_frame_at, timeout=5):
    return now - last_frame_at >= timeout
