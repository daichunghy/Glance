# Căn cứ thiết kế Glance

| Giá trị | Căn cứ trong Glance 1.0.0 | Cách thể hiện |
| --- | --- | --- |
| Làm việc riêng tư khi ngồi cạnh người khác | Glance đo góc quay đầu so với hướng đã căn giữa. Chế độ làm mờ theo bên che phía đối diện sau khi vượt ngưỡng. Không xác định ai đang nhìn trộm. | Một màn hình với tài liệu rõ ở bên đang nhìn và lớp mờ ở bên còn lại. Câu đầu nói thẳng lợi ích. |
| Che nội dung khi rời bàn | Chế độ Camera xử lý tình huống mất khuôn mặt và không có thao tác gần đây. Mã hiện tại chuyển sang mờ toàn màn hình nếu trước đó màn hình đang rõ. | Cảnh quay đầu, nhìn thẳng lại, rời khung hình. Hiệu ứng xám thể hiện lớp che, không dùng biểu tượng khóa máy. |
| Dùng camera hoặc AirPods | Camera dùng Apple Vision. AirPods tương thích gửi góc quay qua Core Motion; khi chọn nguồn này, app dừng camera của Glance. AirPods không xác định người dùng đã rời bàn. | Cảnh 3D AirPods riêng, có vị trí căn giữa và ngưỡng mặc định 20°. |
| Kiểm soát cách làm mờ | Ba mức ngưỡng 14°, 20°, 28°. Có lựa chọn làm mờ một bên hoặc toàn màn hình. Camera xét thao tác gần đây trước khi coi người dùng đã rời bàn. | Hiển thị số độ thật trong phần trình diễn và đưa các tùy chọn xuống sau cảnh chuyển động. |
| Xử lý tại máy | Luồng nhận diện dùng Vision hoặc Core Motion. Không có bước tải khung hình lên trong luồng nhận diện. Giao dịch và kiểm tra bản quyền là luồng riêng. | Nói rõ khung hình dùng cho nhận diện được xử lý trên Mac. |
| Thiết kế để chạy gọn | Ứng dụng macOS native nằm trên thanh menu. Camera dùng cấu hình độ phân giải thấp, giãn lần phân tích 120 ms và bỏ khung đến trễ. Lớp phủ dùng hiệu ứng hệ thống. | Hình thanh menu và căn cứ cụ thể. Chưa có số đo nhiệt độ, pin hay CPU trên thiết bị thật. |
| Giá và bản tải | Gói 20.000đ trọn đời, dùng thử 7 ngày. Gói đã build tại máy là 1.0.0 cho Apple silicon, ký ad hoc. | Một giá, một luồng mua, một liên kết tải bản hiện có. |

Hero ưu tiên một lợi ích và một hình có thể hiểu ngay. Nền đen làm khung cho ánh sáng xanh dương. Nội dung đang mở phải đọc được ở phần rõ. Lớp mờ nên chuyển dần ở rìa để người xem hiểu đây là một vùng của cùng một màn hình. Nhịp mở đầu lấy từ MacBook Pro, phần trình diễn ứng dụng lấy từ TryGlance. Các cảnh chi tiết không xuất hiện trước lời hứa chính.
