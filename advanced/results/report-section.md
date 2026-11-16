## Thử thách nâng cao (nếu thực hiện)

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:

  World Bank, [World Development Report 2021: Data for Better Lives](https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf), 350 trang PDF, SHA-256 `606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616`, CC BY 3.0 IGO kèm điều kiện thành phần bên thứ ba. Thông tin ghi công và giới hạn quyền trong [báo cáo vòng một](../../advanced/ROUND1_REPORT.md).

- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:

  Xử lý 350 trang và lưu ảnh gốc có checksum. Index gồm 4995 chunk native text và 498 chunk mô tả 114 vùng trực quan, tổng 5493 chunk. Vision phân tích 107 trang chọn theo caption hoặc ảnh raster. Mười bốn trang trống và một trang nhan đề không có native text. Hình trang trí không mô tả riêng, quy tắc chọn trang có thể bỏ sót hình vector không nhãn. Agent xem ảnh gốc, dùng mô tả chỉ làm tín hiệu tìm kiếm.

- Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:

  Dev vòng hai có 15 câu có đáp án và ba câu thiếu evidence. Test mới có 24 câu có đáp án và sáu câu thiếu evidence. Câu lưu ID, nhóm, đáp án hoặc lý do thiếu evidence, trang, vùng và điều kiện. Hai split được kiểm tra không trùng fact và khóa trước Dev vòng hai. Test vòng một sau khi dùng để sửa pipeline được giữ làm chẩn đoán. Trợ lý soạn Test mới cũng đã chấm Test cũ nên chưa có đánh giá mù giữa những người độc lập.

  Pipeline dùng TF-IDF theo trang kết hợp dense pgvector bằng RRF, embedding 384 chiều và model `gpt-6-luna`. Agent có search, inspect, calculate và thêm lượt tự kiểm câu trả lời bằng ảnh gốc. Citation dùng bbox nguyên trang kèm nhãn vùng/trích dẫn, lưu thêm bbox model đề xuất. Chọn **baseline** theo điểm Dev nghiêm, rồi thời gian và chi phí khi hòa. Gold không được đưa vào model khi inference. Chi tiết trong [báo cáo vòng hai](../../advanced/results/round2/REPORT.md).

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Ảnh, sơ đồ | 5/5 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Biểu đồ | 4/5 | 80,00% | 1 lỗi hệ thống, 1 câu không đạt |
| Multi-hop | 3/4 | 75,00% | 0 lỗi hệ thống, 1 câu không đạt |
| Text | 4/4 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Thiếu bằng chứng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| **Toàn bộ** | **28/30** | **93,33%** | 1 lỗi hệ thống, 2 câu không đạt |

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:

  Test vòng hai đạt **28/30 (93,33%)**, đạt ngưỡng số học 27/30. Nhãn chưa được học viên xác nhận. Lỗi và thiếu kết quả giữ trong mẫu số. [Bảng 30 câu](../../advanced/results/round2/TEST_REVIEW.md) và trace lưu lý do, nguồn và công cụ. [Bảng mọi lượt, token, thời gian và chi phí](../../advanced/results/round2/REPORT.md) giữ cả vòng chẩn đoán.

  Tổng phần nâng cao qua hai vòng là 5459864 input token, 112567 output token và **0,73873792 USD ước tính** trên trần 5 USD. Dự phòng usage chưa rõ là 0,00000000 USD. Đây là phép tính theo response usage và giá công khai, không phải hóa đơn. Reasoning nằm trong output, chi phí local và token trợ lý ngoài pipeline chưa đo.

- Giới hạn, cách tái lập và đường dẫn benchmark:

  [Hướng dẫn nâng cao](../../advanced/README.md), [vòng hai](../../advanced/ROUND2.md), [benchmark](../../advanced/benchmark/round2/test.json), [selection](../../advanced/results/round2/selection-freeze.json) và [ledger](../../advanced/results/round2/ledger.json) cho phép đối chiếu. Chỉ có một tài liệu, một lượt Test vòng hai, không có ablation chỉ-text hoặc đánh giá mù giữa nhiều người. Bbox nguyên trang có độ chính xác định vị thấp. Model alias và mạng có thể làm chạy lại khác lịch sử. Việc nhận bonus phụ thuộc kiểm tra đủ yêu cầu của giảng viên.
