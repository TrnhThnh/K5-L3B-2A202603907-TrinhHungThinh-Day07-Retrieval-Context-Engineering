# Bonus Day07 — multimodal RAG trên PDF 107 trang

Phần này tách riêng khỏi code, benchmark và kết quả cơ bản đã chốt. Điều kiện
bonus là >=90% **toàn bộ** test (30 câu cần >=27 đạt), đồng thời đủ nguồn, index,
benchmark đa dạng và đối chiếu bản gốc. Không loại lỗi API khỏi mẫu số bonus.

## Nguồn và index

- `data/advanced/source.pdf`: World Bank (2026), *Cybersecurity in Ports: Shifting
  from Risk to Resilience*, 107 trang vật lý. Ghi công/quyền phi thương mại trong
  `data/advanced/manifest.json`; bản PDF gốc có trang Rights and Permissions.
- `pages/pNNN.jpg`: ảnh gốc render đủ 107 trang, rộng 1600 px.
- `pages.json`: native text và đường dẫn ảnh/hash cho từng trang.
- `visual_catalog.machine.json`: đầu ra vision ban đầu, chưa hiệu chỉnh.
- `visual_catalog.json`: catalog dùng cho retrieval, gồm mô tả, loại, nhãn và bbox.
- `extraction_audit.json`: lỗi đã đối chiếu/sửa với ảnh gốc; gồm lỗi nhầm legend
  Port authority/Port association, nhầm số hình và bbox cắt thiếu nhãn.
- `index_rows.json`: text chunks và region/summary có metadata nguồn/trang/bbox.
- `regions/`: crop theo bbox catalog, chỉ để định vị; agent đọc ảnh toàn trang gốc.
- PostgreSQL `day6_chunks`, strategy riêng **ADVANCED_M1**, embedding MiniLM 384
  chiều giống Day06. Native text của mọi trang có nội dung đều được index, kể cả
  phụ lục, bibliography và các trang không có trong benchmark; trang 2 trắng bỏ.

Catalog tạo độc lập câu hỏi trên toàn tài liệu. Caption do vision sinh có thể sai;
agent được yêu cầu xem lại ảnh gốc, đọc đúng hàng/cột/legend/đơn vị/mũi tên trước
khi trả lời. Không đưa gold hoặc vùng evidence chuẩn vào pipeline runtime.

## Cài đặt và tái tạo

Từ root Day07, dùng môi trường mới hoặc Python Day06 có sẵn:

```powershell
$py = 'C:/Users/admin/Downloads/AI20K/Day06/K5-L3B-Day06-2A202603907-DataIngestionEngineering/starter/.venv/Scripts/python.exe'
$envFile = 'C:/Users/admin/Downloads/AI20K/Day06/K5-L3B-Day06-2A202603907-DataIngestionEngineering/starter/.env'
# Môi trường mới: cài requirements-advanced.txt vào .venv của Day07.
# Không bắt buộc cài lại nếu các dependency đã sẵn có.
& $py -m pip install -r requirements-advanced.txt
& $py -m src.advanced.ingest --source data/advanced/source.pdf
& $py -m src.advanced.vision_index --env-file $envFile
& $py -m src.advanced.vision_index --env-file $envFile --model openai/gpt-4.1-mini --retry-errors
python artifacts/advanced_catalog_qa.py
& $py -m src.advanced.store --env-file $envFile
& $py -m src.advanced.audit
```

Vision index gửi ảnh trang tới OpenRouter và tính phí. Ở máy thực hiện, PyMuPDF
1.26.7 được cài riêng trong `.bonus-deps/` để không thay môi trường Day06; thư mục
này được gitignore. Render đọc PDF không sửa bản gốc. Caption trang đã tồn tại
được giữ khi chạy lại, trừ khi chỉ định retry-errors cho trang lỗi. Sau QA, không
chạy lại extractor làm mất bản catalog đã sửa trước khi đánh giá test.

## Agent

Tool `search` dùng hybrid RRF trên native text và mô tả hình; `inspect_pages`
gửi ảnh gốc của các trang được agent chọn; `calculate` chỉ nhận biểu thức số học
cơ bản; `finish` trả lời hoặc từ chối. Mỗi citation gồm physical page, bbox chuẩn
hóa 0–1, nhãn Figure/Table/Box/heading và nội dung evidence hỗ trợ. Chỉ được cite
trang đã mở. Kiểm tra hình thức không thay thế việc chấm nội dung.

```powershell
& $py -m src.advanced.cli --env-file $envFile 'In Figure 13, identify the three labeled roles in personalized cybersecurity training.' --trace results/advanced/my-demo.json
```

Hai cấu hình hiện tại trong `configs/advanced.json`: `vision-lite` và
`vision-lite-wide`, đều dùng `google/gemini-2.5-flash-lite`, khác candidate,
context và giới hạn search/page. Đã chọn `vision-lite` từ dev trong run-05.
Không cần chạy lại phần cơ bản. Code kiểm tra quota trước mỗi paid call, giữ
headroom và trần USD 0.70/ngày. HTTP 403 daily limit khác HTTP 429 shared-pool
rate limit ở provider; nâng daily limit không tự xử lý được lỗi 429.

Bước local `citation_alignment.py` tra nhãn trang/hình/bảng và text layout để
định vị bbox, không đọc gold. Giữ raw model output và `model_bbox` để kiểm tra.
Code/nguồn/catalog đã khóa trước test; không sửa chúng dựa trên test.

## Benchmark và chấm

`data/advanced/benchmark.json` khóa 48 câu trước thử nghiệm: dev 15 positive + 3
negative; test 24 positive + 6 negative. Test có 6 bảng, 5 sơ đồ/hình có thông tin,
5 biểu đồ, 4 multi-hop, 4 text; mỗi câu một nhóm chính. Multi-hop yêu cầu đủ
evidence từ ít nhất hai trang. Câu tính toán ghi rõ đơn vị/phép tính và số liệu
giả định do câu hỏi cung cấp. Câu thiếu bằng chứng có audit riêng.

```powershell
# Tạo benchmark chỉ khi bắt đầu thí nghiệm mới, không thay sau khi chốt.
python -m src.advanced.prepare_benchmark
& $py -m src.advanced.benchmark --env-file $envFile --output results/advanced/new-run run --split dev
```

Đọc từng trace và ảnh PDF gốc, điền `reviews.json` theo `reviews.template.json`:
`passed` boolean, `reason`, `source_pages_checked`, `citations_support_all_claims`,
`original_page_verified`, `reviewer`, `student_confirmed`. Đúng một phần hoặc
citation không hỗ trợ đủ thì không đạt. Nhãn Codex hỗ trợ phải ghi đúng nguồn;
học viên/giảng viên kiểm tra lại. Sau đó:

```powershell
& $py -m src.advanced.benchmark --output results/advanced/new-run score --split dev
& $py -m src.advanced.benchmark --output results/advanced/new-run select
& $py -m src.advanced.benchmark --env-file $envFile --output results/advanced/new-run run --split test
& $py -m src.advanced.audit --run results/advanced/new-run/test/vision-lite
# Điền reviews.json sau khi đọc original pages và crop citation.
& $py -m src.advanced.benchmark --output results/advanced/new-run score --split test
```

Selection lấy pass rate dev cao nhất; hòa chọn chi phí thấp hơn. Hash benchmark,
config, corpus, index và code được khóa trước test. Thư mục test chỉ chạy cấu
hình đã chọn. Mọi câu test phải có trace; lỗi/timeout vẫn là không đạt. Đổi
pipeline sau khi đọc test thì cần test mới, không chạy lại rồi chọn kết quả tốt.

Nhãn `original_page_verified` chỉ đánh dấu người review đã thực sự mở/đối chiếu
bản gốc. Không tự đặt true từ quote match, crop existence hoặc LLM judge.

## Giới hạn cần trình bày

Học viên đã nâng daily limit lên USD 0.70 và cho phép chạy model rẻ hơn.
Kết quả hiện tại ở `results/advanced/run-05`; các lượt thăm dò cũ được giữ riêng.
Lượt test đầu có 24 lỗi HTTP 429, đã tính không đạt. Mọi lần lặp lại phải ghi
riêng và giữ nguyên kết quả đầu, không chọn/ghép các câu tốt nhất giữa các lượt.
Các lệnh sau không gọi model ngoài:

```powershell
& $py -m src.advanced.audit
& $py -m src.advanced.local_benchmark --env-file $envFile
& $py -m unittest discover -s tests -v
```

Local benchmark chỉ chạy query gốc dev, báo page coverage top-16, không tạo đáp
án và không thay kết quả test bonus. Xem báo cáo nâng cao để biết trạng thái
thực tế của từng lượt test, không suy điểm từ local page coverage.

- Benchmark do Codex hỗ trợ xây dựng, biết tài liệu, không phải test mù bên ngoài.
- Native extraction còn lỗi font ở một số trang; bản ảnh giữ nguyên để kiểm tra.
- Catalog có lỗi đã phát hiện và còn phần chưa kiểm tra độc lập. Tài liệu/ảnh gốc
  là nguồn quyết định; mô tả vision chỉ hỗ trợ định vị.
- Hạn mức API có thể ngắt thí nghiệm; ghi trace lỗi trung thực. Chi phí usage
  chỉ là số biết được nếu provider không trả usage cho lần lỗi.
- Dùng các sơ đồ và biểu đồ chứa thông tin; không lấy ảnh trang trí làm đủ quota.
