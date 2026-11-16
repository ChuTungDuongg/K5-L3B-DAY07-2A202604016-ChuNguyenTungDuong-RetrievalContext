# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.


## Bài làm của Chu Nguyễn Tùng Dương

MSSV: **2A202604016**, lớp L3B. Controller và retriever thật nằm trong `starter/agentic.py`, backend Day 6 đã được đưa vào repo để có thể chạy trên máy khác.

- [Báo cáo theo khung của thầy](report/individual/2A202604016_ChuNguyenTungDuong.md)
- [Hướng dẫn cài đặt và tái lập](REPRODUCE.md)
- [Các lượt dùng trong báo cáo và bảng chi phí đầy đủ](docs/RESULTS.md)
- [Phụ lục lịch sử phiên bản, lỗi và chạy lại](docs/EXPERIMENT_HISTORY.md)
- [Kiểm tra yêu cầu và các giới hạn còn lại](docs/REQUIREMENTS_AUDIT.md)
- [Nguồn và điều kiện sử dụng dữ liệu](data/ATTRIBUTION.md)
- [Phần nâng cao World Bank: cài đặt và tái lập](advanced/README.md)
- [Báo cáo nâng cao vòng hai, bảng Dev/Test và chi phí riêng](advanced/results/round2/REPORT.md)
- [Báo cáo nâng cao vòng một, giữ lại để đối chiếu](advanced/ROUND1_REPORT.md)

Báo cáo chính dùng hai split **Dev** (15 câu có đáp án + 2 thiếu bằng chứng) và **Test** (5 + 2). Các bảng chính gồm ba phương pháp retrieval, ba cấu hình agent trên Dev và baseline/ứng viên trên Test. Phụ lục giữ phiên bản cũ và mọi lượt lỗi/chạy lại. Baseline Test dùng lượt chạy lại vì lần đầu lỗi API 1/7 câu, được công bố trong báo cáo. Việc rút gọn cách trình bày giữ nguyên trace, nhãn và các giới hạn đánh giá.
