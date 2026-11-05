# igf (Glance & Privacy Guard for macOS)

> **Simple. yet powerful.**

Ứng dụng macOS bảo vệ riêng tư màn hình thông minh khi làm việc nơi công cộng. Khi bạn quay mặt đi hướng khác, màn hình tự động làm mờ (side blur hoặc full blur) để chống nhìn trộm.

---

## 🌟 Hỗ trợ 2 chế độ nhận diện (Hybrid)

1. **📷 Camera Face Tracking (Mặc định - Không cần AirPods):**
   - Sử dụng Apple Vision Framework (`VNDetectFaceRectanglesRequestRevision3`) trên camera FaceTime HD có sẵn của MacBook.
   - Nhận diện góc quay mặt (Yaw) theo thời gian thực ở tốc độ ~10 FPS, sử dụng Neural Engine tích hợp nên gần như **0% CPU và không tốn pin**.
   - Bất kỳ ai dùng MacBook cũng dùng được ngay, không cần tai nghe đắt tiền.

2. **🎧 AirPods Motion Tracking (Dành cho tai nghe hỗ trợ Spatial Audio):**
   - Khi có AirPods Pro, AirPods 3/4 hoặc AirPods Max, bạn có thể chuyển sang chế độ AirPods để theo dõi chuyển động qua con quay hồi chuyển (`CMHeadphoneMotionManager`).

---

## 🎨 Giao diện tối giản (Minimalist Menu Bar UI)

- **Header**: Bật / Tắt tính năng nhanh bằng nút gạt.
- **Nguồn nhận diện**: Chuyển đổi giữa `Camera` và `AirPods`.
- **Thước đo góc thời gian thực**: Hiển thị độ lệch mặt/đầu và điểm trạng thái trực quan.
- **Chế độ làm mờ**:
  - `Side Blur`: Mờ cạnh hướng bạn quay mặt (ví dụ quay sang phải thì mờ cạnh phải).
  - `Full Screen`: Mờ 100% toàn bộ màn hình.
- **Độ nhạy**: `Low` | `Medium` | `High`.
- **Nút Calibrate**: Căn chỉnh vị trí ngồi thẳng làm mốc 0°.

---

## 🚀 Khởi chạy ứng dụng

Chạy lệnh trong Terminal:
```bash
open /Users/macos/.gemini/antigravity/scratch/igf/igf.app
```
Hoặc mở thư mục trong Finder:
```bash
open /Users/macos/.gemini/antigravity/scratch/igf
```
*(Lần đầu mở bằng Camera, macOS sẽ hiển thị hộp thoại xin cấp quyền Camera để nhận diện khuôn mặt).*
