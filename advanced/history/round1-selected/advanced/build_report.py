"""Vietnamese report tables derived from saved runs and source reviews."""
from decimal import Decimal

from .analyze import RESULTS, read, usage_total
from .budget import save
from .source import ROOT

GROUPS={'table':'Bảng','image':'Ảnh, sơ đồ','chart':'Biểu đồ','multihop':'Multi-hop',
        'text':'Text','unanswerable':'Thiếu bằng chứng'}


def num(v,d=3):return f'{v:.{d}f}'.replace('.',',')
def rate(n,N):return f'{n}/{N} ({num(100*n/N,2)}%)'
def clean(v):return str(v).replace('|','/').replace('\n',' ')


def main():
    ledger=read(RESULTS/'ledger.json');selection=read(RESULTS/'selection-freeze.json')
    test=[r for r in ledger['runs'] if r['split']=='test']
    if len(test)!=1:raise ValueError('Build report from one official Test run')
    test=test[0];m=test['metrics'];u=ledger['total']
    chosen={r['run_id'] for r in selection['dev_evidence']}
    dev=[r for r in ledger['runs'] if r['run_id'] in chosen]
    history=[r for r in ledger['runs'] if r['split']=='dev' and r['run_id'] not in chosen]
    def run_table(rows):
        lines=['| Lượt | Đạt / tổng | Input / output token | Cached / write 30m / write 12h | Tổng s / trung vị s | USD ước tính | Lỗi |',
               '|---|---|---|---|---|---|---|']
        for r in rows:
            a=r['usage_cost'];q=r['metrics']
            lines.append(f"| [{r['split'].title()} {r['config_name']}](results/runs/{r['run_id']}/config.json) | {rate(q['passed'],q['total'])} | {a['input_tokens']} / {a['output_tokens']} | {a['cached_input_tokens']} / {a['cache_write_30m_tokens']} / {a['cache_write_12h_tokens']} | {num(r['elapsed_all_seconds'])} / {num(r['median_ms']/1000)} | {num(Decimal(a['estimated_usd']),8)} | {q['errors']}/{q['total']} |")
        return '\n'.join(lines)
    group_rows=['| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |','|---|---|---|---|']
    for group,label in GROUPS.items():
        g=m['groups'][group]
        group_rows.append(f"| {label} | {g['passed']}/{g['total']} | {num(100*g['passed']/g['total'],2)}% | {g['errors']} lỗi hệ thống, {g['total']-g['passed']} câu không đạt |")
    group_rows.append(f"| **Toàn bộ** | **{m['passed']}/{m['total']}** | **{num(100*m['rate'],2)}%** | {m['errors']} lỗi hệ thống, {m['missing_results']} thiếu kết quả, {m['unreviewed']} chưa chấm |")
    threshold=('đạt ngưỡng số học 27/30' if m['score_threshold_met'] else 'chưa đạt ngưỡng số học 27/30')
    status=('Nhãn đã có xác nhận của học viên theo artifact xác nhận.' if m['labels_confirmed'] else
            'Nhãn đang là đề xuất có trợ lý hỗ trợ đối chiếu PDF gốc, chưa có xác nhận riêng của học viên cho phần nâng cao và chưa có người chấm độc lập.')
    costs=['| Giai đoạn | Request sinh / có usage | Input / output | USD ước tính |','|---|---|---|---|']
    for label,a in [('Mô tả trang để index',ledger['index']),*[(f"{r['split'].title()} {r['config_name']} {r['run_id']}",r['usage_cost']) for r in ledger['runs']],('Toàn bộ phần nâng cao',u)]:
        costs.append(f"| {label} | {a['generation_requests']} / {a['responses_with_usage']} | {a['input_tokens']} / {a['output_tokens']} | {num(Decimal(a['estimated_usd']),8)} |")
    directory=ROOT/test['path'];traces=read(directory/'traces.json');reviews=read(directory/'reviews-proposed.json')
    by_id={r['query_id']:r for r in reviews}
    cases=read(ROOT/'advanced/benchmark/test.json');case_by_id={c['id']:c for c in cases}
    failure_summary='\n'.join(f"- {r['query_id']}: {r['reason']}" for r in reviews if not r['passed']) or 'Không có câu không đạt trong lượt quan sát.'
    api_events=[read(p) for p in (RESULTS/'api-events').glob('*.json')]
    case_ledger=[]
    for run in ledger['runs']:
        for trace in read(ROOT/run['path']/'traces.json'):
            prefix=run['run_id']+':'+trace['query_id']+':'
            requests=[e for e in api_events if e['label'].startswith(prefix)]
            case_ledger.append({'run_id':run['run_id'],'query_id':trace['query_id'],'split':run['split'],
                                'group':trace['group'],'status':trace['status'],'elapsed_ms':trace['elapsed_ms'],
                                'usage_cost':usage_total(requests),'api_event_ids':[e['id'] for e in requests],
                                'error_type':trace.get('error_type'),'error':trace.get('error')})
    save(RESULTS/'case-ledger.json',case_ledger)
    per_case=['# Đối chiếu từng câu Test nâng cao','',status,'',
              'Chấm đạt hoặc không đạt trên toàn bộ 30 câu, đối chiếu ảnh PDF gốc. Vùng bbox dùng tọa độ chuẩn hóa theo góc trên trái. Gold và review không được đưa vào inference. Xem JSON review để kiểm tra chi tiết từng citation.','',
              '| ID / nhóm | Câu hỏi | Câu trả lời hệ thống | Trang và vùng citation | Nhãn và lý do |','|---|---|---|---|---|']
    for t in traces:
        r=by_id[t['query_id']];citations=' / '.join(f"p{c['page']}: {c['region_label']} {c['bbox']}" for c in t.get('citations',[])) or 'Không có'
        per_case.append(f"| {t['query_id']} / {GROUPS[case_by_id[t['query_id']]['group']]} | {clean(t['question'])} | {clean(t.get('answer',t.get('error','')))} | {clean(citations)} | {'Đạt' if r['passed'] else 'Không đạt'}. {clean(r['reason'])} |")
    (RESULTS/'TEST_REVIEW.md').write_text('\n'.join(per_case)+'\n',encoding='utf-8')
    text=f'''# Báo cáo bổ sung phần nâng cao

Chu Nguyễn Tùng Dương (ChuNguyenTungDuong), MSSV 2A202604016, lớp L3B. Thực nghiệm ngày 16/11/2026 theo UTC+7.

Kết quả Test là **{rate(m['passed'],m['total'])}**, {threshold}. {status} Điểm bonus do giảng viên quyết định sau khi kiểm tra đầy đủ yêu cầu, không suy ra tự động từ tỷ lệ.

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

{run_table(dev+[test])}

Cấu hình chốt là **{selection['config_name']}**, theo [selection-freeze.json](results/selection-freeze.json). Lựa chọn, code, index, ảnh và benchmark đã khóa trước Test. Chỉ chạy một lượt chính thức trên cả 30 câu, không chọn lại đáp án theo từng câu. Hai cấu hình Dev chạy đồng thời nên thời gian có thể chịu tranh chấp tài nguyên. Không coi chênh lệch một lượt là ưu thế thống kê.

## Chấm Test nghiêm và phân tích lỗi

{chr(10).join(group_rows)}

Tỷ lệ bằng số đạt chia toàn bộ 30 câu và không làm tròn để vượt ngưỡng. Câu trả lời đúng một phần, sai đối tượng đo, sai đơn vị, thiếu điều kiện, sai vùng citation hoặc từ chối câu có đáp án đều không đạt. Lỗi hệ thống và thiếu kết quả cũng nằm trong mẫu số. Các tỷ lệ này khác thang 0/1/2 ở phần cơ bản và không cộng hai bộ điểm với nhau.

[Bảng đối chiếu đủ 30 câu](results/TEST_REVIEW.md) ghi câu hỏi, câu trả lời, citation và lý do từng nhãn. JSON trong thư mục run lưu source_check, trace và toàn bộ thông tin chấm. Lỗi quan sát phải được giữ trong kết quả Test, không sửa code hoặc chạy lại để thay điểm của lượt chính thức.

Các câu Test không đạt trong lượt chính thức:

{failure_summary}

## Token, thời gian và chi phí

{chr(10).join(costs)}

Tổng riêng phần nâng cao là **{u['input_tokens']} input token, {u['output_tokens']} output token và {num(Decimal(u['estimated_usd']),8)} USD ước tính**. Trần học viên chọn là 5 USD. Khoản dự phòng thiếu usage hiện là {num(Decimal(ledger['unknown_reserved_usd']),8)} USD. Tổng này gồm mô tả để index, cả Dev chẩn đoán và Dev cuối, cùng Test. Không cộng lại dòng tổng với các dòng thành phần và không gộp chi phí phần cơ bản vào đây.

[Ledger từng câu](results/case-ledger.json) giữ thời gian, token, chi phí, lỗi và danh sách API event cho mọi câu Dev/Test, kể cả câu lỗi calculator sau khi API đã trả usage.

Giá Standard short-context được kiểm tra ngày 16/11/2026 trên [trang model](https://developers.openai.com/api/docs/models/gpt-6-luna) và [bảng giá OpenAI](https://developers.openai.com/api/docs/pricing). Trên một triệu token, input không cache là 0,10 USD, cached input 0,01 USD, cache write 30 phút 0,125 USD, cache write 12 giờ 0,25 USD và output 0,50 USD. Công thức là `(uncached*0.10 + cached*0.01 + write30m*0.125 + write12h*0.25 + output*0.50)/1_000_000`. Uncached bằng input trừ cached và cache write để tránh cộng hai lần. Output đã gồm reasoning, không cộng reasoning riêng. Token ảnh nằm trong input usage của API.

Trước mỗi request sinh nội dung có một request đếm token cùng input và một khoản giữ chỗ thận trọng. Có {u['token_count_requests']} request đếm được ghi nhận đi kèm các request sinh, được báo riêng chứ không coi là response sinh nội dung. Không xác nhận hóa đơn hoặc suy chi phí không ghi nhận là bằng không. Tổng không gồm chi phí máy local, điện, thuế, phụ phí tier/vùng hoặc token trợ lý dùng khi soạn code và nhãn ngoài các API event của pipeline.

Thời gian theo câu bao gồm retrieve, đếm token, gọi model và xử lý công cụ. Tổng là cộng elapsed của các câu, không phải wall time toàn quy trình. Trung vị xét tất cả kết quả đã chạy. Không tính khởi tạo embedding, kiểm hash toàn index, tải model hoặc ghi JSON ngoài vòng đo. API event có elapsed gồm đếm token và sinh nội dung. Index vision chạy ba worker nên tổng elapsed của các request chồng lấn, không dùng tổng đó như wall time. Tổng wall time trích xuất và embedding chưa được lưu bằng đồng hồ của pipeline, nên không bổ sung số suy đoán.

## Lượt Dev chẩn đoán được giữ để kiểm tra lịch sử

{run_table(history)}

Các lượt này giữ nguyên trace và nhãn, không trộn với cặp Dev cuối khi chọn cấu hình. Sai vùng citation và sai đối tượng đo trong Dev minh họa rằng nhận đúng con số hoặc có citation đúng trang chưa đủ để được chấm đạt.

Ba file code đã đổi giữa hai cặp Dev được lưu tại `advanced/history/pipeline-v1`, khôi phục từ các thay đổi đã biết và kiểm tra khớp từng byte với hash ghi trước lượt Dev đầu. Những file runtime còn lại giữ cùng hash. Bản lưu này phục vụ kiểm tra lịch sử, không thay pipeline đã chốt cho Test.

## Tái lập và giới hạn

[README nâng cao](README.md) hướng dẫn tải đúng PDF, cài dependency đã khóa, khởi động database, khôi phục vector snapshot và 350 ảnh, kiểm tra artifact rồi xem lại nhãn mà không gọi model. `python -m advanced.analyze`, `python -m advanced.build_report` và `python -m advanced.verify` chỉ đọc kết quả đã lưu. `python -m advanced.restore --check-only` đối chiếu dữ liệu live với snapshot. Lệnh chạy Dev/Test gọi OpenAI thật và có thể phát sinh chi phí. Model alias, độ ngẫu nhiên, mạng và môi trường phần cứng có thể làm kết quả chạy lại khác lịch sử dù hash source/index giống nhau.

Chỉ có một tài liệu tiếng Anh và một lượt Test, chưa đánh giá nhiều tài liệu, dữ liệu tiếng Việt hoặc độ ổn định qua nhiều seed. Mô tả hình có thể sai và model embedding có cửa sổ 128 token, nên chuỗi dài có thể bị cắt. Benchmark có locator hoặc tên nội dung khá cụ thể và chưa đại diện hoàn toàn cho câu hỏi mở không biết vị trí. Bbox nguyên trang có thể đủ định vị khi kèm tên vùng và quote nhưng kém chính xác hơn crop sát đối tượng. Chưa đo tác dụng riêng của vision bằng một ablation chỉ-text, vì hai cấu hình đều dùng vision. Kết quả không chứng minh mọi câu trong các nhóm hình bắt buộc phải nhìn ảnh mới trả lời được. Hệ thống chưa có kiểm thử an toàn prompt injection chuyên biệt.

{status} Khi chưa hoàn tất xác nhận và kiểm tra yêu cầu, chỉ báo tỷ lệ đề xuất và trạng thái {threshold}, không tự cộng 15 điểm.
'''
    (ROOT/'advanced/REPORT.md').write_text(text,encoding='utf-8')
    section=f'''## Thử thách nâng cao (nếu thực hiện)

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:

  Thực hiện riêng trên World Bank, World Development Report 2021: Data for Better Lives, bản PDF 350 trang vật lý. Nguồn, SHA-256, giấy phép CC BY 3.0 IGO và điều kiện thành phần bên thứ ba được ghi trong [báo cáo nâng cao](../../advanced/REPORT.md). Tài liệu, benchmark và index này tách khỏi phần cơ bản.

- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:

  Cả 350 trang được xử lý và giữ ảnh gốc có hash, tạo 4995 chunk native text và 498 chunk mô tả trực quan, tổng 5493. Vision xử lý 107 trang theo caption hoặc ảnh raster, tạo 114 vùng, không có request mô tả lỗi. Agent xem ảnh PDF gốc để kiểm tra bảng, sơ đồ và biểu đồ. Mô tả chỉ phục vụ retrieval. Mười bốn trang trống và một bìa minh họa không có native text. Hình trang trí không mô tả riêng, quy tắc chọn trang có thể bỏ sót hình không nhãn. Chi tiết coverage và các vùng kiểm tra thủ công ở hồ sơ nâng cao.

- Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:

  Dev có 18 câu gồm 15 có đáp án và ba thiếu bằng chứng. Test có 30 câu gồm 24 có đáp án và sáu thiếu bằng chứng. Benchmark khóa trước Dev. Câu hỏi có ID, nhóm, đáp án, evidence trang/vùng, đơn vị, phép tính hoặc cách kiểm tra thiếu bằng chứng. Cấu hình **{selection['config_name']}** được chốt trên cặp Dev cuối trước Test bằng số câu đạt, rồi thời gian và chi phí khi hòa. Hai lượt Dev đầu chỉ là chẩn đoán và được giữ nguyên. Inference không nhận gold.

  Pipeline dùng TF-IDF theo trang kết hợp dense pgvector 384 chiều bằng RRF. Embedding và model `gpt-6-luna` dùng cùng phiên bản đã công bố. Agent có công cụ search, inspect ảnh gốc và calculate, bắt buộc citation về trang và vùng đã xem. [Cấu hình và hash đã chốt](../../advanced/results/selection-freeze.json) giữ chi tiết baseline/candidate, giới hạn bước, ảnh và các file code/index.

{chr(10).join(group_rows)}

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:

  Test đạt **{rate(m['passed'],m['total'])}**, {threshold}. {status} Mẫu số giữ cả lỗi API, timeout và thiếu kết quả. Không chấm một phần như thang 0/1/2 của phần cơ bản. [Bảng 30 câu](../../advanced/results/TEST_REVIEW.md) dẫn tới trace, nhãn và kiểm tra vùng gốc. [Bảng Dev, thử nghiệm, token, thời gian và chi phí](../../advanced/REPORT.md) công bố cả lượt chẩn đoán.

  Chi phí riêng phần nâng cao ghi nhận **{num(Decimal(u['estimated_usd']),8)} USD ước tính**, gồm index, bốn lượt Dev và một lượt Test, với {u['input_tokens']} input và {u['output_tokens']} output token. Trần là 5 USD, dự phòng thiếu usage {num(Decimal(ledger['unknown_reserved_usd']),8)} USD. Đây là ước tính từ response usage theo giá công khai, không phải hóa đơn tài khoản. Quy ước cached input, cache write và reasoning giữ như phần cơ bản. Chi phí local và token trợ lý soạn bài ngoài pipeline chưa đo.

- Giới hạn, cách tái lập và đường dẫn benchmark:

  [Hướng dẫn nâng cao](../../advanced/README.md) có lệnh khôi phục snapshot vector và ảnh gốc mà không gọi API, kiểm hash, đọc lại metric và chạy model thật khi cần. [Dev](../../advanced/benchmark/dev.json), [Test](../../advanced/benchmark/test.json), [freeze benchmark](../../advanced/benchmark/freeze.json) và [ledger](../../advanced/results/ledger.json) đủ để kiểm tra lại phép tính. Chỉ có một tài liệu và một lượt Test, model alias và phản hồi API có thể thay đổi. Chưa có ablation chỉ-text, đánh giá nhiều người hoặc bảo đảm mọi hình không nhãn đều được mô tả. Không tự cộng điểm bonus khi chưa kiểm tra đủ điều kiện.
'''
    (RESULTS/'report-section.md').write_text(section,encoding='utf-8')
    print('Built advanced report, teacher section and full Test review table.')


if __name__=='__main__':main()
