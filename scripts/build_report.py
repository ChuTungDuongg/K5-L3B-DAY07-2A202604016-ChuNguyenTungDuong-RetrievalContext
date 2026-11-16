"""Build the individual Vietnamese report from stored, auditable results."""
import json
from decimal import Decimal
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

MAIN_LABELS = {'dense':'Dev, Dense', 'tfidf':'Dev, TF-IDF', 'hybrid':'Dev, Hybrid',
               'dev_base':'Dev, baseline', 'dev_candidate':'Dev, cải thiện 1',
               'dev_more':'Dev, cải thiện 2', 'test_base_repeat':'Test, baseline',
               'test_candidate':'Test, ứng viên'}


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def number(value, digits=2): return f'{value:.{digits}f}'.replace('.', ',')
def rate(n, N): return f'{n}/{N} ({number(100*n/N,1)}%)' if N else '0/0 (không áp dụng)'
def clean(value): return str(value).replace('|','/').replace('\n',' ')


def totals(rows):
    return {'input_tokens':sum(r['usage_cost']['input_tokens'] for r in rows),
            'output_tokens':sum(r['usage_cost']['output_tokens'] for r in rows),
            'estimated_usd':str(sum((Decimal(r['usage_cost']['estimated_usd']) for r in rows), Decimal(0)))}


def agent_row(row, label):
    m=row['metrics'];g=m['grounded_answer']
    distribution=', '.join(f'{k} lượt: {v} câu' for k,v in sorted(row['search_distribution'].items(),key=lambda x:int(x[0])))
    def rat(field): return rate(m[field]['n'],m[field]['N'])
    return f"| {label} | {rat('tool_use')} | {distribution} | 0/1/2 = {g['0']}/{g['1']}/{g['2']}, N={g['N']}, TB {number(g['mean'])}/2 | {rat('citation_validity')} | {rat('answer_citation_coverage')} | {rat('abstention')} | {rat('false_abstention')} |"


def case_rows(row, label):
    directory=ROOT/row['path'];traces=read(directory/'traces.json')
    reviews={x['query_id']:x for x in read(directory/'reviews.json')}
    rows=[]
    for t in traces:
        q=t['query_id'];review=reviews.get(q);events=[e for e in t.get('events',[]) if e.get('event')=='search']
        kind='Có đáp án' if t['answerable'] else 'Thiếu evidence'
        if review is None:
            rows.append(f"| {label}: {q} | {kind} | Không lưu được context cuối do API error | Không có đáp án | Lỗi {t.get('error_type')}, báo riêng và không gán 0 |")
            continue
        ids=events[-1]['context_ids'] if events else []
        pages=sorted({c['page'] for e in events for c in e['results'] if c['id'] in ids})
        context=f"{len(ids)} chunk, trang {', '.join(map(str,pages))}" if ids else 'context rỗng'
        mark=(f"Trả lời {review['answer_grade']}/2, context {review['context_grade']}/2" if t['answerable']
              else 'Từ chối phù hợp' if review['abstention_correct'] else 'Từ chối không phù hợp')
        rows.append(f"| {label}: {q} | {kind} | {len(events)} search, {context} | {clean(t.get('answer',''))} | {mark}. {clean(review['reason'])} |")
    return rows


def main():
    ledger = read(ROOT/'results/run_ledger.json')
    runs = {r['run_id']:r for r in ledger['runs']}
    selected = {k:runs[v] for k,v in IDS.items()}
    main_runs=[selected[key] for key in MAIN_LABELS]
    main_ids={r['run_id'] for r in main_runs}
    historical=[r for r in ledger['runs'] if r['run_id'] not in main_ids]
    main_totals=totals(main_runs)
    def money(row): return number(float(row['usage_cost']['estimated_usd']),8)+' USD'
    def timing(row): return f"trung vị {number(row['median_ms']/1000,4)} s/câu, tổng {number(row['elapsed_all_seconds'],3)} s, {money(row)}"
    def retriever_row(key, label, method):
        r=selected[key]; s=r['summary']; N=s['metric_denominator']
        return f"| {label} | {method}, top 3, không filter/rerank, budget 2000 ký tự | So sánh cùng câu gốc, corpus A | Dev | {rate(s['hit1'],N)} | {rate(s['hit3'],N)} | {rate(s['context_hit'],N)} | {timing(r)} |"
    retrieval = [retriever_row('dense','Baseline','Dense cosine pgvector'),
                 retriever_row('tfidf','Phương pháp 2','TF-IDF'),
                 retriever_row('hybrid','Phương pháp 3','Hybrid RRF, 10 ứng viên mỗi nhánh, hằng số 60')]
    for key,label,description in [('dev_candidate','Cải thiện 1','Agent dense, budget 4000, tối đa 3 search'),('dev_more','Cải thiện 2','Agent dense, budget 2000, tối đa 5 search')]:
        r=selected[key]; s=selected['dense']['summary']; cer=r['metrics']['context_exact']
        retrieval.append(f"| {label} | {description}, top 3, không filter/rerank | Thử thêm context hoặc thêm lượt, không bảo đảm tăng điểm | Dev | {rate(s['hit1'],15)} câu gốc | {rate(s['hit3'],15)} câu gốc | {rate(cer['n'],cer['N'])} trên câu chạy thành công | {timing(r)}, lỗi {r['errors']}/17 |")
    for key,label in [('test_candidate','Cấu hình đã chọn'),('test_base_repeat','Baseline')]:
        r=selected[key];s=r['summary'];N=s['retrieval_denominator']
        retrieval.append(f"| {label} | Agent dense, budget {r['config']['budget_chars']}, tối đa 3 search, top 3 | Cùng bộ Test, baseline dùng lượt chạy lại do lỗi API | Test | {rate(s['original_hit1'],N)} câu gốc | {rate(s['original_hit3'],N)} câu gốc | {rate(s['agent_context_hit'],N)} exact gold | {timing(r)} |")
    agent_rows=[agent_row(selected[key],MAIN_LABELS[key]) for key in
                ('dev_base','dev_candidate','dev_more','test_base_repeat','test_candidate')]
    query_rows=[]
    for key,label in [('test_base_repeat','B'),('test_candidate','C')]:
        query_rows.extend(case_rows(selected[key],label))

    token_rows=[]
    for key in ('dev_base','dev_candidate','dev_more','test_base_repeat','test_candidate'):
        label=MAIN_LABELS[key]
        r=selected[key];u=r['usage_cost']
        token_rows.append(f"| {label} | {u['input_tokens']} | {u['output_tokens']} | {u['cached_input_tokens']} | {u['cache_write_30m_tokens']} / {u['cache_write_12h_tokens']} | {number(r['elapsed_all_seconds'],3)} | {number(r['median_ms']/1000,4)} | {money(r)} | {r['errors']}/{r['total']} |")

    report = '''# Báo cáo Day 7

Họ và tên: Chu Nguyễn Tùng Dương (ChuNguyenTungDuong)

MSSV: 2A202604016. Lớp: L3B. Ngày thực nghiệm và tổng hợp: 16/11/2026, múi giờ Việt Nam UTC+7.

Repo bài nộp: [K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext](https://github.com/ChuTungDuongg/K5-L3B-DAY07-2A202604016-ChuNguyenTungDuong-RetrievalContext).

Bài thực hành gồm ba phương pháp tìm kiếm là Dense, TF-IDF và Hybrid, cùng ba cấu hình agent dùng Dense. Phần chính trình bày hai split Dev và Test. Các phiên bản dữ liệu cũ, lượt debug và kết quả trước lần chạy lại nằm trong [phụ lục lịch sử](../../docs/EXPERIMENT_HISTORY.md). Nhãn có Codex hỗ trợ đối chiếu, học viên xác nhận sử dụng và chưa có người chấm độc lập.

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
@@RETRIEVAL@@

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
@@AGENT_ROWS@@

  Lỗi được tách khỏi mẫu số chất lượng theo starter. Dev có 2 lỗi ở baseline và 1 lỗi ở mỗi cải thiện, nên điểm câu trả lời dùng N=13 hoặc N=14. Hai cấu hình Test đều có N=5 ở các lượt trong bảng. Baseline Test dùng lượt chạy lại đầy đủ do lượt đầu lỗi API 400 ở 1/7 câu. Lượt đầu và nhãn của sáu câu thành công được giữ trong [phụ lục lịch sử](../../docs/EXPERIMENT_HISTORY.md). Lượt chạy lại giữ cùng cấu hình và được thực hiện vì lỗi API, không chọn dựa vào điểm. Mẫu số khác nhau và lỗi hệ thống hạn chế khả năng so sánh.

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
@@QUERY_ROWS@@

  B là baseline 2000, C là ứng viên 4000. Bảng có 14 dòng, đủ bảy câu cho mỗi cấu hình. Với baseline, câu 387 nhận 1/2 vì nguồn thiếu điều kiện true, câu 397 nhận 0 vì citation chỉ liệt kê thuật ngữ. Context baseline có ba câu mức 2 và hai câu mức 1, ứng viên có bốn câu mức 2 và một câu mức 1. Chi tiết từng chunk và toàn bộ tool call nằm trong trace. Các nhãn có tính diễn giải và chưa được đối chiếu giữa nhiều người chấm.

- Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:

  Phần chính dùng tám lượt đã lưu: ba lượt retrieval Dev, ba lượt agent Dev và hai lượt agent Test. [Danh sách lượt chính và toàn bộ lịch sử](../../docs/RESULTS.md) dẫn tới config, trace, summary và nhãn. File [report_selection.json](../../results/report_selection.json) ghi rõ các lượt dùng trong báo cáo. JSON được ghi sau mỗi câu, nhưng exception giữa vòng agent có thể làm thiếu các event trước lỗi. Khi đó không tự gán context grade 0 cho lần lỗi.

  Thời gian là elapsed theo từng câu, không tính khởi tạo model, tải weights, tạo TF-IDF index hoặc ghi file. Trung vị chỉ xét câu không lỗi. Tổng thời gian là tổng elapsed của tất cả câu, có cả thời gian chờ của câu lỗi, không phải thời gian toàn tiến trình. Test runner tính cả truy xuất câu gốc trước vòng agent, trong khi dev agent runner không có bước đo đó. Một số lượt chạy đồng thời nên độ trễ chịu ảnh hưởng mạng và tranh chấp tài nguyên. Chưa đo RAM, CPU riêng, cold start, tải đồng thời có kiểm soát hoặc độ biến thiên qua nhiều lần lặp cân bằng.

| Lượt | Input token | Output token | Cached input | Cache write 30m / 12h | Tổng elapsed câu (s) | Trung vị câu thành công (s) | Chi phí ước tính | Lỗi / số câu |
|---|---|---|---|---|---|---|---|---|
@@TOKEN_ROWS@@

  Quy ước chi phí dùng USD, giá Standard short-context của `gpt-6-luna` kiểm tra ngày 16/11/2026 trên [trang model OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá](https://developers.openai.com/api/docs/pricing). Mỗi một triệu token: input không cache 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Tất cả request ghi nhận ngắn hơn ngưỡng long-context. Không thêm phí hosted file search hoặc tool OpenAI vì retriever chạy trên PostgreSQL local.

  Công thức là `(input không cache × 0,10 + cached input × 0,01 + cache write 30m × 0,125 + cache write 12h × 0,25 + output × 0,50) / 1.000.000`. Input không cache bằng input tổng trừ cached và cache-write tokens, tránh tính hai lần. Output theo API đã gồm reasoning nếu có, không cộng reasoning lần nữa. Chi phí là ước tính theo các response usage đã lưu, không phải hóa đơn tài khoản, không gồm thuế, phụ phí vùng hoặc cấu hình tier khác chưa ghi nhận.

  Tám lượt dùng trong phần chính có @@MAIN_INPUT@@ input token, @@MAIN_OUTPUT@@ output token và chi phí ghi nhận ước tính @@MAIN_COST@@ USD. Ba lượt retrieval không gọi OpenAI, nên bảng token chỉ có năm lượt agent. Đây là tổng của phần chính. Tổng toàn bộ lịch sử, bao gồm lượt debug và lỗi, được báo riêng trong phụ lục. Request không có usage không được suy là chắc chắn bị tính 0. Chi phí máy, điện và request thiếu log chưa được đo.

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
            'MAIN_INPUT':str(main_totals['input_tokens']), 'MAIN_OUTPUT':str(main_totals['output_tokens']),
            'MAIN_COST':number(Decimal(main_totals['estimated_usd']),8)}
    for key,val in values.items(): report=report.replace('@@'+key+'@@',val)
    target=ROOT/'report/individual/2A202604016_ChuNguyenTungDuong.md'
    target.write_text(report,encoding='utf-8')

    selection={'purpose':'Display selection for the simplified report, not a new evaluation or retuning.',
               'datasets':{'Dev':{'folder':'starter/data/day6-A','answerable':15,'unanswerable':2},
                           'Test':{'folder':'starter/data/test-v2','answerable':5,'unanswerable':2}},
               'main_runs':[{'label':label,'run_id':selected[key]['run_id'],
                             'split':selected[key]['split'].title(),'path':selected[key]['path'],
                             'dataset_version':selected[key]['dataset_version']} for key,label in MAIN_LABELS.items()],
               'historical_run_ids':[r['run_id'] for r in historical],
               'main_usage':main_totals, 'historical_usage':totals(historical), 'all_usage':totals(ledger['runs']),
               'baseline_test_first_attempt':{'run_id':selected['test_base_first']['run_id'],
                                            'errors':selected['test_base_first']['errors'],
                                            'total':selected['test_base_first']['total'],
                                            'note':'Main table uses the complete rerun because the first attempt had an API error, not because its score was compared and preferred.'},
               'chronology_note':'Provisional selection used original dev; corrected dev was evaluated after test. Historical criteria were recorded after partial dev inspection. This presentation change does not establish a new independent test.'}
    (ROOT/'results/report_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    appendix=['# Danh sách lượt chạy và quy ước kết quả Day 7','',
              'Báo cáo chính chỉ dùng hai tên Dev và Test. Tám lượt chính được chỉ rõ dưới đây, còn lịch sử phiên bản và lần đầu lỗi API nằm trong [phụ lục lịch sử](EXPERIMENT_HISTORY.md). Không có lượt API mới phát sinh khi rút gọn báo cáo.','',
              '## Các lượt dùng trong báo cáo chính','',
              '| Nhãn trong báo cáo | Run ID | Dataset kỹ thuật |','|---|---|---|']
    for key,label in MAIN_LABELS.items():
        r=selected[key]
        appendix.append(f"| {label} | [{r['run_id']}](../{r['path']}/summary.json) | {r['dataset_version']} |")
    appendix += ['',f"Tổng phần chính: {main_totals['input_tokens']} input token, {main_totals['output_tokens']} output token, ước tính {number(Decimal(main_totals['estimated_usd']),8)} USD. Ba lượt retrieval không gọi API, năm lượt agent có response usage.",'',
                 '## Toàn bộ lượt đã ghi nhận','',
                 'Bảng này gồm cả tám lượt chính và các lượt lịch sử, không cộng chúng như những lần đánh giá độc lập. Mỗi run ID dẫn tới thư mục config, traces, summary và nhãn nếu đã chấm. Chi phí chỉ cộng response usage ghi nhận, không phải hóa đơn tài khoản.','',
                 '| Run ID | Vai trò | Dataset | Cấu hình | Thành công / tổng, lỗi | Input / output | Tổng s / trung vị s | USD ước tính |','|---|---|---|---|---|---|---|---|']
    for r in ledger['runs']:
        c=r['config'];m=c.get('method',c.get('config','unknown'));budget=c.get('budget_chars');search=c.get('max_searches');u=r['usage_cost']
        med=number(r['median_ms']/1000,4) if r['median_ms'] is not None else 'không có'
        role='Phần chính' if r['run_id'] in main_ids else 'Lịch sử'
        appendix.append(f"| [{r['run_id']}](../{r['path']}/summary.json) | {role} | {r['dataset_version']} | {m}, budget {budget}, search {search} | {r['successful']}/{r['total']}, lỗi {r['errors']} | {u['input_tokens']} / {u['output_tokens']} | {number(r['elapsed_all_seconds'],3)} / {med} | {money(r)} |")
    appendix += ['',f"Tổng recorded usage: {ledger['total_recorded_input_tokens']} input, {ledger['total_recorded_output_tokens']} output, ước tính {number(float(ledger['total_estimated_usd']),8)} USD.",'',
                 'Giá ngày 16/11/2026: input 0,10 USD, cached input 0,01 USD, write 30m 0,125 USD, write 12h 0,25 USD, output 0,50 USD trên một triệu token, theo [OpenAI](https://developers.openai.com/api/docs/models/gpt-6-luna). Công thức chi tiết ở báo cáo và script `scripts/summarize_results.py`. Các lượt local không có phí API, nhưng chi phí CPU/điện chưa đo.','',
                 'Dev-original có 15 dòng có đáp án nhưng 14 câu hỏi khác nhau. Dev-final thay câu lặp bằng data compliance, đủ 15 câu khác nhau. Dev-unversioned là các lượt chẩn đoán ngắn thiếu hash dataset và không có ID giúp phân biệt phiên bản, nên không tự gán vào dev gốc. Test-v1 là bộ trước sửa retry, Test-v2 là bộ tạo sau khi ghi phiên bản. Baseline test-v2 chạy lại giữ riêng với lần đầu. Một số test trước lỗi vẫn chưa chấm tay, vì vậy bảng lịch sử ghi trạng thái và token, không bịa điểm chất lượng.','',
                 'Các lượt dev cuối được chạy để kiểm tra bộ dữ liệu sau loại câu trùng, sau khi test đã hoàn tất. Không dùng chúng để viết lại lịch sử lựa chọn trước test. Việc đóng gói code sau các lượt đo không làm thay đổi các file log đã lưu.','']
    (ROOT/'docs/RESULTS.md').write_text('\n'.join(appendix),encoding='utf-8')

    history=['# Phụ lục lịch sử phát triển và đánh giá','',
             'Phụ lục giữ chi tiết các phiên bản và lượt chạy được lược khỏi báo cáo chính. File dữ liệu, trace và nhãn vẫn ở đường dẫn cũ. Dev/Test trong báo cáo là tên trình bày của hai bộ dữ liệu chính, không phải thay đổi nhãn cho mọi kết quả cũ.','',
             '## Trình tự phát triển','',
             '1. Dev gốc có 15 dòng có đáp án nhưng một cặp trùng câu hỏi data quality, nên chỉ có 14 câu khác nhau. Bản này nằm ở `starter/data/dev-original-archive`. Các lượt so sánh đầu và thử budget/search dùng bản đó. Tiêu chí lựa chọn được ghi sau khi xem một phần dev, như khai báo trong `starter/results/dev-runs/experiment-notes.md`.','',
             '2. Giới hạn output ban đầu 600 đã gây response incomplete. Sau tăng lên 1600, hai lượt dev không lỗi cho baseline 1,73/2 và ứng viên 4000 ký tự 1,87/2. Đây là căn cứ chọn sơ bộ 4000, chưa chứng minh tối ưu hoặc ưu thế ổn định.','',
             '3. Test v1 đã dùng để phát hiện lỗi output và kết nối. Sau sửa retry một lần với 3200 token, các lượt chạy lại v1 là chẩn đoán, không được coi là test độc lập cho bản sửa. Bộ này nằm ở `starter/data/test-v1-archive`.','',
             '4. Phiên bản agent được ghi hash trước khi tạo test v2 tại `starter/results/test-v2-freeze.json`. V2 là bộ Test chính, không dùng để đổi retrieval hoặc chọn lại budget. Baseline lần đầu lỗi API 400 ở câu v2-test-391. Baseline được chạy lại toàn bộ vì lỗi vận hành, giữ cùng cấu hình, cùng bộ câu và nhãn. Cả lần đầu và lần lặp được công bố.','',
             '5. Khi rà soát hồ sơ, dev-auto-373 bị trùng được thay bằng dev-extra-compliance. Bộ Dev chính có đủ 15 câu có đáp án khác nhau. Ba retrieval và ba cấu hình agent đã chạy trên bộ này sau Test, nên các số liệu đó chỉ là kiểm tra bổ sung, không viết lại lịch sử chọn trước Test.','',
             '6. Lần sửa báo cáo này đưa các bảng lịch sử sang phụ lục, không chạy lại model, không sửa benchmark hoặc nhãn và không tạo một bộ test độc lập mới. Cùng trợ lý tham gia soạn câu, triển khai và chấm nhãn nên chưa có đánh giá mù.','',
             '## Các bộ dữ liệu và cách chạy lại','',
             '| Tên lưu trữ | Nội dung và vai trò | Đường dẫn |','|---|---|---|',
             '| Dev gốc | Bộ phát triển trước khi sửa một câu trùng | `starter/data/dev-original-archive/` |',
             '| Dev chính | 15 câu có đáp án khác nhau + 2 thiếu bằng chứng | `starter/data/day6-A/` |',
             '| Test v1 | Bộ cũ đã dùng chẩn đoán sau sửa controller | `starter/data/test-v1-archive/` |',
             '| Test chính, phiên bản v2 | 5 câu có đáp án + 2 thiếu bằng chứng | `starter/data/test-v2/` |','',
             'Lệnh `python run_dev.py --method ...` đọc Dev chính. `python run_test.py --config baseline` hoặc `--config candidate` mặc định đọc Test chính, tương đương thêm `--test-version v2`. Thêm `--test-version v1` chỉ để đối chiếu lịch sử. Mọi lệnh agent đều có thể phát sinh phí và cho phản hồi khác lịch sử. Đọc JSON hoặc build lại báo cáo không gọi API.','',
             '## Metric đã chấm của các lượt lịch sử','',
             'Chỉ liệt kê các lượt ngoài phần chính đã có nhãn. Những lượt khác giữ trạng thái, thời gian và token trong [bảng toàn bộ lượt chạy](RESULTS.md), không tự tạo điểm chất lượng. Mỗi ID dưới đây dẫn tới nhãn và metric gốc.','',
             '| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |',
             '|---|---|---|---|---|---|---|---|']
    for r in historical:
        if (ROOT/r['path']/'agent-metrics.json').exists():
            label=f"[{r['run_id']}](../{r['path']}/agent-metrics.json), {r['dataset_version']}, budget {r['config']['budget_chars']}"
            history.append(agent_row(r,label))
    history += ['', '## Baseline Test lần đầu có lỗi API','',
                'Lượt `20261116-103658-baseline-d7c3d519` có 6/7 câu thành công và 1/7 lỗi API 400. Grounded answer là 1,00/2 trên bốn câu có đáp án thành công, citation hợp lệ 2/3. Lượt đầy đủ dùng trong báo cáo là `20261116-104442-baseline-1fc447dc`, đạt 1,40/2 trên năm câu và citation hợp lệ 5/7. Hai mẫu số khác nhau, không gộp hoặc lấy giá trị tốt nhất theo từng câu.','',
                'Context của lần đầu có ba câu mức 2, một câu mức 1 và một câu không có nhãn do lỗi API. Lượt chạy lại có ba câu mức 2 và hai câu mức 1. Bảng dưới giữ bảy dòng lần đầu, gồm cả lỗi.','',
                '| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |','|---|---|---|---|---|',
                *case_rows(selected['test_base_first'],'B lần đầu'),'',
                '## Phạm vi token và chi phí','',
                f"| Phạm vi | Số lượt | Input token | Output token | USD ước tính |",'|---|---|---|---|---|']
    for label,rows in [('Phần chính',main_runs),('Lịch sử ngoài phần chính',historical),('Toàn bộ ledger',ledger['runs'])]:
        u=totals(rows)
        history.append(f"| {label} | {len(rows)} | {u['input_tokens']} | {u['output_tokens']} | {number(Decimal(u['estimated_usd']),8)} |")
    history += ['',
                'Toàn bộ ledger gồm phần chính và phần lịch sử, không cộng lại ba dòng của bảng. File `results/report_selection.json` ghi rõ phép chia này. Giá và cách tính cached input/cache write giữ nguyên quy ước đã công bố ngày 16/11/2026.','',
                'Các lần soạn câu hỏi có tổng token quan sát trong phiên là 6183 nhưng không giữ đủ breakdown input/output trong artifact, nên không cộng như một chi phí chính xác. Kiểm tra key, debug và demo ngoài ledger cũng không nằm trong tổng trên. Request lỗi thiếu usage không được suy là chắc chắn bị tính 0. Giá trị này là ước tính từ log, không phải hóa đơn tài khoản.','']
    (ROOT/'docs/EXPERIMENT_HISTORY.md').write_text('\n'.join(history),encoding='utf-8')
    print(f'Built main report ({len(main_runs)} runs, {len(query_rows)} test rows), history and selection manifest.')


if __name__ == '__main__': main()
