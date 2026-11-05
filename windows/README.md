# Glance cho Windows

Thư mục này chứa mã nguồn đang phát triển. Bản Windows chưa được kiểm thử trên máy Windows thực tế và chưa có tệp cài đặt hoặc tệp `.exe` được xác minh.

- Cài Python 3.11 hoặc 3.12 cùng Python Launcher, giải nén gói tải về rồi mở `start_windows.bat`. Tệp này tạo môi trường Python, cài OpenCV qua Internet và khởi chạy Glance.
- Mở Command Prompt trong thư mục `windows`, cài Python 3.11 hoặc 3.12 và chạy `py -3 -m pip install -r requirements.txt`.
- Chạy ứng dụng bằng `py -3 glance_windows.py`. Chọn số camera, thời gian chờ rồi nhấn “Bật camera”. Nếu camera mặc định không hoạt động, thử số khác và kiểm tra quyền camera dành cho ứng dụng desktop trong Windows.
- Chọn “Che màn hình ngay” để che thủ công mà không cần camera. Cửa sổ Glance vẫn dùng để bỏ che. Đóng cửa sổ để thoát.
- Chạy `build_exe.bat` trên Windows để tạo `dist\Glance.exe`. Việc đóng gói, khởi chạy và quyền camera của tệp này vẫn cần được kiểm thử trên Windows 10 và 11.

Camera chỉ được dùng khi người dùng bật. Mã xử lý khung hình cục bộ, không lưu hoặc gửi khung hình. Lớp che chỉ làm tối các cửa sổ trên màn hình, không làm mờ nội dung thực và không thay thế khóa máy. Ứng dụng không xác minh danh tính, ảnh hoặc khuôn mặt người khác có thể ảnh hưởng đến nhận diện. Ánh sáng yếu, góc mặt và vật che camera cũng có thể gây nhận diện sai. Cài đặt chống che khi dùng chuột hoặc bàn phím có thể bị kích hoạt bởi bất kỳ ai thao tác trên máy.

Nếu camera bị từ chối, mất tín hiệu hoặc không phản hồi, chế độ tự động dừng và hiển thị thông báo. Khi Windows báo lỗi tạo vị trí hoặc thuộc tính lớp che, ứng dụng dừng chế độ tự động và báo không thể che màn hình. Tính năng che thủ công vẫn có thể dùng. Ứng dụng không tự phát hiện cuộc gọi, không tự nhả camera cho ứng dụng khác và không nhận diện hướng quay đầu. Các tình huống nhiều màn hình, thay đổi tỉ lệ hiển thị, màn hình khóa, cửa sổ toàn màn hình, cuộc gọi và camera ngoài cần được kiểm thử trên thiết bị thật trước khi phát hành.

Tài liệu tham khảo kỹ thuật gồm [quyền camera Windows](https://learn.microsoft.com/en-us/windows/apps/develop/camera/camera-privacy-setting), [cửa sổ trong suốt Windows](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features) và [bộ nhận diện Cascade của OpenCV](https://docs.opencv.org/4.12.0/d1/de5/classcv_1_1CascadeClassifier.html).

Việc kiểm tra kết quả của lớp che dựa trên hướng dẫn [SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos) và [SetWindowLongPtr](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowlongptrw) của Microsoft. Kiểm thử giả lập lỗi API không thay thế kiểm thử giao diện trên Windows thật.
