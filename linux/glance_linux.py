"""
Glance for Linux
Privacy & Anti-Peeping Screen Guard for Ubuntu, Fedora, Arch, Debian
"""

import fcntl
import json
import os
import sys
import time
import threading
import cv2
from PyQt6.QtWidgets import (
    QApplication, QLabel, QMenu, QMessageBox, QStyle,
    QSystemTrayIcon, QToolButton, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QColor, QPainter, QAction, QActionGroup

from posture import PostureGuard, frame_too_dark

_LOCK_FILE = None


def acquire_single_instance_lock():
    """Prevent multiple Glance instances from competing for the same webcam."""
    global _LOCK_FILE
    try:
        folder = os.path.join(os.path.expanduser("~"), ".glance")
        os.makedirs(folder, exist_ok=True)
        lock_path = os.path.join(folder, "glance_linux.lock")
        fh = open(lock_path, "w", encoding="utf-8")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.write(str(os.getpid()))
        fh.flush()
        _LOCK_FILE = fh
        return True
    except BlockingIOError:
        return False
    except OSError:
        return True


def load_face_detector():
    """Load the Haar cascade face detector from bundled, cv2, or system paths."""
    cascade_name = "haarcascade_frontalface_default.xml"
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(os.path.join(sys._MEIPASS, "models", cascade_name))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", cascade_name))
    if hasattr(cv2, "data") and getattr(cv2.data, "haarcascades", None):
        candidates.append(os.path.join(cv2.data.haarcascades, cascade_name))
    candidates.extend([
        os.path.join("/usr/share/opencv4/haarcascades", cascade_name),
        os.path.join("/usr/share/opencv/haarcascades", cascade_name),
    ])
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        raise FileNotFoundError("Không tìm thấy tệp nhận diện khuôn mặt haarcascade_frontalface_default.xml.")
    with open(path, "r", encoding="utf-8") as fh:
        contents = fh.read()
    storage = cv2.FileStorage(contents, cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY)
    try:
        if not storage.isOpened():
            raise RuntimeError("Không mở được bộ nhận diện khuôn mặt.")
        detector = cv2.CascadeClassifier()
        if not detector.read(storage.getFirstTopLevelNode()) or detector.empty():
            raise RuntimeError("Không tải được bộ nhận diện khuôn mặt.")
    finally:
        storage.release()
    return detector


def open_camera(preferred_index=0, probe_indices=tuple(range(10))):
    """Try V4L2 and default backends across common /dev/video* indices."""
    ordered = [preferred_index] + [i for i in probe_indices if i != preferred_index]
    backends = []
    if hasattr(cv2, "CAP_V4L2"):
        backends.append(cv2.CAP_V4L2)
    backends.append(getattr(cv2, "CAP_ANY", 0))

    for cam_idx in ordered:
        for backend in backends:
            cap = None
            try:
                cap = cv2.VideoCapture(cam_idx, backend)
                if cap is not None and cap.isOpened():
                    ok, frame = cap.read()
                    if ok and frame is not None:
                        return cap
            except cv2.error:
                pass
            if cap is not None:
                cap.release()
    return None


class SignalEmitter(QObject):
    camera_error = pyqtSignal(str)
    camera_waiting = pyqtSignal(str)  # busy / blocked / disabled — not fatal
    camera_ready = pyqtSignal()
    update_protection = pyqtSignal(str, float)  # side, alpha
    posture_status = pyqtSignal(str)   # human-readable posture state
    posture_warning = pyqtSignal(str)  # emitted once per bad-posture episode


class GlanceOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.active_side = "none"
        self.alpha_val = 0.0

        # X11 / Wayland transparent, click-through, non-focusing, always-on-top flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Keep hidden when inactive so desktops without a compositor never black out.
        self.sync_geometry()
        self.hide()

    def sync_geometry(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            screens = QApplication.screens()
            screen = screens[0] if screens else None
        screen_geo = screen.virtualGeometry() if screen is not None else QRect(0, 0, 1920, 1080)
        self.setGeometry(screen_geo)

    def set_protection(self, side, alpha):
        self.active_side = side
        self.alpha_val = alpha
        if side == "none" or alpha <= 0.0:
            if self.isVisible():
                self.hide()
            return
        self.sync_geometry()
        if not self.isVisible():
            self.show()
        self.raise_()
        self.update()

    def paintEvent(self, event):
        if self.alpha_val <= 0.0 or self.active_side == "none":
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        alpha_int = int(self.alpha_val * 240)
        color = QColor(25, 25, 25, alpha_int)

        w = self.width()
        h = self.height()

        if self.active_side == "full":
            painter.fillRect(0, 0, w, h, color)
        elif self.active_side == "left":
            # Blur left half
            painter.fillRect(0, 0, int(w * 0.55), h, color)
        elif self.active_side == "right":
            # Blur right half without a 1px gap on odd widths
            start_x = int(w * 0.45)
            painter.fillRect(start_x, 0, w - start_x, h, color)


class GlanceLinuxController(QObject):
    def __init__(self, overlay, signals):
        super().__init__()
        self.overlay = overlay
        self.signals = signals
        self.is_enabled = True
        self.blur_mode = "Side Blur"
        self.sensitivity_threshold = 18.0
        self.away_delay_seconds = 2.5

        self.baseline_yaw = 0.0
        self.smoothed_yaw = 0.0
        self.is_looking_away = False
        self.running = True
        self.stop_event = threading.Event()

        # Posture guard (gù lưng / cổ rùa): opt-in, off by default, shares
        # the same camera frames. It never touches the overlay.
        self.posture_guard = PostureGuard()
        self.posture_enabled = False
        self._last_posture_text = None
        self.share_until = None
        self._last_dark_notice = 0.0
        self._was_blocked_or_busy = False
        self._load_posture_profile()

        self.signals.update_protection.connect(self.apply_protection)

    def stop(self):
        self.running = False
        self.stop_event.set()

    @pyqtSlot(str, float)
    def apply_protection(self, side, alpha):
        if self.is_enabled:
            self.overlay.set_protection(side, alpha)

    def set_enabled(self, enabled):
        self.is_enabled = enabled
        if not enabled:
            self.overlay.set_protection("none", 0.0)

    def set_blur_mode(self, mode):
        self.blur_mode = mode
        if not self.is_looking_away:
            return
        if self.blur_mode == "Full Screen":
            self.signals.update_protection.emit("full", 0.95)
        elif self.smoothed_yaw > self.sensitivity_threshold:
            self.signals.update_protection.emit("left", 0.95)
        elif self.smoothed_yaw < -self.sensitivity_threshold:
            self.signals.update_protection.emit("right", 0.95)

    def set_sensitivity(self, threshold):
        self.sensitivity_threshold = float(threshold)

    def set_posture_enabled(self, enabled):
        self.posture_enabled = enabled
        if not enabled:
            self.posture_guard.reset_timers()
            self._emit_posture_text("Tư thế: đang tắt")

    # -- posture profile persistence (~/.glance/posture.json) --------------
    @staticmethod
    def _profile_path():
        folder = os.path.join(os.path.expanduser("~"), ".glance")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "posture.json")

    def _load_posture_profile(self):
        try:
            with open(self._profile_path(), encoding="utf-8") as fh:
                self.posture_guard.import_profile(json.load(fh))
        except (OSError, ValueError):
            pass

    def _save_posture_profile(self):
        profile = self.posture_guard.export_profile()
        if profile is None:
            return
        try:
            with open(self._profile_path(), "w", encoding="utf-8") as fh:
                json.dump(profile, fh)
        except OSError:
            pass

    def calibrate_posture(self):
        if not self.posture_enabled:
            self._emit_posture_text("Tư thế: bật Cảnh báo tư thế trước khi căn chỉnh")
            return
        if self.posture_guard.calibrate():
            self._save_posture_profile()
            self._emit_posture_text("Tư thế: đã ghi tư thế chuẩn (đã lưu, mở lại không cần căn chỉnh)")
        else:
            self._emit_posture_text("Tư thế: chưa thấy khuôn mặt, hãy nhìn vào camera rồi thử lại")

    def dismiss_posture(self):
        self.posture_guard.dismiss_as_not_bad(time.monotonic())
        self._save_posture_profile()
        self._emit_posture_text("Tư thế: đã ghi nhận — Glance bớt nhạy hơn một chút")

    def snooze_posture(self):
        self.posture_guard.snooze(time.monotonic())
        self._emit_posture_text("Tư thế: tạm tắt nhắc 30 phút")

    def start_share(self):
        """Deliberately show the screen to someone next to you for 2 min."""
        self.share_until = time.monotonic() + 120
        self.is_looking_away = False
        self.signals.update_protection.emit("none", 0.0)

    def _emit_posture_text(self, text):
        if text != self._last_posture_text:
            self._last_posture_text = text
            self.signals.posture_status.emit(text)

    def process_posture(self, result):
        if not self.posture_enabled:
            return
        if result.status == "uncalibrated":
            self._emit_posture_text("Tư thế: chưa căn chỉnh — ngồi thẳng rồi chọn Căn chỉnh tư thế")
        elif result.status == "no_face":
            self._emit_posture_text("Tư thế: tạm dừng (chưa thấy khuôn mặt)")
        elif result.status == "warning":
            names = []
            if "turtle_neck" in result.kinds:
                names.append("cổ rùa")
            if "hunch" in result.kinds:
                names.append("gù lưng")
            text = "Tư thế: hãy ngồi thẳng lại — đang " + " và ".join(names)
            if result.suggest_break:
                text += " — nhắc nhiều rồi, thử đứng dậy giãn người 1 phút"
            elif result.just_triggered and self.posture_guard.total_warnings <= 3:
                text += " (mấy lần đầu chưa chuẩn là bình thường — chọn 'Không phải tư thế xấu' để Glance học theo bạn)"
            self._emit_posture_text(text)
            if result.just_triggered:
                self.signals.posture_warning.emit(text)
        elif result.status == "bad_pending":
            self._emit_posture_text("Tư thế: đang hơi sai, hãy ngồi thẳng lại")
        elif result.status == "snoozed":
            self._emit_posture_text("Tư thế: đang tạm tắt nhắc 30 phút")
        else:
            self._emit_posture_text("Tư thế: tốt")

    def process_face(self, yaw_degrees, is_present):
        if not self.is_enabled:
            self.signals.update_protection.emit("none", 0.0)
            return
        if self.share_until is not None and time.monotonic() < self.share_until:
            self.signals.update_protection.emit("none", 0.0)
            return

        release_threshold = max(5.0, self.sensitivity_threshold - 6.0)

        if is_present and yaw_degrees is not None:
            if self.is_looking_away:
                if abs(yaw_degrees) < release_threshold:
                    self.is_looking_away = False
                    self.signals.update_protection.emit("none", 0.0)
                else:
                    if yaw_degrees > self.sensitivity_threshold:
                        self.signals.update_protection.emit("left" if self.blur_mode == "Side Blur" else "full", 0.95)
                    elif yaw_degrees < -self.sensitivity_threshold:
                        self.signals.update_protection.emit("right" if self.blur_mode == "Side Blur" else "full", 0.95)
            else:
                if yaw_degrees > self.sensitivity_threshold:
                    self.is_looking_away = True
                    self.signals.update_protection.emit("left" if self.blur_mode == "Side Blur" else "full", 0.95)
                elif yaw_degrees < -self.sensitivity_threshold:
                    self.is_looking_away = True
                    self.signals.update_protection.emit("right" if self.blur_mode == "Side Blur" else "full", 0.95)
        else:
            # Away blur
            self.is_looking_away = True
            self.signals.update_protection.emit("full", 0.95)

    def camera_worker(self):
        cap = None
        busy_announced = False
        try:
            face_cascade = load_face_detector()
            no_face_since = None
            read_failures = 0
            last_state = None
            frame_wait = 0.12

            while self.running and not self.stop_event.is_set():
                # Protection off = camera truly released (LED off), not
                # merely ignored. Re-enabled -> reopened by this loop.
                if not self.is_enabled:
                    if cap is not None:
                        cap.release()
                        cap = None
                    no_face_since = None
                    self.stop_event.wait(0.4)
                    continue

                if cap is None:
                    cap = open_camera(0)
                    if cap is None:
                        # Busy (a call app holds it) or unplugged: wait and
                        # retry; Glance resumes by itself when it frees.
                        if not busy_announced:
                            self.signals.camera_waiting.emit(
                                "Camera đang bận hoặc chưa sẵn sàng — Glance tự thử lại.")
                            busy_announced = True
                            self._was_blocked_or_busy = True
                        self.stop_event.wait(3)
                        continue
                    busy_announced = False
                    if self._was_blocked_or_busy:
                        self._was_blocked_or_busy = False
                        self.signals.camera_ready.emit()
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

                ret, frame = cap.read()
                if not ret or frame is None:
                    read_failures += 1
                    if read_failures >= 5:
                        cap.release()
                        cap = None
                        read_failures = 0
                    self.stop_event.wait(0.1)
                    continue
                read_failures = 0

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                now = time.monotonic()
                if frame_too_dark(float(gray.mean())):
                    # Covered camera / pitch-black room: hold everything and
                    # clear any active privacy cover so screen isn't stuck dark.
                    no_face_since = None
                    self.is_looking_away = False
                    self.signals.update_protection.emit("none", 0.0)
                    self._was_blocked_or_busy = True
                    if now - self._last_dark_notice > 10:
                        self._last_dark_notice = now
                        self.signals.camera_waiting.emit(
                            "Camera có vẻ bị che hoặc quá tối — Glance tạm đứng yên.")
                    self.stop_event.wait(0.12)
                    continue

                if self._was_blocked_or_busy:
                    self._was_blocked_or_busy = False
                    self.signals.camera_ready.emit()

                faces = face_cascade.detectMultiScale(gray, 1.2, 4)

                if len(faces) > 0:
                    no_face_since = None
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    frame_center = frame.shape[1] / 2.0
                    face_center = x + w / 2.0
                    relative = (face_center - frame_center) / frame_center
                    estimated_yaw = relative * 35.0 - self.baseline_yaw
                    self.smoothed_yaw = (self.smoothed_yaw * 0.7) + (estimated_yaw * 0.3)
                    self.process_face(self.smoothed_yaw, is_present=True)
                    self.process_posture(self.posture_guard.update(
                        now, True,
                        face_size=w / frame.shape[1],
                        center_y=(y + h / 2) / frame.shape[0]))
                else:
                    self.process_posture(self.posture_guard.update(now, False))
                    if no_face_since is None:
                        no_face_since = now
                    if now - no_face_since >= self.away_delay_seconds:
                        self.process_face(None, is_present=False)

                # Battery-aware sampling: stretch toward ~3 FPS while the
                # scene is stable, snap back to ~8 FPS on any change.
                state = (len(faces) > 0, self.is_looking_away)
                if state == last_state:
                    frame_wait = min(0.30, frame_wait * 1.5)
                else:
                    frame_wait = 0.12
                    last_state = state
                self.stop_event.wait(frame_wait)

        except (OSError, RuntimeError, cv2.error) as exc:
            self.signals.camera_error.emit(str(exc))
        finally:
            if cap is not None:
                cap.release()

    def calibrate(self):
        self.baseline_yaw = self.smoothed_yaw + self.baseline_yaw
        self.smoothed_yaw = 0.0
        self.process_face(0.0, is_present=True)


class FallbackControlPanel(QWidget):
    """Non-dialog control panel when no system tray is available (Esc won't quit Glance)."""

    def __init__(self, on_close):
        super().__init__()
        self._on_close = on_close

    def closeEvent(self, event):
        self._on_close()
        super().closeEvent(event)


def run_self_test():
    import numpy as np
    detector = load_face_detector()
    detector.detectMultiScale(np.zeros((64, 64), dtype=np.uint8))


def main():
    if "--self-test" in sys.argv:
        run_self_test()
        return 0

    if not acquire_single_instance_lock():
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName("Glance")
    app.setQuitOnLastWindowClosed(False)

    overlay = GlanceOverlay()
    app.screenAdded.connect(lambda _s: overlay.sync_geometry())
    app.screenRemoved.connect(lambda _s: overlay.sync_geometry())

    signals = SignalEmitter()
    controller = GlanceLinuxController(overlay, signals)

    # System tray icon
    tray = QSystemTrayIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
    tray.setToolTip("Glance Privacy Guard")

    menu = QMenu()
    toggle_act = QAction("Bật lớp che", checkable=True)
    toggle_act.setChecked(True)
    toggle_act.toggled.connect(controller.set_enabled)
    menu.addAction(toggle_act)

    cal_act = QAction("Căn giữa", triggered=controller.calibrate)
    menu.addAction(cal_act)

    style_menu = menu.addMenu("Kiểu làm mờ")
    style_group = QActionGroup(menu)
    side_blur_act = QAction("Làm mờ một bên", checkable=True)
    side_blur_act.setChecked(True)
    full_blur_act = QAction("Làm mờ toàn màn hình", checkable=True)
    side_blur_act.triggered.connect(lambda: controller.set_blur_mode("Side Blur"))
    full_blur_act.triggered.connect(lambda: controller.set_blur_mode("Full Screen"))
    for act in (side_blur_act, full_blur_act):
        style_group.addAction(act)
        style_menu.addAction(act)

    sens_menu = menu.addMenu("Độ nhạy góc quay")
    sens_group = QActionGroup(menu)
    for label_txt, deg in (("Cao (13°)", 13.0), ("Vừa (18°)", 18.0), ("Thấp (28°)", 28.0)):
        act = QAction(label_txt, checkable=True)
        act.setChecked(deg == 18.0)
        act.triggered.connect(lambda _checked=False, val=deg: controller.set_sensitivity(val))
        sens_group.addAction(act)
        sens_menu.addAction(act)

    menu.addSeparator()

    posture_act = QAction("Cảnh báo tư thế (gù lưng, cổ rùa)", checkable=True)
    posture_act.setChecked(False)
    posture_act.toggled.connect(controller.set_posture_enabled)
    menu.addAction(posture_act)

    posture_cal_act = QAction("Căn chỉnh tư thế chuẩn", triggered=controller.calibrate_posture)
    menu.addAction(posture_cal_act)

    posture_status_act = QAction("Tư thế: đang tắt")
    posture_status_act.setEnabled(False)
    menu.addAction(posture_status_act)
    signals.posture_status.connect(posture_status_act.setText)

    def posture_warning(text):
        tray.setToolTip("Glance — " + text)
        if QSystemTrayIcon.isSystemTrayAvailable() and tray.supportsMessages():
            tray.showMessage("Glance — Tư thế", text, QSystemTrayIcon.MessageIcon.Warning, 5000)

    signals.posture_warning.connect(posture_warning)

    posture_dismiss_act = QAction("Không phải tư thế xấu", triggered=controller.dismiss_posture)
    menu.addAction(posture_dismiss_act)

    posture_snooze_act = QAction("Tạm tắt nhắc tư thế 30 phút", triggered=controller.snooze_posture)
    menu.addAction(posture_snooze_act)

    share_act = QAction("Hiện màn hình 2 phút (cho người bên cạnh xem)", triggered=controller.start_share)
    menu.addAction(share_act)

    menu.addSeparator()
    quit_act = QAction("Thoát Glance", triggered=app.quit)
    menu.addAction(quit_act)

    tray.setContextMenu(menu)
    panel = None
    status_label = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()
    else:
        panel = FallbackControlPanel(app.quit)
        panel.setWindowTitle("Glance")
        panel.resize(340, 320)
        layout = QVBoxLayout(panel)
        status_label = QLabel("Trạng thái: đang bật bảo vệ")
        status_label.setWordWrap(True)
        layout.addWidget(status_label)
        posture_label = QLabel("Tư thế: đang tắt")
        posture_label.setWordWrap(True)
        layout.addWidget(posture_label)
        signals.posture_status.connect(posture_label.setText)
        for action in (toggle_act, cal_act, side_blur_act, full_blur_act,
                       posture_act, posture_cal_act, posture_dismiss_act,
                       posture_snooze_act, share_act, quit_act):
            button = QToolButton(panel)
            button.setDefaultAction(action)
            layout.addWidget(button)
        panel.show()

    def on_waiting(text):
        tray.setToolTip("Glance — " + text)
        if status_label is not None:
            status_label.setText(text)

    def on_ready():
        tray.setToolTip("Glance Privacy Guard")
        if status_label is not None:
            status_label.setText("Trạng thái: đang bật bảo vệ")

    signals.camera_waiting.connect(on_waiting)
    signals.camera_ready.connect(on_ready)

    def camera_failed(message):
        toggle_act.setChecked(False)
        toggle_act.setEnabled(False)
        cal_act.setEnabled(False)
        if status_label is not None:
            status_label.setText("Lỗi camera: " + message)
        QMessageBox.warning(None, "Glance", message + "\nKiểm tra camera rồi mở lại Glance.")

    signals.camera_error.connect(camera_failed)

    # Start vision worker
    t = threading.Thread(target=controller.camera_worker, daemon=True)
    t.start()

    def shutdown():
        controller.stop()
        t.join(timeout=1.5)

    app.aboutToQuit.connect(shutdown)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
