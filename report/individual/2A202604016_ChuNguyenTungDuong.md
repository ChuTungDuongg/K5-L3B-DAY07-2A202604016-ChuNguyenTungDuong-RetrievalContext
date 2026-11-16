# Báo cáo Day 7

Họ và tên: Chu Nguyễn Tùng Dương (ChuNguyenTungDuong)

MSSV: 2A202604016. Lớp: L3B. Ngày thực nghiệm và tổng hợp: 16/11/2026, múi giờ Việt Nam UTC+7.

Repo bài nộp: [K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext](https://github.com/ChuTungDuongg/K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext).

Bài thực hành xây agent tìm bằng chứng trong corpus Day 6, trả lời có citation và nhận biết giới hạn bằng chứng. Các bảng giữ cả kết quả không cải thiện, lỗi API và lần chạy lại. Nhãn do Codex hỗ trợ đối chiếu, học viên xác nhận sử dụng trong phiên làm việc. Phần kiểm tra bổ sung cuối dùng cùng quy ước và công bố lý do từng nhãn, nhưng chưa có người chấm độc lập.

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

  Bộ nộp cuối gồm 17 câu dev và 7 câu test v2, đủ 15 câu dev có đáp án, 2 câu dev thiếu bằng chứng, 5 câu test có đáp án và 2 câu test thiếu bằng chứng. Bốn câu dev dùng lại Day 6 là `day6-q01`, `day6-q03`, `day6-q06`, `day6-q08`. Bản dev gốc có hai ID cùng hỏi định nghĩa data quality, nên 15 dòng chỉ tương ứng 14 câu khác nhau. Khi kiểm tra hồ sơ cuối, câu `dev-auto-373` được thay bằng `dev-extra-compliance`. Dữ liệu gốc và kết quả cũ được lưu trong `starter/data/dev-original-archive` và các thư mục run ban đầu. Bộ dev cuối có 15 câu có đáp án khác nhau, không sửa ngược các bảng lịch sử.

  Test v1 đã dùng để phát hiện vấn đề output bị cắt và lỗi kết nối. Sau khi bổ sung retry, các lần chạy lại v1 là chẩn đoán và giữ riêng. Phiên bản agent được ghi hash trước khi tạo test v2 tại `starter/results/test-v2-freeze.json`. Test v2 chọn evidence ở các trang 386, 387, 391, 393, 397 và có hai câu hỏi về tổ chức hư cấu. Bộ v2 không dùng để đổi retrieval hoặc chọn lại context budget. Riêng baseline v2 được chạy lại một lần vì lượt đầu có lỗi API 400. Báo cáo giữ cả lần đầu và lần lặp, không chỉ lấy lần có điểm tốt hơn.

  Việc sửa câu dev trùng và kiểm tra dev cuối diễn ra sau test, vì vậy các lượt đó là kiểm tra bổ sung. Quyết định ứng viên 4000 ký tự ban đầu dựa trên dev gốc, không được mô tả lại như một lựa chọn thực hiện trên bộ dev cuối trước test. Tiêu chí lựa chọn cũng đã được ghi sau khi thấy một phần dev, như thừa nhận trong `starter/results/dev-runs/experiment-notes.md`. Đây là giới hạn của thiết kế thực nghiệm.

- Cách xác định câu có/thiếu evidence và tiêu chí chấm:

  Câu có đáp án lưu `question`, `expected_answer` và gold gồm `source_id`, `page`, `evidence`. Script xác nhận mỗi evidence nằm nguyên văn trong chunk đúng nguồn và trang. Khi soạn câu, evidence được đọc lại để loại trường hợp chỉ có thuật ngữ mà không có quan hệ cần trả lời. Gold và đáp án chuẩn chỉ đi vào evaluator, không đi vào model hay retriever query. Các câu mới có AI hỗ trợ soạn từ corpus nên có nguy cơ gần cách diễn đạt của nguồn.

  Các câu thiếu bằng chứng hỏi về chi tiết nội bộ của tổ chức hư cấu. Tên tổ chức được kiểm tra trên toàn bộ 273 chunk A và không xuất hiện. Đây là bằng chứng về phạm vi corpus, không phải kết luận dựa vào top 3 không tìm thấy. Các câu này tương đối dễ nhận biết và không đại diện cho trường hợp thiếu bằng chứng tinh vi gần chủ đề. Các câu thiếu bằng chứng không vào mẫu số Hit@1, Evidence Hit@3 hoặc Context Evidence Rate.

  Hit@1 và Evidence Hit@3 kiểm tra đúng nguồn, trang và chứa nguyên văn evidence ở top 1 hoặc top 3. Context Evidence Rate tự động kiểm tra gold trong context cuối. Nhãn thủ công chấm context 0 khi thiếu evidence, 1 khi chỉ có một phần hoặc thiếu điều kiện và 2 khi đủ nội dung cùng nguồn. Grounded answer chấm 0 khi sai hoặc thiếu evidence, 1 khi đúng một phần và 2 khi đúng đủ. Từ chối câu có đáp án nhận 0. Vì vậy, câu trả lời đúng từ khóa vẫn có thể nhận 0 nếu citation không hỗ trợ quan hệ được hỏi.

  Citation chỉ được tính hợp lệ khi ID có trong context và nội dung nguồn hỗ trợ khẳng định tương ứng. Một câu trả lời có nhiều citation được chấm từng citation. Đáp án khác gold nhưng nguồn hỗ trợ vẫn có thể được chấp nhận, như banking và health care cho câu yêu cầu nêu hai ngành. Trường hợp chưa có gold thay thế vẫn có thể làm metric exact-match thấp hơn đánh giá thủ công. Nhãn ở `reviews.json` lưu lý do và danh tính người hỗ trợ chấm, còn `reviews-proposed.json` giữ bản đề xuất trước xác nhận.

## Retrieval và thử nghiệm

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| Baseline | Dense cosine pgvector, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | dev cuối | 14/15 (93,3%) | 14/15 (93,3%) | 14/15 (93,3%) | trung vị 0,0922 s/câu, tổng 1,416 s, 0,00000000 USD |
| Phương pháp 2 | TF-IDF, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | dev cuối | 13/15 (86,7%) | 15/15 (100,0%) | 15/15 (100,0%) | trung vị 0,0009 s/câu, tổng 0,013 s, 0,00000000 USD |
| Phương pháp 3 | Hybrid RRF, 10 ứng viên mỗi nhánh, hằng số 60, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | dev cuối | 14/15 (93,3%) | 15/15 (100,0%) | 15/15 (100,0%) | trung vị 0,0917 s/câu, tổng 1,466 s, 0,00000000 USD |
| Cải thiện 1 | Agent dense, budget 4000, tối đa 3 search, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | dev cuối | 14/15 (93,3%) câu gốc | 14/15 (93,3%) câu gốc | 13/14 (92,9%) trên câu chạy thành công | trung vị 10,6577 s/câu, tổng 258,671 s, 0,00518235 USD, lỗi 1/17 |
| Cải thiện 2 | Agent dense, budget 2000, tối đa 5 search, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | dev cuối | 14/15 (93,3%) câu gốc | 14/15 (93,3%) câu gốc | 12/14 (85,7%) trên câu chạy thành công | trung vị 11,5531 s/câu, tổng 274,421 s, 0,00469830 USD, lỗi 1/17 |
| Cấu hình đã chọn | Agent dense, budget 4000, tối đa 3 search, top 3 | v2, baseline là lượt chạy lại, giữ lượt đầu ở bảng lịch sử | test | 2/5 (40,0%) câu gốc | 4/5 (80,0%) câu gốc | 4/5 (80,0%) exact gold | trung vị 10,1901 s/câu, tổng 65,659 s, 0,00254600 USD |
| Baseline | Agent dense, budget 2000, tối đa 3 search, top 3 | v2, baseline là lượt chạy lại, giữ lượt đầu ở bảng lịch sử | test | 2/5 (40,0%) câu gốc | 4/5 (80,0%) câu gốc | 3/5 (60,0%) exact gold | trung vị 6,4914 s/câu, tổng 46,985 s, 0,00171740 USD |

Một cấu hình có thể đồng thời là phương pháp mới và cải thiện. Các tỷ lệ và thời gian ở bảng này phải được đọc cùng mẫu số và lỗi từng lượt.

  Dense, TF-IDF và hybrid được chạy trên cùng 15 câu dev cuối, cùng 273 chunk A và câu hỏi gốc. TF-IDF dùng cách tách từ đơn giản trong starter, vector từ vựng chuẩn hóa và cosine. Hybrid lấy top 10 của dense và TF-IDF, cộng `1/(60 + rank)` theo ID rồi giữ top 3, nên không cộng trực tiếp điểm cosine với điểm TF-IDF. Không có reranker hoặc filter ngoài chiến lược A. Cả TF-IDF và hybrid giữ được gold trong top 3 cho 15/15 câu, còn dense đạt 14/15 trong lượt này. Không suy rộng các kết quả trên bộ câu nhỏ sang tài liệu khác.

  Hai dòng cải thiện giữ Hit@1/Hit@3 của phép đo dense bằng câu gốc làm mốc so sánh. Đây không phải ranking của query do agent viết lại. CER của hai dòng đó là context cuối sau nhiều lượt tìm và chỉ có mẫu số câu có đáp án chạy thành công, nên không được so trực tiếp như các mẫu số đều bằng 15. Các query viết lại, thứ hạng từng lượt và context tích lũy nằm trong trace.

  Cải thiện 1 tăng budget từ 2000 lên 4000 ký tự, với giả thuyết giữ được evidence tìm thấy ở lượt sau. Cải thiện 2 giữ budget 2000 và tăng giới hạn từ 3 lên 5 lượt tìm, với giả thuyết có thêm cơ hội tìm lại. Cả hai là thử nghiệm nhằm cải thiện, không mặc định phải tăng điểm. Các lượt đầu sau tăng output cho thấy baseline đạt 1,73/2 và ứng viên 4000 đạt 1,87/2 trên dev gốc, đều không lỗi. Từ đó chọn sơ bộ 4000 để sang test. Việc chạy dev cuối sau bỏ câu trùng có lỗi mạng và mẫu số khác, không tái xác nhận một ưu thế ổn định của 4000.

  Lỗi dev thứ nhất là `dev01` về trọng tâm NoSQL. Với câu gốc, TF-IDF đưa gold ở trang 380 lên hạng 2, dense chỉ tìm thấy đoạn đó ở hạng 10 trong demo. Baseline TF-IDF budget 800 chỉ giữ đoạn hạng 1 dài 627 ký tự, còn budget 2000 giữ được ba đoạn tổng 1882 ký tự. Trong vòng agent, model tự mở rộng query bằng các từ như scalability và flexibility nhưng có lượt không tìm được gold. Đây là lỗi ranking và query transformation, không phải corpus không có đáp án. Thử nhiều lượt không bảo đảm khắc phục.

  Lỗi dev thứ hai là `dev-auto-383` về dữ liệu mà RDBMS không phù hợp. Ở trace baseline gốc, gold trang 383 đã xuất hiện ở lượt 2 và 3 nhưng bị bỏ vì context ưu tiên các đoạn trước. Tăng budget có lần giữ được bằng chứng đầy đủ và có lần chỉ đưa vào một đoạn thay thế ở trang 403 về dữ liệu phi cấu trúc, còn thiếu bán cấu trúc. Do đó, tăng budget có thể giảm mất bằng chứng nhưng chưa thay thế được việc chọn lại context theo độ liên quan. Báo cáo không coi tất cả câu answered là đúng đủ.

  Hướng cải tiến sau thực nghiệm là xếp lại candidate mới và cũ, deduplicate theo nội dung rồi chọn evidence dưới budget. Hướng này chưa được triển khai hoặc đo, nên không có số liệu cải thiện tương ứng. Nếu thực hiện, cần chọn bằng dev và đánh giá bằng một bộ test chưa dùng để chỉnh.

## Agent và đánh giá

- Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:

  Công cụ dense tạo query embedding thật rồi gọi PostgreSQL, trả ID, văn bản, nguồn, trang, metadata và score. Model nhận câu hỏi cùng context cuối tích lũy, không nhận nhãn answerable, expected answer hoặc gold. Cumulative context ưu tiên thứ tự candidate của những lượt trước, bỏ ID trùng và bỏ chunk không vừa budget. Budget tính bằng số ký tự Python, gồm nhãn nguồn và dấu phân cách, không phải số token model. Chunk dài không được tự cắt hoặc nén để nhét vào context.

  Cấu hình baseline dừng sau tối đa 3 search, ứng viên cũng 3 và thí nghiệm thêm lượt cho phép 5. Vòng lặp có một lần quyết định sau lượt search cuối để model trả lời. Nếu model tiếp tục yêu cầu search vượt giới hạn, hệ thống trả abstain. Nếu citation thiếu, không có trong context hoặc không xuất hiện dạng `[id]` trong answer, hệ thống cũng trả thông báo không đủ bằng chứng. Các trạng thái này đánh giá phản hồi cuối của hệ thống, không luôn chứng minh model đã chủ động nhận biết thiếu thông tin.

  Controller dùng structured JSON action và không đọc chỉ dẫn từ tài liệu như chỉ dẫn hệ thống. Đây là biện pháp trong prompt, chưa có thử nghiệm prompt injection riêng. Lỗi API, parse JSON và database được báo riêng, không thay bằng kết quả giả. Giới hạn output ban đầu 600 đã gây response incomplete, sau tăng lên 1600 và thêm tối đa một lần thử lại 3200 khi API báo incomplete vì giới hạn output. Usage của response incomplete vẫn được cộng. Test runner cho SDK thử lại lỗi kết nối tối đa 2 lần, còn các lượt dev đã lưu dùng max_retries 0. Vì vậy retry policy và thời gian khác nhau phải được khai báo.

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| Dev gốc, baseline sau tăng output | 17/17 (100,0%) | 1 lượt: 13 câu, 3 lượt: 4 câu | 0/1/2 = 2/0/13, N=15, TB 1,73/2 | 13/13 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 2/15 (13,3%) |
| Dev gốc, ứng viên sau tăng output | 17/17 (100,0%) | 1 lượt: 12 câu, 2 lượt: 2 câu, 3 lượt: 3 câu | 0/1/2 = 1/0/14, N=15, TB 1,87/2 | 14/14 (100,0%) | 14/14 (100,0%) | 2/2 (100,0%) | 1/15 (6,7%) |
| Dev cuối, baseline | 15/15 (100,0%) | 1 lượt: 13 câu, 3 lượt: 2 câu | 0/1/2 = 1/0/12, N=13, TB 1,85/2 | 12/12 (100,0%) | 12/12 (100,0%) | 2/2 (100,0%) | 1/13 (7,7%) |
| Dev cuối, 4000 | 16/16 (100,0%) | 1 lượt: 10 câu, 2 lượt: 2 câu, 3 lượt: 4 câu | 0/1/2 = 1/1/12, N=14, TB 1,79/2 | 15/15 (100,0%) | 13/13 (100,0%) | 2/2 (100,0%) | 1/14 (7,1%) |
| Dev cuối, 5 search | 16/16 (100,0%) | 1 lượt: 12 câu, 5 lượt: 4 câu | 0/1/2 = 2/0/12, N=14, TB 1,71/2 | 12/12 (100,0%) | 12/12 (100,0%) | 2/2 (100,0%) | 2/14 (14,3%) |
| Test v2, baseline lần đầu | 6/6 (100,0%) | 1 lượt: 2 câu, 2 lượt: 1 câu, 3 lượt: 3 câu | 0/1/2 = 2/0/2, N=4, TB 1,00/2 | 2/3 (66,7%) | 3/3 (100,0%) | 2/2 (100,0%) | 1/4 (25,0%) |
| Test v2, ứng viên lần đầu | 7/7 (100,0%) | 1 lượt: 2 câu, 3 lượt: 5 câu | 0/1/2 = 1/0/4, N=5, TB 1,60/2 | 5/5 (100,0%) | 4/4 (100,0%) | 2/2 (100,0%) | 1/5 (20,0%) |
| Test v2, baseline chạy lại | 7/7 (100,0%) | 1 lượt: 5 câu, 2 lượt: 1 câu, 3 lượt: 1 câu | 0/1/2 = 1/1/3, N=5, TB 1,40/2 | 5/7 (71,4%) | 5/5 (100,0%) | 2/2 (100,0%) | 0/5 (0,0%) |

  Lỗi được tách khỏi mẫu số chất lượng theo starter. Dev cuối baseline có 2 lỗi nên điểm câu trả lời dùng N=13, hai cấu hình còn lại dùng N=14. Test v2 baseline lần đầu dùng N=4 do một lỗi API, còn ứng viên và baseline chạy lại dùng N=5. Các trung bình khác mẫu số không là so sánh trực tiếp. Bộ kiểm tra bổ sung dev cũng có lỗi mạng và API 400 nên không thể dùng điểm trên phần thành công để tuyên bố cấu hình nào chắc chắn tốt hơn.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| B lần đầu: v2-test-386 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p384:part0:fixed:500:50:900,openstax-intro-cs:p385:part0:fixed:500:50:450,openstax-intro-cs:p386:part0:fixed:500:50:0` | Không đủ bằng chứng để trả lời. | Trả lời 0/2, context 2/2. Context cuối trang 386 nêu đầy đủ lý do nhưng agent đạt giới hạn tìm kiếm rồi từ chối; câu có đáp án bị từ chối chấm 0. |
| B lần đầu: v2-test-387 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p386:part0:fixed:500:50:3150,openstax-intro-cs:p386:part0:fixed:500:50:2250,openstax-intro-cs:p387:part0:fixed:500:50:0` | The tuple is selected for inclusion in the result. [openstax-intro-cs:p387:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 387 nói tuple được chọn khi điều kiện đúng, khớp câu trả lời. |
| B lần đầu: v2-test-391 | Có đáp án | Không lưu được context cuối do API error | Không có đáp án | Lỗi BadRequestError, báo riêng và không gán 0 |
| B lần đầu: v2-test-393 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p393:part0:fixed:500:50:0,openstax-intro-cs:p392:part0:fixed:500:50:0,openstax-intro-cs:p377:part0:fixed:500:50:0` | A tablespace is the physical storage container in which tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 393 mô tả tablespace là nơi lưu bảng và vật chứa đối tượng database. |
| B lần đầu: v2-test-397 | Có đáp án | 2 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:0,openstax-intro-cs:p382:part1:fixed:500:50:450,openstax-intro-cs:p398:part0:fixed:500:50:450` | Concurrency control [openstax-intro-cs:p397:part0:fixed:500:50:0] | Trả lời 0/2, context 1/2. Câu trả lời đúng thuật ngữ, nhưng citation trang 397 đoạn 0 chỉ liệt kê concurrency control và không chỉ ra nó điều phối giao dịch đồng thời; không đủ evidence cho kết luận. |
| B lần đầu: v2-test-no-evidence-01 | Thiếu evidence | 1 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:2700,openstax-intro-cs:p403:part0:fixed:500:50:3150,openstax-intro-cs:p399:part0:fixed:500:50:0` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả thông báo không đủ bằng chứng; corpus không có chính sách tổ chức hư cấu. Trace kết thúc do citation không hợp lệ hoặc thiếu, không chứng minh ý định nội bộ của model. |
| B lần đầu: v2-test-no-evidence-02 | Thiếu evidence | 3 search, context IDs `openstax-intro-cs:p399:part0:fixed:500:50:450,openstax-intro-cs:p378:part0:fixed:500:50:2700,openstax-intro-cs:p409:part0:fixed:500:50:1350,openstax-intro-cs:p379:part0:fixed:500:50:2250` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống từ chối, phù hợp với việc corpus không có danh tính nhân sự tổ chức hư cấu; trace kết thúc do giới hạn tìm kiếm. |
| C: v2-test-386 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p384:part0:fixed:500:50:900,openstax-intro-cs:p385:part0:fixed:500:50:450,openstax-intro-cs:p386:part0:fixed:500:50:0` | Select, Project, Difference, Product, and Union are called primitive because all other relational algebra operators can be derived from them [openstax-intro-cs:p386:part0:fixed:500:50:0]. | Trả lời 2/2, context 2/2. Nguồn trang 386 ghi các phép toán còn lại được suy ra từ năm phép cơ bản. |
| C: v2-test-387 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p386:part0:fixed:500:50:3150,openstax-intro-cs:p386:part0:fixed:500:50:0,openstax-intro-cs:p387:part0:fixed:500:50:0,openstax-intro-cs:p386:part0:fixed:500:50:2700,openstax-intro-cs:p387:part0:fixed:500:50:450` | If the formula evaluates to true for a tuple, that tuple is selected in the result. [openstax-intro-cs:p387:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 387 nói tuple được chọn khi điều kiện đúng, khớp câu trả lời. |
| C: v2-test-391 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p391:part0:fixed:500:50:0,openstax-intro-cs:p391:part0:fixed:500:50:450,openstax-intro-cs:p391:part0:fixed:500:50:900,openstax-intro-cs:p390:part0:fixed:500:50:2250` | A dependent is fully identified using the key of its owning strong entity (the employee) together with the dependent’s partial key, if any. [openstax-intro-cs:p391:part0:fixed:500:50:0] [openstax-intro-cs:p391:part0:fixed:500:50:450] | Trả lời 2/2, context 2/2. Nguồn trang 391 đoạn 0 nêu ID employee, đoạn 450 nêu khóa kết hợp với partial key nếu có; cả hai hỗ trợ nội dung tương ứng. |
| C: v2-test-393 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p393:part0:fixed:500:50:0,openstax-intro-cs:p392:part0:fixed:500:50:0,openstax-intro-cs:p377:part0:fixed:500:50:0,openstax-intro-cs:p383:part0:fixed:500:50:3150` | A tablespace is the physical storage container in which database tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Nguồn trang 393 nêu tablespace chứa bảng và là vật chứa đối tượng database. |
| C: v2-test-397 | Có đáp án | 3 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:0,openstax-intro-cs:p382:part1:fixed:500:50:450,openstax-intro-cs:p395:part0:fixed:500:50:2250,openstax-intro-cs:p398:part0:fixed:500:50:450` | Không đủ bằng chứng để trả lời. | Trả lời 0/2, context 1/2. Agent từ chối khi hết lượt tìm; context có tên concurrency control nhưng không có định nghĩa liên kết nó với việc điều phối hoạt động đồng thời. |
| C: v2-test-no-evidence-01 | Thiếu evidence | 1 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:2700,openstax-intro-cs:p403:part0:fixed:500:50:3150,openstax-intro-cs:p383:part0:fixed:500:50:450` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả thông báo không đủ bằng chứng; corpus không có chính sách tổ chức hư cấu. Trace kết thúc do citation không hợp lệ hoặc thiếu, không chứng minh ý định nội bộ của model. |
| C: v2-test-no-evidence-02 | Thiếu evidence | 3 search, context IDs `openstax-intro-cs:p399:part0:fixed:500:50:450,openstax-intro-cs:p379:part0:fixed:500:50:2250,openstax-intro-cs:p378:part0:fixed:500:50:2700,openstax-intro-cs:p377:part0:fixed:500:50:3150` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống từ chối, phù hợp với việc corpus không có danh tính nhân sự tổ chức hư cấu; trace kết thúc do giới hạn tìm kiếm. |
| B chạy lại: v2-test-386 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p384:part0:fixed:500:50:900,openstax-intro-cs:p385:part0:fixed:500:50:450,openstax-intro-cs:p386:part0:fixed:500:50:0` | They are considered primitive because they form a sufficient basic set: every other relational algebra operator can be derived by combining Select, Project, Difference, Product, and Union. [openstax-intro-cs:p386:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Context trang 386 nói đủ rằng mọi phép còn lại có thể suy ra từ năm phép primitive; câu trả lời và citation phù hợp. |
| B chạy lại: v2-test-387 | Có đáp án | 2 search, context IDs `openstax-intro-cs:p386:part0:fixed:500:50:3150,openstax-intro-cs:p386:part0:fixed:500:50:2250,openstax-intro-cs:p386:part0:fixed:500:50:0` | The tuple is included in the query’s result relation, with the specified attribute values retrieved. [openstax-intro-cs:p386:part0:fixed:500:50:3150] | Trả lời 1/2, context 1/2. Câu trả lời nêu tuple được đưa vào kết quả; đoạn trích trang 386 nói condition dùng để chọn tuple và truy xuất thuộc tính nhưng không nêu rõ khi công thức nhận giá trị true thì tuple được chọn. Chấm thận trọng một phần; gold cụ thể ở trang 387 không nằm trong context cuối. |
| B chạy lại: v2-test-391 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p391:part0:fixed:500:50:0,openstax-intro-cs:p391:part0:fixed:500:50:450,openstax-intro-cs:p390:part0:fixed:500:50:2250` | A dependent is fully identified using the key of its strong owner (the employee), combined with the dependent’s partial key, if it has one. The owner’s key supplies the context needed to identify the weak entity [openstax-intro-cs:p391:part0:fixed:500:50:0] [openstax-intro-cs:p391:part0:fixed:500:50:450] [openstax-intro-cs:p390:part0:fixed:500:50:2250]. | Trả lời 2/2, context 2/2. Hai đoạn trang 391 hỗ trợ ID employee và kết hợp partial key nếu có; đoạn cuối trang 390 hỗ trợ phải dựa vào strong entity để cung cấp ngữ cảnh nhận dạng, dù đoạn trích bị cắt ở đầu. |
| B chạy lại: v2-test-393 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p393:part0:fixed:500:50:0,openstax-intro-cs:p392:part0:fixed:500:50:0,openstax-intro-cs:p377:part0:fixed:500:50:0` | A tablespace is the physical storage container in which database tables and other database objects are stored. [openstax-intro-cs:p393:part0:fixed:500:50:0] | Trả lời 2/2, context 2/2. Đoạn trang 393 mô tả tablespace là nơi lưu bảng và vật chứa database objects, phù hợp câu trả lời. |
| B chạy lại: v2-test-397 | Có đáp án | 1 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:0,openstax-intro-cs:p382:part1:fixed:500:50:450,openstax-intro-cs:p398:part0:fixed:500:50:450` | Concurrency control addresses the coordination of simultaneous database activity. [openstax-intro-cs:p397:part0:fixed:500:50:0] | Trả lời 0/2, context 1/2. Đáp án nêu đúng concurrency control nhưng đoạn citation trang 397 chỉ liệt kê nó là tính năng; không giải thích điều phối giao dịch đồng thời. Định nghĩa gold không có trong context cuối, nên câu trả lời thiếu evidence. |
| B chạy lại: v2-test-no-evidence-01 | Thiếu evidence | 1 search, context IDs `openstax-intro-cs:p397:part0:fixed:500:50:2700,openstax-intro-cs:p403:part0:fixed:500:50:3150,openstax-intro-cs:p383:part0:fixed:500:50:450` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả không đủ bằng chứng; tên tổ chức hư cấu không xuất hiện trong 273 chunk A. Event kết thúc invalid_or_missing_citations nên không đủ thông tin để kết luận model chủ động từ chối. |
| B chạy lại: v2-test-no-evidence-02 | Thiếu evidence | 3 search, context IDs `openstax-intro-cs:p399:part0:fixed:500:50:450,openstax-intro-cs:p378:part0:fixed:500:50:2700,openstax-intro-cs:p409:part0:fixed:500:50:1350,openstax-intro-cs:p379:part0:fixed:500:50:2250` | Không đủ bằng chứng để trả lời. | Từ chối phù hợp. Hệ thống trả không đủ bằng chứng; tổ chức hư cấu không xuất hiện trong corpus. Kết thúc do search_limit; không đủ thông tin để kết luận model chủ động từ chối. |

  Ký hiệu B là baseline 2000, C là ứng viên 4000. Các dòng B lần đầu, C và B chạy lại giữ riêng toàn bộ test v2. Trong baseline chạy lại, câu 387 được chấm thận trọng 1/2 vì nguồn chỉ mô tả điều kiện chọn tuple và không nêu rõ điều kiện true. Câu 397 đúng thuật ngữ nhưng citation chỉ liệt kê tính năng nên nhận 0 về grounded answer. Các nhãn có tính diễn giải và không có thỏa thuận giữa nhiều người chấm. Học viên xác nhận nhãn có Codex hỗ trợ, không coi trợ lý là người chấm độc lập.

  Context của baseline v2 lần đầu có ba câu mức 2, một câu mức 1 và một câu không có nhãn do lỗi API. Baseline chạy lại có ba câu mức 2 và hai câu mức 1, đủ năm câu có đáp án được đọc. Ứng viên có bốn câu mức 2 và một câu mức 1. Vì baseline đã được chạy lại, cần báo cả hai lần thay vì coi lượt lặp là một mẫu test mới hoặc chọn lượt có điểm đẹp hơn.

- Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:

  Thư mục run chính được liệt kê trong [phụ lục RESULTS](../../docs/RESULTS.md). Mỗi lượt có `config.json`, `traces.json`, `summary.json`. Những lượt đã chấm có `reviews.json` và `agent-metrics.json`. File [run_ledger.json](../../results/run_ledger.json) lưu toàn bộ 27 lượt batch trong phạm vi cộng usage, gồm cả chạy thử có limit và các lần lỗi. JSON được ghi sau mỗi câu, nhưng khi một exception xảy ra giữa vòng agent thì log lịch sử có thể thiếu các event trước lỗi. Không có context cuối được lưu không được suy thành context grade 0 của lần lỗi.

  Thời gian là elapsed theo từng câu, không tính khởi tạo model, tải weights, tạo TF-IDF index hoặc ghi file. Trung vị chỉ xét câu không lỗi. Tổng thời gian là tổng elapsed của tất cả câu, có cả thời gian chờ của câu lỗi, không phải thời gian toàn tiến trình. Test runner tính cả truy xuất câu gốc trước vòng agent, trong khi dev agent runner không có bước đo đó. Một số lượt chạy đồng thời nên độ trễ chịu ảnh hưởng mạng và tranh chấp tài nguyên. Chưa đo RAM, CPU riêng, cold start, tải đồng thời có kiểm soát hoặc độ biến thiên qua nhiều lần lặp cân bằng.

| Lượt | Input token | Output token | Cached input | Cache write 30m / 12h | Tổng elapsed câu (s) | Trung vị câu thành công (s) | Chi phí ước tính | Lỗi / số câu |
|---|---|---|---|---|---|---|---|---|
| Dev gốc B | 21900 | 3625 | 0 | 0 / 0 | 104,223 | 5,2182 | 0,00400250 USD | 0/17 |
| Dev gốc C | 23819 | 3630 | 0 | 4671 / 0 | 104,613 | 5,3064 | 0,00431368 USD | 0/17 |
| Dev cuối B | 18592 | 4520 | 0 | 0 / 0 | 241,856 | 5,7131 | 0,00411920 USD | 2/17 |
| Dev cuối C | 24445 | 5421 | 0 | 1094 / 0 | 258,671 | 10,6577 | 0,00518235 USD | 1/17 |
| Dev cuối 5 search | 27473 | 3902 | 0 | 0 / 0 | 274,421 | 11,5531 | 0,00469830 USD | 1/17 |
| Test v2 B lần đầu | 11086 | 1643 | 0 | 0 / 0 | 71,660 | 10,1077 | 0,00193010 USD | 1/7 |
| Test v2 C lần đầu | 15268 | 1979 | 0 | 1188 / 0 | 65,659 | 10,1901 | 0,00254600 USD | 0/7 |
| Test v2 B chạy lại | 8939 | 1647 | 0 | 0 / 0 | 46,985 | 6,4914 | 0,00171740 USD | 0/7 |

  Quy ước chi phí dùng USD, giá Standard short-context của `gpt-6-luna` kiểm tra ngày 16/11/2026 trên [trang model OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá](https://developers.openai.com/api/docs/pricing). Mỗi một triệu token: input không cache 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Tất cả request ghi nhận ngắn hơn ngưỡng long-context. Không thêm phí hosted file search hoặc tool OpenAI vì retriever chạy trên PostgreSQL local.

  Công thức là `(input không cache × 0,10 + cached input × 0,01 + cache write 30m × 0,125 + cache write 12h × 0,25 + output × 0,50) / 1.000.000`. Input không cache bằng input tổng trừ cached và cache-write tokens, tránh tính hai lần. Output theo API đã gồm reasoning nếu có, không cộng reasoning lần nữa. Chi phí là ước tính theo các response usage đã lưu, không phải hóa đơn tài khoản, không gồm thuế, phụ phí vùng hoặc cấu hình tier khác chưa ghi nhận.

  Phạm vi 27 lượt có 268372 input token, 49854 output token và chi phí ghi nhận ước tính 0,05206185 USD. Những request lỗi không có usage không được suy là tài khoản chắc chắn bị tính 0. Các lần soạn bộ câu hỏi có tổng token quan sát trong phiên là 6183 nhưng không giữ đủ breakdown input/output trong artifact, nên không được cộng như một chi phí chính xác. Ngoài ra có kiểm tra key, debug và demo riêng ngoài phạm vi ledger. Chi phí embedding/retrieval local bằng 0 về phí API, nhưng vẫn có chi phí máy và điện chưa đo.

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
  python run_test.py --config baseline --test-version v2
  python run_test.py --config candidate --test-version v2
  python scripts/summarize_results.py
  python scripts/verify_submission.py
  ```

  Snapshot có SHA-256 và công cụ restore từ chối ghi đè index A khác. Máy thực nghiệm dùng database Day 6 cổng 55433, còn compose cho máy mới dùng cổng 55434 để tránh xung đột. Các biến kết nối và key đọc từ `.env`, file này không nằm trong Git. Đọc lại số liệu đã nộp hoặc kiểm thử mock không gọi API. Mỗi lần chạy agent tạo kết quả mới và không bảo đảm giống từng phản hồi cũ vì model API, mạng và môi trường có thể thay đổi.

  Kiểm tra tái lập đã khởi tạo database Day 7 riêng trống, khôi phục 273 vector, đối chiếu toàn bộ snapshot và xác nhận top-3 của câu NoSQL giống trace dense tham chiếu. Biên bản ở `results/restore-validation.json`. Lần kiểm tra dùng môi trường Python đã khóa và cache model có sẵn, chưa thử cài toàn bộ wheel trên một máy Windows mới.

- Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:

  Trên dev gốc sau tăng output, budget 4000 đạt 1,87/2 so với 1,73/2 của baseline, nhưng chỉ một lượt mỗi cấu hình và dev có câu trùng. Kết quả bổ sung sau khi sửa bộ dev không xác nhận ưu thế đó, đồng thời có lỗi mạng và mẫu số khác. Test v2 lần đầu ứng viên đạt 1,60/2 trên năm câu có đáp án, baseline đạt 1,00/2 trên bốn câu thành công và có một lỗi API. Baseline chạy lại đạt 1,40/2 trên năm câu, nên kết luận chỉ là quan sát trong các lượt đã báo, không phải bằng chứng thống kê về độ vượt trội. Việc chọn 4000 là lựa chọn sơ bộ theo giai đoạn phát triển, chưa chứng minh tối ưu.

  Báo cáo giữ lịch sử test v1, các lần chẩn đoán sau sửa retry, test v2 và baseline v2 chạy lại. Không tối ưu prompt hoặc chọn tham số theo điểm test v2. Tuy nhiên, cùng trợ lý tham gia viết code, soạn câu hỏi và chấm nhãn nên có nguy cơ thiên lệch. Bộ v2 mới không xóa ảnh hưởng của toàn bộ quá trình phát triển và không là đánh giá mù.

  Corpus chỉ là 38 trang của một sách tiếng Anh, đã loại trang thiên về bảng/hình. Chưa có OCR, retrieval đa phương thức, dữ liệu tiếng Việt hoặc nhiều tài liệu. Chunk theo ký tự có thể cắt câu và vượt giới hạn token của embedding model. Day 6 ghi nhận model có cửa sổ 128 token, nên một số chunk dài bị cắt đầu vào khi encode. Có dòng đầu/chân trang làm nhiễu ranking. Exact gold chưa bao quát mọi bằng chứng hợp lệ ở trang khác.

  Câu thiếu bằng chứng sử dụng tên tổ chức hư cấu, dễ hơn các câu gần đúng có điều kiện bị thiếu. Abstain cuối có thể do validator hoặc giới hạn search, không tách hoàn toàn năng lực nhận biết thiếu bằng chứng của model. Kiểm tra citation trong code chưa chấm được hỗ trợ ngữ nghĩa. Các nhãn thủ công và cách xử lý trường hợp một phần cần người chấm khác kiểm tra thêm. Không có fine-tuning hay huấn luyện model trong bài, chỉ điều chỉnh retrieval, context và vòng agent.

  Bản đóng gói cuối chuyển lớp cụ thể vào starter và đưa backend Day 6 vào repo, giữ nguyên ý nghĩa prompt/schema/retry đã đo. Các hash lịch sử được giữ nhưng không có snapshot đầy đủ của mọi phiên bản code trước commit này, nên không khẳng định có thể tái tạo chính xác từng log cũ. Các test offline kiểm tra adapter, cắt output, bảo toàn token, chống ghi đè snapshot và tách gold khỏi model. Kiểm thử code không thay thế đánh giá chất lượng thật.

## Thử thách nâng cao (nếu thực hiện)

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:

  Không thực hiện thử thách nâng cao. Corpus index có 38 trang nội dung, không đáp ứng yêu cầu tài liệu từ 100 trang dù PDF gốc dài 939 trang. Bài nộp chỉ báo phần cơ bản, không tự nhận 15 điểm bonus.

- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:

  Chỉ dùng văn bản từ corpus Day 6. Không có pipeline bảng, ảnh, biểu đồ hoặc evidence theo vùng để đánh giá nâng cao.

- Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:

  Không có benchmark riêng cho nâng cao. Bộ 24 câu cuối phục vụ phần cơ bản.

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | Không đánh giá | Không áp dụng | Chưa xử lý bảng |
| Ảnh, sơ đồ | Không đánh giá | Không áp dụng | Chưa xử lý ảnh |
| Biểu đồ | Không đánh giá | Không áp dụng | Chưa xử lý biểu đồ |
| Multi-hop | Không đánh giá | Không áp dụng | Chưa có bộ nhãn multi-hop riêng |
| Text | Không đánh giá nâng cao | Không áp dụng | Kết quả text cơ bản đã trình bày phía trên |
| Thiếu bằng chứng | Không đánh giá nâng cao | Không áp dụng | Hai câu test thiếu evidence thuộc phần cơ bản |
| **Toàn bộ** | Không thực hiện | Không áp dụng | Không đề nghị bonus |

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:

  Không phát sinh trace, nhãn hoặc chi phí riêng cho phần nâng cao.

- Giới hạn, cách tái lập và đường dẫn benchmark:

  Hướng dẫn tái lập phần cơ bản ở `REPRODUCE.md`. Muốn thực hiện nâng cao phải bổ sung corpus, pipeline và bộ đánh giá đúng yêu cầu `ADVANCED.md`, sau đó báo kết quả như một thí nghiệm riêng.
