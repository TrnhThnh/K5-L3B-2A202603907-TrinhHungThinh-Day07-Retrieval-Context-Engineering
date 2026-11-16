Giao diện chat: chạy ` .\run-web.ps1 `, mở http://127.0.0.1:8070. [Hướng dẫn UI](docs/WEB_UI.md).

# Day 7 — Agentic RAG

## Bài thực hiện — Trịnh Hưng Thịnh · 2A202603907 · L3B

Đã tích hợp corpus và pgvector Day06: 80 trang, 212 chunk, MiniLM 384 chiều;
3 phương pháp TF-IDF/dense/hybrid, agent OpenRouter dùng tool calling, benchmark
41 câu và trace/review có thể kiểm chứng.

- [Hướng dẫn cài đặt, chạy demo và benchmark](docs/DAY07_RUNBOOK.md)
- [Báo cáo cá nhân](report/individual/2A202603907_TrinhHungThinh.md)
- [Cấu hình thí nghiệm](configs/experiments.json)
- [Benchmark và nhãn nguồn](data/benchmark.json)
- [Kết quả chạy cuối](results/final/)
- [Bonus multimodal — benchmark Flash Lite, kết quả và lỗi provider](report/individual/2A202603907_TrinhHungThinh_Advanced.md)
- [Cách chạy phần nâng cao](docs/ADVANCED_RUNBOOK.md)

Kiểm tra offline: `python -m src.day7.cli check` và
`python -m unittest discover -s tests -v`.
Đề bài gốc được giữ bên dưới để đối chiếu yêu cầu.

---

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
