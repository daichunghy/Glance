---
version: 1.4.1
name: Glance Apple Pro Blue
---

# Thiết kế Glance

Nền chính là đen than `#08090c` với xanh hành động `#0071e3` và xanh nhạt `#78b8ff` cho chữ trên nền tối. Dùng nền sáng `#f5f5f7` ở cảnh AirPods để thấy hình khối trắng và ở phần tải ứng dụng. Mỗi cảnh ưu tiên một ý và một đối tượng.

Tiêu đề dùng kiểu chữ hệ thống Apple trên Mac, với Segoe UI hoặc Calibri làm lựa chọn thay thế. Nội dung ưu tiên Calibri. Dùng cỡ chữ và khoảng trống để tạo thứ bậc. Nút chính dạng con nhộng. Phân vùng bằng nền và khoảng cách thay cho đường viền trang trí.

Hero tập trung vào giá trị riêng tư khi làm việc nơi công cộng. Hình MacBook cho thấy cùng một tài liệu với vùng rõ và vùng mờ, để lợi ích đọc được trước khi cuộn. Không đặt thông số màn hình của Apple, lời giới thiệu cổng thanh toán hay prompt sản xuất trong hero.

Chuyển động bám vào vị trí cuộn. Cảnh MacBook giữ khung khi cuộn qua các góc nhìn. Góc quay, độ phóng và lớp mờ thay đổi liên tục rồi trở về trạng thái tương ứng khi cuộn ngược. Cảnh AirPods xoay theo cuộn và dừng kết xuất khi đứng yên. Dải thẻ riêng tư chạy ngang theo cuộn dọc trên máy tính và vuốt ngang trên điện thoại. Khi chọn giảm chuyển động, các cảnh hiển thị ở bố cục tĩnh. Thiết bị không có WebGL dùng ảnh AirPods tĩnh. Không đặt nút xoay hoặc nút dừng chuyển động.

Dùng các khối có kích cỡ khác nhau để trình bày những chức năng chính. Bảng khám phá thay hình và lời giải thích theo tính năng được chọn. Thẻ riêng tư mở phần chi tiết khi người xem cần đọc thêm.

Nguồn thiết kế duy nhất là [MacBook Pro và TryGlance](DESIGN_REFERENCES.md). Nội dung về quyền riêng tư, camera, AirPods và hiệu năng phải có căn cứ trong mã nguồn hoặc số đo thực tế.

Khi sửa nội dung, dùng nguyên văn câu hoặc nhãn đã có trong tài liệu Glance, giao diện ứng dụng và kịch bản đã đối chiếu với mã nguồn. Có thể bỏ phần thừa, đổi vị trí hoặc rút một cụm có sẵn làm tiêu đề. Nếu tài liệu cũ ghi khác mã đang chạy, dùng mã để kiểm tra và tìm lại câu chữ phù hợp. Khi chưa có câu phù hợp, để phần đó chờ bổ sung. Apple và TryGlance dùng để tham khảo cách đặt tên và thứ tự trình bày. Nếu dẫn lời từ nguồn bên ngoài, chỉ dùng trích đoạn ngắn và ghi nguồn.

Các câu mở đầu và nhãn về nguồn nhận diện, độ nhạy và làm mờ lấy từ [căn cứ thiết kế Glance](Tư%20liệu%20video/Căn%20cứ%20thiết%20kế%20Glance.md) và phần Cài đặt của ứng dụng. “Tìm hiểu Glance” dùng mẫu tên phần “Tìm hiểu MacBook Pro” từ trang Apple. Nội dung về cuộc gọi và bàn phím dùng cách gọi đã có trong phần hỏi đáp.
