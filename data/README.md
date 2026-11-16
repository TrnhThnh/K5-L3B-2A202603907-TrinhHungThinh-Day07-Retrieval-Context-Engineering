# Định dạng dữ liệu

Các file `example_*.json` chỉ minh họa định dạng, không đủ để nộp bài. Dữ liệu thật là JSON array UTF-8; nếu dùng định dạng khác, ghi cách chuyển trong README.

- **Chunk:** `id`, `text`, `source_id`, `source`, `page`, `metadata`. ID phải duy nhất; giữ phiên bản hoặc ngày nếu có.
- **Câu có đáp án:** `id`, `split` (`dev` hoặc `test`), `question`, `expected_answer`, `gold`: danh sách `{source_id, page, evidence}`. Với schema mẫu, mỗi evidence phải nằm trọn trong một chunk đúng nguồn và trang; các phần tử `gold` là evidence thay thế. Với câu multi-hop cần nhiều đoạn, bạn có thể mở rộng schema, ghi rõ nhóm evidence bắt buộc và cách chấm. Có thể thêm `filter` do người dùng cung cấp trước.
- **Câu thiếu evidence:** `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`. Xem `agent_cases_example.json`.

Không đưa `gold` hoặc nhãn đáp án vào model và retrieval tool. Ghi nguồn dữ liệu và quyền sử dụng. Cách chuyển một số định dạng Day 6: [starter/README.md](../starter/README.md).
# Dữ liệu thực hiện Day07

Corpus Day06 ở `day06/pages.jsonl` và quyền sử dụng ở `day06/manifest.json`.
`benchmark.json` là bộ đánh giá cuối gồm 41 câu (34 dev, 7 test).
`absence_audit.json` ghi phạm vi kiểm tra câu thiếu bằng chứng.
Tái tạo bằng `python -m src.day7.cli prepare`; nếu thay benchmark sau khi chốt
selection, phải dùng thư mục thí nghiệm mới. Các file `example_*` phía dưới chỉ
là fixture của đề, không dùng làm kết quả bài thực hiện.
