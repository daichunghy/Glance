# Glance — Smart Screen Privacy for Mac, Windows & Linux

> **Simple. yet powerful.**  
> Ứng dụng bảo vệ riêng tư màn hình thông minh khi làm việc nơi công cộng. Tự động làm mờ góc nhìn trộm ("quay bên nào mờ bên còn lại") và làm mờ 100% khi người dùng rời bàn.

---

## 📁 Cấu trúc thư mục dự án

```text
Glance/
├── macos/                  # Phiên bản Native macOS (Swift 6 + AppKit + Vision + CoreMotion)
│   ├── Glance.app          # File app đã build sẵn, chạy được ngay trên Mac
│   ├── build_app.sh        # Script build release và đóng gói .app tự động
│   └── Sources/            # Toàn bộ mã nguồn Swift
├── windows/                # Phiên bản Windows (Python/Win32 + OpenCV + DWM Acrylic)
│   ├── glance_windows.py   # Mã nguồn chính cho Windows 10 & 11
│   ├── requirements.txt    # Thư viện phụ thuộc
│   └── build_exe.bat       # Script đóng gói thành Glance.exe chỉ với 1 click
├── linux/                  # Phiên bản Linux (Python + PyQt6 + V4L2/OpenCV)
│   ├── glance_linux.py     # Mã nguồn cho Ubuntu, Fedora, Arch, Debian
│   ├── requirements.txt    # Thư viện phụ thuộc
│   └── build_linux.sh      # Script đóng gói thành binary độc lập
├── licensing/              # Hệ thống bản quyền (Mac, Windows, Linux)
│   ├── LicenseManager.swift # Module bản quyền cho Mac
│   ├── license_manager.py   # Module bản quyền cho Windows & Linux
│   └── COMMERCIAL_GUIDE.md  # Hướng dẫn chi tiết cách bán và thu tiền qua PayOS VietQR
├── server/                 # Cổng thanh toán PayOS VietQR & Cấp key tự động
│   ├── server.py           # Backend server Python 3 (Zero-dependency)
│   ├── server.js           # Backend server Node.js
│   ├── start.sh            # Script khởi chạy 1-click
│   └── .env                # Thông tin cấu hình PayOS Client ID, API Key, Checksum Key
├── landing-page/           # Landing page chính thức chuẩn Apple Pro Blue tích hợp PayOS VietQR 20k
├── DESIGN.md               # Quy chuẩn Design System Apple Pro Blue (Design Tokens & CSS)
├── DESIGN_REFERENCES.md    # Danh sách các website & tài liệu tham khảo thiết kế cho AI
└── LAUNCH_VIDEO_BENCHMARK.md # Kế hoạch & benchmark video launch (Numtera reference)
```

---

## 🎨 Tài liệu tham khảo thiết kế cho AI
Bất kỳ mô hình AI nào khi tham gia thiết kế, tạo trang web hay media cho Glance đều cần đọc trước:
* **[DESIGN_REFERENCES.md](file:///Users/macos/Desktop/Glance/DESIGN_REFERENCES.md):** Danh sách đầy đủ các link website gốc (TryGlance, Apple Liquid Retina XDR, DesignMD Apple, Video Launch Benchmark, PayOS).
* **[DESIGN.md](file:///Users/macos/Desktop/Glance/DESIGN.md):** Quy chuẩn thông số kỹ thuật (Tokens, màu Action Blue, font Calibri 11pt, kỷ luật Zero-Chrome).

---

## 🚀 Hướng dẫn khởi chạy theo từng hệ điều hành

### 1. Trên macOS (Có sẵn bản chạy ngay)
Bạn có thể mở ngay file ứng dụng tại:
```bash
open /Users/macos/Desktop/Glance/macos/Glance.app
```
Hoặc build lại từ mã nguồn:
```bash
cd /Users/macos/Desktop/Glance/macos
./build_app.sh
```

### 2. Trên Windows 10 & 11
1. Chuyển thư mục `windows/` sang máy tính Windows.
2. Cài đặt thư viện: `pip install -r requirements.txt`
3. Chạy trực tiếp: `python glance_windows.py`
4. Để xuất file `.exe` cho khách hàng: Chạy file `build_exe.bat` (kết quả nằm tại `dist/Glance.exe`).

### 3. Trên Linux (Ubuntu / Fedora / Arch)
1. Cài đặt thư viện: `pip install -r requirements.txt`
2. Chạy ứng dụng: `python glance_linux.py`
3. Xuất file binary độc lập: Chạy `./build_linux.sh`.

---

## 🔒 Triết lý bảo mật & Hiệu năng
* **100% On-Device:** Toàn bộ quá trình quét góc mặt được xử lý trực tiếp trên chip nội bộ máy tính, không lưu ảnh và không gửi bất kỳ dữ liệu nào qua mạng.
* **Typing & Mouse Guard:** Tự động phát hiện khi người dùng đang gõ phím hoặc di chuột để không bao giờ bị mờ nhầm.
* **Video Call Friendly:** Tự động tạm dừng khi camera bị chiếm dụng bởi Zoom, Google Meet, Microsoft Teams hoặc FaceTime.
