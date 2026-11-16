# Thử nghiệm agent dev ngày 16/11/2026

Baseline: dense strategy A, top_k=3, context 2000 ký tự, tối đa 3 lượt search, gpt-6-luna; lượt 20261116-100310-agent-1ba613e8.

- A: tăng context lên 4000, giữ tối đa 3 lượt. Giả thuyết: các bằng chứng tìm thấy ở lượt sau có thể được giữ thay vì bỏ vì context đã đầy. Đánh đổi: nhiều input token và độ trễ.
- B: giữ context 2000, tăng tối đa 5 lượt. Giả thuyết: agent có thêm cơ hội truy xuất lại. Đánh đổi: thêm số lượt, token và thời gian; context cũ có thể vẫn đầy.

Các cấu hình chạy trên cùng 17 câu dev, không đưa gold vào agent. Mô hình có tính ngẫu nhiên; mỗi cấu hình chỉ một lượt nên khác biệt không chứng minh quan hệ nhân quả. Tính và so sánh đúng theo nhãn kiểm tra evidence, citation và từ chối; ghi rõ chi phí và lỗi. Ưu tiên grounded answer và từ chối đúng, sau đó tỷ lệ citation có hỗ trợ; khi tương đương xét thời gian và token. Không dùng test để chọn.

Lưu ý ngày giờ: bản kế hoạch này ghi sau khi hai lượt thử đã bắt đầu, và dev01 của A đã có trạng thái answered. Vì vậy không mô tả các tiêu chí là đã được chốt trước khi xem bất kỳ kết quả; cần công bố giới hạn này trong báo cáo.
