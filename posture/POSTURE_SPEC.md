# Glance — Tính năng cảnh báo tư thế: gù lưng & cổ rùa (Posture Guard)

Trạng thái: **đang phát triển trên branch `feature/posture-guard` — CHƯA publish,
CHƯA merge vào `main`, KHÔNG đụng vào `landing-page/` và website hiện tại.**

## 1. Mục tiêu

Nhắc người dùng khi ngồi sai tư thế trong lúc làm việc trước máy tính:

- **Cổ rùa (turtle neck / forward head):** đầu đưa ra trước, tiến sát màn hình.
- **Gù lưng (hunch / slouch):** đầu và vai sụp xuống so với tư thế chuẩn.

Cảnh báo phải *nhẹ nhàng, không phạt*: không che màn hình, không bật cửa sổ
modal, không phát âm thanh lặp lại. Chỉ hiện trạng thái / thông báo một lần
cho mỗi đợt ngồi sai, và tự tắt khi người dùng ngồi lại đúng.

## 2. Nguyên tắc ổn định trên mọi thiết bị (Mac / Windows / Linux)

1. **Không thêm thư viện ML mới.** Tính năng dùng lại đúng pipeline camera
   hiện có của Glance (macOS: Vision face rectangles; Windows/Linux: OpenCV
   Haar cascade) — cùng độ phân giải thấp 320×240, cùng nhịp ~8 FPS. Không
   tải model, không cần GPU, không tăng đáng kể CPU/RAM.
2. **Logic thuần, tách khỏi camera và UI** — giống mẫu `windows/guard.py`
   (`PresenceGuard`): module `posture` chỉ nhận số đo hình học của khuôn mặt
   (kích thước tương đối + vị trí dọc + góc pitch nếu có) và trả về trạng
   thái. Nhờ vậy logic chạy giống hệt trên 3 hệ điều hành và test được bằng
   unit test mà không cần camera thật.
3. **Mặc định TẮT (opt-in).** Người dùng tự bật và tự căn chỉnh
   (calibrate) tư thế chuẩn của chính mình. Khi tắt, code tư thế không chạy
   và hành vi Glance cũ không thay đổi chút nào.
4. **Fail-safe:** không có camera, camera bị app khác chiếm, mất mặt khỏi
   khung hình, hoặc chưa căn chỉnh → tính năng tư thế *tạm dừng im lặng*,
   không cảnh báo, không ảnh hưởng tính năng che màn hình riêng tư.
5. **Riêng tư:** khung hình chỉ xử lý tại máy, không lưu, không gửi đi —
   đúng triết lý hiện tại của Glance. Module tư thế chỉ giữ vài số đo vô
   danh (tỉ lệ kích thước mặt, vị trí dọc) trong RAM.

## 3. Cách đo (chung cho cả 3 nền tảng)

Sau khi người dùng ngồi đúng tư thế và bấm **Căn chỉnh tư thế chuẩn**,
Glance ghi baseline:

| Số đo | Ý nghĩa |
|---|---|
| `face_size` | Chiều rộng mặt / chiều rộng khung hình (proxy cho khoảng cách đầu ↔ camera) |
| `center_y` | Vị trí dọc của tâm mặt, quy về hệ "dương = đầu sụp xuống" |
| `pitch` | Góc cúi/ngẩng (chỉ macOS có sẵn từ Vision; Windows/Linux bỏ qua) |

Mỗi khung hình, số đo được làm mượt bằng EMA (α = 0.30, cùng hệ số làm mượt
góc yaw hiện có) rồi so với baseline:

- `forward = smoothed_size / baseline_size − 1` — đầu tiến sát camera bao nhiêu.
- `drop = smoothed_center_y − baseline_center_y` — đầu sụp xuống bao nhiêu
  (đơn vị: phần của chiều cao khung hình).
- `pitch_drop = baseline_pitch − pitch` — cúi thêm bao nhiêu độ (nếu có pitch).

### Quy tắc phân loại

- **Cổ rùa:** `forward ≥ 0.18` kèm (`drop ≥ 0.03` hoặc `pitch_drop ≥ 8°`),
  hoặc `forward ≥ 0.28` đứng một mình.
- **Gù lưng:** `drop ≥ 0.07` kèm (`pitch_drop ≥ 8°` hoặc `forward ≥ 0.08`),
  hoặc `drop ≥ 0.12` đứng một mình.
- **Ngoại lệ nhìn bàn phím/giấy:** nếu có pitch và `pitch_drop ≥ 20°` nhưng
  đầu không tiến sát (`forward < 0.08`) và không sụp sâu (`drop < 0.12`) thì
  coi là đang nhìn xuống bàn phím — không cảnh báo. (Khớp ngoại lệ sẵn có
  trong `CameraTracker.swift` của macOS.)

### Máy trạng thái chống báo nhầm

- Chỉ cảnh báo khi tư thế xấu **liên tục ≥ 10 giây** (tham số `hold_seconds`).
- Cảnh báo tự tắt khi ngồi đúng lại **liên tục ≥ 3 giây** (`release_seconds`).
- Sau mỗi cảnh báo có **60 giây cooldown** (`cooldown_seconds`): không cảnh
  báo lại trong thời gian này dù người dùng chưa sửa tư thế ngay.
- Mất mặt khỏi khung hình → bộ đếm tư thế xấu reset (người dùng có thể đang
  quay đi / rời bàn — đó là việc của tính năng che màn hình, không phải tư thế).

## 4. Hiển thị cảnh báo theo nền tảng

| Nền tảng | Cách cảnh báo |
|---|---|
| macOS | Dòng trạng thái tư thế trong popover (Good / Turtle neck / Slouching) + đổi màu chấm trạng thái; không che màn hình |
| Windows | Dòng trạng thái riêng trong cửa sổ Glance, chỉ cập nhật khi trạng thái thay đổi |
| Linux | Thông báo khay hệ thống (`QSystemTrayIcon.showMessage`) một lần mỗi đợt + tooltip khay; nơi không có khay thì ghi vào mục trạng thái của panel |

## 5. Căn chỉnh (calibration)

- Bấm nút căn chỉnh *khi đang ngồi đúng tư thế, nhìn thẳng màn hình*.
- Cần ít nhất vài khung hình mặt ổn định trước đó; nếu chưa thấy mặt, nút
  báo "chưa thấy khuôn mặt" và không lưu baseline rỗng.
- Đổi camera / đổi ghế / đổi màn hình → căn chỉnh lại.

## 6. Kiểm thử

- Unit test logic thuần: `windows/tests/test_posture.py`,
  `linux/tests/test_posture.py` (hai bản `posture.py` phải giống hệt nhau),
  `macos/Tests/igfTests/PostureGuardTests.swift` (cùng bộ ca kiểm thử).
- Test hồi quy cũ phải vẫn pass: `windows/tests/test_guard.py`,
  `windows/tests/test_screen_cover.py`.
- Checklist tay trên máy thật (làm trước khi merge):
  - [ ] Mac: bật/tắt, căn chỉnh, cúi gù 15s → báo; ngồi thẳng → hết báo; gọi FaceTime → tư thế tạm dừng theo video call.
  - [ ] Windows 10 & 11: như trên; camera bị Zoom chiếm → không crash, không báo.
  - [ ] Linux (Ubuntu/X11 + Wayland): như trên; máy không có tray → panel vẫn hiện trạng thái.
  - [ ] Cả 3: tắt tính năng tư thế → hành vi che màn hình y hệt bản cũ.
  - [ ] Cả 3: không có camera → Glance vẫn mở, tư thế báo "không khả dụng" im lặng.

## 7. Ngoài phạm vi đợt này

- Không nhận diện vai/xương sống bằng body-pose (cần model mới, nặng và
  không ổn định trên máy yếu) — để dành đợt sau nếu số đo mặt không đủ.
- Không thống kê lịch sử tư thế, không đồng bộ server, không đụng landing page.
