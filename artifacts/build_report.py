"""Build submission report from actual final artifacts; no synthetic metrics."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'results/final'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))


def ratio(value):
    n, total = value['n'], value['N']
    return f'{n}/{total} ({100*n/total:.1f}%)' if total else '0/0 (N/A)'


def main():
    selection = load(RUN / 'selection.json')
    runtime = load(RUN / 'runtime.json')
    retrieval_rows, agent_rows, totals = [], [], []
    for split in ['dev', 'test']:
        summaries = load(RUN / split / 'summaries.json')
        for name, s in summaries.items():
            retrieval_rows.append(f"| {name} | {split} | {ratio(s['hit1'])} | {ratio(s['hit3'])} | {ratio(s['context_evidence_rate'])} | {s['median_ms']:.2f} |")
            a = load(RUN / split / name / 'agent_summary.json')
            ts = load(RUN / split / name / 'agent.json')
            g = a['grounded_answer']
            latency = statistics.median(t['elapsed_ms'] for t in ts)
            cost = a['service_cost_usd']
            cost_text = f'{cost:.6f}' if cost is not None else f"≥{a['known_service_cost_usd']:.6f} (thiếu usage lượt lỗi)"
            agent_rows.append(f"| {name}/{split} | {ratio(a['tool_use'])} | {g['0']}/{g['1']}/{g['2']} | {g['mean']:.3f}/2 | {ratio(a['citation_validity'])} | {ratio(a['abstention'])} | {ratio(a['false_abstention'])} | {a['provider_errors']} | {latency:.0f} | {cost_text} |")
            totals.append(a['known_service_cost_usd'])
    context_reviews = load(RUN / 'test/context_reviews.json')
    context_rows = []
    for name in ['tfidf-base', 'hybrid-context']:
        rows = [r for r in context_reviews if r['config'] == name]
        counts = [sum(r['context_grade'] == grade for r in rows) for grade in range(3)]
        context_rows.append(f"| {name} | {counts[0]}/{counts[1]}/{counts[2]} | {sum(r['context_grade'] for r in rows)/len(rows):.2f}/2 |")
    test_rows = []
    for name in ['tfidf-base', 'hybrid-context']:
        ts = {t['query_id']: t for t in load(RUN / 'test' / name / 'agent.json')}
        for r in load(RUN / 'test' / name / 'reviews.json'):
            t = ts[r['query_id']]
            grade = r.get('answer_grade', 'từ chối đúng' if r.get('abstention_correct') else 'chưa đạt')
            test_rows.append(f"| {name} | {r['query_id']} | {t['status']} | {grade} | {r['reason']} |")
    report = f'''# Báo cáo Day07 — Agentic RAG

**Trịnh Hưng Thịnh · MSSV 2A202603907 · L3B**

## Dữ liệu và kết nối Day06

Tích hợp repo [Day06 của học viên](https://github.com/TrnhThnh/K5-L3B-Day06-2A202603907-DataIngestionEngineering),
commit `bf21bc0b5d7ab8a7ae4902c0905da5dfabd3469c`. Giữ nguyên module chunking,
embedding, model dữ liệu và store ở [vendor](../../vendor/README.md).

Corpus: World Bank (2026), *Cybersecurity in Ports: Shifting from Risk to Resilience*.
Nguồn và quyền tái sử dụng phi thương mại có ghi công trong
[manifest](../../data/day06/manifest.json). PDF có 107 trang vật lý; sử dụng 80
trang nội dung, trang 12–16 và 19–93. Dữ liệu text/metadata đã xuất được lưu trong
repo; loại trang font lỗi, divider, front matter, bibliography theo manifest
Day06. Không OCR, không mô hình ảnh; giữ số trang PDF vật lý.

Dùng đúng chunking B `by_paragraph(max_size=1000)`: **212 chunk**, không overlap,
giữ nguyên chunk ID, source/document ID, page và metadata. Code đối chiếu toàn
bộ ID/text/metadata/số chiều giữa corpus và bảng thật trước khi truy vấn.

Embedding **sentence-transformers/all-MiniLM-L6-v2**, local, normalize, **384 chiều**;
PostgreSQL **{runtime['postgresql']}**, pgvector **{runtime['pgvector']}**, cosine exact
search trên `day6_chunks`, strategy `{runtime['strategy']}`. Không thay embedding bằng
vector giả. Bảng Day06 không lưu model revision; tên model dựa trên provenance và
cache Day06, số chiều được kiểm tra thực tế. Tùy chọn init-index ghi riêng DAY7_B,
không ghi đè A/B/C/CHAT. Runtime và hash đầu vào/code ở
[runtime.json](../../results/final/runtime.json).

Agent dùng **{runtime['chat_model']}** qua OpenRouter, temperature 0, tối đa 800
output token/call. Việc gửi câu hỏi và đoạn trích báo cáo tới OpenRouter có phí
đã được học viên cho phép. API key/database URL không nằm trong trace hay báo cáo.

## Benchmark và tính độc lập

[Benchmark](../../data/benchmark.json) có **41 câu**: dev 30 có đáp án + 4 thiếu
bằng chứng, test 5 có đáp án + 2 thiếu bằng chứng. Evidence quote được chuẩn hóa
NFKC/whitespace và kiểm tra đúng nguồn, trang, chunk. Truy xuất và agent không nhận
gold, expected answer hay nhãn answerable. Filter benchmark để rỗng cho mọi
phương pháp, tránh dùng nhãn category không suy ra rõ từ câu hỏi. Demo cho phép
người dùng chỉ định category trực tiếp.

Lượt thăm dò `results/run-01` phát hiện lỗi citation: model trả ID trong structured
output nhưng thiếu inline, dẫn tới từ chối hình thức. Đã sửa renderer lấy đúng ID
model cung cấp, chuẩn hóa ngoặc, kiểm tra thuộc context rồi thêm footer nguồn nếu
cần. Không tự tạo citation từ ranking/gold. Test cũ q26–q30/u03/u04 đã được đọc khi
chẩn đoán nên chuyển sang dev. Test mới q31–q35/u05/u06 được tạo và khóa trước
lượt `results/final`; sau đó không chỉnh retrieval, agent hay tham số theo test.
Đây là test prospective do AI hỗ trợ tạo, người thiết kế biết corpus, **không phải
test mù độc lập**. Snapshot và hạn chế lượt cũ được giữ trong README của run-01.

Negative audit: [absence_audit.json](../../data/absence_audit.json). Kiểm tra phạm vi
corpus, năm của báo cáo và đoạn liên quan; không suy ra thiếu thông tin chỉ từ
top-k. Hai negative test hỏi số liệu chính xác năm 2034/2036 không được báo cáo
2026 cung cấp. Các negative tương đối dễ; cần mở rộng câu thiếu bằng chứng gần
ngữ nghĩa nhưng khó hơn trong một vòng đánh giá độc lập sau này.

## Retrieval và hai cải thiện

Cùng corpus B, cùng câu hỏi gốc, cùng gold và top-3 khi so ranking:

| Cấu hình | Phương pháp | Top-k context | Budget ký tự | Max search agent | Giả thuyết |
|---|---|---:|---:|---:|---|
| tfidf-base | TF-IDF cosine, tách từ đơn giản | 3 | 1600 | 1 | Baseline lexical/context nhỏ |
| dense-base | MiniLM + pgvector B | 3 | 1600 | 1 | Bắt tương đồng ngữ nghĩa |
| hybrid-rrf | Dense + TF-IDF, RRF | 3 | 1600 | 1 | Cải thiện 1: kết hợp hai ranking |
| hybrid-context | Cùng hybrid, context lớn | 6 | 6000 | 3 | Cải thiện 2: giảm mất evidence và cho phép tìm lại |

RRF lấy 20 candidate mỗi nhánh, score `sum(1/(60+rank))`; không cộng trực tiếp
TF-IDF với cosine. Budget gồm header nguồn, giữ nguyên đoạn vừa dung lượng,
dedup theo ID và xếp lại candidate tích lũy. Cấu hình thứ tư đổi đồng thời top-k,
budget và search cap nên chưa tách được tác động riêng của từng biến.

| Cấu hình | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median retrieval ms |
|---|---|---|---|---|---:|
{chr(10).join(retrieval_rows)}

Embedding/retrieval local không có phí dịch vụ (USD 0), chưa tính điện, phần cứng
hay API agent. Thời gian trên là một lần đo, không phải latency benchmark nhiều
vòng. Index B có sẵn từ Day06, không gộp lại chi phí ingest vào query latency.

Tiêu chí chọn công bố trong code/config: ưu tiên dev Context Evidence Rate,
Hit@3, Hit@1; hòa thì budget nhỏ, ít search, ID. Chọn **{selection['config']['id']}**,
khóa tại `{selection['selected_at_utc']}` trước test. Hash benchmark/config trong
[selection.json](../../results/final/selection.json). Đây là tiêu chí retrieval-first;
chất lượng agent và chi phí báo riêng. Có thể dùng bài toán trade-off khác cho
một vòng dev mới, không thay lựa chọn sau khi biết test.

### Đọc context test 0/1/2

Đã đọc đủ 5 câu có đáp án cho baseline và cấu hình chọn. Nhãn chi tiết trong
[context_reviews.json](../../results/final/test/context_reviews.json), có lý do.

| Cấu hình | Số câu mức 0/1/2 | Trung bình |
|---|---|---|
{chr(10).join(context_rows)}

q31 baseline có câu exemption nhưng thiếu antecedent xác định circular của Italy,
nên chấm context 1 dù metric quote-hit là true. q32 baseline giữ phần giới thiệu
bảng nhưng rơi hàng 24 giờ/CSIRT, nên context 0. Hybrid giữ đủ hai đoạn q31 và
hàng bảng q32. Đây là ví dụ metric khớp quote và chấm đủ ngữ cảnh khác nhau.

## Agent, trace và chất lượng câu trả lời

Model quyết định tool `search` và `finish`; request đầu bắt buộc search, sau đó
có thể viết lại query hoặc tìm tiếp. Tài liệu là dữ liệu không đáng tin, không phải
chỉ dẫn. Lịch sử model chỉ chứa câu hỏi và context tích lũy mới nhất, tránh nhân
budget qua message history. Trace giữ cả model call, query/arguments, ranking,
source/page, context, citation, usage và latency. Citation hợp lệ về hình thức
chưa đủ: nội dung nguồn được chấm riêng. Lỗi API/store/protocol là `error`, không
thay bằng mock, không tính như abstention đúng.

**Nhãn dưới đây có Codex hỗ trợ đọc đáp án/nguồn, chưa được học viên hoặc người
chấm độc lập xác nhận.** `student_confirmed=false` trong reviews. Đã đọc từng
đáp án và citation, chấp nhận evidence thay thế hợp lệ (ví dụ q03 bảng tỷ lệ chính
xác, q15 một chỉ số khác nhưng đúng yêu cầu). Chấm thiếu điều kiện/khẳng định
vượt nguồn là mức 1; trả lời lệch trọng tâm/false abstention là 0. Citation chỉ
có tiêu đề hoặc sai đối tượng bị chấm false. Việc tổng hợp không tự suy nội dung
đúng từ ID. Các script/nhãn ở [artifacts](../../artifacts/).

| Config/split | Tool use | Số câu grade 0/1/2 | Grounded mean | Citation hỗ trợ | Abstention đúng | Từ chối nhầm | Lỗi | Median agent ms | API USD |
|---|---|---|---|---|---|---|---:|---:|---:|
{chr(10).join(agent_rows)}

Chi phí biết được cho các lượt agent trong `results/final` là **USD {sum(totals):.6f}**,
theo trường usage/cost do OpenRouter trả. Một lượt lỗi dense-dev không đủ usage nên
không khẳng định đây là hóa đơn tổng. Chưa bao gồm smoke test, demo và thăm dò.
Lượt dense-dev q20 lỗi sau model call đầu được giữ nguyên, không chạy lại để chọn
kết quả tốt hơn. Mẫu số chất lượng loại lượt lỗi và báo riêng.

Mọi câu trả lời thành công đều có citation trong output. Dev baseline/dense/RRF
dùng 1 search mỗi câu thành công; hybrid-context có 33 câu dùng 1 search và u02
dùng 3. Test hybrid có 6 câu dùng 1 search, u06 dùng 3 rồi chạm giới hạn: đây là
từ chối do giới hạn của hệ thống, không phải bằng chứng model đã chứng minh toàn
bộ corpus không có đáp án. Negative vẫn được xác nhận bằng audit corpus riêng.

### Audit toàn bộ test cuối

| Cấu hình | Query | Status | Nhãn | Lý do đối chiếu |
|---|---|---|---|---|
{chr(10).join(test_rows)}

## Phân tích lỗi dev và đánh đổi

1. **q24, PDF 72:** baseline giữ para:0 nói có thể tận dụng cấu trúc hiện hữu,
   nhưng mất para:1 nêu governance, risk management, capacity-building và operational
   processes. Baseline/RRF context nhỏ trả lời mức 1; hybrid-context giữ para:1,
   trả lời đủ bốn phần, mức 2. Giả thuyết tăng budget/top-k được kiểm chứng ở trace.
2. **q25, PDF 75:** context nhỏ đưa trang 77 về hạn chế khảo sát, model chỉ trả ba
   ngôn ngữ và bỏ ngày, mức 1. Hybrid-context giữ trang 75 về thiết kế khảo sát,
   trả early November–mid-December 2025 và ba ngôn ngữ, mức 2.
3. **q30, PDF 88:** mọi cấu hình đều thêm communication interception như một tác
   động của DoS, trong khi tài liệu mô tả đó là vector riêng. Retrieval đúng chưa
   ngăn lỗi gộp ý từ bảng; chấm câu trả lời 1, citation false. Chưa sửa theo test;
   vòng sau cần tách hàng bảng hoặc yêu cầu trích đúng câu hỗ trợ từng khẳng định.
4. **q12/q18:** hybrid-context vẫn không đưa ra đầy đủ định nghĩa resilience/ROSI;
   q18 bị từ chối nhầm. Context lớn không bảo đảm agent chọn đúng trọng tâm.

Hybrid-context tăng evidence retention dev từ 13/30 lên 27/30 và grounded mean
từ 1.333/2 lên 1.600/2 theo nhãn AI-assisted, đổi lại context/API token lớn hơn.
Dense đơn lẻ không vượt TF-IDF trên bộ query gốc tiếng Anh, vì vậy không tuyên bố
embedding luôn tốt hơn lexical. RRF context nhỏ tăng Hit@1 nhưng giảm Hit@3 so
với TF-IDF; lưu cả kết quả không cải thiện. Test chỉ 5 positive, nên mỗi câu làm
tỷ lệ thay đổi 20 điểm phần trăm; kết quả tốt không suy rộng cho mọi tài liệu.

## Tái lập, demo và phạm vi bài nộp

- [Runbook](../../docs/DAY07_RUNBOOK.md): cài dependencies, dùng `.env` Day06,
  Docker/pgvector, lệnh dev → chốt → test, demo và tổng hợp review.
- [Kịch bản demo](../../docs/DEMO.md); trace thật ở `results/demo-answer.json`
  và `results/demo-abstain.json`.
- Code ở `src/day7/`, cấu hình ở `configs/experiments.json`, corpus/benchmark
  trong `data/`, trace/summary/review ở `results/final/{{dev,test}}/<config>/`.
- `python -m unittest discover -s tests -v`: **23/23 đạt**, gồm contract retrieval,
  RRF, filters, budget/dedup, citation, failure và selection hash. Đây là test
  offline, không dùng làm số liệu chất lượng model. Đã compile code và diff-check.
- Học viên cần đọc/xác nhận các nhãn AI-assisted trước khi nộp. Chưa push repo
  hoặc công bố kết quả lên GitHub trong phiên này.
- Báo cáo này ghi nhận phần cơ bản. Xem [báo cáo nâng cao](2A202603907_TrinhHungThinh_Advanced.md)
  cho pipeline vision riêng trên PDF 107 trang, dùng Flash Lite trong daily cap
  USD 0.70. Xem báo cáo nâng cao để đối chiếu kết quả và lỗi từng lượt.
'''
    path = ROOT / 'report/individual/2A202603907_TrinhHungThinh.md'
    path.write_text(report, encoding='utf-8')
    print(path.name, 'written from final artifacts')


if __name__ == '__main__':
    main()
