# Vòng thực nghiệm thứ hai

Hồ sơ này giữ kết quả của vòng trước tại `advanced/results/runs` và lưu các lượt vòng hai tại `advanced/results/round2/runs`. Bộ câu hỏi mới nằm tại `advanced/benchmark/round2`. Tất cả lượt dùng chung sổ chi phí `advanced/results/budget.json` và cùng trần 5 USD, không cấp lại ngân sách khi mở vòng mới.

Sau khi phân tích Test vòng một, phiên bản mới hỗ trợ các ký tự tính toán thường gặp và thêm một lượt model kiểm tra lại câu trả lời với ảnh PDF gốc. Citation cuối dùng bbox nguyên trang kèm nhãn vùng, câu trích và bbox model đề xuất trong trường `model_bbox`. Vùng nguyên trang thuận tiện kiểm tra đầy đủ phần hỗ trợ nhưng kém chính xác hơn crop theo đối tượng. Việc model tự kiểm tra không bảo đảm câu trả lời hoặc citation đúng.

Dev dùng cùng 18 câu, còn Test vòng hai được soạn riêng và kiểm tra không hỏi lại cùng fact với Dev hoặc Test trước. Phải chốt benchmark trước khi chạy Dev và chốt code, index, cấu hình trước Test. Mỗi cấu hình Dev có một lượt theo kế hoạch đã ghi. Lựa chọn ưu tiên số câu đạt nghiêm, sau đó trung vị thời gian và chi phí khi hòa. Kết quả của Test trước được giữ làm chẩn đoán sau khi dùng để sửa pipeline.

Trợ lý soạn Test mới cũng đã tham gia chấm Test cũ nên biết các loại lỗi đã quan sát. Bộ câu hỏi mới không phải đánh giá mù giữa những người soạn và chấm độc lập, dù được tách fact và khóa trước khi chạy vòng hai. Độ khó và nhãn vẫn cần học viên kiểm tra lại, không thể suy ra độ khó tương đương chỉ từ số lượng mỗi nhóm.

Sau khi hoàn tất và chấm các lượt, các file cấu hình, trace, nhãn, metric và bảng chi phí được lưu cùng run. Tất cả 30 câu Test, kể cả lỗi và câu thiếu kết quả, nằm trong mẫu số. Nhãn có trợ lý hỗ trợ đối chiếu PDF gốc, cần học viên xem lại trước khi nộp. Việc tính điểm tự động không thay thế bước kiểm tra nguồn của người học.

Hướng dẫn cài đặt PDF, Python và Docker được giữ ở [README nâng cao](README.md). Từ thư mục gốc repo, sau khi có PDF, ảnh trang và database đúng snapshot, xem và kiểm tra hồ sơ đã lưu bằng:

```powershell
python -m advanced.restore --check-only
python -m advanced.analyze --round 2
python -m advanced.verify --round 2
python -m advanced.report_round2
python scripts/build_report.py
```

Các lệnh này không gọi OpenAI. `analyze` cộng usage qua cả hai vòng, `verify` kiểm checksum và thứ tự freeze, còn `report_round2` dựng bảng từ trace và nhãn đã lưu. Việc tạo report yêu cầu có đủ review. Verifier không tự kiểm tra đúng sai ngữ nghĩa.

Khi xây một vòng đánh giá mới, cần soạn và khóa một Test độc lập khác trước Dev. Các lệnh dùng trong vòng hai là `python -m advanced.run --round 2 --split dev --config baseline` và tương tự với `--config candidate`, tiếp theo `python -m advanced.select --round 2` sau khi chấm Dev, rồi `python -m advanced.official_test --round 2`. Trong hồ sơ đã công bố, selection và marker không cho ghi đè lượt chính thức. Không xóa các marker để lấy kết quả tốt hơn. Các lượt model thật có thể phát sinh chi phí và không tái tạo chính xác từng phản hồi cũ.
