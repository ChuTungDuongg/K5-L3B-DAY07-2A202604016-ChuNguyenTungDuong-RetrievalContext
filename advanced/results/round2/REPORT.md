# Báo cáo nâng cao: vòng thực nghiệm thứ hai

Chu Nguyễn Tùng Dương (ChuNguyenTungDuong), MSSV 2A202604016, lớp L3B. Thực nghiệm tại múi giờ Việt Nam UTC+7.

Test vòng hai đạt **28/30 (93,33%)**, đạt ngưỡng số học 27/30 theo nhãn đề xuất. Nhãn chưa được học viên xác nhận. Kết quả không tự động xác nhận đủ điều kiện nhận bonus, vì còn yêu cầu về nguồn, index và kiểm tra của giảng viên.

Vòng trước đạt 26/30 và đã được dùng để xác định lỗi calculator, đọc sai số liệu và citation thiếu vùng. Vì pipeline sau đó đã thay đổi, kết quả vòng trước chỉ dùng chẩn đoán cho phiên bản mới. [Báo cáo vòng một](../../ROUND1_REPORT.md) giữ chi tiết nguồn 350 trang, 5493 chunk, 114 vùng trực quan và các lượt cũ. [Hướng dẫn vòng hai](../../ROUND2.md) giải thích chia phiên bản và các giới hạn.

## Pipeline và cách chọn

Cùng index, dữ liệu và model `gpt-6-luna` được dùng lại. Agent hỗ trợ phép tính `÷`, `×`, `−` và gọi thêm model để kiểm lại đề xuất trả lời trên ảnh PDF gốc. Model có thể sửa hoặc từ chối nếu nguồn không đủ. Đây là bước tự kiểm, không bảo đảm tính đúng và không thay việc đối chiếu độc lập. Bbox citation cuối bao toàn trang, kèm tên vùng và trích dẫn cụ thể. Bbox model đề xuất được lưu riêng trong `model_bbox`. Vùng nguyên trang kém chính xác hơn crop, nhưng người chấm vẫn phải kiểm tra nó thực sự chứa bằng chứng hỗ trợ mọi khẳng định.

Dev gồm 15 câu có đáp án và ba câu thiếu evidence, giữ nguyên bộ đã dùng. Test mới gồm 24 câu có đáp án và sáu câu thiếu evidence, theo sáu nhóm ở bảng dưới. Bộ Test mới được soạn và đóng băng trước các lượt Dev vòng hai, không hỏi lại cùng fact với Dev hoặc Test trước theo kiểm tra của người soạn. Trợ lý soạn Test mới cũng đã chấm Test cũ và biết các loại lỗi trước đó, nên không phải đánh giá mù giữa những người độc lập. Không có bằng chứng đủ để khẳng định hai bộ có độ khó tương đương chỉ dựa vào số lượng câu.

Cả hai cấu hình dùng cùng model và retrieval, khác số trang ảnh và số bước. Cấu hình được chọn là **baseline**, dựa trên số câu Dev đạt, rồi trung vị thời gian và chi phí khi hòa. [Kế hoạch và hash](dev-experiment-plan.json) được ghi trước Dev, [selection freeze](selection-freeze.json) chốt trước Test. Model chỉ nhận câu hỏi và evidence được truy xuất, không nhận đáp án chuẩn, nhãn hay bbox gold.

| Vòng / lượt | Đạt / tổng | Input / output | Cached / write 30m / write 12h | Tổng s / trung vị s | Ước tính USD | Lỗi |
|---|---|---|---|---|---|---|
| [1 / dev baseline](../runs/20261116-121843-dev-baseline-488da010/config.json) | 14/18 (77,78%) | 313846 / 4396 | 0 / 313783 / 0 | 149,681 / 6,732 | 0,04142718 | 0 |
| [1 / dev candidate](../runs/20261116-121901-dev-candidate-25029307/config.json) | 16/18 (88,89%) | 594521 / 4918 | 0 / 594449 / 0 | 247,757 / 9,769 | 0,07677232 | 0 |
| [1 / dev baseline](../runs/20261116-122648-dev-baseline-91fbfbb2/config.json) | 17/18 (94,44%) | 370243 / 4784 | 0 / 370174 / 0 | 162,758 / 7,229 | 0,04867065 | 0 |
| [1 / dev candidate](../runs/20261116-122658-dev-candidate-fdc3f714/config.json) | 17/18 (94,44%) | 664083 / 5696 | 0 / 664005 / 0 | 245,262 / 8,372 | 0,08585642 | 0 |
| [1 / test baseline](../runs/20261116-123301-test-baseline-45143179/config.json) | 26/30 (86,67%) | 558094 / 7171 | 0 / 557986 / 0 | 274,191 / 6,327 | 0,07334455 | 1 |
| [2 / dev baseline](runs/20261116-164337-r2-dev-baseline-8b5e219c/config.json) | 18/18 (100,00%) | 615634 / 9844 | 0 / 615514 / 0 | 359,001 / 15,057 | 0,08187325 | 0 |
| [2 / dev candidate](runs/20261116-164337-r2-dev-candidate-7d01ebc6/config.json) | 16/18 (88,89%) | 982980 / 10386 | 0 / 982857 / 0 | 471,360 / 22,303 | 0,12806242 | 1 |
| [2 / test baseline](runs/20261116-165446-r2-test-baseline-cbad637d/config.json) | 28/30 (93,33%) | 929376 / 17232 | 0 / 929187 / 0 | 507,536 / 14,467 | 0,12478328 | 1 |

Các thời gian là tổng elapsed từng câu và trung vị của các câu đã chạy, gồm retrieval và các request model, không gồm tải model, tạo index hay khởi tạo process. Các lượt Dev có thể chạy đồng thời, chịu ảnh hưởng mạng và tranh chấp tài nguyên. Một lượt mỗi cấu hình không chứng minh ưu thế thống kê.

## Test và nhãn theo từng nhóm

| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |
|---|---|---|---|
| Bảng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Ảnh, sơ đồ | 5/5 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Biểu đồ | 4/5 | 80,00% | 1 lỗi hệ thống, 1 câu không đạt |
| Multi-hop | 3/4 | 75,00% | 0 lỗi hệ thống, 1 câu không đạt |
| Text | 4/4 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| Thiếu bằng chứng | 6/6 | 100,00% | 0 lỗi hệ thống, 0 câu không đạt |
| **Toàn bộ** | **28/30** | **93,33%** | 1 lỗi hệ thống, 2 câu không đạt |

Tỷ lệ là số câu đạt chia toàn bộ 30 câu. Sai đơn vị, đối tượng đo, điều kiện, phép tính hoặc citation đều không đạt. Lỗi API, lỗi công cụ, timeout và thiếu kết quả không bị loại khỏi mẫu số. Số lỗi là 1, số kết quả thiếu là 0, số chưa chấm là 0.

[Bảng 30 câu](TEST_REVIEW.md) ghi câu hỏi, đáp án, citation và lý do từng nhãn, còn JSON review ghi kiểm tra nguồn gốc. Các câu không đạt:

- adv-r2-test-12: Công cụ tính toán báo `SyntaxError: invalid syntax` vì biểu thức chứa cả câu và đơn vị. Không có đầu ra hợp lệ để chấm phép tính.
- adv-r2-test-19: Câu trả lời thiếu cơ chế hiện diện trong dữ liệu được hỏi. Trang 130 nêu người ít tiếp cận điện thoại, internet hoặc tài khoản ngân hàng có thể ít hiện diện trong dữ liệu. Các nguồn được dẫn không bù phần thiếu.

## Token và chi phí

Toàn bộ phần nâng cao qua cả hai vòng gồm **5459864 input token**, **112567 output token**, ước tính **0,73873792 USD** theo usage đã ghi, trong trần 5 USD. Dự phòng cho usage chưa rõ là 0,00000000 USD. Bảng trên giữ từng lượt Dev/Test, còn index được ghi riêng ở [ledger](ledger.json). Không cộng dòng tổng với các dòng thành phần. [Ledger từng câu](case-ledger.json) liên kết API event và lỗi.

Giá `gpt-6-luna` Standard short-context kiểm tra 16/11/2026: input 0,10, cached input 0,01, cache write 30 phút 0,125, cache write 12 giờ 0,25 và output 0,50 USD trên một triệu token. Output đã bao gồm reasoning. Chi phí là ước tính response usage, không phải hóa đơn, chưa gồm chi phí local, thuế, tier khác hoặc token trợ lý soạn bài ngoài pipeline. Mỗi request sinh có một request đếm input riêng. Giá và model alias có thể thay đổi.

## Tái lập và giới hạn

Tải PDF đúng hash và khôi phục ảnh/vector theo [README](../../README.md), sau đó chạy `python -m advanced.analyze --round 2` và `python -m advanced.verify --round 2` để đối chiếu các artifact không gọi API. Việc chạy lại model phát sinh phí, có thể khác phản hồi lịch sử và không thay lượt Test chính thức. File `official-test.json` ghi lượt chính thức của từng vòng. Xem `advanced/benchmark/round2`, `advanced/results/round2` và các hash để kiểm tra thứ tự chốt.

Thực nghiệm chỉ dùng một tài liệu tiếng Anh, một lượt Test vòng hai và một model. Không có ablation chỉ-text, đánh giá mù giữa nhiều người hoặc bảo đảm quy tắc phát hiện hình bao phủ mọi hình vector không nhãn. Chất lượng mô tả vision, thứ tự text, cửa sổ embedding 128 token và bbox toàn trang là các giới hạn. Các câu có tên hình hoặc bảng cụ thể có thể dễ truy xuất hơn câu hỏi mở. Chưa được học viên xác nhận là trạng thái nhãn của bộ nâng cao, khác xác nhận trước đây đối với phần cơ bản.
