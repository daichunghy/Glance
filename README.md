# Glance

<img src="docs/images/glance-icon.png" alt="Glance app icon" width="96">

Glance blurs or covers your screen when you look away or leave your desk, and clears it when you come back. It is meant for cafés, open offices and other places where someone standing behind you can read your screen. It does the job of a stick-on privacy filter in software, so your screen stays at full brightness and color while you are looking at it.

Glance runs on macOS, Windows and Linux. All processing happens on your own machine.

## How it works

Each build reads frames from the webcam at low resolution and looks for a face rectangle. macOS uses the Vision framework (`VNDetectFaceRectanglesRequest`). The Windows and Linux builds use the OpenCV Haar cascade at 320 pixels wide and about 8 frames per second, slowing down when nothing in the scene changes.

A face rectangle gives two things: whether you are there, and roughly where your head points. A small state machine turns that into three states: present, looking away, and away. Looking away triggers the blur overlay (on macOS you can blur one side or the whole screen). Away triggers a full cover. Coming back clears both.

On Windows the decision sits in `PresenceGuard` in `windows/guard.py`. It is plain Python with no camera or UI code, so it can be unit tested on its own:

```python
    def update(self, now, face_present, idle_seconds):
        if face_present or (self.activity_guard and idle_seconds < 2.5):
            self.reset()
            return False
        if self.absent_since is None:
            self.absent_since = now
        return now - self.absent_since >= self.delay


def camera_is_stale(now, last_frame_at, timeout=5):
    return now - last_frame_at >= timeout
```

The delay defaults to 3 seconds, so a quick glance sideways does not cover the screen. Recent mouse or keyboard activity also counts as being present.

On macOS you can skip the camera. AirPods with head tracking (Pro, 3, 4 and Max) report head motion through CoreMotion, and Glance can follow head turns from that instead.

## Privacy

Frames are processed in memory and thrown away. The code keeps a few geometry numbers in RAM, such as face width as a fraction of frame width, and nothing else. Face detection returns rectangles. It never works out who a face belongs to, and there is no enrollment step.

Turning Glance off stops the camera capture, and the camera light goes off with it. If another app is using the camera, for example a video call, Glance waits and tries again later instead of taking the camera over. If the camera is covered or the room is too dark, Glance does nothing: not seeing you is not treated as you being away. On macOS, the shortcut Option+Shift+S shows the screen for 2 minutes when you want to share it with the person next to you, then protection resumes on its own.

## Repository layout

```text
Glance/
├── macos/          native macOS app (Swift 6, AppKit, Vision, CoreMotion)
├── windows/        Windows app in Python (OpenCV, Win32)
├── linux/          Linux app in Python (PyQt6, OpenCV)
├── posture/        shared Posture Guard spec, POSTURE_SPEC.md
├── landing-page/   source of the website at glance-privacy.vercel.app
├── server/         donation endpoints used by the website
├── licensing/      license key code in Swift and Python
├── docs/           images used in this README
├── DESIGN.md
├── DESIGN_REFERENCES.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## Build and run

### macOS

Needs macOS 13 or later (Universal binary: Apple silicon & Intel; AirPods head tracking requires macOS 14 or later) and Swift 6. The build script compiles a release Universal build, assembles `Glance.app` and `Glance-macOS.zip` in the same folder, and signs it ad hoc.

```bash
cd macos
./build_app.sh
```

Open `Glance.app` and allow camera access when macOS asks. Glance lives in the menu bar.

### Windows

Needs Python 3.11 or 3.12. From the `windows` folder:

```powershell
py -3 -m pip install -r requirements.txt
py -3 glance_windows.py
```

Pick a camera in the window and press the button to turn the camera on. If the default camera does not work, try another index and check that Windows allows desktop apps to use the camera.

### Linux

From the `linux` folder:

```bash
python3 -m pip install -r requirements.txt
python3 glance_linux.py
```

`./build_linux.sh` in the same folder packages a single file binary with PyInstaller and puts it in `dist/`.

## Posture Guard

Posture Guard watches for two habits while you work: head pushed forward toward the screen (turtle neck) and head dropped down (hunching). It reuses the same camera frames as the privacy cover and adds no new libraries.

The policy lives in `posture.py`. That file is byte for byte identical in `windows/` and `linux/`, and the macOS build mirrors it in `PostureGuard.swift`. The policy takes plain geometry as input: face width divided by frame width, the vertical position of the face center, and head pitch on macOS where Vision provides it. Measurements are smoothed with an exponential moving average and compared against a baseline you set by sitting up straight and pressing the calibrate button.

Calibration is stored per camera, because a laptop camera and an external webcam see you from different angles. Windows keeps profiles in `~/.glance/posture_profiles.json`, Linux in `~/.glance/posture.json`, and macOS in UserDefaults. Only the baseline numbers are stored.

| Setting | Default |
| --- | --- |
| Time in bad posture before a warning | 10 seconds |
| Warning clears after good posture | 3 seconds |
| Cooldown after a warning | 60 seconds, then 120, then 300 for repeats within an hour |
| Snooze | 30 minutes |
| Dark frame cutoff | mean brightness below 15 of 255 counts as covered or too dark |

If a warning is wrong, the "not bad posture" button clears it and widens every threshold by 10 percent, up to 1.5 times the original values, so the guard adjusts to how you actually sit. After the third warning within an hour it suggests a short break. Posture Guard is off by default, and Glance is not a medical device. It is a reminder, nothing more.

Run the Python tests from inside the platform folder:

```powershell
cd windows
py -3 -m unittest discover -s tests
```

```bash
cd linux
python3 -m unittest discover -s tests
```

Windows currently passes 28 tests (posture, presence guard and screen cover). Linux passes 19 (posture). The macOS test file at `macos/Tests/igfTests/PostureGuardTests.swift` uses the same cases as the Python posture tests.

## Project status

The macOS build is the most complete of the three. It is a native menu bar app with camera and AirPods input, side or full screen blur, and the share mode shortcut. The Windows and Linux builds run from source and have not been verified on real hardware yet, so expect rough edges there. Posture Guard code is in `main` on all three platforms but is not in a stable release. There are no packaged downloads yet.

## Roadmap

- First stable release on macOS
- Windows and Linux verified on real hardware
- Posture Guard in a stable release
- Signed and notarized macOS build

## Support

Glance is free. There is no paid version and no account to create. If you want to chip in, the website at [glance-privacy.vercel.app](https://glance-privacy.vercel.app) accepts voluntary contributions through PayOS.

Glance miễn phí. Nếu bạn muốn ủng hộ, trang web glance-privacy.vercel.app có nhận đóng góp tự nguyện qua PayOS, cỡ một ly cà phê.

## Contributing and security

Bug reports from real machines are welcome, especially for Windows and Linux. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before sending a change. For anything security related, read [SECURITY.md](SECURITY.md) instead of opening a public issue.

## License

MIT. Copyright 2026 Chung Hy Dai. See [LICENSE](LICENSE).

## Tóm tắt tiếng Việt

Glance là phần mềm chống nhìn trộm màn hình cho macOS, Windows và Linux. Khi bạn quay mặt đi hoặc rời bàn, Glance làm mờ hoặc che màn hình, và mở lại khi bạn quay lại. Mọi xử lý đều chạy trên máy của bạn: khung hình không được lưu, không được gửi đi đâu, và camera chỉ đo vị trí khuôn mặt chứ không nhận diện danh tính. Tính năng Posture Guard dùng cùng camera để nhắc khi bạn gù lưng hoặc đưa đầu ra trước quá lâu; tính năng này mặc định tắt và cần bạn tự căn chỉnh tư thế chuẩn. Bản macOS hoàn thiện nhất, bản Windows và Linux chưa được kiểm chứng trên máy thật, và Posture Guard chưa có trong bản phát hành ổn định.
