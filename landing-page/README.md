# Glance cho Mac

Bản thiết kế 1.4.1 của landing page. Hai nguồn thiết kế được ghi trong [DESIGN_REFERENCES.md](../DESIGN_REFERENCES.md).

Xem tại máy qua HTTP để xem mô hình 3D.

```sh
python3 -m http.server 8176 --bind 127.0.0.1 --directory landing-page
```

Mở [http://127.0.0.1:8176/](http://127.0.0.1:8176/). Mở trực tiếp index.html vẫn xem được phần trình bày và hình AirPods tĩnh.

Trang dùng mô hình 3D dựng bằng mã nguồn tại `airpods.js`. Three.js 0.183.2 được lưu cục bộ theo giấy phép MIT, tải khi cuộn gần cảnh AirPods và không kết xuất liên tục. Cảnh màn hình chạy trên web không dùng camera và không truy cập AirPods. Khi cuộn, khung MacBook giữ vị trí, thay đổi góc, tiến gần và đổi vùng mờ theo từng giai đoạn. Bảng tính năng và thẻ riêng tư giải thích hành vi của ứng dụng macOS.

Tệp tải về là bản Glance 1.0.0 hiện có cho Apple silicon. Gói ZIP giữ nguyên chữ ký ad hoc của ứng dụng. Xác minh notarization và trải nghiệm cài đặt trên một máy khác trước khi phát hành rộng.

Glance chuyển sang miễn phí và nhận ủng hộ tự nguyện. Luồng PayOS mới được chuẩn bị tại máy nhưng mặc định tắt và chưa được xác minh bằng giao dịch thật. Để mở luồng cần thay khóa PayOS đã lộ, cấu hình địa chỉ HTTPS và kiểm tra đầy đủ trước khi phát hành. Các tệp checkout và API cấp mã cũ không phải luồng ủng hộ.

Bản giao diện trước nằm trong `.archive/landing-before-redesign-20261104/`. Kịch bản và khung hình làm video nằm trong thư mục `Tư liệu video`.
