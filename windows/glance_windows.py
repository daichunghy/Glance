"""Glance for Windows. Camera frames are processed locally and never saved."""
import ctypes
from ctypes import wintypes
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import traceback
from tkinter import ttk

import cv2
from guard import PresenceGuard, camera_is_stale
from posture import PostureGuard, frame_too_dark


if sys.platform != "win32":
    raise SystemExit("Glance for Windows cần Windows 10 hoặc Windows 11.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except (OSError, AttributeError):
    user32.SetProcessDPIAware()

user32.GetParent.argtypes = [wintypes.HWND]
user32.GetParent.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
kernel32.GetTickCount.restype = wintypes.DWORD

if ctypes.sizeof(ctypes.c_void_p) == 8:
    get_style = user32.GetWindowLongPtrW
    set_style = user32.SetWindowLongPtrW
    style_type = ctypes.c_ssize_t
else:
    get_style = user32.GetWindowLongW
    set_style = user32.SetWindowLongW
    style_type = ctypes.c_long
get_style.argtypes = [wintypes.HWND, ctypes.c_int]
get_style.restype = style_type
set_style.argtypes = [wintypes.HWND, ctypes.c_int, style_type]
set_style.restype = style_type


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Glance")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CAMERA_ERROR_PATH = os.path.join(CONFIG_DIR, "camera-error.log")


def record_camera_error():
    """Save diagnostic details locally without recording camera frames."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CAMERA_ERROR_PATH, "w", encoding="utf-8") as log:
            traceback.print_exc(file=log)
    except OSError:
        pass


def open_camera(index):
    """Try Windows camera backends independently when one cannot open a device."""
    for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
        capture = None
        try:
            capture = cv2.VideoCapture(index, backend)
            if capture is not None and capture.isOpened():
                return capture
        except cv2.error:
            pass
        if capture is not None:
            capture.release()
    return None


def load_face_detector():
    cascade_name = "haarcascade_frontalface_default.xml"
    candidates = []
    if hasattr(cv2, "data") and getattr(cv2.data, "haarcascades", None):
        candidates.append(os.path.join(cv2.data.haarcascades, cascade_name))
    if getattr(sys, "_MEIPASS", None):
        candidates.append(os.path.join(sys._MEIPASS, "cv2", "data", cascade_name))
        candidates.append(os.path.join(sys._MEIPASS, cascade_name))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), cascade_name))
    path = next((candidate for candidate in candidates if os.path.exists(candidate)), None)
    if path is None:
        raise FileNotFoundError("Face detection model is missing")
    detector = cv2.CascadeClassifier(path)
    if detector.empty():
        raise RuntimeError("Face detection model could not be loaded")
    return detector


def load_config():
    defaults = {
        "camera": 0,
        "delay": 5,
        "opacity": 90,
        "activity": True,
        "autostart": False,
        "auto_camera": False,
        "minimize_on_close": True,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update({k: v for k, v in data.items() if k in defaults})
        except Exception:
            pass
    return defaults


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_launch_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    python_exe = sys.executable
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    runner = pythonw if os.path.exists(pythonw) else python_exe
    script = os.path.abspath(__file__)
    return f'"{runner}" "{script}" --startup'


def set_windows_autostart(enable: bool) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, "Glance", 0, winreg.REG_SZ, get_launch_command())
            else:
                try:
                    winreg.DeleteValue(key, "Glance")
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def get_windows_autostart() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, "Glance")
            return bool(val)
    except Exception:
        return False


class LastInputInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds():
    info = LastInputInfo(ctypes.sizeof(LastInputInfo), 0)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0  # Do not assume inactivity if the OS cannot provide it.
    return ((kernel32.GetTickCount() - info.dwTime) & 0xffffffff) / 1000


class _Rect(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def foreground_is_fullscreen():
    """True when another app fills the screen (slideshow, video, game).

    During presentations and fullscreen media the privacy cover must not
    pop up; the desktop shell itself does not count as fullscreen.
    """
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        class_name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, class_name, 64)
        if class_name.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
            return False
        rect = _Rect()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return (rect.left <= 0 and rect.top <= 0
                and rect.right >= width and rect.bottom >= height)
    except (OSError, AttributeError):
        return False


class ScreenCover:
    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(background="#08090c")
        self.window.attributes("-topmost", True)
        self.visible = False
        self.bounds = None

    def update(self, visible, opacity):
        if not visible:
            if self.visible:
                self.window.withdraw()
                self.visible = False
            return
        self.window.attributes("-alpha", opacity / 100)
        bounds = tuple(user32.GetSystemMetrics(i) for i in (76, 77, 78, 79))
        if not self.visible:
            self.window.deiconify()
            self.window.update_idletasks()
            hwnd = user32.GetParent(self.window.winfo_id()) or self.window.winfo_id()
            # Click through, remain out of Alt-Tab, and do not activate the overlay.
            current_style = get_style(hwnd, -20)
            ctypes.set_last_error(0)
            previous_style = set_style(hwnd, -20, current_style | 0x20 | 0x80 | 0x08000000)
            if previous_style == 0 and ctypes.get_last_error() != 0:
                self.window.withdraw()
                self.visible = False
                self.bounds = None
                raise OSError("Windows không thiết lập được lớp che")
            self.visible = True
            self.bounds = None
        if bounds != self.bounds:
            hwnd = user32.GetParent(self.window.winfo_id()) or self.window.winfo_id()
            x, y, width, height = bounds
            if width <= 0 or height <= 0 or not user32.SetWindowPos(
                    hwnd, wintypes.HWND(-1), x, y, width, height, 0x0010 | 0x0040):
                self.window.withdraw()
                self.visible = False
                self.bounds = None
                raise OSError("Windows không đặt được lớp che màn hình")
            self.bounds = bounds


class App:
    def __init__(self, root):
        self.root = root
        root.title("Glance")
        root.configure(bg="#08090c")
        root.geometry("520x860")
        root.minsize(480, 760)
        root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.cover = ScreenCover(root)
        self.events = queue.Queue(maxsize=1)
        self.stop_event = None
        self.worker = None
        self.generation = 0
        self.manual = False
        self.automatic_cover = False
        self.camera_started_at = None
        self.last_frame_at = None
        self.controls_topmost = False
        self.status = tk.StringVar(value="Chưa bật camera. Màn hình chưa được che tự động.")
        
        cfg = load_config()
        self.camera = tk.IntVar(value=cfg.get("camera", 0))
        self.delay = tk.IntVar(value=cfg.get("delay", 5))
        self.opacity = tk.IntVar(value=cfg.get("opacity", 90))
        self.activity = tk.BooleanVar(value=cfg.get("activity", True))
        
        is_registered = get_windows_autostart()
        self.autostart = tk.BooleanVar(value=is_registered if sys.platform == "win32" else cfg.get("autostart", False))
        self.auto_camera = tk.BooleanVar(value=cfg.get("auto_camera", False))
        self.minimize_on_close = tk.BooleanVar(value=cfg.get("minimize_on_close", True))

        # Posture guard (gù lưng / cổ rùa): opt-in, off by default, shares the
        # same camera frames. It never covers the screen.
        self.posture_enabled = tk.BooleanVar(value=False)
        self.posture_status = tk.StringVar(value="Tư thế: đang tắt.")
        self.posture_guard = PostureGuard()
        self.share_until = None
        self.presentation_mode = False
        # Saved posture calibrations, one per camera, under ~/.glance/
        self._profiles = self._load_profiles()
        self._apply_profile_for_camera(self.camera.get())
        self.make_ui()
        self.root.after(120, self.poll)

        is_startup = "--startup" in sys.argv or "--minimized" in sys.argv
        if is_startup:
            self.root.iconify()
        if self.auto_camera.get() or is_startup:
            self.root.after(400, self.toggle_camera)

    def persist_settings(self):
        try:
            cfg = {
                "camera": self.camera.get(),
                "delay": self.delay.get(),
                "opacity": self.opacity.get(),
                "activity": self.activity.get(),
                "autostart": self.autostart.get(),
                "auto_camera": self.auto_camera.get(),
                "minimize_on_close": self.minimize_on_close.get(),
            }
            save_config(cfg)
        except Exception:
            pass

    def on_autostart_changed(self):
        set_windows_autostart(self.autostart.get())
        self.persist_settings()

    def on_window_close(self):
        self.persist_settings()
        # Nếu cửa sổ đang mở bình thường thì thu nhỏ xuống Taskbar; nếu người dùng đóng khi đã thu nhỏ thì tắt hẳn.
        if self.minimize_on_close.get() and self.root.state() != "iconic":
            self.root.iconify()
        else:
            self.close()

    def exit_app(self):
        self.persist_settings()
        self.close()

    def make_ui(self):
        bg, fg, muted, blue = "#08090c", "#f5f5f7", "#adb8c7", "#0071e3"
        body = tk.Frame(self.root, bg=bg, padx=26, pady=20)
        body.pack(fill="both", expand=True)

        def label(text, size=11, color=fg, bold=False):
            return tk.Label(body, text=text, bg=bg, fg=color, anchor="w", justify="left",
                            wraplength=460, font=("Calibri", size, "bold" if bold else "normal"))

        label("Glance", 22, bold=True).pack(fill="x")
        label("Che màn hình khi bạn rời bàn", 12, muted).pack(fill="x", pady=(0, 14))
        
        tk.Label(body, textvariable=self.status, bg="#19212b", fg="#b9d9ff", anchor="w",
                 justify="left", wraplength=440, padx=14, pady=10,
                 font=("Calibri", 11)).pack(fill="x", pady=(0, 14))

        self.start_button = tk.Button(body, text="Bật camera", command=self.toggle_camera,
                                      bg=blue, fg="white", activebackground="#1884ee",
                                      activeforeground="white", relief="flat", padx=18, pady=8,
                                      font=("Calibri", 11, "bold"))
        self.start_button.pack(fill="x")

        self.manual_button = tk.Button(body, text="Che màn hình ngay", command=self.toggle_manual,
                                       bg="#242d39", fg=fg, activebackground="#334254",
                                       activeforeground="white", relief="flat", padx=18, pady=8,
                                       font=("Calibri", 11))
        self.manual_button.pack(fill="x", pady=(8, 0))
        self.share_button = tk.Button(body, text="Hiện màn hình 2 phút (cho người bên cạnh xem)", command=self.start_share,
                                      bg="#242d39", fg=fg, activebackground="#334254",
                                      activeforeground="white", relief="flat", padx=18, pady=8,
                                      font=("Calibri", 11))
        self.share_button.pack(fill="x", pady=(8, 12))
        row = tk.Frame(body, bg=bg)
        row.pack(fill="x", pady=2)
        tk.Label(row, text="Camera", bg=bg, fg=fg, font=("Calibri", 11)).pack(side="left")
        tk.Spinbox(row, from_=0, to=9, textvariable=self.camera, width=4,
                   font=("Calibri", 11), state="readonly", command=self.persist_settings).pack(side="right")

        row = tk.Frame(body, bg=bg)
        row.pack(fill="x", pady=2)
        tk.Label(row, text="Thời gian chờ khi không thấy mặt", bg=bg, fg=fg,
                 font=("Calibri", 11)).pack(side="left")
        cb = ttk.Combobox(row, textvariable=self.delay, values=(3, 5, 10, 20, 30),
                          state="readonly", width=4)
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda e: self.persist_settings())

        label("Giây. Đổi camera hoặc thời gian chờ sau khi tắt camera.", 10, muted).pack(fill="x")

        tk.Checkbutton(body, text="Không che khi đang dùng chuột hoặc bàn phím", variable=self.activity,
                       command=self.persist_settings, bg=bg, fg=fg, selectcolor="#242d39",
                       activebackground=bg, activeforeground=fg, anchor="w", font=("Calibri", 11)).pack(fill="x", pady=(8, 2))

        tk.Checkbutton(body, text="Khởi động cùng Windows (Tự động chạy khi bật máy)",
                       variable=self.autostart, command=self.on_autostart_changed,
                       bg=bg, fg=fg, selectcolor="#242d39", activebackground=bg,
                       activeforeground=fg, anchor="w", font=("Calibri", 11)).pack(fill="x", pady=2)

        tk.Checkbutton(body, text="Tự động bật camera bảo vệ khi khởi động",
                       variable=self.auto_camera, command=self.persist_settings,
                       bg=bg, fg=fg, selectcolor="#242d39", activebackground=bg,
                       activeforeground=fg, anchor="w", font=("Calibri", 11)).pack(fill="x", pady=2)

        tk.Checkbutton(body, text="Thu nhỏ xuống thanh Taskbar khi bấm đóng (X)",
                       variable=self.minimize_on_close, command=self.persist_settings,
                       bg=bg, fg=fg, selectcolor="#242d39", activebackground=bg,
                       activeforeground=fg, anchor="w", font=("Calibri", 11)).pack(fill="x", pady=2)

        tk.Checkbutton(body, text="Cảnh báo tư thế: gù lưng, cổ rùa (cần bật camera)", variable=self.posture_enabled,
                       command=self.toggle_posture, bg=bg, fg=fg, selectcolor="#242d39", activebackground=bg,
                       activeforeground=fg, anchor="w", font=("Calibri", 11)).pack(fill="x", pady=(6, 0))
        tk.Label(body, textvariable=self.posture_status, bg=bg, fg=muted, anchor="w",
                 justify="left", wraplength=440, font=("Calibri", 10)).pack(fill="x")
        self.posture_button = tk.Button(body, text="Căn chỉnh tư thế chuẩn", command=self.calibrate_posture,
                                        bg="#242d39", fg=fg, activebackground="#334254",
                                        activeforeground="white", relief="flat", padx=18, pady=6,
                                        font=("Calibri", 11))
        self.posture_button.pack(fill="x", pady=(4, 0))
        prow = tk.Frame(body, bg=bg)
        prow.pack(fill="x", pady=(6, 0))
        tk.Button(prow, text="Không phải tư thế xấu", command=self.dismiss_posture,
                  bg="#242d39", fg=fg, activebackground="#334254", activeforeground="white",
                  relief="flat", padx=10, pady=5, font=("Calibri", 10)).pack(side="left", fill="x", expand=True)
        tk.Button(prow, text="Tạm tắt nhắc 30 phút", command=self.snooze_posture,
                  bg="#242d39", fg=fg, activebackground="#334254", activeforeground="white",
                  relief="flat", padx=10, pady=5, font=("Calibri", 10)).pack(side="left", fill="x", expand=True, padx=(8, 0))

        label("Mức che", 11).pack(fill="x", pady=(6, 0))
        scale = tk.Scale(body, variable=self.opacity, from_=60, to=95, orient="horizontal", bg=bg,
                         fg=fg, highlightthickness=0, troughcolor="#242d39", activebackground=blue,
                         font=("Calibri", 10))
        scale.pack(fill="x")
        scale.bind("<ButtonRelease-1>", lambda e: self.persist_settings())

        label("Lớp che làm tối màn hình. Khi camera lỗi, tính năng tự động sẽ dừng.", 10, muted).pack(fill="x", pady=(4, 0))

        footer = tk.Frame(body, bg=bg)
        footer.pack(fill="x", pady=(12, 0))
        tk.Button(footer, text="Mở quyền camera trong Windows", command=self.open_camera_settings,
                  bg=bg, fg="#78b8ff", activebackground=bg, activeforeground="white",
                  relief="flat", anchor="w", padx=0, font=("Calibri", 10)).pack(side="left")
        tk.Button(footer, text="Thoát Glance", command=self.exit_app,
                  bg=bg, fg="#adb8c7", activebackground=bg, activeforeground="#ff6b6b",
                  relief="flat", anchor="e", padx=0, font=("Calibri", 10)).pack(side="right")

    def open_camera_settings(self):
        os.startfile("ms-settings:privacy-webcam")

    def toggle_manual(self):
        self.manual = not self.manual
        self.manual_button.configure(text="Bỏ che thủ công" if self.manual else "Che màn hình ngay")
        self.refresh_cover()

    def toggle_posture(self):
        if self.posture_enabled.get():
            if self.posture_guard.is_calibrated:
                self.posture_status.set("Tư thế: đã có căn chỉnh lưu sẵn cho camera này — đang theo dõi.")
            else:
                self.posture_status.set("Tư thế: hãy ngồi thẳng, nhìn thẳng vào màn hình rồi bấm Căn chỉnh tư thế chuẩn.")
        else:
            self.posture_guard.reset_timers()
            self.posture_status.set("Tư thế: đang tắt.")

    # -- posture profile persistence --------------------------------------
    @staticmethod
    def _profiles_path():
        folder = os.path.join(os.path.expanduser("~"), ".glance")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "posture_profiles.json")

    def _load_profiles(self):
        try:
            with open(self._profiles_path(), encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _apply_profile_for_camera(self, index):
        saved = self._profiles.get("cameras", {}).get(str(index))
        if saved:
            self.posture_guard.import_profile(saved)

    def _save_profile_for_camera(self):
        profile = self.posture_guard.export_profile()
        if profile is None:
            return
        self._profiles.setdefault("cameras", {})[str(self.camera.get())] = profile
        try:
            with open(self._profiles_path(), "w", encoding="utf-8") as fh:
                json.dump(self._profiles, fh)
        except OSError:
            pass

    def calibrate_posture(self):
        if not self.posture_enabled.get():
            self.posture_status.set("Tư thế: bật Cảnh báo tư thế trước khi căn chỉnh.")
            return
        if self.posture_guard.calibrate():
            self._save_profile_for_camera()
            self.posture_status.set("Tư thế: đã ghi tư thế chuẩn (đã lưu cho camera này, lần sau mở app không cần căn chỉnh lại). Glance sẽ nhắc nếu bạn gù lưng hoặc cổ rùa liên tục 10 giây.")
        else:
            self.posture_status.set("Tư thế: chưa thấy khuôn mặt. Hãy bật camera, ngồi thẳng và nhìn vào màn hình rồi thử lại.")

    def apply_posture_result(self, result):
        if not self.posture_enabled.get():
            return
        if result.status == "uncalibrated":
            text = "Tư thế: chưa căn chỉnh. Ngồi thẳng rồi bấm Căn chỉnh tư thế chuẩn."
        elif result.status == "no_face":
            text = "Tư thế: chưa thấy khuôn mặt nên tạm dừng kiểm tra."
        elif result.status == "warning":
            names = []
            if "turtle_neck" in result.kinds:
                names.append("cổ rùa (đầu đưa ra trước)")
            if "hunch" in result.kinds:
                names.append("gù lưng (đầu sụp xuống)")
            text = "Tư thế: hãy ngồi thẳng lại — đang " + " và ".join(names) + "."
            if result.suggest_break:
                text += " Nhắc nhiều rồi — thử đứng dậy giãn người 1 phút."
            elif result.just_triggered and self.posture_guard.total_warnings <= 3:
                text += " (Mấy lần đầu nhắc chưa chuẩn là bình thường — bấm 'Không phải tư thế xấu' để Glance học theo bạn.)"
        elif result.status == "bad_pending":
            text = "Tư thế: đang hơi sai, hãy ngồi thẳng lại."
        elif result.status == "snoozed":
            text = "Tư thế: đang tạm tắt nhắc 30 phút."
        else:
            text = "Tư thế: tốt."
        if self.posture_status.get() != text:
            self.posture_status.set(text)

    def start_share(self):
        """Deliberately show the screen to someone next to you for 2 min."""
        self.share_until = time.monotonic() + 120
        self.automatic_cover = False
        self.refresh_cover()
        self.status.set("Đang hiện màn hình cho người bên cạnh xem — tự bảo vệ lại sau 2 phút.")

    def dismiss_posture(self):
        self.posture_guard.dismiss_as_not_bad(time.monotonic())
        self._save_profile_for_camera()
        self.posture_status.set("Tư thế: đã ghi nhận. Glance sẽ bớt nhạy hơn một chút; nhắc lại nếu cần.")

    def snooze_posture(self):
        self.posture_guard.snooze(time.monotonic())
        self.posture_status.set("Tư thế: đã tạm tắt nhắc 30 phút.")

    def _share_active(self):
        until = getattr(self, "share_until", None)
        return until is not None and time.monotonic() < until

    def refresh_cover(self):
        sharing = self._share_active()
        fullscreen_fn = globals().get("foreground_is_fullscreen")
        presenting = bool(fullscreen_fn and fullscreen_fn())
        self.presentation_mode = presenting
        try:
            self.cover.update(not sharing and not presenting
                              and (self.manual or self.automatic_cover), self.opacity.get())
        except OSError:
            self.generation += 1
            if self.stop_event:
                self.stop_event.set()
            self.manual = False
            self.automatic_cover = False
            self.camera_started_at = None
            self.last_frame_at = None
            self.start_button.configure(text="Bật camera")
            self.manual_button.configure(text="Che màn hình ngay")
            self.status.set("Không thể che màn hình. Tính năng tự động đã dừng; hãy thử lại.")
        active = not sharing and not presenting and (self.manual or self.automatic_cover)
        if active != self.controls_topmost:
            self.root.attributes("-topmost", active)
            self.controls_topmost = active
            if active:
                self.root.lift()

    def toggle_camera(self):
        if self.worker and self.worker.is_alive():
            if self.stop_event and self.stop_event.is_set():
                self.status.set("Đang giải phóng camera. Vui lòng chờ rồi bật lại.")
            else:
                self.stop_camera()
            return
        self.generation += 1
        generation = self.generation
        self._apply_profile_for_camera(self.camera.get())
        self.stop_event = threading.Event()
        self.camera_started_at = time.monotonic()
        self.last_frame_at = None
        self.status.set("Đang mở camera…")
        self.start_button.configure(text="Tắt camera")
        self.worker = threading.Thread(target=self.camera_loop,
                                       args=(generation, self.stop_event, self.camera.get(),
                                             self.delay.get()), daemon=True)
        self.worker.start()

    def stop_camera(self):
        self.generation += 1
        if self.stop_event:
            self.stop_event.set()
        self.posture_guard.reset_timers()
        self.automatic_cover = False
        self.camera_started_at = None
        self.last_frame_at = None
        self.refresh_cover()
        self.status.set("Đã tắt camera. Màn hình chưa được che tự động.")
        self.start_button.configure(text="Bật camera")
        # The device may still be releasing; disallow a second worker until it finishes.

    def publish(self, generation, kind, value=None):
        item = (generation, kind, value)
        try:
            self.events.put_nowait(item)
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            self.events.put_nowait(item)

    def camera_loop(self, generation, stop, index, delay):
        cap = None
        try:
            detector = load_face_detector()
            cap = open_camera(index)
            while cap is None and not stop.is_set():
                # Each retry refreshes the watchdog while waiting for a device.
                self.publish(generation, "busy", index)
                if stop.wait(3):
                    return
                cap = open_camera(index)
            if stop.is_set():
                return
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            guard = PresenceGuard(delay=delay)
            posture_guard = self.posture_guard
            failures = 0
            last_state = None
            wait_seconds = 0.12
            while not stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    failures += 1
                    if failures >= 5:
                        self.publish(generation, "error", "Mất tín hiệu camera. Tính năng tự động đã dừng.")
                        return
                    stop.wait(0.2)
                    continue
                failures = 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if frame_too_dark(float(gray.mean())):
                    # Covered camera / pitch-black room: hold everything,
                    # never cover or nag on "no face" we cannot verify.
                    self.publish(generation, "blocked", None)
                    stop.wait(0.12)
                    continue
                faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))
                now = time.monotonic()
                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    posture = posture_guard.update(now, True,
                                                   face_size=w / frame.shape[1],
                                                   center_y=(y + h / 2) / frame.shape[0])
                else:
                    posture = posture_guard.update(now, False)
                self.publish(generation, "face", (len(faces) > 0, now, guard, posture))
                # Battery-aware sampling: while nothing changes (present +
                # good posture, or steadily absent) stretch the interval
                # from ~8 FPS toward ~3 FPS; any change snaps it back.
                state = (len(faces) > 0, posture.status)
                if state == last_state:
                    wait_seconds = min(0.30, wait_seconds * 1.5)
                else:
                    wait_seconds = 0.12
                    last_state = state
                stop.wait(wait_seconds)
        except Exception:
            record_camera_error()
            self.publish(generation, "error", "Camera gặp lỗi. Tính năng tự động đã dừng. "
                         "Thông tin lỗi được lưu tại %APPDATA%\\Glance\\camera-error.log.")
        finally:
            if cap is not None:
                cap.release()

    def poll(self):
        try:
            while True:
                generation, kind, value = self.events.get_nowait()
                if generation != self.generation:
                    continue
                if kind == "error":
                    self.automatic_cover = False
                    self.camera_started_at = None
                    self.last_frame_at = None
                    self.status.set(value)
                    self.start_button.configure(text="Bật camera")
                elif kind == "busy":
                    self.last_frame_at = time.monotonic()
                    self.status.set(f"Không mở được camera {value}. Kiểm tra quyền camera, "
                                    "đóng ứng dụng đang dùng camera hoặc thử camera 0. Glance đang thử lại.")
                elif kind == "blocked":
                    self.last_frame_at = time.monotonic()
                    self.automatic_cover = False
                    self.status.set("Camera có vẻ bị che hoặc quá tối — Glance tạm đứng yên, không che màn hình.")
                elif kind == "face":
                    present, observed_at, guard, posture = value
                    self.last_frame_at = observed_at
                    guard.activity_guard = self.activity.get()
                    self.automatic_cover = guard.update(observed_at, present, idle_seconds())
                    self.apply_posture_result(posture)
                    if present:
                        self.status.set("Camera đang hoạt động. Đã nhận diện khuôn mặt.")
                    elif self.automatic_cover:
                        self.status.set("Không thấy khuôn mặt. Đang che màn hình.")
                    else:
                        self.status.set("Camera đang hoạt động. Chưa thấy khuôn mặt.")
        except queue.Empty:
            pass
        if self.camera_started_at is not None:
            now = time.monotonic()
            last = self.last_frame_at if self.last_frame_at is not None else self.camera_started_at
            timeout = 5 if self.last_frame_at is not None else 15
            if camera_is_stale(now, last, timeout):
                self.stop_camera()
                self.status.set("Camera không phản hồi. Tính năng tự động đã dừng; hãy kiểm tra camera rồi bật lại.")
        self.refresh_cover()
        self.root.after(120, self.poll)

    def close(self):
        self.persist_settings()
        if self.stop_event:
            self.stop_event.set()
        self.cover.window.destroy()
        self.root.destroy()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        import numpy as np
        load_face_detector().detectMultiScale(np.zeros((64, 64), dtype=np.uint8))
    else:
        App(tk.Tk()).root.mainloop()
