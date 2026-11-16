"""Update advanced report from preserved trials, not selected best answers."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.common import read_json,DATA
from src.day7.data import write_json

run=ROOT/'results/advanced/run-05'
selection=read_json(run/'selection.json')
first=read_json(run/'test/vision-lite/summary.json')
rep_folder=run/'repeat-01/test/vision-lite'
rep=read_json(rep_folder/'summary.json') if (rep_folder/'summary.json').exists() else None
rep_traces=read_json(rep_folder/'traces.json') if (rep_folder/'traces.json').exists() else []
path=ROOT/'report/individual/2A202603907_TrinhHungThinh_Advanced.md'
text=path.read_text(encoding='utf-8').split('## Thí nghiệm và trạng thái thực tế')[0]
start=text.index('**Trạng thái:')
end=text.index('## Tài liệu',start)
text=text[:start]+'''**Trạng thái: đã đổi sang model tiết kiệm và chạy benchmark thật trong hạn mức
USD 0.70/ngày. Chưa ghi nhận đạt bonus.** Lượt test đầu đạt 5/30, có 24 lỗi
provider HTTP 429 và một câu sai. Bảng dưới giữ riêng mọi lượt chạy; không ghép
câu trả lời tốt nhất hoặc loại lỗi khỏi mẫu số.

'''+text[end:]
text=text.replace('triển khai multimodal local','đánh giá multimodal với model tiết kiệm')
devrows=[]
for name in ['vision-lite','vision-lite-wide']:
    s=read_json(run/'dev'/name/'summary.json')
    devrows.append(f"| {name} | {s['passed']}/{s['total']} | {100*s['rate']:.2f}% | {s['service_cost']['known_usd']:.6f} |")
groups=[]
for name,g in first['groups'].items():
    second=rep['groups'][name] if rep else None
    groups.append(f"| {name} | {g['passed']}/{g['total']} | {str(second['passed'])+'/'+str(second['total']) if second else 'Chưa hoàn tất'} |")
quota_path=ROOT/'results/advanced/key-quota-final.json'
quota=read_json(quota_path) if quota_path.exists() else None
quota_text=(f"Provider xác nhận usage_daily **USD {quota['usage_daily']:.6f} / {quota['limit']:.2f}**; còn **USD {quota['limit_remaining']:.6f}**."
            if quota else 'Quota cuối sẽ được ghi sau khi dừng/chạy xong các request đang xử lý.')
rep_text=(f"Lượt lặp lại: **{rep['passed']}/{rep['total']} ({100*rep['rate']:.2f}%)**, lỗi cuối cùng {rep['system_errors']}."
          if rep else f"Lượt lặp lại hiện có {len(rep_traces)}/30 trace; chưa có điểm benchmark hoàn chỉnh.")
text+=f'''## Thí nghiệm và trạng thái thực tế

Theo yêu cầu mới của học viên, daily limit tăng từ USD 0.50 lên **USD 0.70** và
model được đổi sang **google/gemini-2.5-flash-lite**. Theo [trang model OpenRouter](https://openrouter.ai/google/gemini-2.5-flash-lite)
đã kiểm tra ngày 16/11/2026, mức niêm yết là USD 0.10 input và USD 0.40 output
trên một triệu token. Chi phí thực nghiệm dùng `usage.cost`, không suy từ giá
niêm yết. Dùng lại catalog/index, không trả phí vision extraction lần nữa.

Trước mỗi paid request, code đọc quota của key và giữ khoảng dự phòng cho các
request đang xử lý. Trần an toàn là USD 0.70/ngày, không sửa hạn mức tài khoản.
Đã thêm hỗ trợ batch search/inspect của Gemini, schema bbox 0–1 và phản hồi lỗi
định dạng. Các thay đổi này được thử trên dev, trước test.

### Citation alignment local

Model đôi khi dự đoán bbox lệch. Bước `citation_alignment.py` dùng trang/nhãn mà
model đã chọn để tra catalog độc lập query hoặc tìm nhãn/đoạn hỗ trợ trong layout
PDF gốc. Giữ `model_bbox`, raw `traces.model-output.json` và manifest alignment;
không đọc benchmark/gold để sửa tọa độ, không sửa nội dung đáp án, không tự xác
nhận semantic support. Bước này được hoàn thiện trên dev và khóa trước test.

### Chọn cấu hình trên dev

| Config | Đạt / tổng | Tỷ lệ | API USD biết được |
|---|---|---:|---:|
{chr(10).join(devrows)}

Cả hai cùng model Flash Lite. `vision-lite` dùng top-10/context 14 rows/search 4/
max 6 pages; `vision-lite-wide` dùng top-16/context 22/search 6/max 8 pages.
Chọn **{selection['config']['id']}** theo pass rate dev, hòa chọn chi phí thấp.
Chốt lúc `{selection['selected_at_utc']}`; hash benchmark, PDF, catalog/index,
config và code trong [selection](../../results/advanced/run-05/selection.json).

Lỗi dev tiêu biểu: lite trả ROSI đúng ý nhưng thiếu citation trang 60 trong câu
multi-hop; wide đọc sai North America 4.6% là nhỏ nhất, trong khi bản gốc Figure
16 có South Asia 2.8%. Context rộng hơn không bảo đảm đọc đúng hình. Không dùng
các kết quả test để đổi model, prompt, retrieval hay chọn lại cấu hình.

### Test: giữ riêng mọi lượt

**Lượt đầu: {first['passed']}/{first['total']} ({100*first['rate']:.2f}%)**, có
**{first['system_errors']} lỗi HTTP 429**. Sáu câu có output: năm đúng, một sai
(at04 lấy các loại attack khác thay vì cơ chế Insider Threats ở trang 88).
Lỗi vẫn nằm trong mẫu số 30. Chi phí usage biết được của lượt này là
USD {first['service_cost']['known_usd']:.6f}.

Chẩn đoán provider xác định `upstream_provider_shared_pool` của Google đang bị
rate-limit; đây không phải hết hạn mức key USD 0.70. Text probe có thể thành công
trong khi request ảnh vẫn bị 429. Endpoint model chỉ cung cấp các tier của Google
AI Studio, chưa có provider độc lập để chuyển tuyến trong lượt hiện tại.

Đã khai báo một lượt lặp lại đầy đủ với cùng frozen pipeline, chạy tuần tự,
nghỉ 15 giây giữa câu và backoff 45 giây, tối đa hai retry **chỉ cho HTTP 429**.
Không retry câu sai/từ chối và không thay lượt đầu. Mọi attempt được giữ riêng.
{rep_text}

| Nhóm chính | Lượt đầu | Lặp lại |
|---|---|---|
{chr(10).join(groups)}

Không gộp các câu đúng giữa hai lượt, không chọn điểm cao hơn để che lượt lỗi.
Benchmark test yêu cầu >=27/30 và đủ evidence. Nhãn nội dung do Codex đối chiếu
PDF gốc hỗ trợ, `student_confirmed=false`, cần học viên/giảng viên xác nhận.

## Chi phí, kiểm tra và đường dẫn

{quota_text}
Catalog trước đó có usage biết được tối thiểu USD 0.406671; các lượt lỗi schema
đầu chưa lưu đủ usage. Các lượt thăm dò run-02/03/04 được giữ để kiểm chứng chi
phí và lỗi adapter, không dùng làm accuracy cuối. Embedding/retrieval local có
phí dịch vụ USD 0, không tính điện/phần cứng.

**33/33 unit test đạt**, gồm quota guard, batch calls, sửa citation chưa mở trang,
alignment theo catalog, calculator và chấm multi-hop/lỗi hệ thống đúng mẫu số.
Đây là kiểm tra code offline, không thay benchmark model.

- Final dev/selection/lượt test đầu: `results/advanced/run-05/`.
- Lượt lặp lại: `results/advanced/run-05/repeat-01/`.
- Mỗi lượt có trace, raw model output, review và summary; crop citation tái tạo
  bằng `python -m src.advanced.audit --run <folder>`.
- Code model và transport ở `src/advanced/`, cách chạy trong
  [runbook](../../docs/ADVANCED_RUNBOOK.md).
- Phần cơ bản đã chốt trong `results/final` được giữ nguyên.
'''
path.write_text(text,encoding='utf-8')
print('Advanced report updated from preserved trial artifacts.')
