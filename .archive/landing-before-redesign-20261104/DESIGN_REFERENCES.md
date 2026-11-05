# Glance — Danh Sách Website Tham Khảo Thiết Kế (Design References)

> **Dành cho các mô hình AI & Designer tiếp quản dự án:**  
> Tài liệu này tổng hợp toàn bộ các đường dẫn website, video và hệ thống tài liệu tham chiếu chuẩn đã được phê duyệt để thiết kế toàn bộ hệ thống giao diện, ứng dụng và tài liệu truyền thông của Glance. Bất kỳ mô hình AI nào khi bước vào dự án cần đọc và tuân thủ tuyệt đối các nguồn tham khảo này.

---

## 1. Bảng Tổng Hợp Website Tham Khảo Cốt Lõi

| Nhóm tham chiếu | Đường dẫn (URL) | Mục đích & Phạm vi áp dụng | Điểm cốt lõi cần trích xuất khi thiết kế |
| :--- | :--- | :--- | :--- |
| **Sản phẩm gốc & Kiến trúc UX** | [https://www.tryglance.app/#design](https://www.tryglance.app/#design) | Tham khảo cấu trúc sản phẩm Glance gốc, luồng tính năng bảo vệ màn hình | • Cách trình bày 2 tính năng chính: **Directional Blur** ("Quay bên nào mờ bên còn lại") và **Presence Guard** (tự động khóa mờ khi rời bàn).<br>• Cấu trúc Bento Grid và các thẻ lợi ích on-device privacy. |
| **Ngôn ngữ thẩm mỹ & Tone Vibe Apple** | [https://www.apple.com/vn/macbook-pro/proled-xdr-display/](https://www.apple.com/vn/macbook-pro/proled-xdr-display/) | Chuẩn thẩm mỹ Apple Pro, dải màu xanh dương và nhịp điệu Canvas | • **Màu xanh Sapphire / Action Blue** (`#0066cc`, `#0071e3`, `#2997ff`).<br>• **Nhịp điệu Canvas luân phiên:** Nền đen Obsidian (`#000000`) ➔ Nền sáng Parchment (`#f5f5f7`) / Pearl White (`#ffffff`) ➔ Space Black (`#000000`).<br>• Tiêu đề ngắn gọn, tự tin ("Rồi cháy hết với đam mê."). |
| **Hệ thống Design System chuẩn hóa** | [https://www.designmd.co/d/apple](https://www.designmd.co/d/apple) | Bộ thông số kỹ thuật (Design Tokens) và quy chuẩn giao diện Apple | • **Kỷ luật Zero-Chrome:** Không dùng box-shadow dày; chỉ dùng viền hairline siêu mảnh `1px solid rgba(255,255,255,0.12)` (nền tối) và `1px solid rgba(0,0,0,0.08)` (nền sáng).<br>• **Pill Buttons:** Bo tròn tuyệt đối (`border-radius: 9999px`), chiều cao click tối thiểu `44px`.<br>• Thư mục hướng dẫn nội bộ tại: `/Users/macos/Desktop/Design System Apple`. |
| **Benchmark Video Launch & Motion** | [https://www.youtube.com/watch?v=awUYikrGsKk](https://www.youtube.com/watch?v=awUYikrGsKk) | Benchmark video giới thiệu sản phẩm chuẩn SaaS cao cấp (Numtera) | • Cấu trúc video 60-95s theo mô hình "Chaos to Clarity" (Hỗn loạn ➔ Trật tự).<br>• Motion design cận cảnh chi tiết tương tác UI góc nghiêng 3D, sound design dứt khoát.<br>• Tài liệu phân tích chi tiết tại: [LAUNCH_VIDEO_BENCHMARK.md](file:///Users/macos/Desktop/Glance/LAUNCH_VIDEO_BENCHMARK.md). |
| **Tài liệu Cổng thanh toán VietQR** | [https://payos.vn/docs/](https://payos.vn/docs/) | Tích hợp cổng thanh toán tự động VietQR cho gói bản quyền 20.000đ | • Luồng tạo mã QR thanh toán PayOS VietQR tự động, đối soát tức thời và cấp License Key bản quyền trọn đời. |

---

## 2. Chi Tiết Từng Nguồn Tham Khảo & Hướng Dẫn Kỹ Thuật Cho AI

### 2.1. Website Sản Phẩm Gốc — [tryglance.app/#design](https://www.tryglance.app/#design)
* **Nguyên tác chức năng:** Glance là ứng dụng phát hiện hướng nhìn của khuôn mặt qua webcam (100% on-device) để tự động bảo vệ riêng tư màn hình nơi công cộng.
* **Quy chuẩn hiển thị nội dung:**
  1. **Directional Blur:** Khi người dùng nghiêng đầu nhìn sang một phía của màn hình, nửa còn lại nơi người khác có thể nhìn trộm sẽ bị phủ mờ kính đục (Frosted Glass Blur). Khi mắt quay trở lại, màn hình sắc nét lập tức với độ trễ 0ms.
  2. **Presence Guard:** Khi người dùng đứng dậy rời khỏi bàn làm việc, toàn màn hình tự động mờ 100% và hiện biểu tượng khóa bảo vệ.
  3. **Smart Guard:** Tự động giữ nét khi người dùng đang gõ phím hoặc di chuột; tự nhường camera khi có cuộc gọi Zoom / Google Meet / FaceTime.

### 2.2. Ngôn Ngữ Thẩm Mỹ Apple — [apple.com/vn/macbook-pro/proled-xdr-display](https://www.apple.com/vn/macbook-pro/proled-xdr-display/)
* **Yêu cầu quan trọng từ người dùng:** Giao diện bắt buộc phải mang **sắc xanh dương Apple Pro** (đồng nhất, chuẩn xác), không dùng gam màu tùy tiện hay tím/hồng neon lệch tông.
* **Nhịp điệu Canvas (Alternating Canvas Rhythm):**
  * Không làm landing page toàn màu đen đơn điệu hay toàn màu trắng lóa mắt.
  * Phải đan xen các khối Canvas:
    - **Hero Tile:** Nền đen Obsidian (`#000000`), điểm sáng xanh Sapphire `#0071e3` / `#2997ff`.
    - **Display Showcase Section:** Chuyển sang nền sáng **Apple Parchment (`#f5f5f7`)** hoặc **Pure White (`#ffffff`)**, chữ Near-Black Ink (`#1d1d1f`), thẻ trắng viền hairline mảnh.
    - **Spotlight Tile:** Chuyển lại nền Space Black (`#000000`) với quầng sáng xanh tạo độ sâu thị giác.

### 2.3. Quy Chuẩn DesignMD Apple — [designmd.co/d/apple](https://www.designmd.co/d/apple)
* **Kỷ luật "Zero-Chrome":**
  * Cấm dùng `box-shadow` mờ mịt, neon phát sáng lem nhem trên các thẻ card hay nút bấm.
  * Chỉ dùng viền hairline siêu mỏng `1px`:
    ```css
    /* Nền tối (Dark Canvas) */
    border: 1px solid rgba(255, 255, 255, 0.12);
    /* Nền sáng (Light Canvas) */
    border: 1px solid rgba(0, 0, 0, 0.08);
    ```
  * Ngoại lệ duy nhất cho shadow: Khung phần cứng MacBook Pro khi đặt trên mặt sàn phẳng (`0 35px 80px rgba(0, 0, 0, 0.85)`).
* **Nút bấm dạng con nhộng (Pill CTA):**
  * Nút chính: `border-radius: 9999px; background: #0071e3; color: #ffffff; min-height: 44px;`
  * Nút phụ: `border-radius: 9999px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15);`

### 2.4. Quy Chuẩn Font Chữ Calibri Toàn Diện
* **Quy tắc bắt buộc:** Luôn luôn ưu tiên sử dụng font **Calibri** (cỡ chữ 10-12pt cho body text, 12-16pt cho đề mục) để đảm bảo tính chuyên nghiệp, hiện đại, hiển thị sắc nét, thoáng mắt, tương thích hoàn hảo trên mọi hệ điều hành (macOS, Windows, Linux) và **không bao giờ lỗi dấu tiếng Việt**:
  ```css
  font-family: 'Calibri', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
  ```

---

## 3. Checklist Cho Bất Kỳ Mô Hình AI Nào Khi Tiếp Tục Phát Triển

Khi nhận yêu cầu tạo mới trang con, sửa giao diện, xuất hình ảnh hoặc làm video cho Glance:
- [ ] **Kiểm tra URL tham khảo:** Đối chiếu bố cục với [tryglance.app](https://www.tryglance.app/#design) và tinh thần thị giác từ [Apple Liquid Retina XDR](https://www.apple.com/vn/macbook-pro/proled-xdr-display/).
- [ ] **Bảng màu:** Đảm bảo màu chủ đạo là Apple Action Blue (`#0066cc` / `#0071e3` / `#2997ff`) trên nền Obsidian Black (`#000000`) và Parchment (`#f5f5f7`).
- [ ] **Kiểu dáng nút & thẻ:** Nút con nhộng `border-radius: 9999px`, viền hairline 1px siêu mảnh, tuyệt đối không dùng shadow mờ làm bẩn UI.
- [ ] **Font chữ:** Ưu tiên `Calibri` 10-12pt cho body text.
- [ ] **Bản quyền & Giá:** Gói bản quyền Glance được phân phối tại Việt Nam với mức giá **20.000đ** trọn đời thông qua cổng VietQR PayOS.
