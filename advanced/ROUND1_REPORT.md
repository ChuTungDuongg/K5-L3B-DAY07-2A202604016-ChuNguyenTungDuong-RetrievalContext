# Báo cáo bổ sung phần nâng cao

Chu Nguyễn Tùng Dương (ChuNguyenTungDuong), MSSV 2A202604016, lớp L3B. Thực nghiệm ngày 16/11/2026 theo UTC+7.

Kết quả Test là **26/30 (86,67%)**, chưa đạt ngưỡng số học 27/30. Nhãn đang là đề xuất có trợ lý hỗ trợ đối chiếu PDF gốc, chưa có xác nhận riêng của học viên cho phần nâng cao và chưa có người chấm độc lập. Điểm bonus do giảng viên quyết định sau khi kiểm tra đầy đủ yêu cầu, không suy ra tự động từ tỷ lệ.

## Tài liệu và phạm vi xử lý

Nguồn là [World Development Report 2021: Data for Better Lives](https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf), World Bank, 2021, DOI 10.1596/978-1-4648-1600-0. Bản PDF có 350 trang vật lý và SHA-256 `606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616`. Giấy phép trang PDF 4 là CC BY 3.0 IGO, kèm điều kiện ghi công và thành phần bên thứ ba. Repo cung cấp cách tải bản gốc, không đóng gói PDF. Diễn giải trong bài không đại diện cho World Bank.

Pipeline xử lý cả 350 trang, tạo 4995 chunk native text và 498 chunk từ mô tả 114 vùng trực quan, tổng 5493 chunk. Mọi chunk giữ nguồn, trang vật lý và vị trí ký tự hoặc bbox. Toàn bộ 350 ảnh trang có hash để tái tạo và kiểm chứng. Quy tắc độc lập với benchmark chọn 107 trang có caption Figure/Table/Map hoặc ảnh raster đủ lớn để phân tích vision, hoàn tất 107/107 và không có request mô tả lỗi. Những trang candidate không có vùng hữu ích được giữ trong coverage, không tự tạo mô tả.

Có 15 trang không có native text: 2, 3, 12, 22, 42, 72, 140, 174, 176, 208, 246, 284, 322, 347 và 349. Kiểm tra ảnh cho thấy 14 trang trống và trang 3 là bìa minh họa. Bìa và hình trang trí không được mô tả riêng. Không chọn bỏ trang có bảng hoặc biểu đồ theo benchmark. Quy tắc caption và kích thước raster vẫn có thể bỏ sót hình vector không nhãn, vì vậy không khẳng định đã kiểm tra thủ công mọi chi tiết của 350 trang. Native text có thể sai thứ tự đọc hoặc glyph. Các ảnh gốc vẫn có thể truy cập khi trang đó được retrieve.

PDFium 5.13.0 lấy text và render JPEG cạnh dài 1800 pixel, chất lượng 92 với Pillow 13.0.0. Vision `gpt-6-luna` tạo mô tả tìm kiếm, không được coi mô tả đó là nguồn đúng tuyệt đối. Người soạn benchmark kiểm tra 59 vùng evidence trên ảnh PDF gốc, gồm header, ô bảng, trục, chú giải, mũi tên và đoạn nối cột. Một lượt kiểm tra khác đối chiếu từng citation của kết quả chạy. Những kiểm tra này có trợ lý AI hỗ trợ và chưa thay thế việc học viên hoặc giảng viên kiểm tra lại.

## Pipeline, cấu hình và split

Index riêng `ADV-WDR2021-v1` ở database Day 7, cổng mặc định 55434, không ghi đè strategy A/B của Day 6. Embedding local dùng sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, 384 chiều, revision đã khóa trong backend. Dense exact cosine lấy 60 chunk, mỗi trang nhận một phiếu từ hạng chunk đầu tiên. TF-IDF trên text và mô tả theo trang lấy 40 trang. RRF cộng `1/(60+rank)`, giữ 12 trang. Locator Figure/Table/Map chỉ được lấy từ câu hỏi hoặc query model và tăng 0,05 cho trang có nhãn khớp. Không dùng trang hoặc bbox gold để ưu tiên.

Agent xem trước ảnh gốc của ba trang với baseline và năm trang với candidate. Baseline có tối đa ba bước model, sáu ảnh đang hoạt động. Candidate có bốn bước và tám ảnh. Model chọn search, inspect, calculate hoặc answer, còn Python thực thi công cụ. Tối đa ba query mỗi action search. Context gồm native text, mô tả tìm kiếm và ảnh các trang đang hoạt động. Khi xem lại một ảnh cũ, ảnh đó trở lại context. Hết số bước mà chưa có đáp án hợp lệ thì từ chối. Mỗi response có tối đa 3500 output token, reasoning low, timeout 75 giây và không tự retry. Code chỉ kiểm cấu trúc citation và trang đã xem, còn hỗ trợ ngữ nghĩa được chấm riêng.

Dev gồm 18 câu, trong đó 15 có đáp án chia đều năm nhóm và ba thiếu bằng chứng. Test gồm 30 câu, trong đó 24 có đáp án và sáu thiếu bằng chứng. Hai split được soạn và khóa hash trước Dev. Mỗi câu chỉ có một nhóm chính. Các câu multi-hop yêu cầu ít nhất hai trang. Câu thiếu bằng chứng gần chủ đề nhưng thiếu phân tổ, điều kiện hoặc quan hệ nhân quả cần hỏi, đã tìm toàn corpus và kiểm tra vùng nguồn gần nhất. Không dùng tên tổ chức hư cấu để làm câu thiếu evidence dễ nhận biết.

Một trợ lý chuyên soạn benchmark tách khỏi việc triển khai inference đã đọc nguồn và tạo gold. Trợ lý triển khai chỉ dùng Dev trước freeze. Điều này giảm việc đọc Test khi chỉnh code nhưng không tạo ra đánh giá mù giữa các con người. File gold chỉ phục vụ evaluator, còn inference nhận câu hỏi, không nhận nhóm, nhãn answerable, đáp án chuẩn hoặc bbox chuẩn.

Hai lượt Dev đầu là chẩn đoán: nội dung có thể đúng nhưng citation cắt mất chú giải hoặc phần đoạn văn. Prompt được sửa chung để vùng citation bao đủ object, legend, header và đoạn văn qua các cột. Đồng thời bổ sung kiểm tra hash ảnh tái tạo và hash benchmark ở Test. Không sửa theo đáp án riêng từng câu. Kế hoạch chạy lại được ghi trước cặp Dev cuối, mỗi cấu hình đúng một lượt. Tiêu chí chọn đã ghi trước là số câu đạt Dev, rồi trung vị thời gian và chi phí khi hòa.

| Lượt | Đạt / tổng | Input / output token | Cached / write 30m / write 12h | Tổng s / trung vị s | USD ước tính | Lỗi |
|---|---|---|---|---|---|---|
| [Dev baseline](results/runs/20261116-122648-dev-baseline-91fbfbb2/config.json) | 17/18 (94,44%) | 370243 / 4784 | 0 / 370174 / 0 | 162,758 / 7,229 | 0,04867065 | 0/18 |
| [Dev candidate](results/runs/20261116-122658-dev-candidate-fdc3f714/config.json) | 17/18 (94,44%) | 664083 / 5696 | 0 / 664005 / 0 | 245,262 / 8,372 | 0,08585642 | 0/18 |
| [Test baseline](results/runs/20261116-123301-test-baseline-45143179/config.json) | 26/30 (86,67%) | 558094 / 7171 | 0 / 557986 / 0 | 274,191 / 6,327 | 0,07334455 | 1/30 |

Cấu hình chốt là **baseline**, theo [selection-freeze.json](results/selection-freeze.json). Lựa chọn, code, index, ảnh và benchmark đã khóa trước Test. Chỉ chạy một lượt chính thức trên cả 30 câu, không chọn lại đáp án theo từng câu. Hai cấu hình Dev chạy đồng thời nên thời gian có thể chịu tranh chấp tài nguyên. Không coi chênh lệch một lượt là ưu thế thống kê.

## Chấm Test nghiêm và phân tích lỗi

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Ảnh, sơ đồ | 5/5 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Biểu đồ | 4/5 | 80,00% | 1 lỗi hệ thống, 1 câu không đạt |
| Multi-hop | 2/4 | 50,00% | 0 lỗi hệ thống, 2 câu không đạt |
| Text | 3/4 | 75,00% | 0 lỗi hệ thống, 1 câu không đạt |
| Thiếu bằng chứng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| **Toàn bộ** | **26/30** | **86,67%** | 1 lỗi hệ thống, 0 thiếu kết quả, 0 chưa chấm |

Tỷ lệ bằng số đạt chia toàn bộ 30 câu và không làm tròn để vượt ngưỡng. Câu trả lời đúng một phần, sai đối tượng đo, sai đơn vị, thiếu điều kiện, sai vùng citation hoặc từ chối câu có đáp án đều không đạt. Lỗi hệ thống và thiếu kết quả cũng nằm trong mẫu số. Các tỷ lệ này khác thang 0/1/2 ở phần cơ bản và không cộng hai bộ điểm với nhau.

[Bảng đối chiếu đủ 30 câu](results/TEST_REVIEW.md) ghi câu hỏi, câu trả lời, citation và lý do từng nhãn. JSON trong thư mục run lưu source_check, trace và toàn bộ thông tin chấm. Lỗi quan sát phải được giữ trong kết quả Test, không sửa code hoặc chạy lại để thay điểm của lượt chính thức.

Các câu Test không đạt trong lượt chính thức:

- adv-test-14: Lỗi hệ thống/calculator: trace kết thúc với invalid character ÷ (U+00F7), không có đáp án hay citation. Tính fail và giữ nguyên trong mẫu số 30; không thay bằng đáp án tính ngoài hoặc loại khỏi mẫu.
- adv-test-17: Usage gap 64% so với 49% và chênh 15 điểm phần trăm đúng. Nhưng đáp án đọc South Asia thành 0,1 GB thay vì 1,1 GB/người/tháng, rồi kết luận Sub-Saharan Africa cao hơn và chênh 0,2 GB. Nguồn Figure 5.6 p186 và chính quote của trace ghi South Asia 1,1; Sub-Saharan Africa 0,3, nên South Asia cao hơn 0,8 GB. Hai citation chứa đủ nguồn nhưng câu trả lời sai số, chiều so sánh và phép trừ: fail.
- adv-test-18: Các mốc và nội dung trả lời đúng (2007/CPI, 2011/inaccurate CPI+GDP, dỡ censure 2016 sau cải cách), nhưng citation p295 bbox [0.091,0.75,0.804,0.928] chỉ bao đáy hai cột. Nó kết thúc ở consumer price ở cột trái và ghép vùng antitrust không liên quan ở cột phải; phần tiếp nối index and GDP cùng mốc dỡ censure 2016 nằm đầu cột phải ngoài bbox. Citation p89 không bù được evidence thiếu của hop p295: fail vì vùng không hỗ trợ toàn bộ điều kiện.
- adv-test-22: Đáp án nội dung đúng nhưng bbox p286 [0.205,0.405,0.702,0.506] chỉ bao tiêu đề Box 8.1 và vài dòng mở đầu nói cải cách phức tạp. Nó không chứa định nghĩa soft infrastructure cùng standards/methods/accountable people, cũng không chứa đoạn first step về access/classification/producers-users/limitations/provenance ở phía dưới cột trái. Quote không nằm trong vùng đã trả: fail citation.

## Token, thời gian và chi phí

| Giai đoạn | Request sinh / có usage | Input / output | USD ước tính |
|---|---|---|---|
| Mô tả trang để index | 107 / 107 | 431087 / 48140 | 0,07794785 |
| Dev baseline 20261116-121843-dev-baseline-488da010 | 21 / 21 | 313846 / 4396 | 0,04142718 |
| Dev candidate 20261116-121901-dev-candidate-25029307 | 24 / 24 | 594521 / 4918 | 0,07677232 |
| Dev baseline 20261116-122648-dev-baseline-91fbfbb2 | 23 / 23 | 370243 / 4784 | 0,04867065 |
| Dev candidate 20261116-122658-dev-candidate-fdc3f714 | 26 / 26 | 664083 / 5696 | 0,08585642 |
| Test baseline 20261116-123301-test-baseline-45143179 | 36 / 36 | 558094 / 7171 | 0,07334455 |
| Toàn bộ phần nâng cao | 237 / 237 | 2931874 / 75105 | 0,40401898 |

Tổng riêng phần nâng cao là **2931874 input token, 75105 output token và 0,40401898 USD ước tính**. Trần học viên chọn là 5 USD. Khoản dự phòng thiếu usage hiện là 0,00000000 USD. Tổng này gồm mô tả để index, cả Dev chẩn đoán và Dev cuối, cùng Test. Không cộng lại dòng tổng với các dòng thành phần và không gộp chi phí phần cơ bản vào đây.

[Ledger từng câu](results/case-ledger.json) giữ thời gian, token, chi phí, lỗi và danh sách API event cho mọi câu Dev/Test, kể cả câu lỗi calculator sau khi API đã trả usage.

Giá Standard short-context được kiểm tra ngày 16/11/2026 trên [trang model](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá OpenAI](https://developers.openai.com/api/docs/pricing). Trên một triệu token, input không cache là 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Công thức là `(uncached*0.10 + cached*0.01 + write30m*0.125 + write12h*0.25 + output*0.50)/1_000_000`. Uncached bằng input trừ cached và cache write để tránh cộng hai lần. Output đã gồm reasoning, không cộng reasoning riêng. Token ảnh nằm trong input usage của API.

Trước mỗi request sinh nội dung có một request đếm token cùng input và một khoản giữ chỗ thận trọng. Có 237 request đếm được ghi nhận đi kèm các request sinh, được báo riêng chứ không coi là response sinh nội dung. Không xác nhận hóa đơn hoặc suy chi phí không ghi nhận là bằng không. Tổng không gồm chi phí máy local, điện, thuế, phụ phí tier/vùng hoặc token trợ lý dùng khi soạn code và nhãn ngoài các API event của pipeline.

Thời gian theo câu bao gồm retrieve, đếm token, gọi model và xử lý công cụ. Tổng là cộng elapsed của các câu, không phải wall time toàn quy trình. Trung vị xét tất cả kết quả đã chạy. Không tính khởi tạo embedding, kiểm hash toàn index, tải model hoặc ghi JSON ngoài vòng đo. API event có elapsed gồm đếm token và sinh nội dung. Index vision chạy ba worker nên tổng elapsed của các request chồng lấn, không dùng tổng đó như wall time. Tổng wall time trích xuất và embedding chưa được lưu bằng đồng hồ của pipeline, nên không bổ sung số suy đoán.

## Lượt Dev chẩn đoán được giữ để kiểm tra lịch sử

| Lượt | Đạt / tổng | Input / output token | Cached / write 30m / write 12h | Tổng s / trung vị s | USD ước tính | Lỗi |
|---|---|---|---|---|---|---|
| [Dev baseline](results/runs/20261116-121843-dev-baseline-488da010/config.json) | 14/18 (77,78%) | 313846 / 4396 | 0 / 313783 / 0 | 149,681 / 6,732 | 0,04142718 | 0/18 |
| [Dev candidate](results/runs/20261116-121901-dev-candidate-25029307/config.json) | 16/18 (88,89%) | 594521 / 4918 | 0 / 594449 / 0 | 247,757 / 9,769 | 0,07677232 | 0/18 |

Các lượt này giữ nguyên trace và nhãn, không trộn với cặp Dev cuối khi chọn cấu hình. Sai vùng citation và sai đối tượng đo trong Dev minh họa rằng nhận đúng con số hoặc có citation đúng trang chưa đủ để được chấm đạt.

Ba file code đã đổi giữa hai cặp Dev được lưu tại `advanced/history/pipeline-v1`, khôi phục từ các thay đổi đã biết và kiểm tra khớp từng byte với hash ghi trước lượt Dev đầu. Những file runtime còn lại giữ cùng hash. Bản lưu này phục vụ kiểm tra lịch sử, không thay pipeline đã chốt cho Test.

## Tái lập và giới hạn

[README nâng cao](README.md) hướng dẫn tải đúng PDF, cài dependency đã khóa, khởi động database, khôi phục vector snapshot và 350 ảnh, kiểm tra artifact rồi xem lại nhãn mà không gọi model. `python -m advanced.analyze`, `python -m advanced.build_report` và `python -m advanced.verify` chỉ đọc kết quả đã lưu. `python -m advanced.restore --check-only` đối chiếu dữ liệu live với snapshot. Lệnh chạy Dev/Test gọi OpenAI thật và có thể phát sinh chi phí. Model alias, độ ngẫu nhiên, mạng và môi trường phần cứng có thể làm kết quả chạy lại khác lịch sử dù hash source/index giống nhau.

Chỉ có một tài liệu tiếng Anh và một lượt Test, chưa đánh giá nhiều tài liệu, dữ liệu tiếng Việt hoặc độ ổn định qua nhiều seed. Mô tả hình có thể sai và model embedding có cửa sổ 128 token, nên chuỗi dài có thể bị cắt. Benchmark có locator hoặc tên nội dung khá cụ thể và chưa đại diện hoàn toàn cho câu hỏi mở không biết vị trí. Bbox nguyên trang có thể đủ định vị khi kèm tên vùng và quote nhưng kém chính xác hơn crop sát đối tượng. Chưa đo tác dụng riêng của vision bằng một ablation chỉ-text, vì hai cấu hình đều dùng vision. Kết quả không chứng minh mọi câu trong các nhóm hình bắt buộc phải nhìn ảnh mới trả lời được. Hệ thống chưa có kiểm thử an toàn prompt injection chuyên biệt.

Nhãn đang là đề xuất có trợ lý hỗ trợ đối chiếu PDF gốc, chưa có xác nhận riêng của học viên cho phần nâng cao và chưa có người chấm độc lập. Khi chưa hoàn tất xác nhận và kiểm tra yêu cầu, chỉ báo tỷ lệ đề xuất và trạng thái chưa đạt ngưỡng số học 27/30, không tự cộng 15 điểm.
