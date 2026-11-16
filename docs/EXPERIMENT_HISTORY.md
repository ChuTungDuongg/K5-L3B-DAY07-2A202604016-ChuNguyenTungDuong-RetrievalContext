# Phụ lục lịch sử phát triển và đánh giá

Phụ lục giữ chi tiết các phiên bản và lượt chạy được lược khỏi báo cáo chính. File dữ liệu, trace và nhãn vẫn ở đường dẫn cũ. Dev/Test trong báo cáo là tên trình bày của hai bộ dữ liệu chính, không phải thay đổi nhãn cho mọi kết quả cũ.

## Trình tự phát triển

1. Dev gốc có 15 dòng có đáp án nhưng một cặp trùng câu hỏi data quality, nên chỉ có 14 câu khác nhau. Bản này nằm ở `starter/data/dev-original-archive`. Các lượt so sánh đầu và thử budget/search dùng bản đó. Tiêu chí lựa chọn được ghi sau khi xem một phần dev, như khai báo trong `starter/results/dev-runs/experiment-notes.md`.

2. Giới hạn output ban đầu 600 đã gây response incomplete. Sau tăng lên 1600, hai lượt dev không lỗi cho baseline 1,73/2 và ứng viên 4000 ký tự 1,87/2. Đây là căn cứ chọn sơ bộ 4000, chưa chứng minh tối ưu hoặc ưu thế ổn định.

3. Test v1 đã dùng để phát hiện lỗi output và kết nối. Sau sửa retry một lần với 3200 token, các lượt chạy lại v1 là chẩn đoán, không được coi là test độc lập cho bản sửa. Bộ này nằm ở `starter/data/test-v1-archive`.

4. Phiên bản agent được ghi hash trước khi tạo test v2 tại `starter/results/test-v2-freeze.json`. V2 là bộ Test chính, không dùng để đổi retrieval hoặc chọn lại budget. Baseline lần đầu lỗi API 400 ở câu v2-test-391. Baseline được chạy lại toàn bộ vì lỗi vận hành, giữ cùng cấu hình, cùng bộ câu và nhãn. Cả lần đầu và lần lặp được công bố.

5. Khi rà soát hồ sơ, dev-auto-373 bị trùng được thay bằng dev-extra-compliance. Bộ Dev chính có đủ 15 câu có đáp án khác nhau. Ba retrieval và ba cấu hình agent đã chạy trên bộ này sau Test, nên các số liệu đó chỉ là kiểm tra bổ sung, không viết lại lịch sử chọn trước Test.

6. Lần sửa báo cáo này đưa các bảng lịch sử sang phụ lục, không chạy lại model, không sửa benchmark hoặc nhãn và không tạo một bộ test độc lập mới. Cùng trợ lý tham gia soạn câu, triển khai và chấm nhãn nên chưa có đánh giá mù.

## Các bộ dữ liệu và cách chạy lại

| Tên lưu trữ | Nội dung và vai trò | Đường dẫn |
|---|---|---|
| Dev gốc | Bộ phát triển trước khi sửa một câu trùng | `starter/data/dev-original-archive/` |
| Dev chính | 15 câu có đáp án khác nhau + 2 thiếu bằng chứng | `starter/data/day6-A/` |
| Test v1 | Bộ cũ đã dùng chẩn đoán sau sửa controller | `starter/data/test-v1-archive/` |
| Test chính, phiên bản v2 | 5 câu có đáp án + 2 thiếu bằng chứng | `starter/data/test-v2/` |

Lệnh `python run_dev.py --method ...` đọc Dev chính. `python run_test.py --config baseline` hoặc `--config candidate` mặc định đọc Test chính, tương đương thêm `--test-version v2`. Thêm `--test-version v1` chỉ để đối chiếu lịch sử. Mọi lệnh agent đều có thể phát sinh phí và cho phản hồi khác lịch sử. Đọc JSON hoặc build lại báo cáo không gọi API.

## Metric đã chấm của các lượt lịch sử

Chỉ liệt kê các lượt ngoài phần chính đã có nhãn. Những lượt khác giữ trạng thái, thời gian và token trong [bảng toàn bộ lượt chạy](RESULTS.md), không tự tạo điểm chất lượng. Mỗi ID dưới đây dẫn tới nhãn và metric gốc.

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| [20261116-100310-agent-1ba613e8](../starter/results/dev-runs/20261116-100310-agent-1ba613e8/agent-metrics.json), dev-original, budget 2000 | 17/17 (100,0%) | 1 lượt: 12 câu, 3 lượt: 5 câu | 0/1/2 = 2/0/13, N=15, TB 1,73/2 | 13/13 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 2/15 (13,3%) |
| [20261116-100808-agent-226af6a2](../starter/results/dev-runs/20261116-100808-agent-226af6a2/agent-metrics.json), dev-original, budget 4000 | 15/15 (100,0%) | 1 lượt: 11 câu, 3 lượt: 4 câu | 0/1/2 = 1/1/11, N=13, TB 1,77/2 | 11/12 (91,7%) | 12/12 (100,0%) | 2/2 (100,0%) | 1/13 (7,7%) |
| [20261116-100808-agent-77a4573b](../starter/results/dev-runs/20261116-100808-agent-77a4573b/agent-metrics.json), dev-original, budget 2000 | 17/17 (100,0%) | 1 lượt: 12 câu, 4 lượt: 2 câu, 5 lượt: 3 câu | 0/1/2 = 2/0/13, N=15, TB 1,73/2 | 15/15 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 2/15 (13,3%) |
| [20261116-101748-agent-519fb4bf](../starter/results/dev-runs/20261116-101748-agent-519fb4bf/agent-metrics.json), dev-original, budget 2000 | 17/17 (100,0%) | 1 lượt: 13 câu, 3 lượt: 4 câu | 0/1/2 = 2/0/13, N=15, TB 1,73/2 | 13/13 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 2/15 (13,3%) |
| [20261116-101748-agent-fbc1b0be](../starter/results/dev-runs/20261116-101748-agent-fbc1b0be/agent-metrics.json), dev-original, budget 4000 | 17/17 (100,0%) | 1 lượt: 12 câu, 2 lượt: 2 câu, 3 lượt: 3 câu | 0/1/2 = 1/0/14, N=15, TB 1,87/2 | 14/14 (100,0%) | 14/14 (100,0%) | 2/2 (100,0%) | 1/15 (6,7%) |
| [20261116-103658-baseline-d7c3d519](../starter/results/test-runs/20261116-103658-baseline-d7c3d519/agent-metrics.json), test-v2, budget 2000 | 6/6 (100,0%) | 1 lượt: 2 câu, 2 lượt: 1 câu, 3 lượt: 3 câu | 0/1/2 = 2/0/2, N=4, TB 1,00/2 | 2/3 (66,7%) | 3/3 (100,0%) | 2/2 (100,0%) | 1/4 (25,0%) |

## Baseline Test lần đầu có lỗi API

Lượt `20261116-103658-baseline-d7c3d519` có 6/7 câu thành công và 1/7 lỗi API 400. Grounded answer là 1,00/2 trên bốn câu có đáp án thành công, citation hợp lệ 2/3. Lượt đầy đủ dùng trong báo cáo là `20261116-104442-baseline-1fc447dc`, đạt 1,40/2 trên năm câu và citation hợp lệ 5/7. Hai mẫu số khác nhau, không gộp hoặc lấy giá trị tốt nhất theo từng câu.

Context của lần đầu có ba câu mức 2, một câu mức 1 và một câu không có nhãn do lỗi API. Lượt chạy lại có ba câu mức 2 và hai câu mức 1. Bảng dưới giữ bảy dòng lần đầu, gồm cả lỗi.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| B lần đầu: v2-test-386 | Có đáp án | 3 search, 3 chunk, trang 384, 385, 386 | Không đủ bằng chứng để trả lời. | Trả lời 0/2, context 2/2. Context cuối trang 386 nêu đầy đủ lý do nhưng agent đạt giới hạn tìm kiếm rồi từ chối; câu có đáp án bị từ chối chấm 0. |
| B lần đầu: v2-test-387 | Có đáp án | 1 search, 3 chunk, trang 386, 387 | The tuple is selected for inclusion in the result. [openstax-intro-cs:p387:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 387 nói tuple được chọn khi điều kiện đúng, khớp câu trả lời. |
| B lần đầu: v2-test-391 | Có đáp án | Không lưu được context cuối do API error | Không có đáp án | Lỗi BadRequestError, báo riêng và không gán 0 |
| B lần đầu: v2-test-393 | Có đáp án | 3 search, 3 chunk, trang 377, 392, 393 | A tablespace is the physical storage container in which tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 393 mô tả tablespace là nơi lưu bảng và vật chứa đối tượng database. |
| B lần đầu: v2-test-397 | Có đáp án | 2 search, 3 chunk, trang 382, 397, 398 | Concurrency control [openstax-intro-cs:p397:part0:fixed:500:50:0] | Trả lời 0/2, context 1/2. Câu trả lời đúng thuật ngữ, nhưng citation trang 397 đoạn 0 chỉ liệt kê concurrency control và không chỉ ra nó điều phối giao dịch đồng thời; không đủ evidence cho kết luận. |
| B lần đầu: v2-test-no-evidence-01 | Thiếu evidence | 1 search, 3 chunk, trang 397, 399, 403 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả thông báo không đủ bằng chứng; corpus không có chính sách tổ chức hư cấu. Trace kết thúc do citation không hợp lệ hoặc thiếu, không chứng minh ý định nội bộ của model. |
| B lần đầu: v2-test-no-evidence-02 | Thiếu evidence | 3 search, 4 chunk, trang 378, 379, 399, 409 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống từ chối, phù hợp với việc corpus không có danh tính nhân sự tổ chức hư cấu; trace kết thúc do giới hạn tìm kiếm. |

## Phạm vi token và chi phí

| Phạm vi | Số lượt | Input token | Output token | USD ước tính |
|---|---|---|---|---|
| Phần chính | 8 | 94717 | 17469 | 0,01826325 |
| Lịch sử ngoài phần chính | 19 | 173655 | 32385 | 0,03379860 |
| Toàn bộ ledger | 27 | 268372 | 49854 | 0,05206185 |

Toàn bộ ledger gồm phần chính và phần lịch sử, không cộng lại ba dòng của bảng. File `results/report_selection.json` ghi rõ phép chia này. Giá và cách tính cached input/cache write giữ nguyên quy ước đã công bố ngày 16/11/2026.

Các lần soạn câu hỏi có tổng token quan sát trong phiên là 6183 nhưng không giữ đủ breakdown input/output trong artifact, nên không cộng như một chi phí chính xác. Kiểm tra key, debug và demo ngoài ledger cũng không nằm trong tổng trên. Request lỗi thiếu usage không được suy là chắc chắn bị tính 0. Giá trị này là ước tính từ log, không phải hóa đơn tài khoản.
