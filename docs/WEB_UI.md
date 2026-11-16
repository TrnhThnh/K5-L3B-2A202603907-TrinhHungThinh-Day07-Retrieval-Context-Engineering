# Giao diện agent Day07

Yêu cầu “tóm tắt”, “tổng quan”, “summarize/summary/overview” tự chuyển sang luồng tổng hợp: đọc toàn bộ trang có text theo lô 14 trang, tạo ghi chú kèm đoạn trích được kiểm tra khớp text gốc, rồi tổng hợp tiếng Việt có citation. Không đòi tài liệu có sẵn abstract. Top-k không giới hạn luồng này; trace có `mode: document_summary`, `summary_coverage`, read_document_batch, summary_notes, synthesize_summary. Luồng có nhiều model call hơn Q&A và vẫn áp dụng budget guard; lỗi provider/ngân sách được báo, không biến kết quả một phần thành tóm tắt đầy đủ. Tổng hợp text chưa đảm bảo bao phủ nội dung chỉ có trong ảnh; câu trả lời ghi rõ giới hạn. Pipeline benchmark lịch sử giữ nguyên; điểm benchmark cũ không phải điểm của luồng mới.

Agent trên web trả lời và giải thích citation bằng tiếng Việt, kể cả câu hỏi tiếng Anh. Giữ nguyên số liệu, đơn vị, tên riêng và nhãn nguồn gốc để đối chiếu; search vẫn dùng tiếng Anh. Trace mới ghi `response_language: vi`. Replay giữ nguyên ngôn ngữ của kết quả lịch sử, không dịch hay sửa benchmark đã lưu.

Chạy `.\run-web.ps1` trong PowerShell tại repo, mở http://127.0.0.1:8070.
Giữ terminal mở; Ctrl+C để dừng. Script dùng Python và `.env` Day06 đã cung cấp.
Đổi đường dẫn hoặc cổng bằng `-EnvFile 'C:\path\starter\.env' -Port 8071`.
Cần PostgreSQL Day06 đang chạy, index ADVANCED_M1 và dependencies nâng cao đã cài.

- Mỗi câu hỏi là một lượt độc lập, không gửi lịch sử chat làm context.
- Tool calls hiển thị arguments, search results, context IDs, score và usage. Model call và search hiển thị dần qua polling; các event khác hoàn chỉnh khi lượt chạy kết thúc.
- Citation có số trang PDF vật lý, label, support, bbox và ảnh gốc tô vùng bằng chứng; mở được PDF/ảnh gốc.
- Thông số gồm model, retrieval, top-k, context rows, caps, thời gian agent (không gồm nạp embedding), token, chi phí provider, số call và trang đã đọc.
- Tải JSON bằng nút trong inspector. Trace thô, trace căn bbox và manifest lưu `results/web/<id>/`.
- Xem trace đã lưu là replay kết quả thật, không gọi API.
- Benchmark đầu và lượt lặp được báo riêng, giữ lỗi trong mẫu số. Không tự tính độ đúng/Hit@k/recall cho câu tự nhập khi chưa có gold. Nhãn benchmark cần sinh viên xác nhận.

Giữ nguyên file agent/retrieval đã đóng băng, dùng config selection run-05. Citation alignment đọc catalog và PDF, không đọc gold. Không tự retry khi provider lỗi. Trần $0.70/ngày áp dụng trước mỗi model call.

Server bind loopback; không phục vụ `.env` hay toàn bộ repo. POST yêu cầu session token và Host loopback, không bật CORS. Một câu tại một thời điểm. Không mở port ra Internet. Font Google Fonts có fallback hệ thống. Khóa chỉ ở backend.

Chọn **Top-k**: 3, **5**, 10, 16, 20 hoặc 30; chọn **TF-IDF**, **Dense** hoặc **Hybrid** trước khi gửi câu hỏi. Thông số được lưu trong trace của lượt web, không sửa config/benchmark đã đóng băng. Top-k là số kết quả cho mỗi search; context có thể tích lũy qua nhiều lần search và vẫn chịu giới hạn context rows.

Nút **So sánh 3 phương pháp** chạy cùng câu hỏi gốc/corpus/top-k qua cả ba retriever, không gọi LLM hoặc OpenRouter. Inspector hiển thị từng thứ hạng, trang, score, nội dung và metadata; lưu `results/web/<id>/comparison.json`. Score khác thang đo, thời gian gồm tác động cache/thứ tự chạy; không suy ra độ đúng khi chưa có gold. So sánh này chỉ đánh giá retrieval; muốn so sánh câu trả lời, chọn lần lượt từng phương pháp rồi gửi (có phí API).
