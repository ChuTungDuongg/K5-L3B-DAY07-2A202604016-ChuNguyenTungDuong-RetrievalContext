"""Build the Vietnamese round-two report and teacher section from saved artifacts."""
import json
import os
from decimal import Decimal
from pathlib import Path

from .analyze import read, usage_total
from .budget import save
from .source import ROOT

RESULTS=ROOT/'advanced/results'
R2=RESULTS/'round2'
LABELS={'table':'Bảng','image':'Ảnh, sơ đồ','chart':'Biểu đồ','multihop':'Multi-hop',
        'text':'Text','unanswerable':'Thiếu bằng chứng'}


def fmt(v,n=2): return f'{v:.{n}f}'.replace('.',',')
def rate(n,d): return f'{n}/{d} ({fmt(n*100/d)}%)' if d else '0/0'
def clean(value): return str(value).replace('|','/').replace('\n',' ')


def main():
    ledger=read(R2/'ledger.json');selection=read(R2/'selection-freeze.json')
    marker=read(R2/'official-test.json')
    if marker['state']!='completed':raise ValueError('Round two official run is incomplete')
    current=[r for r in ledger['runs'] if r.get('round',1)==2]
    tests=[r for r in current if r['split']=='test']
    if len(tests)!=1 or tests[0]['run_id']!=marker['run_id']:raise ValueError('Official Test mismatch')
    test=tests[0];m=test['metrics'];directory=ROOT/test['path']
    cases=read(ROOT/'advanced/benchmark/round2/test.json');traces=read(directory/'traces.json')
    reviews=read(directory/'reviews-proposed.json');case_by={c['id']:c for c in cases};review_by={r['query_id']:r for r in reviews}
    if {r['query_id'] for r in reviews}!={c['id'] for c in cases}:raise ValueError('Test review incomplete')
    events=[read(p) for p in (RESULTS/'api-events').glob('*.json')]
    case_ledger=[]
    for row in ledger['runs']:
        for trace in read(ROOT/row['path']/'traces.json'):
            prefix=row['run_id']+':'+trace['query_id']+':'
            matching=[event for event in events if event['label'].startswith(prefix)]
            case_ledger.append({'run_id':row['run_id'],'round':row.get('round',1),'split':row['split'],
                                'query_id':trace['query_id'],'group':trace['group'],'status':trace['status'],
                                'elapsed_ms':trace['elapsed_ms'],'error':trace.get('error'),
                                'usage_cost':usage_total(matching),'api_event_ids':[e['id'] for e in matching]})
    save(R2/'case-ledger.json',case_ledger)
    group_rows=['| Nhóm test | Đạt / tổng | Tỷ lệ | Lỗi / nhận xét |','|---|---|---|---|']
    for key,name in LABELS.items():
        group=m['groups'][key]
        group_rows.append(f"| {name} | {group['passed']}/{group['total']} | {fmt(100*group['passed']/group['total'])}% | {group['errors']} lỗi hệ thống, {group['total']-group['passed']} câu không đạt |")
    group_rows.append(f"| **Toàn bộ** | **{m['passed']}/{m['total']}** | **{fmt(100*m['rate'])}%** | {m['errors']} lỗi hệ thống, {m['total']-m['passed']} câu không đạt |")
    groups='\n'.join(group_rows)
    run_rows=['| Vòng / lượt | Đạt / tổng | Input / output | Cached / write 30m / write 12h | Tổng s / trung vị s | Ước tính USD | Lỗi |','|---|---|---|---|---|---|---|']
    for row in ledger['runs']:
        a=row['usage_cost'];metric=row['metrics']
        link=Path(os.path.relpath(ROOT/row['path']/'config.json',R2)).as_posix()
        run_rows.append(f"| [{row.get('round',1)} / {row['split']} {row['config_name']}]({link}) | {rate(metric['passed'],metric['total'])} | {a['input_tokens']} / {a['output_tokens']} | {a['cached_input_tokens']} / {a['cache_write_30m_tokens']} / {a['cache_write_12h_tokens']} | {fmt(row['elapsed_all_seconds'],3)} / {fmt(row['median_ms']/1000,3)} | {fmt(Decimal(a['estimated_usd']),8)} | {metric['errors']} |")
    run_table='\n'.join(run_rows)
    per_case=['# Đối chiếu từng câu Test vòng hai','',
              'Nhãn là đề xuất có trợ lý đối chiếu ảnh PDF gốc, chưa được học viên xác nhận. Vùng nguyên trang kèm nhãn và trích dẫn chỉ giúp định vị, không tự chứng minh câu trả lời đúng.','',
              '| ID / nhóm | Câu hỏi | Đáp án hệ thống | Citation | Nhãn và lý do |','|---|---|---|---|---|']
    trace_by={t['query_id']:t for t in traces}
    for case in cases:
        t=trace_by.get(case['id'],{});r=review_by[case['id']]
        citations=' / '.join(f"p{c['page']} {c['region_label']} {c['bbox']}" for c in t.get('citations',[])) or 'Không có'
        per_case.append(f"| {case['id']} / {LABELS[case['group']]} | {clean(case['question'])} | {clean(t.get('answer',t.get('error','Thiếu kết quả')))} | {clean(citations)} | {'Đạt' if r['passed'] else 'Không đạt'}: {clean(r['reason'])} |")
    (R2/'TEST_REVIEW.md').write_text('\n'.join(per_case)+'\n',encoding='utf-8')
    explanations={'adv-r2-test-12':'Công cụ tính toán báo `SyntaxError: invalid syntax` vì biểu thức chứa cả câu và đơn vị. Không có đầu ra hợp lệ để chấm phép tính.',
                  'adv-r2-test-19':'Câu trả lời thiếu cơ chế hiện diện trong dữ liệu được hỏi. Trang 130 nêu người ít tiếp cận điện thoại, internet hoặc tài khoản ngân hàng có thể ít hiện diện trong dữ liệu. Các nguồn được dẫn không bù phần thiếu.'}
    failures='\n'.join(f"- {r['query_id']}: {explanations.get(r['query_id'],r['reason'].replace(';', '.'))}" for r in reviews if not r['passed']) or 'Không có câu không đạt theo nhãn đề xuất.'
    total=ledger['total'];money=fmt(Decimal(total['estimated_usd']),8)
    threshold='đạt ngưỡng số học' if m['score_threshold_met'] else 'chưa đạt ngưỡng số học'
    confirmed='đã được học viên xác nhận' if m['labels_confirmed'] else 'chưa được học viên xác nhận'
    text=f'''# Báo cáo nâng cao: vòng thực nghiệm thứ hai

Chu Nguyễn Tùng Dương (ChuNguyenTungDuong), MSSV 2A202604016, lớp L3B. Thực nghiệm tại múi giờ Việt Nam UTC+7.

Test vòng hai đạt **{rate(m['passed'],m['total'])}**, {threshold} 27/30 theo nhãn đề xuất. Nhãn {confirmed}. Kết quả không tự động xác nhận đủ điều kiện nhận bonus, vì còn yêu cầu về nguồn, index và kiểm tra của giảng viên.

Vòng trước đạt 26/30 và đã được dùng để xác định lỗi calculator, đọc sai số liệu và citation thiếu vùng. Vì pipeline sau đó đã thay đổi, kết quả vòng trước chỉ dùng chẩn đoán cho phiên bản mới. [Báo cáo vòng một](../../ROUND1_REPORT.md) giữ chi tiết nguồn 350 trang, 5493 chunk, 114 vùng trực quan và các lượt cũ. [Hướng dẫn vòng hai](../../ROUND2.md) giải thích chia phiên bản và các giới hạn.

## Pipeline và cách chọn

Cùng index, dữ liệu và model `gpt-6-luna` được dùng lại. Agent hỗ trợ phép tính `÷`, `×`, `−` và gọi thêm model để kiểm lại đề xuất trả lời trên ảnh PDF gốc. Model có thể sửa hoặc từ chối nếu nguồn không đủ. Đây là bước tự kiểm, không bảo đảm tính đúng và không thay việc đối chiếu độc lập. Bbox citation cuối bao toàn trang, kèm tên vùng và trích dẫn cụ thể. Bbox model đề xuất được lưu riêng trong `model_bbox`. Vùng nguyên trang kém chính xác hơn crop, nhưng người chấm vẫn phải kiểm tra nó thực sự chứa bằng chứng hỗ trợ mọi khẳng định.

Dev gồm 15 câu có đáp án và ba câu thiếu evidence, giữ nguyên bộ đã dùng. Test mới gồm 24 câu có đáp án và sáu câu thiếu evidence, theo sáu nhóm ở bảng dưới. Bộ Test mới được soạn và đóng băng trước các lượt Dev vòng hai, không hỏi lại cùng fact với Dev hoặc Test trước theo kiểm tra của người soạn. Trợ lý soạn Test mới cũng đã chấm Test cũ và biết các loại lỗi trước đó, nên không phải đánh giá mù giữa những người độc lập. Không có bằng chứng đủ để khẳng định hai bộ có độ khó tương đương chỉ dựa vào số lượng câu.

Cả hai cấu hình dùng cùng model và retrieval, khác số trang ảnh và số bước. Cấu hình được chọn là **{selection['config_name']}**, dựa trên số câu Dev đạt, rồi trung vị thời gian và chi phí khi hòa. [Kế hoạch và hash](dev-experiment-plan.json) được ghi trước Dev, [selection freeze](selection-freeze.json) chốt trước Test. Model chỉ nhận câu hỏi và evidence được truy xuất, không nhận đáp án chuẩn, nhãn hay bbox gold.

{run_table}

Các thời gian là tổng elapsed từng câu và trung vị của các câu đã chạy, gồm retrieval và các request model, không gồm tải model, tạo index hay khởi tạo process. Các lượt Dev có thể chạy đồng thời, chịu ảnh hưởng mạng và tranh chấp tài nguyên. Một lượt mỗi cấu hình không chứng minh ưu thế thống kê.

## Test và nhãn theo từng nhóm

{groups}

Tỷ lệ là số câu đạt chia toàn bộ 30 câu. Sai đơn vị, đối tượng đo, điều kiện, phép tính hoặc citation đều không đạt. Lỗi API, lỗi công cụ, timeout và thiếu kết quả không bị loại khỏi mẫu số. Số lỗi là {m['errors']}, số kết quả thiếu là {m['missing_results']}, số chưa chấm là {m['unreviewed']}.

[Bảng 30 câu](TEST_REVIEW.md) ghi câu hỏi, đáp án, citation và lý do từng nhãn, còn JSON review ghi kiểm tra nguồn gốc. Các câu không đạt:

{failures}

## Token và chi phí

Toàn bộ phần nâng cao qua cả hai vòng gồm **{total['input_tokens']} input token**, **{total['output_tokens']} output token**, ước tính **{money} USD** theo usage đã ghi, trong trần 5 USD. Dự phòng cho usage chưa rõ là {fmt(Decimal(ledger['unknown_reserved_usd']),8)} USD. Bảng trên giữ từng lượt Dev/Test, còn index được ghi riêng ở [ledger](ledger.json). Không cộng dòng tổng với các dòng thành phần. [Ledger từng câu](case-ledger.json) liên kết API event và lỗi.

Giá `gpt-6-luna` Standard short-context kiểm tra 16/11/2026: input 0,10, cached input 0,01, cache write 30 phút 0,125, cache write 12 giờ 0,25 và output 0,50 USD trên một triệu token. Output đã bao gồm reasoning. Chi phí là ước tính response usage, không phải hóa đơn, chưa gồm chi phí local, thuế, tier khác hoặc token trợ lý soạn bài ngoài pipeline. Mỗi request sinh có một request đếm input riêng. Giá và model alias có thể thay đổi.

## Tái lập và giới hạn

Tải PDF đúng hash và khôi phục ảnh/vector theo [README](../../README.md), sau đó chạy `python -m advanced.analyze --round 2` và `python -m advanced.verify --round 2` để đối chiếu các artifact không gọi API. Việc chạy lại model phát sinh phí, có thể khác phản hồi lịch sử và không thay lượt Test chính thức. File `official-test.json` ghi lượt chính thức của từng vòng. Xem `advanced/benchmark/round2`, `advanced/results/round2` và các hash để kiểm tra thứ tự chốt.

Thực nghiệm chỉ dùng một tài liệu tiếng Anh, một lượt Test vòng hai và một model. Không có ablation chỉ-text, đánh giá mù giữa nhiều người hoặc bảo đảm quy tắc phát hiện hình bao phủ mọi hình vector không nhãn. Chất lượng mô tả vision, thứ tự text, cửa sổ embedding 128 token và bbox toàn trang là các giới hạn. Các câu có tên hình hoặc bảng cụ thể có thể dễ truy xuất hơn câu hỏi mở. {confirmed.capitalize()} là trạng thái nhãn của bộ nâng cao, khác xác nhận trước đây đối với phần cơ bản.
'''
    (R2/'REPORT.md').write_text(text,encoding='utf-8')
    section=f'''## Thử thách nâng cao (nếu thực hiện)

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản:

  World Bank, [World Development Report 2021: Data for Better Lives](https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf), 350 trang PDF, SHA-256 `606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616`, CC BY 3.0 IGO kèm điều kiện thành phần bên thứ ba. Thông tin ghi công và giới hạn quyền trong [báo cáo vòng một](../../advanced/ROUND1_REPORT.md).

- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý:

  Xử lý 350 trang và lưu ảnh gốc có checksum. Index gồm 4995 chunk native text và 498 chunk mô tả 114 vùng trực quan, tổng 5493 chunk. Vision phân tích 107 trang chọn theo caption hoặc ảnh raster. Mười bốn trang trống và một trang nhan đề không có native text. Hình trang trí không mô tả riêng, quy tắc chọn trang có thể bỏ sót hình vector không nhãn. Agent xem ảnh gốc, dùng mô tả chỉ làm tín hiệu tìm kiếm.

- Cách chia benchmark, schema evidence, model và cấu hình đã chốt trên dev:

  Dev vòng hai có 15 câu có đáp án và ba câu thiếu evidence. Test mới có 24 câu có đáp án và sáu câu thiếu evidence. Câu lưu ID, nhóm, đáp án hoặc lý do thiếu evidence, trang, vùng và điều kiện. Hai split được kiểm tra không trùng fact và khóa trước Dev vòng hai. Test vòng một sau khi dùng để sửa pipeline được giữ làm chẩn đoán. Trợ lý soạn Test mới cũng đã chấm Test cũ nên chưa có đánh giá mù giữa những người độc lập.

  Pipeline dùng TF-IDF theo trang kết hợp dense pgvector bằng RRF, embedding 384 chiều và model `gpt-6-luna`. Agent có search, inspect, calculate và thêm lượt tự kiểm câu trả lời bằng ảnh gốc. Citation dùng bbox nguyên trang kèm nhãn vùng/trích dẫn, lưu thêm bbox model đề xuất. Chọn **{selection['config_name']}** theo điểm Dev nghiêm, rồi thời gian và chi phí khi hòa. Gold không được đưa vào model khi inference. Chi tiết trong [báo cáo vòng hai](../../advanced/results/round2/REPORT.md).

{groups}

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống:

  Test vòng hai đạt **{rate(m['passed'],m['total'])}**, {threshold} 27/30. Nhãn {confirmed}. Lỗi và thiếu kết quả giữ trong mẫu số. [Bảng 30 câu](../../advanced/results/round2/TEST_REVIEW.md) và trace lưu lý do, nguồn và công cụ. [Bảng mọi lượt, token, thời gian và chi phí](../../advanced/results/round2/REPORT.md) giữ cả vòng chẩn đoán.

  Tổng phần nâng cao qua hai vòng là {total['input_tokens']} input token, {total['output_tokens']} output token và **{money} USD ước tính** trên trần 5 USD. Dự phòng usage chưa rõ là {fmt(Decimal(ledger['unknown_reserved_usd']),8)} USD. Đây là phép tính theo response usage và giá công khai, không phải hóa đơn. Reasoning nằm trong output, chi phí local và token trợ lý ngoài pipeline chưa đo.

- Giới hạn, cách tái lập và đường dẫn benchmark:

  [Hướng dẫn nâng cao](../../advanced/README.md), [vòng hai](../../advanced/ROUND2.md), [benchmark](../../advanced/benchmark/round2/test.json), [selection](../../advanced/results/round2/selection-freeze.json) và [ledger](../../advanced/results/round2/ledger.json) cho phép đối chiếu. Chỉ có một tài liệu, một lượt Test vòng hai, không có ablation chỉ-text hoặc đánh giá mù giữa nhiều người. Bbox nguyên trang có độ chính xác định vị thấp. Model alias và mạng có thể làm chạy lại khác lịch sử. Việc nhận bonus phụ thuộc kiểm tra đủ yêu cầu của giảng viên.
'''
    (RESULTS/'report-section.md').write_text(section,encoding='utf-8')
    print('Built round-two report, 30-case review table, per-case cost ledger and teacher section.')


if __name__=='__main__':main()
