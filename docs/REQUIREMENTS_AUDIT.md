# Đối chiếu yêu cầu Day 7

Học viên: Chu Nguyễn Tùng Dương, MSSV 2A202604016, lớp L3B. Đối chiếu ngày 16/11/2026 với `README.md`, `GUIDE.md`, `RULES.md`, `BENCHMARK.md`, `RUBRIC.md`, `SUBMISSION.md` và mẫu báo cáo có sẵn. Bảng này chỉ xác nhận hồ sơ và chỉ ra giới hạn, không tự chấm điểm thay giảng viên.

Báo cáo chính dùng hai tên Dev và Test. [Danh sách lượt chính](../results/report_selection.json) gồm tám lượt, tương ứng ba retrieval Dev, ba agent Dev và hai agent Test. Bảng chấm Test có 14 dòng, còn phiên bản cũ và bảy dòng baseline lần đầu được chuyển sang [phụ lục lịch sử](EXPERIMENT_HISTORY.md). Trace, nhãn và dữ liệu không thay đổi.

| Yêu cầu | Bằng chứng trong repo | Kết quả và giới hạn |
|---|---|---|
| Kết nối embedding và vector store thật của Day 6 | `starter/day6_backend/`, provenance, `data/day6_index_A.json.gz`, `starter/restore_day6.py` | Đã dùng 273 vector A thật, 384 chiều. Đã khôi phục vào database Day 7 riêng và đối chiếu toàn bộ snapshot. |
| Nguồn, trang, quyền sử dụng và phiên bản | `data/ATTRIBUTION.md`, `starter/data/ATTRIBUTION.md`, `data/day6_manifest.json`, báo cáo | Có nguồn OpenStax, giấy phép CC BY-NC-SA 4.0 và hash PDF. Không nộp toàn bộ PDF. Index chỉ có 38 trang nội dung. |
| Ít nhất ba phương pháp retrieval trên cùng corpus và nhãn | `run_dev.py`, TF-IDF trong `starter/baseline.py`, dense trong `starter/agentic.py`, RRF trong `run_dev.py` | Dense, TF-IDF và hybrid đã chạy thật trên cùng bộ dev cuối. Trace có nguồn, score, rank RRF và context. |
| Controller và retriever cụ thể, model thật và truy xuất | `starter/agentic.py`, `day6_agent.py`, các trace agent | Các lớp có implementation, không còn thân `...`. Chỉ embedding/store tái sử dụng Day 6. Controller OpenAI được viết cho Day 7, dùng JSON action và vòng điều phối Python. |
| Context budget, điều kiện dừng, citation và lỗi | `starter/agentic.py`, config và events từng run | Có top-k 3, budget theo ký tự, giới hạn search, kiểm tra ID citation. Chưa kiểm chứng hỗ trợ ngữ nghĩa bằng code. Abstain có thể do validator hoặc hết lượt. Lỗi provider lưu riêng. |
| Dev ít nhất 15 câu có đáp án, 2 câu thiếu evidence | `starter/data/day6-A/questions-dev.json`, `agent-cases-dev.json` | Bản cuối đủ 15 câu có đáp án khác nhau và 2 câu thiếu. Dev cũ có một cặp câu trùng, đã lưu archive, không sửa ngược log. |
| Test ít nhất 5 câu có đáp án, 2 câu thiếu evidence | `starter/data/test-v2/` | Đủ 5+2, khác câu dev. Câu thiếu evidence dùng tổ chức hư cấu đã kiểm tra trên toàn bộ 273 chunk. Đây là dạng thiếu evidence tương đối dễ. |
| Gold có đáp án, nguồn, trang và bằng chứng | JSON câu hỏi của từng phiên bản và script kiểm tra | Gold được kiểm tra nằm trong chunk đúng nguồn/trang, không đưa vào model. Exact match có thể bỏ sót bằng chứng thay thế hợp lệ, vì vậy có thêm nhãn đọc context. |
| Hit@1, Evidence Hit@3, Context Evidence Rate | Trace, summary và `results/run_ledger.json` | Có n/N, tỷ lệ và tách câu gốc với query viết lại. Lỗi API không bị đổi thành điểm 0 và được báo riêng với mẫu số thực tế. |
| Chấm ít nhất 5 câu test có đáp án và 2 câu thiếu evidence cho cả hai cấu hình | `reviews.json`, `agent-metrics.json` của candidate v2 và baseline v2 chạy lại | Đã chấm đủ 7 câu mỗi cấu hình. Baseline lần đầu có lỗi nên chỉ chấm 6 câu thành công, vẫn giữ toàn bộ lần đầu và lần chạy lại. Có lý do context, câu trả lời và từng citation. |
| Tool use, grounded answer, citation và abstention | `starter/agent_metrics.py`, các file nhãn và báo cáo | Có phân bố lượt search, điểm 0/1/2 và trung bình, citation hỗ trợ/tổng, coverage, từ chối đúng và từ chối nhầm. Nhãn có Codex hỗ trợ, học viên xác nhận sử dụng, chưa có đánh giá độc lập giữa nhiều người chấm. |
| Ít nhất hai cải thiện có giả thuyết và phân tích lỗi | Budget 4000 so với 2000, tối đa 5 search so với 3, các bảng Dev | Cả hai đã chạy trên agent thật. Không mặc định cấu hình thử sẽ cải thiện, kết quả không tăng vẫn được giữ. Báo cáo phân tích hai ví dụ lỗi NoSQL và RDBMS, các câu còn lại có trace và nhãn tương ứng. |
| Chọn bằng dev trước test, công bố thay đổi sau test | Chú thích trong báo cáo và lịch sử chi tiết ở `docs/EXPERIMENT_HISTORY.md` | Lựa chọn 4000 được ghi theo dev gốc. Test v1 đã dùng chẩn đoán lỗi retry nên không được nhận là test độc lập của bản sửa. V2 là bộ mới sau sửa. Bộ dev bỏ câu trùng được chạy bổ sung sau test, không được gọi là lịch sử chọn trước test. Chưa có một vòng độc lập hoàn toàn mới bắt đầu từ dev cuối đã sửa. |
| Thời gian, token, model, cost và quy ước | `docs/RESULTS.md`, `results/run_ledger.json`, `results/report_selection.json`, script tổng hợp và báo cáo | Phân biệt tám lượt của phần chính với toàn bộ 27 batch, không cộng hai tổng với nhau. Cộng response usage thực sự ghi nhận. Giá Standard công khai ngày 16/11/2026, tách cached input và cache write. Tổng là ước tính, không phải hóa đơn, không bao gồm request thiếu log, chi phí local hoặc toàn bộ quá trình soạn câu hỏi. |
| Tái lập trên máy khác | `REPRODUCE.md`, compose, lock, snapshot, `results/restore-validation.json` | Đã kiểm tra database trống riêng, khôi phục 273 vector và top-3 một query khớp trace tham chiếu. Dùng môi trường Python đã khóa và cache model sẵn có, chưa thử cài lại toàn bộ wheel trên một máy Windows mới. Phản hồi API không bảo đảm tái tạo giống hệt. |
| Giữ khung và điền thông tin học viên | `report/individual/2A202604016_ChuNguyenTungDuong.md` | Giữ nguyên bốn mục cấp 2 và các cột bảng của mẫu, điền tên/MSSV/lớp. Không sửa hai file mẫu của thầy. |
| Không lộ key hoặc dữ liệu mật | `.env` được ignore, `.env.example` chỉ có chỗ nhập key | Kiểm tra bytes trong Git index trước commit. Giữ .env local ngoài Git, không ghi key vào trace hoặc báo cáo. |
| Thử thách nâng cao 100 trang có bảng, ảnh, biểu đồ | Mục cuối báo cáo | Không thực hiện và không đề nghị bonus. PDF dài 939 trang không có nghĩa index đủ 100 trang. |

## Kiểm tra văn phong và tính nhất quán

Đã dùng skill `humanizer-viet-academic`, đọc lại bản tiếng Việt và chạy công cụ `kiem_tra.py`. Công cụ chỉ còn báo hai dấu chấm phẩy ở nhãn mục giữ nguyên từ mẫu của thầy: “Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý” và “Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống”. Giữ nguyên hai nhãn theo yêu cầu không phá khung. Không sửa câu trả lời tiếng Anh trong trace để làm văn phong đẹp hơn.

`scripts/verify_submission.py` kiểm tra checksum, schema, evidence, tách split, nhãn tổng hợp, token/cost, liên kết nội bộ và cấu trúc báo cáo. Kiểm tra bổ sung đối chiếu tám lượt chính, 14 dòng chấm Test và phép chia chi phí giữa phần chính với lịch sử. Script không tự chứng minh câu trả lời có cơ sở ngữ nghĩa, không xác nhận hóa đơn hay quyền xem GitHub của giảng viên.

## Phần người học cần thực hiện khi nộp

Đọc lại báo cáo và các nhãn, giữ nguyên các khai báo giới hạn. Nộp link repo cá nhân theo kênh và hạn do giảng viên thông báo, đồng thời bảo đảm người chấm có quyền truy cập. Hồ sơ hiện tại chưa có thông báo hạn nộp hoặc kênh nộp cụ thể, nên không suy đoán hai thông tin đó. Nếu cần đánh giá độc lập hoàn toàn cho phiên bản đóng gói cuối, phải chốt cấu hình rồi tạo bộ test mới, giữ tách biệt với những lần đã xem.
