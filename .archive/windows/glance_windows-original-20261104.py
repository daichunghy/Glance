"""
Glance for Windows
Privacy & Anti-Peeping Screen Guard for Windows 10 & 11
"""

import sys
import time
import math
import threading
import ctypes
from ctypes import wintypes
import cv2
import numpy as np

# Win32 Constants
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
LWA_ALPHA = 0x00000002
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

class GlanceWindowsApp:
    def __init__(self):
        self.is_enabled = True
        self.blur_mode = "Side Blur"  # "Side Blur" or "Full Screen"
        self.sensitivity_threshold = 18.0  # degrees
        self.auto_away_blur = True
        
        self.current_yaw = 0.0
        self.baseline_yaw = 0.0
        self.smoothed_yaw = 0.0
        self.is_looking_away = False
        self.active_side = "none"  # "none", "left", "right", "full"
        self.is_away = False
        self.running = True
        
        # Win32 user32 & gdi32 bindings
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.dwm = ctypes.windll.dwmapi
        
        # Create overlay window
        self.hwnd = None
        self.setup_overlay_window()
        
    def get_idle_seconds(self):
        """Returns time in seconds since user last touched keyboard or mouse"""
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if self.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = self.kernel32.GetTickCount() - lii.dwTime
            return millis / 1000.0
        return 999.0

    def setup_overlay_window(self):
        """Creates a click-through, topmost borderless overlay covering all displays"""
        x = self.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        y = self.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        w = self.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        h = self.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        
        # Window class
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        def wnd_proc(hwnd, msg, wparam, lparam):
            return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        self._wnd_proc = WNDPROC(wnd_proc)
        
        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ('style', wintypes.UINT),
                ('lpfnWndProc', WNDPROC),
                ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int),
                ('hInstance', wintypes.HINSTANCE),
                ('hIcon', wintypes.HICON),
                ('hCursor', wintypes.HICON),
                ('hbrBackground', wintypes.HBRUSH),
                ('lpszMenuName', wintypes.LPCWSTR),
                ('lpszClassName', wintypes.LPCWSTR)
            ]
            
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = self.kernel32.GetModuleHandleW(None)
        wc.lpszClassName = "GlanceOverlayClass"
        self.user32.RegisterClassW(ctypes.byref(wc))
        
        ex_style = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
        self.hwnd = self.user32.CreateWindowExW(
            ex_style,
            wc.lpszClassName,
            "GlanceOverlay",
            WS_POPUP,
            x, y, w, h,
            None, None, wc.hInstance, None
        )
        
        # Initial transparent state
        self.set_overlay_alpha(0)
        self.user32.ShowWindow(self.hwnd, 5)  # SW_SHOW

    def set_overlay_alpha(self, alpha):
        if self.hwnd:
            self.user32.SetLayeredWindowAttributes(self.hwnd, 0, int(alpha), LWA_ALPHA)

    def process_face_orientation(self, yaw_degrees, is_face_present):
        if not self.is_enabled:
            self.active_side = "none"
            self.set_overlay_alpha(0)
            return

        release_threshold = max(5.0, self.sensitivity_threshold - 6.0)

        if is_face_present:
            self.is_away = False
            self.current_yaw = yaw_degrees
            
            if self.is_looking_away:
                if abs(yaw_degrees) < release_threshold:
                    self.is_looking_away = False
                    self.active_side = "none"
                    self.set_overlay_alpha(0)
                else:
                    # Swapping sides dynamically
                    if yaw_degrees > self.sensitivity_threshold:
                        self.active_side = "left" if self.blur_mode == "Side Blur" else "full"
                        self.set_overlay_alpha(225)
                    elif yaw_degrees < -self.sensitivity_threshold:
                        self.active_side = "right" if self.blur_mode == "Side Blur" else "full"
                        self.set_overlay_alpha(225)
            else:
                if yaw_degrees > self.sensitivity_threshold:
                    self.is_looking_away = True
                    self.active_side = "left" if self.blur_mode == "Side Blur" else "full"
                    self.set_overlay_alpha(225)
                elif yaw_degrees < -self.sensitivity_threshold:
                    self.is_looking_away = True
                    self.active_side = "right" if self.blur_mode == "Side Blur" else "full"
                    self.set_overlay_alpha(225)
        else:
            if self.auto_away_blur:
                self.is_away = True
                self.is_looking_away = True
                self.active_side = "full"
                self.set_overlay_alpha(240)

    def camera_loop(self):
        """Camera vision loop running on background thread"""
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # Load lightweight face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        no_face_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))
            
            if len(faces) > 0:
                no_face_count = 0
                x, y, w, h = faces[0]
                frame_center_x = frame.shape[1] / 2.0
                face_center_x = x + w / 2.0
                
                # Approximate relative yaw based on face position offset & camera geometry
                relative_offset = (face_center_x - frame_center_x) / frame_center_x
                estimated_yaw = relative_offset * 35.0 - self.baseline_yaw
                
                self.smoothed_yaw = (self.smoothed_yaw * 0.7) + (estimated_yaw * 0.3)
                self.process_face_orientation(self.smoothed_yaw, is_face_present=True)
            else:
                if self.get_idle_seconds() < 2.5:
                    # User is actively typing or moving mouse: do NOT trigger away blur
                    no_face_count = 0
                    self.process_face_orientation(0.0, is_face_present=True)
                else:
                    no_face_count += 1
                    if no_face_count >= 7:
                        self.process_face_orientation(None, is_face_present=False)
                        
            time.sleep(0.12)  # ~8 FPS to save battery & CPU
            
        cap.release()

    def calibrate(self):
        self.baseline_yaw = self.smoothed_yaw + self.baseline_yaw
        self.smoothed_yaw = 0.0
        self.process_face_orientation(0.0, is_face_present=True)
        print("[Glance] Calibrated center reference angle.")

    def run(self):
        t = threading.Thread(target=self.camera_loop, daemon=True)
        t.start()
        
        # Win32 Message Loop
        msg = wintypes.MSG()
        while self.running and self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

if __name__ == "__main__":
    app = GlanceWindowsApp()
    app.run()
