# Báo cáo Day 7

Họ và tên: Chu Nguyễn Tùng Dương (ChuNguyenTungDuong)

MSSV: 2A202604016. Lớp: L3B. Ngày thực nghiệm và tổng hợp: 16/11/2026, múi giờ Việt Nam UTC+7.

Repo bài nộp: [K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext](https://github.com/ChuTungDuongg/K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext).

Bài thực hành gồm ba phương pháp tìm kiếm là Dense, TF-IDF và Hybrid, cùng ba cấu hình agent dùng Dense. Phần chính trình bày hai split Dev và Test. Các phiên bản dữ liệu cũ, lượt debug và kết quả trước lần chạy lại nằm trong [phụ lục lịch sử](../../docs/EXPERIMENT_HISTORY.md). Nhãn có Codex hỗ trợ đối chiếu, học viên xác nhận sử dụng và chưa có người chấm độc lập.

Phần nâng cao dùng riêng tài liệu World Bank 350 trang, Dev 18 câu và Test 30 câu. Mục cuối giữ kết quả, chi phí và giới hạn riêng, không trộn với hai split cơ bản.

## Dữ liệu và benchmark

- Nguồn, quyền sử dụng, số trang và số chunk:

  Corpus lấy từ chương 8 về quản lý dữ liệu trong sách [Introduction to Computer Science](https://openstax.org/details/books/introduction-computer-science), OpenStax, Rice University. PDF Day 6 đã dùng có 939 trang vật lý, SHA-256 `fd56aaf80c851e9f3b417745785ea5c832fc2911acfd2094a86f4c517fdf435a`. Giấy phép ở trang PDF 4 là CC BY-NC-SA 4.0. Bài thực hành dùng trích đoạn cho mục đích giáo dục phi thương mại và giữ ghi công, đường dẫn nguồn cùng điều kiện chia sẻ trong [ATTRIBUTION](../../data/ATTRIBUTION.md).

  Phạm vi là 38 trang PDF từ 370 đến 410, loại 389, 394 và 408 vì nhiều bảng hoặc hình. Số trang trong gold và trace là trang vật lý bắt đầu từ 1, khác số in ở chân sách. Chiến lược A của Day 6 dùng cửa sổ tối đa 500 ký tự, overlap 50, tạo 273 chunk. Các ID, nguồn, trang, nội dung, metadata và vector được giữ lại, không tạo embedding giả. Database cũ còn 290 chunk B, nhưng Day 7 chỉ dùng A cho cả ba phương pháp. Manifest ở `data/day6_manifest.json`, JSON chunk ở `starter/data/day6-A/chunks.json` và snapshot vector ở `data/day6_index_A.json.gz`.

- Vector store, embedding model, phiên bản và số chiều:

  Database thực nghiệm là PostgreSQL 16.16 với pgvector 0.8.7, image `pgvector/pgvector:0.8.7-pg16`, container Day 6 tại loopback cổng 55433. Bảng `lab_chunks` có khóa ghép `(strategy, chunk_id)`, vector 384 chiều và không có HNSW hoặc IVFFlat trong thí nghiệm. Dense dùng exact cosine search qua `<=>`, trả score `1 - cosine_distance` và lọc `strategy = A`. Không dùng metadata filter trong các lượt batch, không suy filter từ gold.

  Query và chunk dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revision cache `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, 384 chiều. Bản đóng gói cuối khóa revision này để tái lập. Môi trường quan sát: Python 3.13.9, sentence-transformers 6.3.0, PyTorch 2.15.0, transformers 5.23.0, psycopg 3.3.8, openai 3.51.0 và python-dotenv 1.2.4. Các phiên bản đầy đủ nằm ở `requirements-lock.txt` và `data/runtime-observed.json`.

  Backend embedding và pgvector được tái sử dụng từ Day 6 rồi đưa vào `starter/day6_backend`, với provenance và hash file nguồn. Controller OpenAI là phần triển khai mới của Day 7. `Controller.decide` và `Retriever.search` trong `starter/agentic.py` là lớp cụ thể, còn `day6_agent.py` giữ alias và lệnh demo tương thích. Việc sắp xếp file cuối không được trình bày như thể các log cũ đã chạy bằng cấu trúc file này.

- Agent model, cách chạy và phân chia dev/test:

  Agent gọi `gpt-6-luna` qua OpenAI Responses API và SDK Python. Model quyết định action JSON theo schema, sau đó Python thực thi retriever hoặc trả lời. Đây là vòng điều phối công cụ tùy biến, không dùng khai báo `tools` native của API. Model hỗ trợ structured output, nhưng phản hồi vẫn có thể incomplete hoặc lỗi. Bộ kiểm thử offline dùng mock chỉ kiểm tra code, không tạo số liệu benchmark chất lượng.

  Các tên Dev và Test dưới đây tương ứng với hai bộ dữ liệu sau. Tiền tố phiên bản trong tên thư mục hoặc Query ID được giữ để đối chiếu trace.

  | Split | Số câu | Vai trò | Dữ liệu |
  |---|---|---|---|
  | Dev | 15 câu có đáp án khác nhau + 2 câu thiếu bằng chứng | So sánh ba phương pháp retrieval và ba cấu hình agent | `starter/data/day6-A/` |
  | Test | 5 câu có đáp án + 2 câu thiếu bằng chứng | So sánh baseline với ứng viên đã chọn | `starter/data/test-v2/` |

  Dev dùng lại bốn câu Day 6 là `day6-q01`, `day6-q03`, `day6-q06`, `day6-q08`. Test có evidence ở các trang 386, 387, 391, 393 và 397. Cấu hình được chọn sơ bộ trên dev gốc. Bộ Dev trong bảng đã sửa một câu trùng và được kiểm tra bổ sung sau Test, nên không được xem là một vòng lựa chọn mới trước Test. Lịch sử và thời điểm thay đổi nằm trong phụ lục.

- Cách xác định câu có/thiếu evidence và tiêu chí chấm:

  Câu có đáp án lưu `question`, `expected_answer` và gold gồm `source_id`, `page`, `evidence`. Script xác nhận mỗi evidence nằm nguyên văn trong chunk đúng nguồn và trang. Khi soạn câu, evidence được đọc lại để loại trường hợp chỉ có thuật ngữ mà không có quan hệ cần trả lời. Gold và đáp án chuẩn chỉ đi vào evaluator, không đi vào model hay retriever query. Các câu mới có AI hỗ trợ soạn từ corpus nên có nguy cơ gần cách diễn đạt của nguồn.

  Các câu thiếu bằng chứng hỏi về chi tiết nội bộ của tổ chức hư cấu. Tên tổ chức được kiểm tra trên toàn bộ 273 chunk A và không xuất hiện. Đây là bằng chứng về phạm vi corpus, không phải kết luận dựa vào top 3 không tìm thấy. Các câu này tương đối dễ nhận biết và không đại diện cho trường hợp thiếu bằng chứng tinh vi gần chủ đề. Các câu thiếu bằng chứng không vào mẫu số Hit@1, Evidence Hit@3 hoặc Context Evidence Rate.

  Hit@1 và Evidence Hit@3 kiểm tra đúng nguồn, trang và chứa nguyên văn evidence ở top 1 hoặc top 3. Context Evidence Rate tự động kiểm tra gold trong context cuối. Nhãn thủ công chấm context 0 khi thiếu evidence, 1 khi chỉ có một phần hoặc thiếu điều kiện và 2 khi đủ nội dung cùng nguồn. Grounded answer chấm 0 khi sai hoặc thiếu evidence, 1 khi đúng một phần và 2 khi đúng đủ. Từ chối câu có đáp án nhận 0. Vì vậy, câu trả lời đúng từ khóa vẫn có thể nhận 0 nếu citation không hỗ trợ quan hệ được hỏi.

  Citation chỉ được tính hợp lệ khi ID có trong context và nội dung nguồn hỗ trợ khẳng định tương ứng. Một câu trả lời có nhiều citation được chấm từng citation. Đáp án khác gold nhưng nguồn hỗ trợ vẫn có thể được chấp nhận, như banking và health care cho câu yêu cầu nêu hai ngành. Trường hợp chưa có gold thay thế vẫn có thể làm metric exact-match thấp hơn đánh giá thủ công. Nhãn ở `reviews.json` lưu lý do và danh tính người hỗ trợ chấm, còn `reviews-proposed.json` giữ bản đề xuất trước xác nhận.

## Retrieval và thử nghiệm

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| Baseline | Dense cosine pgvector, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | Dev | 14/15 (93,3%) | 14/15 (93,3%) | 14/15 (93,3%) | trung vị 0,0922 s/câu, tổng 1,416 s, 0,00000000 USD |
| Phương pháp 2 | TF-IDF, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | Dev | 13/15 (86,7%) | 15/15 (100,0%) | 15/15 (100,0%) | trung vị 0,0009 s/câu, tổng 0,013 s, 0,00000000 USD |
| Phương pháp 3 | Hybrid RRF, 10 ứng viên mỗi nhánh, hằng số 60, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | Dev | 14/15 (93,3%) | 15/15 (100,0%) | 15/15 (100,0%) | trung vị 0,0917 s/câu, tổng 1,466 s, 0,00000000 USD |
| Cải thiện 1 | Agent dense, budget 4000, tối đa 3 search, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | Dev | 14/15 (93,3%) câu gốc | 14/15 (93,3%) câu gốc | 13/14 (92,9%) trên câu chạy thành công | trung vị 10,6577 s/câu, tổng 258,671 s, 0,00518235 USD, lỗi 1/17 |
| Cải thiện 2 | Agent dense, budget 2000, tối đa 5 search, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | Dev | 14/15 (93,3%) câu gốc | 14/15 (93,3%) câu gốc | 12/14 (85,7%) trên câu chạy thành công | trung vị 11,5531 s/câu, tổng 274,421 s, 0,00469830 USD, lỗi 1/17 |
| Cấu hình đã chọn | Agent dense, budget 4000, tối đa 3 search, top 3 | Cùng bộ Test, baseline dùng lượt chạy lại do lỗi API | Test | 2/5 (40,0%) câu gốc | 4/5 (80,0%) câu gốc | 4/5 (80,0%) exact gold | trung vị 10,1901 s/câu, tổng 65,659 s, 0,00254600 USD |
| Baseline | Agent dense, budget 2000, tối đa 3 search, top 3 | Cùng bộ Test, baseline dùng lượt chạy lại do lỗi API | Test | 2/5 (40,0%) câu gốc | 4/5 (80,0%) câu gốc | 3/5 (60,0%) exact gold | trung vị 6,4914 s/câu, tổng 46,985 s, 0,00171740 USD |

Một cấu hình có thể đồng thời là phương pháp mới và cải thiện. Các tỷ lệ và thời gian ở bảng này phải được đọc cùng mẫu số và lỗi từng lượt.

  Dense, TF-IDF và Hybrid được chạy trên cùng 15 câu có đáp án của Dev, cùng 273 chunk A và câu hỏi gốc. TF-IDF dùng cách tách từ đơn giản trong starter, vector từ vựng chuẩn hóa và cosine. Hybrid lấy top 10 của Dense và TF-IDF, cộng `1/(60 + rank)` theo ID rồi giữ top 3. Cả TF-IDF và Hybrid giữ được gold trong top 3 cho 15/15 câu, còn Dense đạt 14/15 trong lượt này. Agent chỉ dùng Dense, không chạy mọi tổ hợp của ba phương pháp với ba cấu hình.

  Hai dòng cải thiện giữ Hit@1/Hit@3 của phép đo dense bằng câu gốc làm mốc so sánh. Đây không phải ranking của query do agent viết lại. CER của hai dòng đó là context cuối sau nhiều lượt tìm và chỉ có mẫu số câu có đáp án chạy thành công, nên không được so trực tiếp như các mẫu số đều bằng 15. Các query viết lại, thứ hạng từng lượt và context tích lũy nằm trong trace.

  Baseline dùng 2000 ký tự và tối đa 3 lượt tìm. Cải thiện 1 tăng budget lên 4000, với giả thuyết giữ được evidence tìm thấy ở lượt sau. Cải thiện 2 giữ 2000 và tăng giới hạn lên 5 lượt, với giả thuyết có thêm cơ hội tìm lại. Ứng viên được chọn sơ bộ để đánh giá Test là cải thiện 1. Kết quả Dev trình bày ở đây có lỗi API và mẫu số khác nhau, chưa xác nhận ưu thế ổn định của 4000. Số liệu làm căn cứ lựa chọn ban đầu nằm trong phụ lục lịch sử.

  Hai ví dụ lỗi dưới đây lấy từ giai đoạn phát triển, có trace và cấu hình tương ứng trong phụ lục. Với `dev01` về trọng tâm NoSQL, TF-IDF đưa gold ở trang 380 lên hạng 2, Dense chỉ tìm thấy đoạn đó ở hạng 10 trong demo. Budget 800 chỉ giữ đoạn hạng 1 dài 627 ký tự, còn budget 2000 giữ được ba đoạn tổng 1882 ký tự. Model có lần mở rộng query nhưng vẫn không tìm được gold. Đây là lỗi ranking, query và chọn context, dù corpus có đáp án.

  Lỗi dev thứ hai là `dev-auto-383` về dữ liệu mà RDBMS không phù hợp. Ở trace baseline gốc, gold trang 383 đã xuất hiện ở lượt 2 và 3 nhưng bị bỏ vì context ưu tiên các đoạn trước. Tăng budget có lần giữ được bằng chứng đầy đủ và có lần chỉ đưa vào một đoạn thay thế ở trang 403 về dữ liệu phi cấu trúc, còn thiếu bán cấu trúc. Do đó, tăng budget có thể giảm mất bằng chứng nhưng chưa thay thế được việc chọn lại context theo độ liên quan. Báo cáo không coi tất cả câu answered là đúng đủ.

  Hướng cải tiến sau thực nghiệm là xếp lại candidate mới và cũ, deduplicate theo nội dung rồi chọn evidence dưới budget. Hướng này chưa được triển khai hoặc đo, nên không có số liệu cải thiện tương ứng. Nếu thực hiện, cần chọn bằng dev và đánh giá bằng một bộ test chưa dùng để chỉnh.

## Agent và đánh giá

- Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:

  Công cụ dense tạo query embedding thật rồi gọi PostgreSQL, trả ID, văn bản, nguồn, trang, metadata và score. Model nhận câu hỏi cùng context cuối tích lũy, không nhận nhãn answerable, expected answer hoặc gold. Cumulative context ưu tiên thứ tự candidate của những lượt trước, bỏ ID trùng và bỏ chunk không vừa budget. Budget tính bằng số ký tự Python, gồm nhãn nguồn và dấu phân cách, không phải số token model. Chunk dài không được tự cắt hoặc nén để nhét vào context.

  Cấu hình baseline dừng sau tối đa 3 search, ứng viên cũng 3 và thí nghiệm thêm lượt cho phép 5. Vòng lặp có một lần quyết định sau lượt search cuối để model trả lời. Nếu model tiếp tục yêu cầu search vượt giới hạn, hệ thống trả abstain. Nếu citation thiếu, không có trong context hoặc không xuất hiện dạng `[id]` trong answer, hệ thống cũng trả thông báo không đủ bằng chứng. Các trạng thái này đánh giá phản hồi cuối của hệ thống, không luôn chứng minh model đã chủ động nhận biết thiếu thông tin.

  Controller dùng structured JSON action và nhắc model coi tài liệu là dữ liệu, chưa có thử nghiệm prompt injection riêng. Lỗi API, parse JSON và database được báo riêng. Giới hạn output hiện tại là 1600, thử lại tối đa một lần với 3200 khi API báo incomplete vì giới hạn output. Usage của response incomplete vẫn được cộng. Test runner cho SDK thử lại lỗi kết nối tối đa 2 lần, còn Dev dùng max_retries 0. Lịch sử sửa giới hạn output nằm trong phụ lục.

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| Dev, baseline | 15/15 (100,0%) | 1 lượt: 13 câu, 3 lượt: 2 câu | 0/1/2 = 1/0/12, N=13, TB 1,85/2 | 12/12 (100,0%) | 12/12 (100,0%) | 2/2 (100,0%) | 1/13 (7,7%) |
| Dev, cải thiện 1 | 16/16 (100,0%) | 1 lượt: 10 câu, 2 lượt: 2 câu, 3 lượt: 4 câu | 0/1/2 = 1/1/12, N=14, TB 1,79/2 | 15/15 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 1/14 (7,1%) |
| Dev, cải thiện 2 | 16/16 (100,0%) | 1 lượt: 12 câu, 5 lượt: 4 câu | 0/1/2 = 2/0/12, N=14, TB 1,71/2 | 12/12 (100,0%) | 12/12 (100,0%) | 2/2 (100,0%) | 2/14 (14,3%) |
| Test, baseline | 7/7 (100,0%) | 1 lượt: 5 câu, 2 lượt: 1 câu, 3 lượt: 1 câu | 0/1/2 = 1/1/3, N=5, TB 1,40/2 | 5/7 (71,4%) | 5/5 (100,0%) | 2/2 (100,0%) | 0/5 (0,0%) |
| Test, ứng viên | 7/7 (100,0%) | 1 lượt: 2 câu, 3 lượt: 5 câu | 0/1/2 = 1/0/4, N=5, TB 1,60/2 | 5/5 (100,0%) | 4/4 (100,0%) | 2/2 (100,0%) | 1/5 (20,0%) |

  Lỗi được tách khỏi mẫu số chất lượng theo starter. Dev có 2 lỗi ở baseline và 1 lỗi ở mỗi cải thiện, nên điểm câu trả lời dùng N=13 hoặc N=14. Hai cấu hình Test đều có N=5 ở các lượt trong bảng. Baseline Test dùng lượt chạy lại đầy đủ do lượt đầu lỗi API 400 ở 1/7 câu. Lượt đầu và nhãn của sáu câu thành công được giữ trong [phụ lục lịch sử](../../docs/EXPERIMENT_HISTORY.md). Lượt chạy lại giữ cùng cấu hình và được thực hiện vì lỗi API, không chọn dựa vào điểm. Mẫu số khác nhau và lỗi hệ thống hạn chế khả năng so sánh.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| B: v2-test-386 | Có đáp án | 1 search, 3 chunk, trang 384, 385, 386 | They are considered primitive because they form a sufficient basic set: every other relational algebra operator can be derived by combining Select, Project, Difference, Product, and Union. [openstax-intro-cs:p386:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Context trang 386 nói đủ rằng mọi phép còn lại có thể suy ra từ năm phép primitive; câu trả lời và citation phù hợp. |
| B: v2-test-387 | Có đáp án | 2 search, 3 chunk, trang 386 | The tuple is included in the query’s result relation, with the specified attribute values retrieved. [openstax-intro-cs:p386:part0:fixed:500:50:3150] | Trả lời 1/2, context 1/2. Câu trả lời nêu tuple được đưa vào kết quả; đoạn trích trang 386 nói condition dùng để chọn tuple và truy xuất thuộc tính nhưng không nêu rõ khi công thức nhận giá trị true thì tuple được chọn. Chấm thận trọng một phần; gold cụ thể ở trang 387 không nằm trong context cuối. |
| B: v2-test-391 | Có đáp án | 1 search, 3 chunk, trang 390, 391 | A dependent is fully identified using the key of its strong owner (the employee), combined with the dependent’s partial key, if it has one. The owner’s key supplies the context needed to identify the weak entity [openstax-intro-cs:p391:part0:fixed:500:50:0] [openstax-intro-cs:p391:part0:fixed:500:50:450] [openstax-intro-cs:p390:part0:fixed:500:50:2250]. | Trả lời 2/2, context 2/2. Hai đoạn trang 391 hỗ trợ ID employee và kết hợp partial key nếu có; đoạn cuối trang 390 hỗ trợ phải dựa vào strong entity để cung cấp ngữ cảnh nhận dạng, dù đoạn trích bị cắt ở đầu. |
| B: v2-test-393 | Có đáp án | 1 search, 3 chunk, trang 377, 392, 393 | A tablespace is the physical storage container in which database tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Đoạn trang 393 mô tả tablespace là nơi lưu bảng và vật chứa database objects, phù hợp câu trả lời. |
| B: v2-test-397 | Có đáp án | 1 search, 3 chunk, trang 382, 397, 398 | Concurrency control addresses the coordination of simultaneous database activity. [openstax-intro-cs:p397:part0:fixed:500:50:0] | Trả lời 0/2, context 1/2. Đáp án nêu đúng concurrency control nhưng đoạn citation trang 397 chỉ liệt kê nó là tính năng; không giải thích điều phối giao dịch đồng thời. Định nghĩa gold không có trong context cuối, nên câu trả lời thiếu evidence. |
| B: v2-test-no-evidence-01 | Thiếu evidence | 1 search, 3 chunk, trang 383, 397, 403 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả không đủ bằng chứng; tên tổ chức hư cấu không xuất hiện trong 273 chunk A. Event kết thúc invalid_or_missing_citations nên không đủ thông tin để kết luận model chủ động từ chối. |
| B: v2-test-no-evidence-02 | Thiếu evidence | 3 search, 4 chunk, trang 378, 379, 399, 409 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả không đủ bằng chứng; tổ chức hư cấu không xuất hiện trong corpus. Kết thúc do search_limit; không đủ thông tin để kết luận model chủ động từ chối. |
| C: v2-test-386 | Có đáp án | 1 search, 3 chunk, trang 384, 385, 386 | Select, Project, Difference, Product, and Union are called primitive because all other relational algebra operators can be derived from them [openstax-intro-cs:p386:part0:fixed:500:50:0]. | Trả lời 2/2, context 2/2. Nguồn trang 386 ghi các phép toán còn lại được suy ra từ năm phép cơ bản. |
| C: v2-test-387 | Có đáp án | 3 search, 5 chunk, trang 386, 387 | If the formula evaluates to true for a tuple, that tuple is selected in the result. [openstax-intro-cs:p387:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 387 nói tuple được chọn khi điều kiện đúng, khớp câu trả lời. |
| C: v2-test-391 | Có đáp án | 3 search, 4 chunk, trang 390, 391 | A dependent is fully identified using the key of its owning strong entity (the employee) together with the dependent’s partial key, if any. [openstax-intro-cs:p391:part0:fixed:500:50:0] [openstax-intro-cs:p391:part0:fixed:500:50:450] | Trả lời 2/2, context 2/2. Nguồn trang 391 đoạn 0 nêu ID employee, đoạn 450 nêu khóa kết hợp với partial key nếu có; cả hai hỗ trợ nội dung tương ứng. |
| C: v2-test-393 | Có đáp án | 3 search, 4 chunk, trang 377, 383, 392, 393 | A tablespace is the physical storage container in which database tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 393 nêu tablespace chứa bảng và là vật chứa đối tượng database. |
| C: v2-test-397 | Có đáp án | 3 search, 4 chunk, trang 382, 395, 397, 398 | Không đủ bằng chứng để trả lời. | Trả lời 0/2, context 1/2. Agent từ chối khi hết lượt tìm; context có tên concurrency control nhưng không có định nghĩa liên kết nó với việc điều phối hoạt động đồng thời. |
| C: v2-test-no-evidence-01 | Thiếu evidence | 1 search, 3 chunk, trang 383, 397, 403 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả thông báo không đủ bằng chứng; corpus không có chính sách tổ chức hư cấu. Trace kết thúc do citation không hợp lệ hoặc thiếu, không chứng minh ý định nội bộ của model. |
| C: v2-test-no-evidence-02 | Thiếu evidence | 3 search, 4 chunk, trang 377, 378, 379, 399 | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống từ chối, phù hợp với việc corpus không có danh tính nhân sự tổ chức hư cấu; trace kết thúc do giới hạn tìm kiếm. |

  B là baseline 2000, C là ứng viên 4000. Bảng có 14 dòng, đủ bảy câu cho mỗi cấu hình. Với baseline, câu 387 nhận 1/2 vì nguồn thiếu điều kiện true, câu 397 nhận 0 vì citation chỉ liệt kê thuật ngữ. Context baseline có ba câu mức 2 và hai câu mức 1, ứng viên có bốn câu mức 2 và một câu mức 1. Chi tiết từng chunk và toàn bộ tool call nằm trong trace. Các nhãn có tính diễn giải và chưa được đối chiếu giữa nhiều người chấm.

- Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:

  Phần chính dùng tám lượt đã lưu: ba lượt retrieval Dev, ba lượt agent Dev và hai lượt agent Test. [Danh sách lượt chính và toàn bộ lịch sử](../../docs/RESULTS.md) dẫn tới config, trace, summary và nhãn. File [report_selection.json](../../results/report_selection.json) ghi rõ các lượt dùng trong báo cáo. JSON được ghi sau mỗi câu, nhưng exception giữa vòng agent có thể làm thiếu các event trước lỗi. Khi đó không tự gán context grade 0 cho lần lỗi.

  Thời gian là elapsed theo từng câu, không tính khởi tạo model, tải weights, tạo TF-IDF index hoặc ghi file. Trung vị chỉ xét câu không lỗi. Tổng thời gian là tổng elapsed của tất cả câu, có cả thời gian chờ của câu lỗi, không phải thời gian toàn tiến trình. Test runner tính cả truy xuất câu gốc trước vòng agent, trong khi dev agent runner không có bước đo đó. Một số lượt chạy đồng thời nên độ trễ chịu ảnh hưởng mạng và tranh chấp tài nguyên. Chưa đo RAM, CPU riêng, cold start, tải đồng thời có kiểm soát hoặc độ biến thiên qua nhiều lần lặp cân bằng.

| Lượt | Input token | Output token | Cached input | Cache write 30m / 12h | Tổng elapsed câu (s) | Trung vị câu thành công (s) | Chi phí ước tính | Lỗi / số câu |
|---|---|---|---|---|---|---|---|---|
| Dev, baseline | 18592 | 4520 | 0 | 0 / 0 | 241,856 | 5,7131 | 0,00411920 USD | 2/17 |
| Dev, cải thiện 1 | 24445 | 5421 | 0 | 1094 / 0 | 258,671 | 10,6577 | 0,00518235 USD | 1/17 |
| Dev, cải thiện 2 | 27473 | 3902 | 0 | 0 / 0 | 274,421 | 11,5531 | 0,00469830 USD | 1/17 |
| Test, baseline | 8939 | 1647 | 0 | 0 / 0 | 46,985 | 6,4914 | 0,00171740 USD | 0/7 |
| Test, ứng viên | 15268 | 1979 | 0 | 1188 / 0 | 65,659 | 10,1901 | 0,00254600 USD | 0/7 |

  Quy ước chi phí dùng USD, giá Standard short-context của `gpt-6-luna` kiểm tra ngày 16/11/2026 trên [trang model OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá](https://developers.openai.com/api/docs/pricing). Mỗi một triệu token: input không cache 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Tất cả request ghi nhận ngắn hơn ngưỡng long-context. Không thêm phí hosted file search hoặc tool OpenAI vì retriever chạy trên PostgreSQL local.

  Công thức là `(input không cache × 0,10 + cached input × 0,01 + cache write 30m × 0,125 + cache write 12h × 0,25 + output × 0,50) / 1.000.000`. Input không cache bằng input tổng trừ cached và cache-write tokens, tránh tính hai lần. Output theo API đã gồm reasoning nếu có, không cộng reasoning lần nữa. Chi phí là ước tính theo các response usage đã lưu, không phải hóa đơn tài khoản, không gồm thuế, phụ phí vùng hoặc cấu hình tier khác chưa ghi nhận.

  Tám lượt dùng trong phần chính có 94717 input token, 17469 output token và chi phí ghi nhận ước tính 0,01826325 USD. Ba lượt retrieval không gọi OpenAI, nên bảng token chỉ có năm lượt agent. Đây là tổng của phần chính. Tổng toàn bộ lịch sử, bao gồm lượt debug và lỗi, được báo riêng trong phụ lục. Request không có usage không được suy là chắc chắn bị tính 0. Chi phí máy, điện và request thiếu log chưa được đo.

  Tái lập trên máy mới: tạo Python venv, cài `requirements-lock.txt`, mở Docker, khởi động `starter/docker-compose.yml`, điền `.env` từ mẫu, khôi phục snapshot và chạy các lệnh sau. Hướng dẫn từng bước, xử lý cổng và môi trường nằm trong [REPRODUCE.md](../../REPRODUCE.md).

  ```powershell
  python -m starter.restore_day6
  python -m starter.restore_day6 --check-only
  python -m unittest discover -s tests -v
  python run_dev.py --method dense
  python run_dev.py --method tfidf
  python run_dev.py --method hybrid
  python run_dev.py --method agent --budget 2000 --max-searches 3
  python run_dev.py --method agent --budget 4000 --max-searches 3
  python run_dev.py --method agent --budget 2000 --max-searches 5
  python run_test.py --config baseline
  python run_test.py --config candidate
  python scripts/summarize_results.py
  python scripts/verify_submission.py
  ```

  Snapshot có SHA-256 và công cụ restore từ chối ghi đè index A khác. Máy thực nghiệm dùng database Day 6 cổng 55433, còn compose cho máy mới dùng cổng 55434 để tránh xung đột. Các biến kết nối và key đọc từ `.env`, file này không nằm trong Git. Đọc lại số liệu đã nộp hoặc kiểm thử mock không gọi API. Mỗi lần chạy agent tạo kết quả mới và không bảo đảm giống từng phản hồi cũ vì model API, mạng và môi trường có thể thay đổi.

  Kiểm tra tái lập đã khởi tạo database Day 7 riêng trống, khôi phục 273 vector, đối chiếu toàn bộ snapshot và xác nhận top-3 của câu NoSQL giống trace dense tham chiếu. Biên bản ở `results/restore-validation.json`. Lần kiểm tra dùng môi trường Python đã khóa và cache model có sẵn, chưa thử cài toàn bộ wheel trên một máy Windows mới.

- Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:

  Trên Test, ứng viên đạt 1,60/2 và baseline đạt 1,40/2 trên cùng năm câu có đáp án. Citation hợp lệ tương ứng là 5/5 và 5/7. Cả hai từ chối phù hợp hai câu thiếu bằng chứng, ứng viên từ chối nhầm một câu có đáp án. Context rộng hơn giữ được thêm gold nhưng tốn thêm token và thời gian trong lượt quan sát. Chỉ một lượt đầy đủ mỗi cấu hình và corpus nhỏ chưa đủ để kết luận ưu thế thống kê hay cấu hình tối ưu.

  Cấu hình 4000 được chọn sơ bộ trong giai đoạn phát triển, Dev sửa câu trùng được đo bổ sung sau Test. Lượt baseline đầu lỗi API vẫn được lưu và công bố. Việc rút gọn báo cáo không tạo ra một đánh giá độc lập mới. Cùng trợ lý tham gia viết code, soạn câu và chấm nhãn nên có nguy cơ thiên lệch, chưa có đánh giá mù.

  Corpus chỉ là 38 trang của một sách tiếng Anh, đã loại trang thiên về bảng/hình. Phần cơ bản chưa có OCR, retrieval đa phương thức, dữ liệu tiếng Việt hoặc nhiều tài liệu. Chunk theo ký tự có thể cắt câu và vượt giới hạn token của embedding model. Day 6 ghi nhận model có cửa sổ 128 token, nên một số chunk dài bị cắt đầu vào khi encode. Có dòng đầu/chân trang làm nhiễu ranking. Exact gold chưa bao quát mọi bằng chứng hợp lệ ở trang khác.

  Câu thiếu bằng chứng sử dụng tên tổ chức hư cấu, dễ hơn các câu gần đúng có điều kiện bị thiếu. Abstain cuối có thể do validator hoặc giới hạn search, không tách hoàn toàn năng lực nhận biết thiếu bằng chứng của model. Kiểm tra citation trong code chưa chấm được hỗ trợ ngữ nghĩa. Các nhãn thủ công và cách xử lý trường hợp một phần cần người chấm khác kiểm tra thêm. Không có fine-tuning hay huấn luyện model trong bài, chỉ điều chỉnh retrieval, context và vòng agent.

  Bản đóng gói cuối chuyển lớp cụ thể vào starter và đưa backend Day 6 vào repo, giữ nguyên ý nghĩa prompt/schema/retry đã đo. Các hash lịch sử được giữ nhưng không có snapshot đầy đủ của mọi phiên bản code trước commit này, nên không khẳng định có thể tái tạo chính xác từng log cũ. Các test offline kiểm tra adapter, cắt output, bảo toàn token, chống ghi đè snapshot và tách gold khỏi model. Kiểm thử code không thay thế đánh giá chất lượng thật.

## Thử thách nâng cao (nếu thực hiện)

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:

  Thực hiện riêng trên World Bank, World Development Report 2021: Data for Better Lives, bản PDF 350 trang vật lý. Nguồn, SHA-256, giấy phép CC BY 3.0 IGO và điều kiện thành phần bên thứ ba được ghi trong [báo cáo nâng cao](../../advanced/REPORT.md). Tài liệu, benchmark và index này tách khỏi phần cơ bản.

- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:

  Cả 350 trang được xử lý và giữ ảnh gốc có hash, tạo 4995 chunk native text và 498 chunk mô tả trực quan, tổng 5493. Vision xử lý 107 trang theo caption hoặc ảnh raster, tạo 114 vùng, không có request mô tả lỗi. Agent xem ảnh PDF gốc để kiểm tra bảng, sơ đồ và biểu đồ. Mô tả chỉ phục vụ retrieval. Mười bốn trang trống và một bìa minh họa không có native text. Hình trang trí không mô tả riêng, quy tắc chọn trang có thể bỏ sót hình không nhãn. Chi tiết coverage và các vùng kiểm tra thủ công ở hồ sơ nâng cao.

- Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:

  Dev có 18 câu gồm 15 có đáp án và ba thiếu bằng chứng. Test có 30 câu gồm 24 có đáp án và sáu thiếu bằng chứng. Benchmark khóa trước Dev. Câu hỏi có ID, nhóm, đáp án, evidence trang/vùng, đơn vị, phép tính hoặc cách kiểm tra thiếu bằng chứng. Cấu hình **baseline** được chốt trên cặp Dev cuối trước Test bằng số câu đạt, rồi thời gian và chi phí khi hòa. Hai lượt Dev đầu chỉ là chẩn đoán và được giữ nguyên. Inference không nhận gold.

  Pipeline dùng TF-IDF theo trang kết hợp dense pgvector 384 chiều bằng RRF. Embedding và model `gpt-6-luna` dùng cùng phiên bản đã công bố. Agent có công cụ search, inspect ảnh gốc và calculate, bắt buộc citation về trang và vùng đã xem. [Cấu hình và hash đã chốt](../../advanced/results/selection-freeze.json) giữ chi tiết baseline/candidate, giới hạn bước, ảnh và các file code/index.

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Ảnh, sơ đồ | 5/5 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Biểu đồ | 4/5 | 80,00% | 1 lỗi hệ thống, 1 câu không đạt |
| Multi-hop | 2/4 | 50,00% | 0 lỗi hệ thống, 2 câu không đạt |
| Text | 3/4 | 75,00% | 0 lỗi hệ thống, 1 câu không đạt |
| Thiếu bằng chứng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| **Toàn bộ** | **26/30** | **86,67%** | 1 lỗi hệ thống, 0 thiếu kết quả, 0 chưa chấm |

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:

  Test đạt **26/30 (86,67%)**, chưa đạt ngưỡng số học 27/30. Nhãn đang là đề xuất có trợ lý hỗ trợ đối chiếu PDF gốc, chưa có xác nhận riêng của học viên cho phần nâng cao và chưa có người chấm độc lập. Mẫu số giữ cả lỗi API, timeout và thiếu kết quả. Không chấm một phần như thang 0/1/2 của phần cơ bản. [Bảng 30 câu](../../advanced/results/TEST_REVIEW.md) dẫn tới trace, nhãn và kiểm tra vùng gốc. [Bảng Dev, thử nghiệm, token, thời gian và chi phí](../../advanced/REPORT.md) công bố cả lượt chẩn đoán.

  Chi phí riêng phần nâng cao ghi nhận **0,40401898 USD ước tính**, gồm index, bốn lượt Dev và một lượt Test, với 2931874 input và 75105 output token. Trần là 5 USD, dự phòng thiếu usage 0,00000000 USD. Đây là ước tính từ response usage theo giá công khai, không phải hóa đơn tài khoản. Quy ước cached input, cache write và reasoning giữ như phần cơ bản. Chi phí local và token trợ lý soạn bài ngoài pipeline chưa đo.

- Giới hạn, cách tái lập và đường dẫn benchmark:

  [Hướng dẫn nâng cao](../../advanced/README.md) có lệnh khôi phục snapshot vector và ảnh gốc mà không gọi API, kiểm hash, đọc lại metric và chạy model thật khi cần. [Dev](../../advanced/benchmark/dev.json), [Test](../../advanced/benchmark/test.json), [freeze benchmark](../../advanced/benchmark/freeze.json) và [ledger](../../advanced/results/ledger.json) đủ để kiểm tra lại phép tính. Chỉ có một tài liệu và một lượt Test, model alias và phản hồi API có thể thay đổi. Chưa có ablation chỉ-text, đánh giá nhiều người hoặc bảo đảm mọi hình không nhãn đều được mô tả. Không tự cộng điểm bonus khi chưa kiểm tra đủ điều kiện.
