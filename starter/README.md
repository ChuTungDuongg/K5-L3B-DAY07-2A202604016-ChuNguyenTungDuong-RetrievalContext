# Starter Day 7 đã hiện thực

Triển khai của Chu Nguyễn Tùng Dương, MSSV 2A202604016. Hướng dẫn tái lập đầy đủ nằm ở [REPRODUCE.md](../REPRODUCE.md).

| File | Vai trò thực tế |
|---|---|
| `agentic.py` | `Controller.decide` gọi OpenAI thật, `Retriever.search` gọi embedding và pgvector, `run_agent` điều phối context/citation |
| `day6_backend/` | Backend Day 6 được đưa vào repo với provenance, không phụ thuộc đường dẫn repo cũ |
| `baseline.py` | TF-IDF, đóng gói context và kiểm tra evidence |
| `restore_day6.py` | Khôi phục snapshot 273 vector A và từ chối ghi đè index khác |
| `agent_metrics.py` | Tổng hợp nhãn do người chấm xác nhận, không tự suy ra grounding từ citation ID |
| `convert_day6.py` | Công cụ chuyển schema JSON khi cần |
| `docker-compose.yml` | Database local riêng tại 127.0.0.1:55434 cho máy mới |

Các lớp `Controller` và `Retriever` hiện là lớp cụ thể, không còn thân hàm `...` của Protocol. Trong các kiểm thử, đối tượng giả vẫn có thể được truyền vào `run_agent` theo cùng giao diện. Những đối tượng giả không được dùng để báo chất lượng agent.

Chạy từ thư mục gốc sau khi đã cài môi trường và cấu hình `.env`:

```powershell
python -m starter.restore_day6 --check-only
python -m unittest discover -s tests -v
python run_dev.py --method dense
python run_dev.py --method tfidf
python run_dev.py --method hybrid
python run_dev.py --method agent --budget 2000 --max-searches 3
python run_dev.py --method agent --budget 4000 --max-searches 3
python run_test.py --config baseline --test-version v2
python run_test.py --config candidate --test-version v2
```

Agent dùng model thật để trả action JSON có cấu trúc, rồi Python gọi retriever. Đây là công cụ tìm kiếm trong vòng lặp tùy biến, không phải cấu hình `tools` native của OpenAI. `day6_agent.py` ở thư mục gốc chỉ giữ lệnh demo và tên alias tương thích.

Mỗi lần batch chạy tạo thư mục riêng trong `results/dev-runs` hoặc `results/test-runs`, ghi config, trace sau từng câu và summary. Thư mục này chứa cả kết quả lỗi và chạy lại. Các file lịch sử đã nộp được đưa vào Git bằng danh sách rõ ràng dù `.gitignore` vẫn bỏ qua dữ liệu phát sinh mới theo mặc định.

Dữ liệu cuối gồm 17 câu dev và 7 câu test v2, phân tách câu có đáp án và thiếu bằng chứng. `reviews.json` là nhãn có người học xác nhận, `reviews-proposed.json` giữ bản đề xuất trước đó. Nguồn trích đoạn và quyền sử dụng nằm ở [ATTRIBUTION](data/ATTRIBUTION.md). Không ghi API key hoặc database URL chứa thông tin bí mật vào trace.

Khung context ưu tiên chunk từ lượt trước. Các chunk mới có thể bị bỏ khi budget đã đầy. Kiểm tra citation trong code chỉ xác nhận ID có trong context và trong câu trả lời, không xác nhận nguồn hỗ trợ nội dung. Nhãn câu trả lời, từng citation, context và từ chối phải được đối chiếu với nguồn. Trạng thái `abstain` cũng có thể do hết lượt tìm hoặc citation không đạt kiểm tra.
