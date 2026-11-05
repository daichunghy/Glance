"""
Glance for Linux
Privacy & Anti-Peeping Screen Guard for Ubuntu, Fedora, Arch, Debian
"""

import sys
import time
import threading
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QPainter, QIcon, QAction

class SignalEmitter(QObject):
    update_protection = pyqtSignal(str, float)  # side, alpha

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

class GlanceLinuxController:
    def __init__(self, overlay, signals):
        self.overlay = overlay
        self.signals = signals
        self.is_enabled = True
        self.blur_mode = "Side Blur"
        self.sensitivity_threshold = 18.0
        
        self.baseline_yaw = 0.0
        self.smoothed_yaw = 0.0
        self.is_looking_away = False
        self.running = True
        
        self.signals.update_protection.connect(self.overlay.set_protection)

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
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        no_face_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 4)
            
            if len(faces) > 0:
                no_face_count = 0
                x, y, w, h = faces[0]
                frame_center = frame.shape[1] / 2.0
                face_center = x + w / 2.0
                relative = (face_center - frame_center) / frame_center
                estimated_yaw = relative * 35.0 - self.baseline_yaw
                self.smoothed_yaw = (self.smoothed_yaw * 0.7) + (estimated_yaw * 0.3)
                self.process_face(self.smoothed_yaw, is_present=True)
            else:
                no_face_count += 1
                if no_face_count >= 6:
                    self.process_face(None, is_present=False)
                    
            time.sleep(0.12)
            
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
    tray = QSystemTrayIcon(QApplication.style().standardIcon(QApplication.Style().SP_ComputerIcon))
    tray.setToolTip("Glance Privacy Guard")
    
    menu = QMenu()
    toggle_act = QAction("Enable Glance", checkable=True)
    toggle_act.setChecked(True)
    toggle_act.toggled.connect(lambda val: setattr(controller, 'is_enabled', val))
    menu.addAction(toggle_act)
    
    cal_act = QAction("Calibrate Center", triggered=controller.calibrate)
    menu.addAction(cal_act)
    
    menu.addSeparator()
    quit_act = QAction("Quit Glance", triggered=app.quit)
    menu.addAction(quit_act)
    
    tray.setContextMenu(menu)
    tray.show()
    
    # Start vision worker
    t = threading.Thread(target=controller.camera_worker, daemon=True)
    t.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
