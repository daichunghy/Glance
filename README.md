# Glance — Smart Screen Privacy for Mac, Windows & Linux

> **Simple. yet powerful.**  
> Ứng dụng hỗ trợ riêng tư màn hình khi làm việc nơi công cộng. Tính năng và mức độ hoàn thiện khác nhau giữa các hệ điều hành; xem hướng dẫn của từng phiên bản trước khi sử dụng.

Glance chuyển sang miễn phí và nhận ủng hộ tự nguyện. Luồng PayOS mới được chuẩn bị tại máy, mặc định tắt và chưa được xác minh bằng giao dịch thật.

---

## 📁 Cấu trúc thư mục dự án

```text
Glance/
├── macos/                  # Phiên bản Native macOS (Swift 6 + AppKit + Vision + CoreMotion)
│   ├── Glance.app          # File app đã build sẵn, chạy được ngay trên Mac
│   ├── build_app.sh        # Script build release và đóng gói .app tự động
│   └── Sources/            # Toàn bộ mã nguồn Swift
├── windows/                # Phiên bản Windows đang phát triển (Python/Win32 + OpenCV)
│   ├── glance_windows.py   # Giao diện và camera cho Windows
│   ├── guard.py            # Quy tắc nhận diện vắng mặt
│   ├── README.md           # Hướng dẫn và giới hạn hiện tại
│   ├── requirements.txt    # Thư viện phụ thuộc
│   └── build_exe.bat       # Script đóng gói trên Windows
├── linux/                  # Phiên bản Linux (Python + PyQt6 + V4L2/OpenCV)
│   ├── glance_linux.py     # Mã nguồn cho Ubuntu, Fedora, Arch, Debian
│   ├── requirements.txt    # Thư viện phụ thuộc
│   └── build_linux.sh      # Script đóng gói thành binary độc lập
├── licensing/              # Mã bản quyền và tài liệu bán hàng cũ
│   ├── LicenseManager.swift # Module bản quyền cho Mac
│   ├── license_manager.py   # Module bản quyền cho Windows & Linux
│   └── COMMERCIAL_GUIDE.md  # Hướng dẫn chi tiết cách bán và thu tiền qua PayOS VietQR
├── server/                 # Máy chủ PayOS và cấp mã của mô hình bán hàng cũ
│   ├── server.py           # Backend server Python 3 (Zero-dependency)
│   ├── server.js           # Backend server Node.js
│   ├── start.sh            # Script khởi chạy 1-click
│   └── .env                # Thông tin cấu hình PayOS Client ID, API Key, Checksum Key
├── landing-page/           # Landing page Glance, luồng ủng hộ mới mặc định tắt
├── DESIGN.md               # Quy chuẩn Design System Apple Pro Blue (Design Tokens & CSS)
├── DESIGN_REFERENCES.md    # Hai website tham khảo thiết kế
└── Tư liệu video/          # Căn cứ nội dung, khung hình và kế hoạch sản xuất
```

---

## Thiết kế Glance

[DESIGN_REFERENCES.md](DESIGN_REFERENCES.md) ghi hai nguồn thiết kế là Apple MacBook Pro và TryGlance. [DESIGN.md](DESIGN.md) ghi quy chuẩn áp dụng cho Glance. Xem [hướng dẫn mở trang](landing-page/README.md) để chạy bản dựng tại máy.

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
Xem [hướng dẫn Windows](windows/README.md). Mã Windows đang phát triển và chưa được kiểm thử trên máy Windows thực tế; chưa có bản `.exe` được xác minh để phát hành.

### 3. Trên Linux (Ubuntu / Fedora / Arch)
Mở thư mục `linux`, cài thư viện bằng `python3 -m pip install -r requirements.txt` rồi chạy `python3 glance_linux.py`. Glance dùng cửa sổ điều khiển khi môi trường desktop thiếu khay hệ thống. Dùng `./build_linux.sh` trên máy Linux để đóng gói. Lớp che và camera vẫn cần xác minh trên Linux thật. [Hướng dẫn về khay hệ thống của Qt](https://doc.qt.io/qt-6/qsystemtrayicon.html).

---

## 🔒 Triết lý bảo mật & Hiệu năng
* Phiên bản Windows xử lý khung hình camera cục bộ, không lưu hoặc gửi khung hình. Tính năng nhận diện có thể sai và không xác minh danh tính.
* Windows có tùy chọn tạm hoãn che khi có thao tác chuột hoặc bàn phím; tùy chọn này không đảm bảo tránh che nhầm.
* Windows chưa tự phát hiện cuộc gọi hoặc tự nhả camera cho ứng dụng khác. Xem giới hạn và hướng dẫn kiểm thử trong [README Windows](windows/README.md).
