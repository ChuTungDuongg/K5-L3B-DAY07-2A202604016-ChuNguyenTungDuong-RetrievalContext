# Kế hoạch đánh giá test Day 7

Ghi trước khi chạy các lượt test này. Người dùng đã đồng ý tiếp tục với baseline 2000 ký tự và ứng viên 4000 ký tự; cả hai dùng dense strategy A, top-k 3, tối đa 3 lượt tìm, model gpt-6-luna và giới hạn 1600 output token.

Căn cứ lựa chọn ứng viên: chạy dev ngày 16/11/2026 trên cùng 17 câu, mã sau khi tăng giới hạn output. Baseline `20261116-101748-agent-519fb4bf` có điểm đề xuất 1,73/2 trên 15 câu có đáp án; ứng viên `20261116-101748-agent-fbc1b0be` có 1,87/2; cả hai từ chối đúng 2/2 câu thiếu bằng chứng và không báo lỗi. Nhãn do Codex đề xuất, chưa được học viên xác nhận; mỗi cấu hình mới chạy một lượt.

Giới hạn: một số tiêu chí đã ghi sau khi thấy một phần dev; bộ dev nhỏ, có câu gần trùng; benchmark test do cùng trợ lý tạo và đã được đọc để đối chiếu evidence, vẫn cùng corpus sách nên không phải đánh giá mù hay độc lập giữa người chấm. Những lần chạy lại test sau khi sửa cấu hình không thể coi là holdout mới.

Chạy cả hai trên cùng bảy câu, giữ kết quả riêng. Hit gốc, context và nhãn tự động chỉ xét exact gold; phải chấm thêm context 0/1/2, grounded answer, từng citation và abstention bằng cách đọc trace, evidence nguồn. Báo riêng lỗi và token.

## Chạy chẩn đoán lại sau khi xem test
Sau khi thấy baseline test-388 bị incomplete và toàn bộ candidate lỗi kết nối, thay đổi controller để thử lại một lần với 3200 output token nếu response incomplete do giới hạn output; SDK retry tối đa hai lần với lỗi kết nối. Hai cấu hình tiếp tục budget 2000/4000, nhưng phiên bản đã thay đổi dựa trên kết quả test, nên các lượt chạy lại là chẩn đoán, không phải đánh giá test độc lập của phiên bản này. Giữ toàn bộ kết quả lỗi gốc. Cần tập test mới sau khi chốt phiên bản sửa.
