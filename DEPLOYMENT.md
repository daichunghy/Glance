# Triển khai Glance

- Website: https://glance-privacy.vercel.app
- Vercel project: `glance-privacy`
- Vercel team: `daichunghys-projects` (`team_Xdq0FvRI5xnpaGqvrT0EKo3N`)
- Tài khoản CLI đã xác nhận: `daichunghy`
- Project ID: `prj_SEDntybf0gN7moygS4IZXFn9HqPZ`
- Production deployment ngày 05/11/2026: `dpl_9PRgr5cKpGYWnaiz5AzsCNgP7KnC`
- Nguồn website: `landing-page/`. Triển khai các tệp giao diện, `api/donation`, `lib/donation.js` và tài nguyên cần thiết; không triển khai toàn bộ thư mục dự án hoặc tệp môi trường.
- Địa chỉ `.vercel.app` do Vercel cấp. Team đang dùng gói Hobby, giới hạn cho mục đích cá nhân, phi thương mại theo chính sách Vercel.
- Các biến `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY`, `BASE_URL`, `GLANCE_DONATIONS_ENABLED` được cấu hình trên Vercel cho Production. Không lưu giá trị khóa trong mã nguồn.
- Ngày 05/11/2026, website đã tạo được một liên kết PayOS 20.000 đồng cho GLANCE và hiển thị tên người nhận DAI CHUNG HY. Liên kết kiểm tra chưa được thanh toán; chưa kiểm thử giao dịch chuyển tiền thực tế.
- Bản Windows là mã nguồn cần Python, chưa kiểm thử trên Windows thật; bản Mac tải về là `Glance-macOS-1.0.0.zip`.
