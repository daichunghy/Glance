"""
Glance for Linux
Privacy & Anti-Peeping Screen Guard for Ubuntu, Fedora, Arch, Debian
"""

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

from posture import PostureGuard

class SignalEmitter(QObject):
    camera_error = pyqtSignal(str)
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

    def calibrate_posture(self):
        if not self.posture_enabled:
            self._emit_posture_text("Tư thế: bật Cảnh báo tư thế trước khi căn chỉnh")
            return
        if self.posture_guard.calibrate():
            self._emit_posture_text("Tư thế: đã ghi tư thế chuẩn")
        else:
            self._emit_posture_text("Tư thế: chưa thấy khuôn mặt, hãy nhìn vào camera rồi thử lại")

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
            self._emit_posture_text(text)
            if result.just_triggered:
                self.signals.posture_warning.emit(text)
        elif result.status == "bad_pending":
            self._emit_posture_text("Tư thế: đang hơi sai, hãy ngồi thẳng lại")
        else:
            self._emit_posture_text("Tư thế: tốt")

    def process_face(self, yaw_degrees, is_present):
        if not self.is_enabled:
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
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("Không mở được camera mặc định.")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if face_cascade.empty():
                raise RuntimeError("Không tải được bộ nhận diện.")
            no_face_count = 0
            read_failures = 0

            while self.running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    read_failures += 1
                    if read_failures >= 5:
                        raise RuntimeError("Mất tín hiệu camera.")
                    time.sleep(0.1)
                    continue
                read_failures = 0

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

                time.sleep(0.12)

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
        for action in (toggle_act, cal_act, posture_act, posture_cal_act, quit_act):
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
