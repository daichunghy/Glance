"""
Glance for Linux
Privacy & Anti-Peeping Screen Guard for Ubuntu, Fedora, Arch, Debian
"""

import json
import os
import sys
import time
import threading
import cv2
from PyQt6.QtWidgets import (
    QApplication, QDialog, QMenu, QMessageBox, QStyle,
    QSystemTrayIcon, QToolButton, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QColor, QPainter, QAction

from posture import PostureGuard, frame_too_dark

class SignalEmitter(QObject):
    camera_error = pyqtSignal(str)
    camera_waiting = pyqtSignal(str)  # busy / blocked / disabled — not fatal
    update_protection = pyqtSignal(str, float)  # side, alpha
    posture_status = pyqtSignal(str)   # human-readable posture state
    posture_warning = pyqtSignal(str)  # emitted once per bad-posture episode

class GlanceOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.active_side = "none"
        self.alpha_val = 0.0
        
        # X11 / Wayland transparent, click-through, always-on-top flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Cover all connected screens
        screen_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geo)
        self.show()

    def set_protection(self, side, alpha):
        self.active_side = side
        self.alpha_val = alpha
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
            # Blur right half
            painter.fillRect(int(w * 0.45), 0, int(w * 0.55), h, color)

class GlanceLinuxController(QObject):
    def __init__(self, overlay, signals):
        super().__init__()
        self.overlay = overlay
        self.signals = signals
        self.is_enabled = True
        self.blur_mode = "Side Blur"
        self.sensitivity_threshold = 18.0
        
        self.baseline_yaw = 0.0
        self.smoothed_yaw = 0.0
        self.is_looking_away = False
        self.running = True

        # Posture guard (gù lưng / cổ rùa): opt-in, off by default, shares
        # the same camera frames. It never touches the overlay.
        self.posture_guard = PostureGuard()
        self.posture_enabled = False
        self._last_posture_text = None
        self.share_until = None
        self._last_dark_notice = 0.0
        self._load_posture_profile()

        self.signals.update_protection.connect(self.apply_protection)

    @pyqtSlot(str, float)
    def apply_protection(self, side, alpha):
        if self.is_enabled:
            self.overlay.set_protection(side, alpha)

    def set_enabled(self, enabled):
        self.is_enabled = enabled
        if not enabled:
            self.overlay.set_protection("none", 0.0)

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
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if face_cascade.empty():
                raise RuntimeError("Không tải được bộ nhận diện.")
            no_face_count = 0
            read_failures = 0
            last_state = None
            frame_wait = 0.12

            while self.running:
                # Protection off = camera truly released (LED off), not
                # merely ignored. Re-enabled -> reopened by this loop.
                if not self.is_enabled:
                    if cap is not None:
                        cap.release()
                        cap = None
                    time.sleep(0.4)
                    continue

                if cap is None:
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        # Busy (a call app holds it) or unplugged: wait and
                        # retry; Glance resumes by itself when it frees.
                        cap.release()
                        cap = None
                        if not busy_announced:
                            self.signals.camera_waiting.emit(
                                "Camera đang bận hoặc chưa sẵn sàng — Glance tự thử lại.")
                            busy_announced = True
                        time.sleep(3)
                        continue
                    busy_announced = False
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

                ret, frame = cap.read()
                if not ret or frame is None:
                    read_failures += 1
                    if read_failures >= 5:
                        cap.release()
                        cap = None
                        read_failures = 0
                    time.sleep(0.1)
                    continue
                read_failures = 0

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if frame_too_dark(float(gray.mean())):
                    # Covered camera / pitch-black room: hold everything.
                    now = time.monotonic()
                    if now - self._last_dark_notice > 10:
                        self._last_dark_notice = now
                        self.signals.camera_waiting.emit(
                            "Camera có vẻ bị che hoặc quá tối — Glance tạm đứng yên.")
                    time.sleep(0.12)
                    continue
                faces = face_cascade.detectMultiScale(gray, 1.2, 4)

                if len(faces) > 0:
                    no_face_count = 0
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    frame_center = frame.shape[1] / 2.0
                    face_center = x + w / 2.0
                    relative = (face_center - frame_center) / frame_center
                    estimated_yaw = relative * 35.0 - self.baseline_yaw
                    self.smoothed_yaw = (self.smoothed_yaw * 0.7) + (estimated_yaw * 0.3)
                    self.process_face(self.smoothed_yaw, is_present=True)
                    self.process_posture(self.posture_guard.update(
                        time.monotonic(), True,
                        face_size=w / frame.shape[1],
                        center_y=(y + h / 2) / frame.shape[0]))
                else:
                    self.process_posture(self.posture_guard.update(time.monotonic(), False))
                    no_face_count += 1
                    if no_face_count >= 6:
                        self.process_face(None, is_present=False)

                # Battery-aware sampling: stretch toward ~3 FPS while the
                # scene is stable, snap back to ~8 FPS on any change.
                state = (len(faces) > 0, self.is_looking_away)
                if state == last_state:
                    frame_wait = min(0.30, frame_wait * 1.5)
                else:
                    frame_wait = 0.12
                    last_state = state
                time.sleep(frame_wait)

        except (RuntimeError, cv2.error) as exc:
            self.signals.camera_error.emit(str(exc))
        finally:
            if cap is not None:
                cap.release()

    def calibrate(self):
        self.baseline_yaw = self.smoothed_yaw + self.baseline_yaw
        self.smoothed_yaw = 0.0
        self.process_face(0.0, is_present=True)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    overlay = GlanceOverlay()
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

    signals.camera_waiting.connect(lambda text: tray.setToolTip("Glance — " + text))

    menu.addSeparator()
    quit_act = QAction("Thoát Glance", triggered=app.quit)
    menu.addAction(quit_act)
    
    tray.setContextMenu(menu)
    panel = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()
    else:
        panel = QDialog()
        panel.setWindowTitle("Glance")
        panel.resize(320, 230)
        layout = QVBoxLayout(panel)
        for action in (toggle_act, cal_act, posture_act, posture_cal_act,
                       posture_dismiss_act, posture_snooze_act, share_act, quit_act):
            button = QToolButton(panel)
            button.setDefaultAction(action)
            layout.addWidget(button)
        panel.finished.connect(app.quit)
        panel.show()
    
    def camera_failed(message):
        toggle_act.setChecked(False)
        toggle_act.setEnabled(False)
        cal_act.setEnabled(False)
        QMessageBox.warning(None, "Glance", message + "\nKiểm tra camera rồi mở lại Glance.")

    signals.camera_error.connect(camera_failed)
    app.aboutToQuit.connect(lambda: setattr(controller, "running", False))

    # Start vision worker
    t = threading.Thread(target=controller.camera_worker, daemon=True)
    t.start()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
