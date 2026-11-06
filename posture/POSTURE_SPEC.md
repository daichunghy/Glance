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
- Sau mỗi cảnh báo có **cooldown thích ứng**: 60 giây lần đầu, bị nhắc lần 2
  trong vòng 1 giờ thì 120 giây, lần 3 trở đi 300 giây — càng bị nhắc càng
  thưa, chống mệt mỏi vì cảnh báo (theo nghiên cứu hành vi người dùng).
- Người dùng bấm **"Không phải tư thế xấu"** ngay trên cảnh báo: cảnh báo
  tắt ngay và các ngưỡng tự nới **+10% mỗi lần bấm, tối đa ×1,5** — app tự
  học độ nhạy hợp với từng người thay vì ép một ngưỡng cho tất cả.
- **Tạm tắt nhắc 30 phút (snooze)**: trong lúc snooze không cảnh báo, hết
  giờ tự hoạt động lại.
- Mất mặt khỏi khung hình → bộ đếm tư thế xấu reset (người dùng có thể đang
  quay đi / rời bàn — đó là việc của tính năng che màn hình, không phải tư thế).
- **Camera bị che / quá tối** (độ sáng khung hình trung bình < 15/255): cả
  tính năng tư thế lẫn che màn hình đều đứng yên — không thấy được người
  dùng không có nghĩa là người dùng đã đi khỏi hoặc đang gù.

## 3b. Camera & quyền riêng tư (bổ sung theo nghiên cứu người dùng)

- **Tắt Glance là camera tắt thật** (đèn camera tắt) ở cả 3 nền tảng —
  không có trạng thái "đã tạm dừng mà camera vẫn chạy".
- **Camera bị ứng dụng họp (Zoom/Teams/Meet) chiếm:** Windows/Linux chờ và
  tự mở lại khi camera trống, hiện trạng thái "camera đang bận"; macOS dùng
  cơ chế interruption có sẵn của AVCaptureSession. Không app nào được làm
  hỏng việc bắt đầu cuộc gọi của người dùng.
- **Hiện màn hình 2 phút (share mode):** một nút/phím tắt (macOS ⌥⇧S) để cố
  ý cho người bên cạnh xem; hết 2 phút tự bảo vệ lại, không phải tắt Glance.
- Glance **không phải thiết bị y tế**: tính năng tư thế chỉ nhắc ý thức tư
  thế ngồi, không chẩn đoán, không hứa giảm đau hay chữa bệnh.

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
  - [ ] Cả 3: bị nhắc → bấm "Không phải tư thế xấu" → hết nhắc ngay; bật snooze 30 phút → không nhắc.
  - [ ] Cả 3: share mode 2 phút → không che; hết 2 phút → che lại bình thường.
  - [ ] Cả 3: lấy tay che camera → không che màn hình, không nhắc tư thế, hiện trạng thái bị che/quá tối.
  - [ ] Mac: tắt Glance bằng ⌥⇧P → đèn camera tắt ngay.
  - [ ] Windows/Linux: đang họp Zoom (camera bận) mở Glance → không lỗi chết, họp xong camera tự chạy lại.

## 7. Ngoài phạm vi đợt này

- Không nhận diện vai/xương sống bằng body-pose (cần model mới, nặng và
  không ổn định trên máy yếu) — để dành đợt sau nếu số đo mặt không đủ.
- Không thống kê lịch sử tư thế, không đồng bộ server, không đụng landing page.
