# Hướng dẫn Bán & Thu tiền tự động cho Glance qua PayOS (VietQR 20.000đ)

Tài liệu này hướng dẫn chi tiết quy trình vận hành cổng thanh toán **PayOS** cho Glance. Hệ thống cho phép khách hàng quét mã VietQR bằng bất kỳ ứng dụng ngân hàng hoặc ví điện tử (MB Bank, Vietcombank, Techcombank, MoMo, ZaloPay,...), nhận tiền về tài khoản ngân hàng và cấp mã bản quyền trọn đời tức thì.

---

## 1. Thông tin cấu hình PayOS đã tích hợp

Kênh thanh toán đã được kết nối trực tiếp với tài khoản PayOS của bạn:

* **Chủ tài khoản:** ĐẠI CHUNG HY
* **Ngân hàng thụ hưởng:** MB Bank (Ngân hàng TMCP Quân Đội - BIN: `970422`)
* **Số tài khoản định danh:** `VQRQANHZY3760`
* **Giá bán niêm yết:** `20.000 VNĐ` / trọn đời (1 máy)
* **Client ID:** `67649131-5fa0-4271-aee3-098127cd96b3`
* **API Key:** `850357a1-e55a-4b7a-b4bf-0d3482f46ba0`
* **Checksum Key:** `dea16585b9b9a7bef274753e0cc7bb83f02a518f68f4dc2f7471ae3404a065cf`

---

## 2. Cách khởi động hệ thống thanh toán

Trong thư mục `server/`, bạn có thể chạy bằng **Python 3** (không cần cài thêm thư viện) hoặc **Node.js**:

### Cách 1: Chạy bằng 1 click script (Khuyên dùng)
```bash
cd /Users/macos/Desktop/Glance/server
./start.sh
```

### Cách 2: Chạy trực tiếp qua Python 3
```bash
cd /Users/macos/Desktop/Glance/server
python3 server.py
```

### Cách 3: Chạy qua Node.js
```bash
cd /Users/macos/Desktop/Glance/server
node server.js
```

Khi server khởi chạy:
* Trang chủ Landing Page mở tại: `http://localhost:3000`
* API tạo link VietQR: `POST http://localhost:3000/api/payment/create`
* API kiểm tra giao dịch: `GET http://localhost:3000/api/payment/status/<orderCode>`
* API Webhook PayOS: `POST http://localhost:3000/api/payment/webhook`
* API xác thực key cho app: `POST http://localhost:3000/api/license/verify`

---

## 3. Quy trình thanh toán & Kích hoạt tự động (Zero-Touch)

1. **Khách hàng bấm mua 20k trên website:**
   * Modal thanh toán mở ra, website gọi `/api/payment/create`.
   * PayOS tự động sinh mã đơn hàng `orderCode` và chuỗi VietQR chuẩn EMVCo.
   * Giao diện hiển thị mã QR VietQR MB Bank với đúng số tiền `20.000 VNĐ` và nội dung chuyển khoản.

2. **Khách hàng chuyển khoản:**
   * Khách mở app ngân hàng hoặc MoMo, quét mã và bấm xác nhận chuyển 20.000đ.
   * Tiền về ngay tài khoản ngân hàng MB Bank của Đại Chung Hy.

3. **Tự động nhận diện & Cấp bản quyền:**
   * Trình duyệt tự động kiểm tra trạng thái mỗi 2.5 giây.
   * Ngay khi nhận được tiền từ PayOS (status: `PAID`), hệ thống phát âm thanh xác nhận, sinh mã bản quyền chính thức `GLANCE-2026-XDR9-XXXX-XXXX` và lưu vào cơ sở dữ liệu `licenses.json`.

4. **Kích hoạt trong ứng dụng:**
   * Khách hàng mở `Glance.app` trên máy tính.
   * Click icon Glance trên Menu Bar $\rightarrow$ **Kích hoạt bản quyền** $\rightarrow$ Dán mã.
   * App kiểm tra và mở khóa vĩnh viễn tính năng làm mờ thông minh.

---

## 4. Cấu hình Webhook trên trang quản trị my.payos.vn

Để PayOS chủ động đẩy thông báo tức thì khi có biến động số dư:

1. Đăng nhập vào [my.payos.vn](https://my.payos.vn).
2. Vào mục **Kênh thanh toán** $\rightarrow$ Chọn kênh của Glance.
3. Tại phần **Webhook URL**, điền URL công khai của bạn (khi đưa lên máy chủ hoặc domain):
   ```text
   https://yourdomain.com/api/payment/webhook
   ```
4. Bấm **Xác nhận Webhook**. Server Glance đã tích hợp sẵn cơ chế kiểm tra chữ ký số HMAC-SHA256 với `Checksum Key` để chống giả mạo dữ liệu 100%.

---

## 5. Cấu trúc lưu trữ dữ liệu

* `server/orders.json`: Lưu danh sách các đơn hàng và trạng thái (`PENDING` hoặc `PAID`).
* `server/licenses.json`: Danh mục mã bản quyền đã phát hành kèm email khách hàng và thời gian cấp.
* `server/.env`: Quản lý an toàn các API Key và Checksum Key của PayOS.
