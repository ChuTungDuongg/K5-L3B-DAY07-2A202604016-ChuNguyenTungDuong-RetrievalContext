"""Build the individual Vietnamese report from stored, auditable results."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = {
    'dense':'20261116-110050-dense-413f3660', 'tfidf':'20261116-110050-tfidf-334bf82c',
    'hybrid':'20261116-110050-hybrid-02a2376c',
    'dev_base':'20261116-105850-agent-42699e90', 'dev_candidate':'20261116-105850-agent-d59aedb5',
    'dev_more':'20261116-105850-agent-c19ed2ae',
    'selection_base':'20261116-101748-agent-519fb4bf', 'selection_candidate':'20261116-101748-agent-fbc1b0be',
    'test_base_first':'20261116-103658-baseline-d7c3d519', 'test_candidate':'20261116-103836-candidate-4c2c7046',
    'test_base_repeat':'20261116-104442-baseline-1fc447dc'}


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def number(value, digits=2): return f'{value:.{digits}f}'.replace('.', ',')
def rate(n, N): return f'{n}/{N} ({number(100*n/N,1)}%)' if N else '0/0 (không áp dụng)'
def clean(value): return str(value).replace('|','/').replace('\n',' ')


def main():
    ledger = read(ROOT/'results/run_ledger.json')
    runs = {r['run_id']:r for r in ledger['runs']}
    selected = {k:runs[v] for k,v in IDS.items()}
    def money(row): return number(float(row['usage_cost']['estimated_usd']),8)+' USD'
    def timing(row): return f"trung vị {number(row['median_ms']/1000,4)} s/câu, tổng {number(row['elapsed_all_seconds'],3)} s, {money(row)}"
    def retriever_row(key, label, method):
        r=selected[key]; s=r['summary']; N=s['metric_denominator']
        return f"| {label} | {method}, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | dev cuối | {rate(s['hit1'],N)} | {rate(s['hit3'],N)} | {rate(s['context_hit'],N)} | {timing(r)} |"
    retrieval = [retriever_row('dense','Baseline','Dense cosine pgvector'),
                 retriever_row('tfidf','Phương pháp 2','TF-IDF'),
                 retriever_row('hybrid','Phương pháp 3','Hybrid RRF, 10 ứng viên mỗi nhánh, hằng số 60')]
    for key,label,description in [('dev_candidate','Cải thiện 1','Agent dense, budget 4000, tối đa 3 search'),('dev_more','Cải thiện 2','Agent dense, budget 2000, tối đa 5 search')]:
        r=selected[key]; s=selected['dense']['summary']; cer=r['metrics']['context_exact']
        retrieval.append(f"| {label} | {description}, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | dev cuối | {rate(s['hit1'],15)} câu gốc | {rate(s['hit3'],15)} câu gốc | {rate(cer['n'],cer['N'])} trên câu chạy thành công | {timing(r)}, lỗi {r['errors']}/17 |")
    for key,label in [('test_candidate','Cấu hình đã chọn'),('test_base_repeat','Baseline')]:
        r=selected[key];s=r['summary'];N=s['retrieval_denominator']
        retrieval.append(f"| {label} | Agent dense, budget {r['config']['budget_chars']}, tối đa 3 search, top 3 | v2, baseline là lượt chạy lại, giữ lượt đầu ở bảng lịch sử | test | {rate(s['original_hit1'],N)} câu gốc | {rate(s['original_hit3'],N)} câu gốc | {rate(s['agent_context_hit'],N)} exact gold | {timing(r)} |")
    agent_rows=[]
    labels={'selection_base':'Dev gốc, baseline sau tăng output','selection_candidate':'Dev gốc, ứng viên sau tăng output',
            'dev_base':'Dev cuối, baseline','dev_candidate':'Dev cuối, 4000','dev_more':'Dev cuối, 5 search',
            'test_base_first':'Test v2, baseline lần đầu','test_candidate':'Test v2, ứng viên lần đầu','test_base_repeat':'Test v2, baseline chạy lại'}
    for key,label in labels.items():
        r=selected[key];m=r['metrics'];g=m['grounded_answer'];distribution=', '.join(f'{k} lượt: {v} câu' for k,v in sorted(r['search_distribution'].items(),key=lambda x:int(x[0])))
        def rat(field): return rate(m[field]['n'],m[field]['N'])
        agent_rows.append(f"| {label} | {rat('tool_use')} | {distribution} | 0/1/2 = {g['0']}/{g['1']}/{g['2']}, N={g['N']}, TB {number(g['mean'])}/2 | {rat('citation_validity')} | {rat('answer_citation_coverage')} | {rat('abstention')} | {rat('false_abstention')} |")
    query_rows=[]
    for key,label in [('test_base_first','B lần đầu'),('test_candidate','C'),('test_base_repeat','B chạy lại')]:
        r=selected[key];p=ROOT/r['path'];traces=read(p/'traces.json');reviews={x['query_id']:x for x in read(p/'reviews.json')}
        for t in traces:
            q=t['query_id'];review=reviews.get(q);events=[e for e in t.get('events',[]) if e.get('event')=='search']
            kind='Có đáp án' if t['answerable'] else 'Thiếu evidence'
            if review is None:
                query_rows.append(f"| {label}: {q} | {kind} | Không lưu được context cuối do API error | Không có đáp án | Lỗi {t.get('error_type')}, báo riêng và không gán 0 |")
                continue
            ids=','.join(events[-1]['context_ids']) if events else 'rỗng'
            answer=clean(t.get('answer',''))
            if t['answerable']:
                mark=f"Trả lời {review['answer_grade']}/2, context {review['context_grade']}/2"
            else: mark='Từ chối phù hợp' if review['abstention_correct'] else 'Từ chối không phù hợp'
            query_rows.append(f"| {label}: {q} | {kind} | {len(events)} search, context IDs `{ids}` | {answer} | {mark}. {clean(review['reason'])} |")

    token_rows=[]
    for key,label in [('selection_base','Dev gốc B'),('selection_candidate','Dev gốc C'),('dev_base','Dev cuối B'),('dev_candidate','Dev cuối C'),('dev_more','Dev cuối 5 search'),('test_base_first','Test v2 B lần đầu'),('test_candidate','Test v2 C lần đầu'),('test_base_repeat','Test v2 B chạy lại')]:
        r=selected[key];u=r['usage_cost']
        token_rows.append(f"| {label} | {u['input_tokens']} | {u['output_tokens']} | {u['cached_input_tokens']} | {u['cache_write_30m_tokens']} / {u['cache_write_12h_tokens']} | {number(r['elapsed_all_seconds'],3)} | {number(r['median_ms']/1000,4)} | {money(r)} | {r['errors']}/{r['total']} |")

    report = '''# Báo cáo Day 7

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
@@RETRIEVAL@@

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
@@AGENT_ROWS@@

  Lỗi được tách khỏi mẫu số chất lượng theo starter. Dev cuối baseline có 2 lỗi nên điểm câu trả lời dùng N=13, hai cấu hình còn lại dùng N=14. Test v2 baseline lần đầu dùng N=4 do một lỗi API, còn ứng viên và baseline chạy lại dùng N=5. Các trung bình khác mẫu số không là so sánh trực tiếp. Bộ kiểm tra bổ sung dev cũng có lỗi mạng và API 400 nên không thể dùng điểm trên phần thành công để tuyên bố cấu hình nào chắc chắn tốt hơn.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
@@QUERY_ROWS@@

  Ký hiệu B là baseline 2000, C là ứng viên 4000. Các dòng B lần đầu, C và B chạy lại giữ riêng toàn bộ test v2. Trong baseline chạy lại, câu 387 được chấm thận trọng 1/2 vì nguồn chỉ mô tả điều kiện chọn tuple và không nêu rõ điều kiện true. Câu 397 đúng thuật ngữ nhưng citation chỉ liệt kê tính năng nên nhận 0 về grounded answer. Các nhãn có tính diễn giải và không có thỏa thuận giữa nhiều người chấm. Học viên xác nhận nhãn có Codex hỗ trợ, không coi trợ lý là người chấm độc lập.

  Context của baseline v2 lần đầu có ba câu mức 2, một câu mức 1 và một câu không có nhãn do lỗi API. Baseline chạy lại có ba câu mức 2 và hai câu mức 1, đủ năm câu có đáp án được đọc. Ứng viên có bốn câu mức 2 và một câu mức 1. Vì baseline đã được chạy lại, cần báo cả hai lần thay vì coi lượt lặp là một mẫu test mới hoặc chọn lượt có điểm đẹp hơn.

- Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:

  Thư mục run chính được liệt kê trong [phụ lục RESULTS](../../docs/RESULTS.md). Mỗi lượt có `config.json`, `traces.json`, `summary.json`. Những lượt đã chấm có `reviews.json` và `agent-metrics.json`. File [run_ledger.json](../../results/run_ledger.json) lưu toàn bộ 27 lượt batch trong phạm vi cộng usage, gồm cả chạy thử có limit và các lần lỗi. JSON được ghi sau mỗi câu, nhưng khi một exception xảy ra giữa vòng agent thì log lịch sử có thể thiếu các event trước lỗi. Không có context cuối được lưu không được suy thành context grade 0 của lần lỗi.

  Thời gian là elapsed theo từng câu, không tính khởi tạo model, tải weights, tạo TF-IDF index hoặc ghi file. Trung vị chỉ xét câu không lỗi. Tổng thời gian là tổng elapsed của tất cả câu, có cả thời gian chờ của câu lỗi, không phải thời gian toàn tiến trình. Test runner tính cả truy xuất câu gốc trước vòng agent, trong khi dev agent runner không có bước đo đó. Một số lượt chạy đồng thời nên độ trễ chịu ảnh hưởng mạng và tranh chấp tài nguyên. Chưa đo RAM, CPU riêng, cold start, tải đồng thời có kiểm soát hoặc độ biến thiên qua nhiều lần lặp cân bằng.

| Lượt | Input token | Output token | Cached input | Cache write 30m / 12h | Tổng elapsed câu (s) | Trung vị câu thành công (s) | Chi phí ước tính | Lỗi / số câu |
|---|---|---|---|---|---|---|---|---|
@@TOKEN_ROWS@@

  Quy ước chi phí dùng USD, giá Standard short-context của `gpt-6-luna` kiểm tra ngày 16/11/2026 trên [trang model OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá](https://developers.openai.com/api/docs/pricing). Mỗi một triệu token: input không cache 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Tất cả request ghi nhận ngắn hơn ngưỡng long-context. Không thêm phí hosted file search hoặc tool OpenAI vì retriever chạy trên PostgreSQL local.

  Công thức là `(input không cache × 0,10 + cached input × 0,01 + cache write 30m × 0,125 + cache write 12h × 0,25 + output × 0,50) / 1.000.000`. Input không cache bằng input tổng trừ cached và cache-write tokens, tránh tính hai lần. Output theo API đã gồm reasoning nếu có, không cộng reasoning lần nữa. Chi phí là ước tính theo các response usage đã lưu, không phải hóa đơn tài khoản, không gồm thuế, phụ phí vùng hoặc cấu hình tier khác chưa ghi nhận.

  Phạm vi 27 lượt có @@TOTAL_INPUT@@ input token, @@TOTAL_OUTPUT@@ output token và chi phí ghi nhận ước tính @@TOTAL_COST@@ USD. Những request lỗi không có usage không được suy là tài khoản chắc chắn bị tính 0. Các lần soạn bộ câu hỏi có tổng token quan sát trong phiên là 6183 nhưng không giữ đủ breakdown input/output trong artifact, nên không được cộng như một chi phí chính xác. Ngoài ra có kiểm tra key, debug và demo riêng ngoài phạm vi ledger. Chi phí embedding/retrieval local bằng 0 về phí API, nhưng vẫn có chi phí máy và điện chưa đo.

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
'''
    values={'RETRIEVAL':'\n'.join(retrieval),'AGENT_ROWS':'\n'.join(agent_rows),
            'QUERY_ROWS':'\n'.join(query_rows),'TOKEN_ROWS':'\n'.join(token_rows),
            'TOTAL_INPUT':str(ledger['total_recorded_input_tokens']), 'TOTAL_OUTPUT':str(ledger['total_recorded_output_tokens']),
            'TOTAL_COST':number(float(ledger['total_estimated_usd']),8)}
    for key,val in values.items(): report=report.replace('@@'+key+'@@',val)
    target=ROOT/'report/individual/2A202604016_ChuNguyenTungDuong.md'
    target.write_text(report,encoding='utf-8')

    appendix=['# Lịch sử đầy đủ và quy ước kết quả Day 7','',
              'Các lượt dưới đây được lấy từ artifact đã lưu. Mỗi run ID dẫn tới config, traces và summary trong repo. Chi phí chỉ cộng response usage ghi nhận, không phải hóa đơn tài khoản. Các phiên bản dataset và code không được gộp như cùng một test độc lập.','',
              '| Run ID | Dataset | Cấu hình | Thành công / tổng, lỗi | Input / output | Tổng s / trung vị s | USD ước tính |','|---|---|---|---|---|---|---|']
    for r in ledger['runs']:
        c=r['config'];m=c.get('method',c.get('config','unknown'));budget=c.get('budget_chars');search=c.get('max_searches');u=r['usage_cost']
        med=number(r['median_ms']/1000,4) if r['median_ms'] is not None else 'không có'
        appendix.append(f"| [{r['run_id']}](../{r['path']}/summary.json) | {r['dataset_version']} | {m}, budget {budget}, search {search} | {r['successful']}/{r['total']}, lỗi {r['errors']} | {u['input_tokens']} / {u['output_tokens']} | {number(r['elapsed_all_seconds'],3)} / {med} | {money(r)} |")
    appendix += ['',f"Tổng recorded usage: {ledger['total_recorded_input_tokens']} input, {ledger['total_recorded_output_tokens']} output, ước tính {number(float(ledger['total_estimated_usd']),8)} USD.",'',
                 'Giá ngày 16/11/2026: input 0,10 USD, cached input 0,01 USD, write 30m 0,125 USD, write 12h 0,25 USD, output 0,50 USD trên một triệu token, theo [OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna). Công thức chi tiết ở báo cáo và script `scripts/summarize_results.py`. Các lượt local không có phí API, nhưng chi phí CPU/điện chưa đo.','',
                 'Dev-original có 15 dòng có đáp án nhưng 14 câu hỏi khác nhau. Dev-final thay câu lặp bằng data compliance, đủ 15 câu khác nhau. Dev-unversioned là các lượt chẩn đoán ngắn thiếu hash dataset và không có ID giúp phân biệt phiên bản, nên không tự gán vào dev gốc. Test-v1 là bộ trước sửa retry, Test-v2 là bộ tạo sau khi ghi phiên bản. Baseline test-v2 chạy lại giữ riêng với lần đầu. Một số test trước lỗi vẫn chưa chấm tay, vì vậy bảng lịch sử ghi trạng thái và token, không bịa điểm chất lượng.','',
                 'Các lượt dev cuối được chạy để kiểm tra bộ dữ liệu sau loại câu trùng, sau khi test đã hoàn tất. Không dùng chúng để viết lại lịch sử lựa chọn trước test. Việc đóng gói code sau các lượt đo không làm thay đổi các file log đã lưu.','']
    (ROOT/'docs/RESULTS.md').write_text('\n'.join(appendix),encoding='utf-8')
    print('Built report and full run appendix.')


if __name__ == '__main__': main()
