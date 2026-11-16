# Hướng dẫn tái lập bài Day 7

Học viên: Chu Nguyễn Tùng Dương, MSSV 2A202604016, lớp L3B. Các lệnh dưới đây chạy trong PowerShell tại thư mục gốc repo. Không cần giữ repo Day 6 trên máy mới vì backend và snapshot vector A đã được đưa vào repo này.

## 1. Đọc số liệu đã nộp trước khi gọi API

- Báo cáo: [report/individual/2A202604016_ChuNguyenTungDuong.md](report/individual/2A202604016_ChuNguyenTungDuong.md).
- Các lượt được dùng trong báo cáo chính: [docs/RESULTS.md](docs/RESULTS.md), đối chiếu bằng [report_selection.json](results/report_selection.json). Tám lượt gồm ba retrieval Dev, ba agent Dev và hai agent Test.
- **Dev:** `starter/data/day6-A/questions-dev.json` và `agent-cases-dev.json`, gồm 15 câu có đáp án khác nhau và 2 câu thiếu bằng chứng.
- **Test:** `starter/data/test-v2/`, gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Runner mặc định đọc bộ này.
- Phiên bản cũ, lỗi API và các lần chạy lại: [phụ lục lịch sử](docs/EXPERIMENT_HISTORY.md). Bảng toàn bộ lượt và tổng chi phí lịch sử vẫn giữ trong `docs/RESULTS.md` và `results/run_ledger.json`.
- Nhãn `reviews.json` và metric `agent-metrics.json` nằm cạnh từng `traces.json`. Các bản `reviews-proposed.json` vẫn giữ lịch sử đề xuất.

Đọc JSON và chạy kiểm thử offline không gọi OpenAI. Chạy lại agent hoặc test có thể phát sinh phí và là một lượt quan sát mới, không thay thế âm thầm kết quả đã nộp.

## 2. Tạo môi trường Python

Môi trường thực nghiệm là Python 3.13.9 trên Windows. File `requirements-lock.txt` ghi toàn bộ phiên bản đã quan sát. Python 3.11 trở lên đáp ứng đề, nhưng máy dùng Python/OS khác có thể cần wheel tương ứng và không bảo đảm kết quả số học giống từng bit.

```powershell
git clone https://github.com/ChuTungDuongg/K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext.git
cd K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Có thể kích hoạt môi trường bằng `& .\.venv\Scripts\Activate.ps1`. Nếu PowerShell không cho chạy script kích hoạt, tiếp tục dùng đường dẫn `.\.venv\Scripts\python.exe` như ví dụ, không cần đổi chính sách hệ thống.

## 3. Kết nối database

Máy thực nghiệm đã dùng container `day6_student_starter-postgres-1`, PostgreSQL 16.16 và pgvector 0.8.7 tại `127.0.0.1:55433`, database `day6_lab`. Nếu dùng lại máy đó, giữ nguyên `.env` đang hoạt động và khởi động container cũ khi cần:

```powershell
docker start day6_student_starter-postgres-1
```

Trên máy mới, mở Docker Desktop rồi dùng database Day 7 riêng tại cổng 55434 để tránh xung đột với Day 6:

```powershell
docker compose -p day7_lab -f starter/docker-compose.yml up -d
docker compose -p day7_lab -f starter/docker-compose.yml ps
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Chỉ sao chép `.env.example` nếu chưa có `.env` cần giữ. Mật khẩu trong compose là mật khẩu mẫu cho lab local, cổng chỉ bind loopback. Không xóa volume Day 6 để khôi phục bài này. `.env.example` trỏ tới database mới. Khi dùng database khác, sửa `DATABASE_URL` tương ứng.

## 4. Khôi phục đúng index A của Day 6

```powershell
.\.venv\Scripts\python.exe -m starter.restore_day6
.\.venv\Scripts\python.exe -m starter.restore_day6 --check-only
```

Lệnh đầu xác minh SHA-256 của `data/day6_index_A.json.gz`, tạo extension/bảng khi cần và nạp 273 vector 384 chiều trong một transaction. Nếu A đã tồn tại, lệnh chỉ chấp nhận index khớp snapshot về ID, nội dung, nguồn, metadata và vector trong sai số cho phép. Lệnh từ chối ghi đè index A khác. `--check-only` không tạo hoặc ghi bảng.

Đã thử trên database Day 7 trống riêng, khôi phục đủ 273 vector, đối chiếu lại snapshot và kiểm tra top-3 một query trùng trace dense tham chiếu. Biên bản ở `results/restore-validation.json`. Lần thử dùng môi trường Python đã khóa và model cache sẵn có, chưa phải kiểm tra cài toàn bộ dependency trên một máy mới.

Snapshot giữ vector thật đã có từ Day 6, không tính embedding lại. Query embedding dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` tại revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Lần đầu chạy dense trên máy mới cần Internet để tải revision đó. Khi model đã có trong cache, có thể đặt `$env:HF_HUB_OFFLINE='1'` để dùng cache. Cờ này không ngắt kết nối OpenAI API.

## 5. Kiểm thử và kiểm tra hồ sơ nộp

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/verify_submission.py
```

Các test dùng adapter giả chỉ kiểm tra hành vi code. Số liệu chất lượng trong báo cáo lấy từ những lượt gọi model/database thật đã lưu, không lấy từ test giả.

## 6. Chạy ba phương pháp retrieval trên dev

```powershell
.\.venv\Scripts\python.exe run_dev.py --method dense
.\.venv\Scripts\python.exe run_dev.py --method tfidf
.\.venv\Scripts\python.exe run_dev.py --method hybrid
.\.venv\Scripts\python.exe run_dev.py --method tfidf --budget 800
```

Dense đọc pgvector. TF-IDF đọc cùng 273 chunk từ JSON. Hybrid dùng RRF với hằng số 60, lấy 10 ứng viên mỗi retriever và giữ top 3. Mặc định context budget là 2000 ký tự, tính cả ID, nguồn, trang và dấu phân cách. Các lượt này không gọi OpenAI API.

## 7. Cấu hình OpenAI và chạy agent dev

Thêm `OPENAI_API_KEY` của tài khoản vào `.env`, không đưa key vào code, terminal log hoặc Git. Phần controller là triển khai Day 7 trong `starter/agentic.py`. Backend Day 6 chỉ cung cấp embedding và pgvector, không cung cấp controller OpenAI.

```powershell
.\.venv\Scripts\python.exe run_dev.py --method agent --budget 2000 --max-searches 3
.\.venv\Scripts\python.exe run_dev.py --method agent --budget 4000 --max-searches 3
.\.venv\Scripts\python.exe run_dev.py --method agent --budget 2000 --max-searches 5
```

Để kiểm tra một câu, thêm `--case-id dev-extra-compliance`. Để chạy N câu đầu, thêm `--limit N`. Chạy có giới hạn không phải benchmark đầy đủ. `day6_agent.py` vẫn là lệnh demo tương thích, còn các lớp thật đã được chuyển vào starter.

Controller yêu cầu model trả action có cấu trúc rồi Python thực thi công cụ tìm kiếm. Đây là vòng điều phối tool tùy biến, không dùng trường `tools` native của Responses API. Model thật quyết định query và khi nào trả lời. Trạng thái `abstain` có thể do controller thiếu citation hoặc hết lượt, không luôn là model chủ động từ chối.

## 8. Chạy test sau khi chốt cấu hình

```powershell
.\.venv\Scripts\python.exe run_test.py --config baseline
.\.venv\Scripts\python.exe run_test.py --config candidate
```

Baseline dùng 2000 ký tự và ứng viên dùng 4000, cả hai dense, top-k 3 và tối đa 3 lượt search. Hai lệnh đọc bộ Test chính, tương đương chỉ định `--test-version v2`. Đây là đánh giá lại bằng code hiện tại, không tái tạo nguyên từng phản hồi lịch sử. Model API và mạng có thể cho kết quả khác, vì vậy cần giữ mọi lượt, gồm lỗi và lần chạy lại. Cách đối chiếu bộ cũ nằm trong phụ lục lịch sử.

Test runner đo thêm dense retrieval của câu hỏi gốc, không đưa kết quả của bước đo đó vào agent. Gold chỉ dùng để chấm sau khi chạy. Hit theo câu gốc và context cuối sau query viết lại phải được báo riêng.

## 9. Đọc kết quả, chấm và tổng hợp

Mỗi lượt tạo thư mục timestamp và ID ngẫu nhiên trong `starter/results/dev-runs` hoặc `test-runs`, gồm `config.json`, `traces.json`, `summary.json`. Trace được ghi sau từng câu. Lỗi khởi tạo có `run-error.json`. Nếu ngắt trước khi xong, summary có thể chưa được tạo. API không trả usage thì chi phí lượt đó không thể được suy ra từ log.

Đọc context cuối, câu trả lời và từng citation để chấm `answer_grade`, `context_grade`, `citation_support` và `abstention_correct`. Giữ nguyên nhãn đã nộp nếu chỉ đọc lại. Nếu có người chấm khác, lưu tệp mới cùng tên người chấm, không ghi đè lịch sử.

Ví dụ tổng hợp nhãn baseline Test đang dùng trong báo cáo chính:

```powershell
.\.venv\Scripts\python.exe starter/agent_metrics.py --cases starter/data/test-v2/agent-cases-test.json --traces starter/results/test-runs/20261116-104442-baseline-1fc447dc/traces.json --reviews starter/results/test-runs/20261116-104442-baseline-1fc447dc/reviews.json --split test --output results/rechecked-baseline-metrics.json
.\.venv\Scripts\python.exe scripts/summarize_results.py
```

`results/run_ledger.json` cộng số token từ toàn bộ response usage đã lưu trong các batch, có tính response incomplete được trả về. `results/report_selection.json` tách tám lượt của báo cáo chính với các lượt lịch sử, tránh gộp nhầm hai phạm vi chi phí. Giá Standard của model được ghi ngày 16/11/2026. Đây là ước tính theo token ghi nhận, không phải hóa đơn OpenAI và không bao gồm các request debug/soạn câu hỏi thiếu log. Thay đổi giá sau ngày kiểm tra sẽ làm chi phí tái lập khác.

Sau khi tổng hợp ledger, dùng `python scripts/build_report.py` để cập nhật báo cáo, danh sách lượt chính và phụ lục từ các lượt đã chỉ định. Lệnh này không chạy benchmark hoặc gọi API. Build giữ danh sách lượt chính đã công bố, các lượt phát sinh mới vẫn được ghi trong lịch sử để người đọc đánh giá riêng.

## 10. Những phần cần khai báo khi dùng kết quả

Phần chính dùng Dev và Test, còn phiên bản dữ liệu cũ và lần đầu lỗi API được giữ trong phụ lục. Cấu hình đã chọn sơ bộ trên dev gốc, bộ Dev sửa câu trùng được kiểm tra bổ sung sau Test. Baseline Test dùng lượt đầy đủ vì lần đầu lỗi API 1/7 câu, không chọn lượt dựa vào điểm. Corpus nhỏ, cùng một sách, câu thiếu evidence dùng tổ chức hư cấu và nhãn có Codex hỗ trợ, nên chưa có đánh giá mù hay kiểm định trên tài liệu khác.

## 11. Phần nâng cao độc lập

Phần World Bank dùng database Day 7 cổng 55434 và strategy riêng `ADV-WDR2021-v1`. Phần cơ bản phía trên giữ nguyên. Xem [hướng dẫn nâng cao](advanced/README.md) để tải đúng PDF, khôi phục 5493 vector và 350 ảnh có checksum. Các lệnh `python -m advanced.analyze --round 2`, `python -m advanced.verify --round 2` và `python -m advanced.report_round2` không gọi API. Sau đó `python scripts/build_report.py` điền phần nâng cao vào khung báo cáo của thầy. Mỗi lần chạy model thật tạo thư mục JSON mới, không sửa trace gốc, và phải phân biệt kết quả chính thức với lượt chẩn đoán.
