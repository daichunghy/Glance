# Glance — Cải thiện theo nghiên cứu hành vi người dùng (đợt 2)

Châm ngôn áp dụng cho mọi thay đổi: **Simple. yet powerful.** — mỗi cải thiện
phải ít nút, ít khái niệm mới, nhưng giải quyết đúng điểm khiến người dùng
tắt/bỏ app. Nguồn: báo cáo nghiên cứu hành vi người dùng ngày 06/11/2026
(Ponemon/3M, HP webcam study, review SitApp/Upright/Stretchly, FAccT 2025).

## Checklist P0 — mỗi mục một test quan sát được

- [x] **Cooldown thích ứng:** bị nhắc lặp lại trong 1 giờ thì cooldown tự dài ra
  60s → 120s → 300s thay vì nhắc mãi một nhịp.
  *Test: unit test — cảnh báo lần 2, 3 trong cùng giờ có cooldown tăng dần.*
- [x] **Nút "Không phải tư thế xấu" ngay trên cảnh báo:** bấm một lần là hết
  cảnh báo hiện tại và ngưỡng tự nới +10% (tối đa ×1,5) — app tự học độ
  nhạy hợp với người dùng thay vì bắt họ vào cài đặt.
  *Test: unit test — sau dismiss, cùng một mức lệch không còn kích hoạt ở
  ngưỡng cũ; hệ số nới tăng đúng cấp.*
- [x] **Tạm tắt nhắc tư thế 30 phút (snooze)** từ chính dòng cảnh báo.
  *Test: unit test — trong thời gian snooze không có cảnh báo nào; hết
  snooze hoạt động lại bình thường.*
- [x] **Pause = camera tắt thật:** tắt Glance (Mac) / tắt bảo vệ (Linux) /
  tắt camera (Windows) là camera được nhả hẳn, đèn camera tắt — không có
  trạng thái "đã pause mà đèn vẫn sáng".
  *Test: đọc code — đường tắt gọi stop capture ở cả 3 nền tảng; Mac:
  isEnabled=false dừng cả CameraTracker lẫn MotionTracker.*
- [x] **Camera bị app họp chiếm → tự nhường và tự quay lại:** Windows/Linux
  mở camera không được thì chờ và thử lại mỗi 3 giây, hiện trạng thái
  "camera đang bận", không chết hẳn bắt người dùng bật tay lại.
  Mac đã có cơ chế interruption sẵn — giữ nguyên và ghi rõ trong spec.
  *Test: đọc code — vòng thử lại nằm trong worker, tôn trọng nút tắt.*
- [x] **Camera bị che / quá tối → không che nhầm, không nhắc nhầm:** khung
  hình gần như đen hẳn (độ sáng trung bình < 15/255) thì cả che màn hình
  lẫn tư thế đều đứng yên và báo "camera có vẻ bị che hoặc quá tối".
  *Test: unit test hàm `frame_too_dark` + đọc code 2 vòng camera Win/Linux.*
- [x] **"Hiện màn hình 2 phút" (share mode):** một nút/phím tắt để cố ý cho
  người bên cạnh xem màn hình (thảo trình, chỉ cho đồng nghiệp) mà không
  phải tắt cả Glance; hết 2 phút tự bảo vệ lại.
  *Test: đọc code — Mac ⌥⇧S + nút trong popover; Windows nút trong cửa sổ;
  Linux mục menu; trạng thái share chặn che tự động ở cả 3 nơi.*
- [x] **Không hứa hẹn y tế:** mọi chữ về tư thế chỉ nói "nhắc ý thức tư thế",
  kèm một dòng "không phải thiết bị y tế" trong README/spec.
  *Test: grep tài liệu — có dòng miễn trừ, không có chữ chữa/giảm đau.*

## Ngoài đợt này (P1/P2, để không phình tính năng)

Hồ sơ theo setup (nhiều màn hình/camera), tiết kiệm pin nâng cao, tóm tắt
cuối ngày, gợi ý đứng dậy sau nhiều cảnh báo, check tư thế trước cuộc họp.
Ghi lại ở đây để khỏi mất, chưa làm.
