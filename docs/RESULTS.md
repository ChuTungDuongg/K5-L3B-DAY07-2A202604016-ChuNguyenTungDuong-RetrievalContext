# Danh sách lượt chạy và quy ước kết quả Day 7

Báo cáo chính chỉ dùng hai tên Dev và Test. Tám lượt chính được chỉ rõ dưới đây, còn lịch sử phiên bản và lần đầu lỗi API nằm trong [phụ lục lịch sử](EXPERIMENT_HISTORY.md). Không có lượt API mới phát sinh khi rút gọn báo cáo.

## Các lượt dùng trong báo cáo chính

| Nhãn trong báo cáo | Run ID | Dataset kỹ thuật |
|---|---|---|
| Dev, Dense | [20261116-110050-dense-413f3660](../starter/results/dev-runs/20261116-110050-dense-413f3660/summary.json) | dev-final |
| Dev, TF-IDF | [20261116-110050-tfidf-334bf82c](../starter/results/dev-runs/20261116-110050-tfidf-334bf82c/summary.json) | dev-final |
| Dev, Hybrid | [20261116-110050-hybrid-02a2376c](../starter/results/dev-runs/20261116-110050-hybrid-02a2376c/summary.json) | dev-final |
| Dev, baseline | [20261116-105850-agent-42699e90](../starter/results/dev-runs/20261116-105850-agent-42699e90/summary.json) | dev-final |
| Dev, cải thiện 1 | [20261116-105850-agent-d59aedb5](../starter/results/dev-runs/20261116-105850-agent-d59aedb5/summary.json) | dev-final |
| Dev, cải thiện 2 | [20261116-105850-agent-c19ed2ae](../starter/results/dev-runs/20261116-105850-agent-c19ed2ae/summary.json) | dev-final |
| Test, baseline | [20261116-104442-baseline-1fc447dc](../starter/results/test-runs/20261116-104442-baseline-1fc447dc/summary.json) | test-v2 |
| Test, ứng viên | [20261116-103836-candidate-4c2c7046](../starter/results/test-runs/20261116-103836-candidate-4c2c7046/summary.json) | test-v2 |

Tổng phần chính: 94717 input token, 17469 output token, ước tính 0,01826325 USD. Ba lượt retrieval không gọi API, năm lượt agent có response usage.

## Toàn bộ lượt đã ghi nhận

Bảng này gồm cả tám lượt chính và các lượt lịch sử, không cộng chúng như những lần đánh giá độc lập. Mỗi run ID dẫn tới thư mục config, traces, summary và nhãn nếu đã chấm. Chi phí chỉ cộng response usage ghi nhận, không phải hóa đơn tài khoản.

| Run ID | Vai trò | Dataset | Cấu hình | Thành công / tổng, lỗi | Input / output | Tổng s / trung vị s | USD ước tính |
|---|---|---|---|---|---|---|---|
| [20261116-095956-hybrid-cb3e35e6](../starter/results/dev-runs/20261116-095956-hybrid-cb3e35e6/summary.json) | Lịch sử | dev-original | hybrid, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,746 / 0,0429 | 0,00000000 USD |
| [20261116-095956-tfidf-6d3dad46](../starter/results/dev-runs/20261116-095956-tfidf-6d3dad46/summary.json) | Lịch sử | dev-original | tfidf, budget 800, search None | 15/15, lỗi 0 | 0 / 0 | 0,014 / 0,0010 | 0,00000000 USD |
| [20261116-100021-agent-9b0e0706](../starter/results/dev-runs/20261116-100021-agent-9b0e0706/summary.json) | Lịch sử | dev-unversioned | agent, budget 2000, search 3 | 1/1, lỗi 0 | 2550 / 316 | 16,627 / 16,6273 | 0,00041300 USD |
| [20261116-100059-dense-24511a3b](../starter/results/dev-runs/20261116-100059-dense-24511a3b/summary.json) | Lịch sử | dev-original | dense, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,800 / 0,0482 | 0,00000000 USD |
| [20261116-100208-dense-9da175cd](../starter/results/dev-runs/20261116-100208-dense-9da175cd/summary.json) | Lịch sử | dev-original | dense, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,927 / 0,0501 | 0,00000000 USD |
| [20261116-100235-tfidf-ec28ade0](../starter/results/dev-runs/20261116-100235-tfidf-ec28ade0/summary.json) | Lịch sử | dev-original | tfidf, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,022 / 0,0012 | 0,00000000 USD |
| [20261116-100239-hybrid-be8c8f15](../starter/results/dev-runs/20261116-100239-hybrid-be8c8f15/summary.json) | Lịch sử | dev-original | hybrid, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,910 / 0,0520 | 0,00000000 USD |
| [20261116-100310-agent-1ba613e8](../starter/results/dev-runs/20261116-100310-agent-1ba613e8/summary.json) | Lịch sử | dev-original | agent, budget 2000, search 3 | 17/17, lỗi 0 | 23535 / 3613 | 113,776 / 5,3302 | 0,00416000 USD |
| [20261116-100808-agent-226af6a2](../starter/results/dev-runs/20261116-100808-agent-226af6a2/summary.json) | Lịch sử | dev-original | agent, budget 4000, search 3 | 15/17, lỗi 2 | 22434 / 4767 | 136,370 / 5,4993 | 0,00465825 USD |
| [20261116-100808-agent-77a4573b](../starter/results/dev-runs/20261116-100808-agent-77a4573b/summary.json) | Lịch sử | dev-original | agent, budget 2000, search 5 | 17/17, lỗi 0 | 30176 / 4656 | 138,834 / 5,3198 | 0,00534560 USD |
| [20261116-101645-agent-12bd40ff](../starter/results/dev-runs/20261116-101645-agent-12bd40ff/summary.json) | Lịch sử | dev-unversioned | agent, budget 4000, search 3 | 1/1, lỗi 0 | 2047 / 384 | 16,647 / 16,6474 | 0,00042363 USD |
| [20261116-101645-agent-9a7c2fb4](../starter/results/dev-runs/20261116-101645-agent-9a7c2fb4/summary.json) | Lịch sử | dev-unversioned | agent, budget 4000, search 3 | 1/1, lỗi 0 | 1745 / 308 | 9,353 / 9,3535 | 0,00032850 USD |
| [20261116-101748-agent-519fb4bf](../starter/results/dev-runs/20261116-101748-agent-519fb4bf/summary.json) | Lịch sử | dev-original | agent, budget 2000, search 3 | 17/17, lỗi 0 | 21900 / 3625 | 104,223 / 5,2182 | 0,00400250 USD |
| [20261116-101748-agent-fbc1b0be](../starter/results/dev-runs/20261116-101748-agent-fbc1b0be/summary.json) | Lịch sử | dev-original | agent, budget 4000, search 3 | 17/17, lỗi 0 | 23819 / 3630 | 104,613 / 5,3064 | 0,00431368 USD |
| [20261116-105850-agent-42699e90](../starter/results/dev-runs/20261116-105850-agent-42699e90/summary.json) | Phần chính | dev-final | agent, budget 2000, search 3 | 15/17, lỗi 2 | 18592 / 4520 | 241,856 / 5,7131 | 0,00411920 USD |
| [20261116-105850-agent-c19ed2ae](../starter/results/dev-runs/20261116-105850-agent-c19ed2ae/summary.json) | Phần chính | dev-final | agent, budget 2000, search 5 | 16/17, lỗi 1 | 27473 / 3902 | 274,421 / 11,5531 | 0,00469830 USD |
| [20261116-105850-agent-d59aedb5](../starter/results/dev-runs/20261116-105850-agent-d59aedb5/summary.json) | Phần chính | dev-final | agent, budget 4000, search 3 | 16/17, lỗi 1 | 24445 / 5421 | 258,671 / 10,6577 | 0,00518235 USD |
| [20261116-110050-dense-413f3660](../starter/results/dev-runs/20261116-110050-dense-413f3660/summary.json) | Phần chính | dev-final | dense, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 1,416 / 0,0922 | 0,00000000 USD |
| [20261116-110050-hybrid-02a2376c](../starter/results/dev-runs/20261116-110050-hybrid-02a2376c/summary.json) | Phần chính | dev-final | hybrid, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 1,466 / 0,0917 | 0,00000000 USD |
| [20261116-110050-tfidf-334bf82c](../starter/results/dev-runs/20261116-110050-tfidf-334bf82c/summary.json) | Phần chính | dev-final | tfidf, budget 2000, search None | 15/15, lỗi 0 | 0 / 0 | 0,013 / 0,0009 | 0,00000000 USD |
| [20261116-102522-baseline-1dac47cf](../starter/results/test-runs/20261116-102522-baseline-1dac47cf/summary.json) | Lịch sử | test-v1 | agent-dense, budget 2000, search 3 | 6/7, lỗi 1 | 10628 / 3038 | 69,133 / 8,2444 | 0,00258180 USD |
| [20261116-102522-candidate-c1647e44](../starter/results/test-runs/20261116-102522-candidate-c1647e44/summary.json) | Lịch sử | test-v1 | agent-dense, budget 4000, search 3 | 0/7, lỗi 7 | 0 / 0 | 9,291 / không có | 0,00000000 USD |
| [20261116-102926-baseline-c22a875f](../starter/results/test-runs/20261116-102926-baseline-c22a875f/summary.json) | Lịch sử | test-v1 | agent-dense, budget 2000, search 3 | 7/7, lỗi 0 | 12547 / 3338 | 118,149 / 8,1836 | 0,00292370 USD |
| [20261116-103202-candidate-896d9107](../starter/results/test-runs/20261116-103202-candidate-896d9107/summary.json) | Lịch sử | test-v1 | agent-dense, budget 4000, search 3 | 7/7, lỗi 0 | 11188 / 3067 | 59,193 / 6,8263 | 0,00271785 USD |
| [20261116-103658-baseline-d7c3d519](../starter/results/test-runs/20261116-103658-baseline-d7c3d519/summary.json) | Lịch sử | test-v2 | agent-dense, budget 2000, search 3 | 6/7, lỗi 1 | 11086 / 1643 | 71,660 / 10,1077 | 0,00193010 USD |
| [20261116-103836-candidate-4c2c7046](../starter/results/test-runs/20261116-103836-candidate-4c2c7046/summary.json) | Phần chính | test-v2 | agent-dense, budget 4000, search 3 | 7/7, lỗi 0 | 15268 / 1979 | 65,659 / 10,1901 | 0,00254600 USD |
| [20261116-104442-baseline-1fc447dc](../starter/results/test-runs/20261116-104442-baseline-1fc447dc/summary.json) | Phần chính | test-v2 | agent-dense, budget 2000, search 3 | 7/7, lỗi 0 | 8939 / 1647 | 46,985 / 6,4914 | 0,00171740 USD |

Tổng recorded usage: 268372 input, 49854 output, ước tính 0,05206185 USD.

Giá ngày 16/11/2026: input 0,10 USD, cached input 0,01 USD, write 30m 0,125 USD, write 12h 0,25 USD, output 0,50 USD trên một triệu token, theo [OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna). Công thức chi tiết ở báo cáo và script `scripts/summarize_results.py`. Các lượt local không có phí API, nhưng chi phí CPU/điện chưa đo.

Dev-original có 15 dòng có đáp án nhưng 14 câu hỏi khác nhau. Dev-final thay câu lặp bằng data compliance, đủ 15 câu khác nhau. Dev-unversioned là các lượt chẩn đoán ngắn thiếu hash dataset và không có ID giúp phân biệt phiên bản, nên không tự gán vào dev gốc. Test-v1 là bộ trước sửa retry, Test-v2 là bộ tạo sau khi ghi phiên bản. Baseline test-v2 chạy lại giữ riêng với lần đầu. Một số test trước lỗi vẫn chưa chấm tay, vì vậy bảng lịch sử ghi trạng thái và token, không bịa điểm chất lượng.

Các lượt dev cuối được chạy để kiểm tra bộ dữ liệu sau loại câu trùng, sau khi test đã hoàn tất. Không dùng chúng để viết lại lịch sử lựa chọn trước test. Việc đóng gói code sau các lượt đo không làm thay đổi các file log đã lưu.
