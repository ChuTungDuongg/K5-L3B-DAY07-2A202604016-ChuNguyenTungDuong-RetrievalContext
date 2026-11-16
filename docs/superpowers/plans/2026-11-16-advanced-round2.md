# Vòng cải tiến nâng cao thứ hai

Kết quả Test vòng một là 26/30. Sau khi xem các lỗi Test, vòng một chỉ còn giá trị chẩn đoán cho phiên bản tiếp theo. Giữ nguyên benchmark, trace, nhãn, chi phí và snapshot code vòng một. Bộ Test mới phải được soạn và đóng băng độc lập trước khi chạy Dev vòng hai, tránh câu diễn đạt lại cùng một fact của 48 câu đã dùng.

- Duy trì cùng tài liệu World Bank, index, Dev 18 câu và trần chi phí tích lũy 5 USD.
- Bổ sung khả năng tính ký hiệu `÷`, `×`, `−` mà vẫn chỉ cho phép biểu thức số an toàn. Trước khi trả lời, model kiểm tra lại đối tượng đo, đơn vị, điều kiện và nguồn trên ảnh PDF gốc.
- Dẫn nguyên trang cùng nhãn vùng và trích dẫn định vị cụ thể, giữ bbox model đề xuất riêng trong trace. Đây là vùng rộng hơn, không được mô tả như crop chính xác. Chấm vẫn yêu cầu evidence thực sự hỗ trợ toàn bộ câu trả lời.
- Chạy một lượt cho mỗi cấu hình trên Dev, chấm từng câu theo nguồn, chọn bằng điểm nghiêm rồi trung vị thời gian và chi phí khi hòa. Ghi kế hoạch cùng hash trước chạy và đóng băng lựa chọn trước Test.
- Chạy toàn bộ 30 câu Test mới một lần. Chấm từng câu đối chiếu ảnh gốc, giữ lỗi và thiếu kết quả trong mẫu số. Không sửa code hoặc chạy lại Test để chọn điểm tốt.
- Báo riêng kết quả vòng một, vòng hai và tổng chi phí mọi vòng. Chỉ đề nghị bonus khi đủ yêu cầu và điểm Test mới đạt ít nhất 27/30, không làm tròn.
