# Đối chiếu yêu cầu ngày 16/11/2026

Đối chiếu README, RUBRIC, RULES, SUBMISSION, BENCHMARK và ADVANCED với code, báo cáo và kết quả đã lưu. Không chạy lại benchmark trả phí.

| Hạng mục | Kết luận |
|---|---|
| Day06, nguồn, MiniLM 384 chiều, pgvector | Có code/provenance và kết quả kết nối đã lưu; lần audit này chưa kiểm lại DB live |
| Ít nhất 3 retrieval | Có TF-IDF, dense và hybrid, cùng corpus và bảng dev |
| Agent thật, tool, context, citation, abstention | Có traces/model usage và đánh giá trong results/final |
| Benchmark cơ bản | 41 câu: dev 30 có đáp án + 4 thiếu evidence; test 5 + 2 |
| Metrics retrieval/context/answer | Có bảng, review và summary trong báo cáo cơ bản/results/final |
| Nhiều cấu hình, chọn dev trước test | Có 4 cấu hình cơ bản và selection; lượt thăm dò được ghi riêng |
| Bonus nguồn >=100 trang | PDF 107 trang; index 582 rows/106 trang có nội dung; có catalog và audit |
| Bonus quota benchmark | Dev 18, test 30 với nhóm bảng/sơ đồ/biểu đồ/multi-hop/text/thiếu evidence |
| Bonus >=90% test | CHƯA ĐẠT: đầu 5/30, lặp riêng 25/30; cần >=27/30 |
| Xác nhận nhãn | CÒN THIẾU: student_confirmed=false; cần người học kiểm tra và xác nhận thực tế |
| Web top-k/phương pháp/tiếng Việt/tóm tắt | Có code và smoke; không nằm trong benchmark frozen; chưa có benchmark độc lập cho bản web mới |
| Unit tests hiện tại | 41/41 qua; không tương đương độ chính xác model |
| Reproducibility | Có runbooks/env example; Python mặc định thiếu dotenv, cần đúng venv Day06 hoặc cài requirements |
| Đồng bộ báo cáo | Số 33 tests và quota trong báo cáo nâng cao là snapshot cũ, chưa bao gồm các lượt web/tóm tắt mới |
| Nộp bài | Remote cá nhân đúng; nhiều file còn modified/untracked, chưa xác minh đã push đủ và quyền giảng viên |

Các test hiện có kiểm tra pipeline cơ bản, calculator, budget guard, citation, multi-hop grading, HTTP boundary, lựa chọn retrieval và luồng tóm tắt. Cần bổ sung đánh giá thực cho tiếng Việt, câu hỏi tổng hợp, bảng/ảnh trong bản tóm tắt, citation hỗ trợ từng khẳng định và các lựa chọn method/top-k nếu muốn công bố chất lượng bản web. Test mock không thay model benchmark. Luồng tóm tắt mới chỉ đọc native text, đã ghi rõ hạn chế với nội dung chỉ có trong ảnh.

Nếu chỉnh semantic pipeline sau khi đã xem test, cần một test mới chốt trước lần đánh giá tiếp theo; không chọn lại câu đúng từ các lượt cũ để đạt 90%. Không sửa nhãn thành đã xác nhận khi người học chưa kiểm tra.
