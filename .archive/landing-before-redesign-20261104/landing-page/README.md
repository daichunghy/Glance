# Glance — Apple Pro Blue Official Landing Page (Liquid Retina XDR)

Trang Landing Page chính thức cho **Glance** được nâng cấp và đồng bộ hóa toàn diện theo **ngôn ngữ Apple Pro Blue chuẩn xác**, lấy cảm hứng trực tiếp từ trang màn hình Liquid Retina XDR của Apple Việt Nam ([apple.com/vn/macbook-pro/proled-xdr-display/](https://www.apple.com/vn/macbook-pro/proled-xdr-display/)), layout tham chiếu chuẩn *"Rồi cháy hết với đam mê"*, sản phẩm gốc [tryglance.app/#design](https://www.tryglance.app/#design), và đặc tả chuẩn hóa từ **[DesignMD (`designmd.co/d/apple`)](https://www.designmd.co/d/apple)**.  
> Chi tiết toàn bộ danh mục website tham khảo cho các mô hình AI xem tại: [DESIGN_REFERENCES.md](file:///Users/macos/Desktop/Glance/DESIGN_REFERENCES.md).

---

## 🎨 Điểm Nâng Cấp Toàn Diện & Tích Hợp DesignMD

1. **Nhịp Điệu Canvas Luân Phiên (Alternating Canvas Rhythm):**
   - **Hero Section:** Nền đen Obsidian sâu thẳm (`#000000`) làm chủ đạo kết hợp quầng sáng xanh dương Sapphire (`#2997ff`, `#0071e3`).
   - **Section Công Nghệ Hiển Thị (`#xdr-display`):** Chuyển nhịp mượt mà sang **Apple Canvas Parchment (`#f5f5f7`)** với chữ Near-Black Ink (`#1d1d1f`), thẻ trắng hairline `1px solid rgba(0,0,0,0.08)` và Action Blue `#0066cc`. Đây là phong cách triển lãm luân phiên kinh điển trên trang chủ Apple.
   - **Section "Rồi cháy hết với đam mê." (`#pro-spotlight`):** Trở về Space Black (`#000000`) với dải ánh sáng xanh beam và bảng thông số kỹ thuật tối giản.
   - **Section Mô phỏng (`#simulator`) & Giá 20k (`#pricing`):** Studio Dark Canvas tinh tế, làm nổi bật khung máy MacBook Pro và thẻ bản quyền.

2. **Kỷ Luật "Zero Chrome" & Viền Hairline:**
   - Loại bỏ các hiệu ứng bóng mờ (box-shadow) neon dày cộm trên các thẻ card thông thường.
   - Ranh giới giữa các thành phần được định hình bằng **viền siêu mỏng 1px hairline** (`rgba(255, 255, 255, 0.12)` trên nền tối, `rgba(0, 0, 0, 0.08)` trên nền sáng).
   - Ngoại lệ bóng duy nhất là drop-shadow tiếp đất của phần cứng máy MacBook Pro.

3. **Cấu Trúc Nút Con Nhộng Chuẩn (Pill Buttons):**
   - Nút chính dạng con nhộng tròn tuyệt đối (`border-radius: 9999px`), chiều cao click công thái học tối thiểu `44px`, màu xanh Action Blue `#0071e3` / `#0066cc` không viền gradient.

4. **Khu vực Mở Bán Trọn Đời — Chỉ 20.000đ ("Mình bán 20k đó"):**
   - Thiết kế thẻ Apple Pro Lifetime Card với mức giá: **20.000đ** (Tiết kiệm 92% so với giá quốc tế).
   - Tích hợp **Modal thanh toán VietQR / PayOS tự động**:
     - Hiển thị mã QR VietQR MB Bank sắc nét kèm số tiền 20.000đ và cú pháp chuyển khoản động.
     - Ô nhập email nhận key và nút bấm xác thực thanh toán.
     - Cơ chế sinh License Key tức thì (`GLANCE-2026-XDR9-XXXX-XXXX`) kèm nút sao chép và hướng dẫn kích hoạt trong app.

5. **Quy Chuẩn Font Chữ Calibri:**
   - Tuân thủ quy chuẩn **Font Calibri** (body 10-12pt / `11pt`, line-height 1.55) hiển thị sắc nét, thoáng mắt, tương thích hoàn hảo mọi hệ thống và không bao giờ lỗi dấu tiếng Việt.

---

## 🚀 Cách mở và trải nghiệm

```bash
open /Users/macos/Desktop/Glance/landing-page/index.html
```
Hoặc chạy máy chủ nội bộ:
```bash
cd /Users/macos/Desktop/Glance/landing-page
python3 -m http.server 8080
```
Truy cập: `http://localhost:8080`
