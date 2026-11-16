# Chạy Day07 — Trịnh Hưng Thịnh, 2A202603907

Chạy lệnh từ thư mục gốc repo. Python 3.11+.

## Cài đặt mới

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Điền `DATABASE_URL`, `OPENROUTER_API_KEY` và model trong `.env`. Không commit file
này. Có thể dùng thẳng `.env` Day06 qua `--env-file`; không cần sao chép secret.

```powershell
$py = '.venv/Scripts/python.exe'
$envFile = 'C:/Users/admin/Downloads/AI20K/Day06/K5-L3B-Day06-2A202603907-DataIngestionEngineering/starter/.env'
& $py -m src.day7.cli --env-file $envFile check
```

Trong phiên tích hợp đã dùng Python 3.12.7 tại `.venv` Day06 có sẵn.
Nếu muốn chạy ngay bằng môi trường đó trên máy hiện tại, thay `$py` bằng:

```powershell
$py = 'C:/Users/admin/Downloads/AI20K/Day06/K5-L3B-Day06-2A202603907-DataIngestionEngineering/starter/.venv/Scripts/python.exe'
```

`check` kiểm tra corpus/benchmark offline, không kiểm tra kết nối dịch vụ.

## Database và embedding

Dùng lại bảng `day6_chunks`, strategy **B**, embedding
`sentence-transformers/all-MiniLM-L6-v2`, 384 chiều, normalize, cosine exact search.
Khi khởi động, ứng dụng đối chiếu toàn bộ ID, text, nguồn, metadata và số chiều
với 212 chunk tái tạo từ corpus Day06. Model name dựa trên provenance Day06;
bảng cũ không có cột model/version nên không thể chứng minh model từ vector đơn lẻ.

Nếu chưa có database, mở Docker Desktop rồi:

```powershell
docker compose up -d
& $py -m src.day7.cli --env-file $envFile init-index
```

Lệnh này chỉ thay strategy **DAY7_B**, giữ nguyên A/B/C/CHAT Day06. Đặt
`DAY6_STRATEGY=DAY7_B` trong `.env` khi dùng index vừa tạo. Nếu máy đã có container
Day06 ở port 55433 thì dùng container đó, không chạy thêm container trùng port.
`EMBEDDING_LOCAL_ONLY=true` yêu cầu model đã có cache; đặt false ở lần tải đầu.

## Demo agent thật

Các lệnh sau gửi câu hỏi và đoạn trích báo cáo tới OpenRouter; API tính phí theo
token. Chạy trên dữ liệu bạn có quyền chia sẻ. Các đoạn trích World Bank của bài
này dùng phi thương mại và ghi công theo `data/day06/manifest.json`.

```powershell
& $py -m src.day7.cli --env-file $envFile ask 'Ngoài lịch định kỳ, khi nào cảng cần quét lỗ hổng?' --method hybrid --trace results/demo-answer.json
& $py -m src.day7.cli --env-file $envFile ask 'Mật khẩu PostgreSQL của trung tâm Cyber Resilience Center Los Angeles là gì?' --trace results/demo-abstain.json
& $py -m src.day7.cli --env-file $envFile ask 'Which rules govern information sharing?' --category barriers --trace results/demo-filter.json
```

Agent gọi model thật để chọn `search(query)` hoặc `finish(status,answer,citations)`.
Search tối đa 3 lần, lấy 6 chunk/lần, budget 6,000 **ký tự gồm header nguồn**.
Context tích lũy được dedup và xếp lại theo score, chỉ giữ nguyên chunk vừa budget.
Không sử dụng gold hoặc benchmark để tạo query. Filter chỉ đến từ người dùng;
các filter Day06 không thể suy ra rõ từ query đã được bỏ trong benchmark Day07.
Agent có thể dịch query sang tiếng Anh; retrieval benchmark luôn dùng query gốc.

Trace có model call, tool arguments, query, ranking, score, nguồn/trang, context,
citation, latency và usage/cost do OpenRouter trả. Lỗi provider có status `error`,
không tính như từ chối đúng. Citation chỉ được kiểm tra hình thức; cần đọc nguồn.

## Benchmark và kiểm chứng

```powershell
& $py -m src.day7.cli prepare
& $py -m unittest discover -s tests -v
& $py -m src.day7.cli --env-file $envFile benchmark --split dev --output results/new-run
& $py -m src.day7.cli --env-file $envFile agent-benchmark --split dev --output results/new-run
# Sau khi chốt selection.json, mới chạy test; không dùng test chỉnh tham số.
& $py -m src.day7.cli --env-file $envFile benchmark --split test --output results/new-run
& $py -m src.day7.cli --env-file $envFile agent-benchmark --split test --output results/new-run
```

Bốn cấu hình trong `configs/experiments.json`: TF-IDF, dense, hybrid RRF, hybrid
với context lớn. Hai cải thiện được công bố trước: fusion và mở rộng context/
số lượt tìm. Cùng corpus, cùng query gốc, cùng top-3 cho ranking; cấu hình cuối
dùng top-6 cho context. RRF dùng `sum(1/(60+rank))`, không cộng trực tiếp cosine
với TF-IDF. Selection chỉ dùng dev: ưu tiên Context Evidence Rate, Hit@3, Hit@1,
sau đó budget nhỏ, ít search và ID. Đây là tiêu chí retrieval-first; đánh giá
agent được báo riêng, không tự chọn cấu hình theo một lời giải model.

`selection.json` khóa hash benchmark và configs. Muốn làm thí nghiệm mới, dùng
thư mục khác; không ghi đè selection. Giữ cùng cấu hình khi chạy lại do lỗi mạng.

Để chạy phần không cần model/database, chỉ dùng standard library:

```powershell
python -m src.day7.cli benchmark --split dev --methods tfidf --output results/offline-new
```

Sau khi đọc từng trace, điền `reviews.json`: `answer_grade` 0–2 cho câu có đáp án,
`citation_support` một boolean cho mỗi citation, `abstention_correct` cho câu thiếu
bằng chứng; ghi reviewer và lý do. Chấm context riêng 0/1/2. Không dùng ID hợp lệ
để tự gán citation đúng.

```powershell
& $py -m src.day7.review --run results/new-run/test/hybrid-context --split test
```

Lệnh tổng hợp từ chối nhãn chưa chấm; không tự tạo điểm chất lượng. Nhãn có Codex
hỗ trợ phải ghi rõ, học viên cần xác nhận trước khi nộp. Với multi-hop cần thêm
schema all-required evidence; benchmark hiện tại là single-evidence passage.

## Nguồn, split và giới hạn

- Corpus 80 trang nội dung, PDF vật lý 12–16 và 19–93, 212 chunk B. Giữ ID/trang
  Day06; không cần PDF để chạy vì text và metadata đã được export.
- 30 câu có evidence + 4 thiếu evidence trên dev; 5 có evidence + 2 thiếu trên test.
- Lượt `results/run-01` là thăm dò: phát hiện lỗi model trả citation riêng nhưng
  thiếu inline. Sau sửa adapter hiển thị, q26–q30 và u03/u04 chuyển sang dev.
  Test cuối q31–q35/u05/u06 được tạo và khóa trước lượt `results/final`.
  Người thiết kế biết corpus; đây là test prospective, không phải test mù độc lập.
  Không chỉnh cấu hình dựa trên kết quả test cuối.
- Adapter chuẩn hóa citation có bọc ngoặc; nếu model trả raw IDs hợp lệ nhưng
  thiếu inline, renderer thêm footer nguồn từ đúng các ID model đã chọn. Không
  suy ra citation từ ranking/gold; không tự xác nhận nội dung nguồn hỗ trợ đáp án.
- Negative audit ở `data/absence_audit.json` chỉ kết luận trong corpus; tìm không
  thấy ở top-k không tự chứng minh tài liệu không có câu trả lời.
- PDF 107 trang nhưng chỉ index 80 trang nội dung, không xử lý hình/bảng đa phương
  thức nên **không tuyên bố đạt bonus nâng cao**.
- Repo Day06 tại commit `bf21bc0b5d7ab8a7ae4902c0905da5dfabd3469c`; xem
  `vendor/README.md` và `data/day06/provenance.json`.
