# Báo cáo bonus Day07 — đánh giá multimodal với model tiết kiệm

**Trịnh Hưng Thịnh · 2A202603907 · L3B**

**Trạng thái: đã đổi sang model tiết kiệm và chạy benchmark thật trong hạn mức
USD 0.70/ngày. Chưa ghi nhận đạt bonus.** Lượt test đầu đạt 5/30, có 24 lỗi
provider HTTP 429 và một câu sai. Bảng dưới giữ riêng mọi lượt chạy; không ghép
câu trả lời tốt nhất hoặc loại lỗi khỏi mẫu số.

## Tài liệu, quyền và phạm vi index

Dùng cùng báo cáo World Bank. 2026. *Cybersecurity in Ports: Shifting from Risk
to Resilience.* © World Bank. Bản gốc trong `data/advanced/source.pdf`, **107
trang vật lý**, SHA256
`654a61f25fba637ca467a1a4d7e7d9fe4247c998bdbf5b6f5392c8b8cef8172e`.
Đã mở ảnh trang 4: Rights and Permissions cho phép tái sử dụng toàn bộ/một phần
phi thương mại với ghi công đầy đủ. Nguồn, phiên bản và hạn chế ở
[manifest](../../data/advanced/manifest.json).

Yêu cầu ADVANCED.md là tài liệu **ít nhất 100 trang**, không yêu cầu phải có 100
trang text nội dung. Bản PDF 107 trang đáp ứng yêu cầu kích thước tài liệu. Đã
render và trích text **107/107 trang**, tạo catalog vision **107/107 trang**,
index **106 trang/582 bản ghi**. Trang 2 hoàn toàn trắng không có dữ liệu để
index. Native text có nội dung từ front matter, phụ lục, tài liệu tham khảo và
trang không thuộc benchmark đều được index. Trang 94 có biểu đồ phụ lục mà corpus
cơ bản trước đây chưa dùng. Bảng [coverage](../../data/advanced/coverage.json) và
[corpus audit](../../data/advanced/corpus_audit.json) ghi từng trang.

Việc đưa cả front matter/references vào index nhằm giữ nội dung hữu ích và nguồn,
không dùng chúng để thay thế các nhóm câu hỏi về bảng, sơ đồ và biểu đồ.

## Pipeline multimodal

1. **Render và native text:** PyMuPDF 1.26.7, ảnh JPEG rộng 1600 px, giữ physical
   page và hash; nguồn PDF không bị sửa. Mọi trang có ảnh gốc để người chấm đối
   chiếu, gồm trang có lỗi font mà Day06 chưa dùng.
2. **Vision catalog độc lập query:** gửi ảnh toàn trang tới OpenRouter theo sự
   cho phép của học viên. 99 trang thành công với gpt-4o-mini, 8 trang lỗi schema
   được chạy lại với gpt-4.1-mini. Lưu summary, loại/nhãn vùng, bbox chuẩn hóa,
   mô tả bảng/biểu đồ/sơ đồ và usage. Không cung cấp câu hỏi/gold cho extractor.
3. **Đối chiếu bản gốc:** mở ảnh trang, kiểm tra caption, legend và crop. Giữ
   `visual_catalog.machine.json`, ghi lỗi và hiệu chỉnh ở `extraction_audit.json`.
4. **Index:** native text chia đoạn 1100 ký tự, bước 900; thêm page summary và
   mô tả visual regions. Lưu ID/source/page/bbox/ảnh/crop. Dùng MiniLM 384 chiều,
   PostgreSQL/pgvector exact cosine, strategy riêng **ADVANCED_M1**, giữ A/B/C và
   toàn bộ kết quả cơ bản. Fusion TF-IDF/dense bằng RRF, candidate 40 mỗi nhánh.
5. **Agent:** `search` định vị evidence; `inspect_pages` mở ảnh gốc model chọn;
   `calculate` xử lý số học cơ bản; `finish` trả lời/từ chối. Trả lời ngắn, đọc
   đúng hàng/cột/legend/đơn vị/mũi tên, không suy số chính xác từ bar không nhãn.
6. **Citation:** mỗi citation ghi physical page, bbox chuẩn hóa, nhãn
   Figure/Table/Box/heading và ý được hỗ trợ. Chỉ cite trang đã mở. Crop citation
   có thể tái tạo để chấm; kiểm tra ID/bbox không tự chứng minh nội dung đúng.

Code ở `src/advanced/`; [runbook](../../docs/ADVANCED_RUNBOOK.md) ghi lệnh cài,
tái tạo index, chạy agent, benchmark và chấm. Không dùng random embeddings,
fake model hoặc đáp án chuẩn làm đầu vào truy xuất.

## Kiểm tra chất lượng trích xuất

Đã phát hiện và sửa các lỗi cụ thể từ ảnh gốc:

| Trang PDF | Lỗi machine extraction | Cách xử lý |
|---|---|---|
| 12 | Gán nhầm Figure 1 cho sơ đồ ripple không đánh số; crop thiếu phần hình | Sửa label và bbox theo ảnh gốc |
| 14 | Gán Figure 1 và bbox chỉ trúng đoạn giới thiệu | Tách ba panel Reporting/Assessing/Capacity, giữ số và đơn vị |
| 35 | Crop thiếu legend | Mở rộng vùng donut/legend |
| 56 | Bbox bỏ tiêu đề/bar trên và chứa ảnh trang trí | Sửa vùng chart/legend; không ghi số exact cho bar không nhãn |
| 58 | Crop cắt nhãn Operations supervisor | Mở rộng vùng Figure 13 |
| 76 | Ảnh cảng bị gán Figure 17 | Bỏ region ảnh trang trí khỏi catalog; giữ Figure 16 |
| 77 | Caption và summary đảo Port association/Port authority | Đọc màu legend: authority 56%, association 4.6%; sửa catalog |

Đây là lý do agent phải mở ảnh gốc thay vì tin caption. Các mô tả còn lại chưa
được xác nhận độc lập toàn bộ; không tuyên bố OCR/vision extraction hoàn hảo.
Các sơ đồ dùng trong benchmark thể hiện thông tin/quan hệ thực, không dùng ảnh
cảng trang trí để đủ quota câu ảnh.

## Benchmark riêng, đã chia trước thử nghiệm

[benchmark.json](../../data/advanced/benchmark.json) gồm **48 câu**:

| Nhóm chính | Dev | Test |
|---|---:|---:|
| Bảng | 3 | 6 |
| Ảnh/sơ đồ có thông tin | 3 | 5 |
| Biểu đồ | 3 | 5 |
| Multi-hop | 3 | 4 |
| Text | 3 | 4 |
| Thiếu bằng chứng | 3 | 6 |
| **Tổng** | **18** | **30** |

Mỗi positive có câu hỏi, expected answer, nguồn, physical page, bbox, nhãn vùng,
điều kiện/đơn vị/phép tính khi cần. Multi-hop yêu cầu evidence từ ít nhất hai
trang. Negative có lý do và audit phạm vi corpus, không kết luận thiếu bằng chứng
chỉ vì top-k không tìm thấy. Dev/test không trùng câu hoặc chỉ đổi cách diễn đạt
cùng một đáp án; có thể dùng cùng bảng nhưng hỏi các sự kiện/phép kết hợp khác.

Benchmark do Codex hỗ trợ tạo từ bản gốc, biết tài liệu; đây là prospective split,
không phải test mù bên ngoài. **Chưa chạy agent trên test** và chưa dùng test
để chọn cấu hình. Điểm cuối phải tính đủ 30 câu, lỗi/timeout là không đạt,
không làm tròn: tối thiểu **27/30** để qua ngưỡng.

## Thí nghiệm và trạng thái thực tế

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
| vision-lite | 17/18 | 94.44% | 0.021510 |
| vision-lite-wide | 17/18 | 94.44% | 0.026916 |

Cả hai cùng model Flash Lite. `vision-lite` dùng top-10/context 14 rows/search 4/
max 6 pages; `vision-lite-wide` dùng top-16/context 22/search 6/max 8 pages.
Chọn **vision-lite** theo pass rate dev, hòa chọn chi phí thấp.
Chốt lúc `2026-11-16T04:00:45.155881+00:00`; hash benchmark, PDF, catalog/index,
config và code trong [selection](../../results/advanced/run-05/selection.json).

Lỗi dev tiêu biểu: lite trả ROSI đúng ý nhưng thiếu citation trang 60 trong câu
multi-hop; wide đọc sai North America 4.6% là nhỏ nhất, trong khi bản gốc Figure
16 có South Asia 2.8%. Context rộng hơn không bảo đảm đọc đúng hình. Không dùng
các kết quả test để đổi model, prompt, retrieval hay chọn lại cấu hình.

### Test: giữ riêng mọi lượt

**Lượt đầu: 5/30 (16.67%)**, có
**24 lỗi HTTP 429**. Sáu câu có output: năm đúng, một sai
(at04 lấy các loại attack khác thay vì cơ chế Insider Threats ở trang 88).
Lỗi vẫn nằm trong mẫu số 30. Chi phí usage biết được của lượt này là
USD 0.005470.

Chẩn đoán provider xác định `upstream_provider_shared_pool` của Google đang bị
rate-limit; đây không phải hết hạn mức key USD 0.70. Text probe có thể thành công
trong khi request ảnh vẫn bị 429. Endpoint model chỉ cung cấp các tier của Google
AI Studio, chưa có provider độc lập để chuyển tuyến trong lượt hiện tại.

Đã khai báo một lượt lặp lại đầy đủ với cùng frozen pipeline, chạy tuần tự,
nghỉ 15 giây giữa câu và backoff 45 giây, tối đa hai retry **chỉ cho HTTP 429**.
Không retry câu sai/từ chối và không thay lượt đầu. Mọi attempt được giữ riêng.
Lượt lặp lại: **25/30 (83.33%)**, lỗi cuối cùng 2.

| Nhóm chính | Lượt đầu | Lặp lại |
|---|---|---|
| table | 5/6 | 5/6 |
| diagram | 0/5 | 5/5 |
| chart | 0/5 | 5/5 |
| multi_hop | 0/4 | 1/4 |
| text | 0/4 | 3/4 |
| unanswerable | 0/6 | 6/6 |

Không gộp các câu đúng giữa hai lượt, không chọn điểm cao hơn để che lượt lỗi.
Benchmark test yêu cầu >=27/30 và đủ evidence. Nhãn nội dung do Codex đối chiếu
PDF gốc hỗ trợ, `student_confirmed=false`, cần học viên/giảng viên xác nhận.

## Chi phí, kiểm tra và đường dẫn

Provider xác nhận usage_daily **USD 0.648382 / 0.70**; còn **USD 0.051618**.
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
