# Phần nâng cao: World Bank Data for Better Lives

Phần này có corpus, benchmark và kết quả riêng. Index cơ bản A/B và các kết quả đã nộp không bị thay đổi. Tài liệu nguồn là World Development Report 2021: Data for Better Lives, bản PDF 350 trang vật lý. Người học chọn tài liệu này và đặt mức trần 5 USD cho OpenAI.

## Chuẩn bị

Chạy từ thư mục gốc repo, dùng Python đã cài dependency cơ bản trong `requirements-lock.txt`:

```powershell
python -m pip install -r advanced/requirements.txt
docker compose -p day7_lab -f starter/docker-compose.yml up -d --wait
New-Item -ItemType Directory -Path advanced/data -Force
Invoke-WebRequest -Uri 'https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf' -OutFile advanced/data/source.pdf
```

Trên máy mới, dùng Python 3.13, tạo venv bằng `py -3.13 -m venv .venv`, kích hoạt bằng `.\.venv\Scripts\Activate.ps1`, rồi cài `python -m pip install -r requirements-lock.txt` trước các lệnh trên. Phiên bản quan sát được lưu ở `advanced/data/runtime-observed.json`. Sao chép `.env.example` thành `.env` nếu chưa có và điền key riêng. Không thay `.env` đã có key hoặc kết nối Day 6 đang sử dụng.

`advanced/source.py` từ chối bản PDF có SHA-256 khác `606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616`. Không tự thay bản tài liệu khi nguồn cập nhật. Mặc định advanced dùng database lab riêng ở cổng 55434. Có thể đặt `ADV_DATABASE_URL` trong `.env` để đổi database, còn tên strategy vẫn là `ADV-WDR2021-v1`. API key lấy từ `.env` hiện có và không được đưa vào Git.

Giấy phép ở trang PDF 4 là CC BY 3.0 IGO, có điều kiện ghi công, bản thích nghi và thành phần của bên thứ ba. Repo cung cấp nguồn tải, checksum, trích đoạn và locators phục vụ kiểm chứng. Không mặc định mọi ảnh của bên thứ ba có giấy phép độc lập giống toàn bộ sách.

Ghi công: World Bank. 2021. World Development Report 2021: Data for Better Lives. Washington, DC: World Bank. doi:10.1596/978-1-4648-1600-0. License: CC BY 3.0 IGO. Đây là bản xử lý phục vụ bài thực hành từ tài liệu gốc. Các diễn giải là trách nhiệm của người làm bài và không được World Bank bảo chứng.

## Khôi phục và đọc lại kết quả đã nộp, không gọi API

Sau khi có đúng PDF và database Docker, ưu tiên các lệnh sau để giữ nguyên index đã đo:

```powershell
python -m advanced.restore
python -m advanced.restore --check-only
python -m advanced.analyze
python -m advanced.build_report
python -m advanced.verify
python scripts/build_report.py
```

`restore` tái tạo 350 ảnh theo phiên bản PDFium/Pillow đã khóa, đối chiếu mọi checksum và khôi phục 5493 vector từ snapshot. Nếu strategy này đã có dữ liệu khác snapshot, lệnh từ chối ghi đè. Các strategy A/B được giữ nguyên. Những lệnh trên không tạo câu trả lời mới hoặc gọi OpenAI. Kết quả kiểm tra lưu ở `advanced/results/verification.json`, metric từng run ở `metrics.json` và tổng token/chi phí ở `advanced/results/ledger.json`. Các nhãn đề xuất không tự trở thành nhãn học viên đã xác nhận khi chạy script.

## Tạo lại text, mô tả và index từ nguồn

```powershell
python -m advanced.source
python -m advanced.visuals
python -m advanced.retrieval
```

Nhánh này dành cho kiểm tra hoặc thực nghiệm trích xuất, không cần chạy khi chỉ khôi phục kết quả đã nộp. Vision có thể phát sinh phí khi cache thiếu hoặc prompt đổi. Nếu tạo mô tả/index khác, hash sẽ khác và không thể dùng selection cũ để báo lại Test độc lập.

Native text được lấy từ tất cả 350 trang. Trang có caption Figure/Table/Map hoặc ảnh raster đáng kể được phân tích thêm bằng vision. Ảnh gốc của mọi trang vẫn có thể render theo yêu cầu, kể cả trang không có mô tả vision. Chunk giữ trang vật lý, vị trí ký tự và metadata. Các visual region có nhãn, bbox chuẩn hóa theo góc trên trái, mô tả và chi tiết hỗ trợ tìm kiếm.

Mô tả do model tạo chỉ giúp retrieval. Khi trả lời, agent được xem ảnh trang gốc và phải kiểm tra lại đơn vị, chú giải, hàng/cột, mũi tên và điều kiện. Native text có thể sai thứ tự đọc, glyph hoặc dấu ngắt dòng. Các trang mô tả lỗi hoặc không có nội dung hữu ích được công bố ở `advanced/data/visual-coverage.json`.

Visual descriptions được cache theo trang, hash PDF và prompt. Chạy lại lệnh visual bỏ qua mô tả đã có đúng phiên bản, chỉ gọi API cho phần còn thiếu. Index dùng embedding local và pgvector, không dùng embedding giả. Chi phí và thời gian nạp index được báo riêng với thời gian trả lời.

## Benchmark và thử nghiệm

Dev có 18 câu, Test có 30 câu riêng theo phân nhóm trong `ADVANCED.md`. `advanced/benchmark/freeze.json` khóa hash trước khi chạy Dev. Pipeline chỉ nhận câu hỏi khi inference, không nhận gold, group, bbox chuẩn hay đáp án.

```powershell
python -m unittest discover -s tests -v
python -m advanced.run --split dev --config baseline
python -m advanced.run --split dev --config candidate
```

Baseline xem trước ba trang ảnh, tối đa ba bước và sáu ảnh trong một request. Candidate xem trước năm trang ảnh, tối đa bốn bước và tám ảnh. Cả hai dùng cùng hybrid retrieval theo trang và cùng model. Chỉ dùng Dev để chọn cấu hình. File `advanced/results/selection-freeze.json` lưu cấu hình, lý do và hash pipeline sau khi chọn. Test runner từ chối chạy khi pipeline thay đổi sau freeze.

```powershell
python -m advanced.analyze
python -m advanced.select
python -m advanced.official_test
```

Các lệnh chọn và Test chính thức trên đã được thực hiện trong hồ sơ này. Selector không ghi đè selection cũ, chỉ chọn đúng cặp Dev theo hash hiện tại và kế hoạch đã ghi trước. Cấu hình chốt là **baseline**, vì hai cấu hình cùng 17/18 trên Dev cuối nhưng baseline có trung vị thời gian thấp hơn. `official_test` dùng cấu hình từ freeze, kiểm hash và tạo marker một lượt, từ chối chạy lượt chính thức thứ hai. Không xóa marker hoặc selection để lấy kết quả tốt hơn.

Nếu cần tái chạy model để khảo sát biến thiên, có thể chạy `python -m advanced.run --split test --config baseline`. Lượt mới được lưu trong thư mục timestamp khác và phải coi là **chẩn đoán**, không thay 30 kết quả chính thức. Bộ kiểm tra hồ sơ và trình tạo báo cáo cố ý từ chối khi có nhiều lượt Test chưa được phân loại, nên cần giữ hồ sơ đã nộp riêng trước khi mở vòng thực nghiệm mới. Nếu dùng kết quả Test để chỉnh pipeline, phải tạo Test độc lập mới trước khi báo điểm cho phiên bản sửa. Chạy Dev thêm sau khi đã xem Test cũng không tạo lại lịch sử lựa chọn trước Test.

## Chi phí và chấm điểm

`advanced/results/budget.json` ghi mức trần, reservation và usage. Trước mỗi request sinh nội dung, API đếm input và giữ trước chi phí theo mức giá thận trọng, có thêm dự phòng. Khi có usage thì đối chiếu lại, khi timeout hoặc lỗi không có usage thì giữ khoản dự phòng chưa rõ. Không ghi hóa đơn OpenAI là đã xác minh. Các phép đếm token không tạo câu trả lời và được phân biệt với request sinh nội dung.

Mỗi run lưu config, hash, trace, context, các ảnh đã xem, action, câu trả lời, citation, elapsed và lỗi. Mọi câu Test đã công bố đều nằm trong mẫu số, gồm lỗi API, timeout và thiếu kết quả. Câu trả lời đúng một phần, thiếu điều kiện, sai đơn vị hoặc citation không hỗ trợ đủ đều không đạt. Với 30 câu cần ít nhất 27 câu đạt và hoàn thành đủ yêu cầu khác mới có căn cứ đề nghị bonus.

Nhãn cần đối chiếu ảnh PDF gốc cho từng câu. Nhãn có trợ lý hỗ trợ được ghi rõ là đề xuất cho đến khi người học xác nhận. Một model judge hoặc citation ID hợp lệ không thay thế việc kiểm tra nguồn.
