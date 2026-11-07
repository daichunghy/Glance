# Glance cho Windows

Thư mục này chứa mã nguồn đang phát triển. Bản Windows chưa được kiểm thử trên máy Windows thực tế và chưa có tệp cài đặt hoặc tệp `.exe` được xác minh.

- Chạy file `start_windows.bat`. Script tự động phát hiện phiên bản Python 3 có sẵn trên máy (hỗ trợ từ Python 3.10 đến mới nhất), tạo môi trường ảo `.venv`, cài đặt thư viện cần thiết và khởi chạy Glance.
- Nếu bạn tự chạy thủ công: Mở Command Prompt trong thư mục `windows`, chạy `py -3 -m pip install -r requirements.txt` rồi khởi chạy bằng `py -3 glance_windows.py`.
- **Tự khởi động cùng Windows**: Tích chọn "Khởi động cùng Windows (Tự động chạy khi bật máy)" trong giao diện. Ứng dụng sử dụng cơ chế đăng ký Registry chuẩn của Windows (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`), hoàn toàn miễn phí và không yêu cầu quyền Admin.
- **Tự động bảo vệ khi mở máy**: Tích chọn "Tự động bật camera bảo vệ khi khởi động". Khi máy tính bật lên, Glance sẽ tự chạy ngầm và kích hoạt camera canh chừng màn hình.
- **Thu nhỏ khi đóng**: Mặc định khi bấm nút `X`, Glance sẽ thu nhỏ xuống thanh Taskbar để tiếp tục duy trì bảo vệ. Bạn có thể nhấn nút "Thoát Glance" ở góc dưới để tắt hoàn toàn ứng dụng.
- **Đóng gói file chạy độc lập (.exe)**: Chạy `build_exe.bat` trên Windows để tạo `dist\Glance.exe`. Khi đã có file `.exe`, người dùng có thể nhấp đúp để dùng ngay mà không cần cài đặt Python.

Camera chỉ được dùng khi người dùng bật. Mã xử lý khung hình cục bộ, không lưu hoặc gửi khung hình. Lớp che chỉ làm tối các cửa sổ trên màn hình, không làm mờ nội dung thực và không thay thế khóa máy. Ứng dụng không xác minh danh tính, ảnh hoặc khuôn mặt người khác có thể ảnh hưởng đến nhận diện. Ánh sáng yếu, góc mặt và vật che camera cũng có thể gây nhận diện sai. Cài đặt chống che khi dùng chuột hoặc bàn phím có thể bị kích hoạt bởi bất kỳ ai thao tác trên máy.

Nếu camera bị từ chối, mất tín hiệu hoặc không phản hồi, chế độ tự động dừng và hiển thị thông báo. Khi Windows báo lỗi tạo vị trí hoặc thuộc tính lớp che, ứng dụng dừng chế độ tự động và báo không thể che màn hình. Tính năng che thủ công vẫn có thể dùng. Ứng dụng không tự phát hiện cuộc gọi, không tự nhả camera cho ứng dụng khác và không nhận diện hướng quay đầu. Các tình huống nhiều màn hình, thay đổi tỉ lệ hiển thị, màn hình khóa, cửa sổ toàn màn hình, cuộc gọi và camera ngoài cần được kiểm thử trên thiết bị thật trước khi phát hành.

Tài liệu tham khảo kỹ thuật gồm [quyền camera Windows](https://learn.microsoft.com/en-us/windows/apps/develop/camera/camera-privacy-setting), [cửa sổ trong suốt Windows](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features) và [bộ nhận diện Cascade của OpenCV](https://docs.opencv.org/4.12.0/d1/de5/classcv_1_1CascadeClassifier.html).

Việc kiểm tra kết quả của lớp che dựa trên hướng dẫn [SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos) và [SetWindowLongPtr](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowlongptrw) của Microsoft. Kiểm thử giả lập lỗi API không thay thế kiểm thử giao diện trên Windows thật.

## Cảnh báo tư thế: gù lưng, cổ rùa (đang phát triển, mặc định tắt)

Tính năng trên branch `feature/posture-guard`, chưa phát hành. Khi bật camera, tích chọn "Cảnh báo tư thế: gù lưng, cổ rùa", ngồi thẳng rồi bấm "Căn chỉnh tư thế chuẩn". Glance dùng lại khung hình camera sẵn có (logic thuần trong `posture.py`, không thêm thư viện) để nhắc khi đầu đưa ra trước hoặc sụp xuống liên tục 10 giây. Cảnh báo chỉ hiện ở dòng trạng thái tư thế trong cửa sổ, không che màn hình, không lưu hoặc gửi khung hình. Đặc tả chung: `posture/POSTURE_SPEC.md` ở thư mục gốc repo. Chạy kiểm thử tư thế bằng `py -3 -m unittest discover -s tests`.
