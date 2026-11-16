# Kịch bản demo Day07

1. Giới thiệu: giữ dữ liệu Day06 (World Bank, 80 trang/212 chunk), thêm agent
   quyết định tìm kiếm, trả lời có nguồn và từ chối khi tài liệu không đủ.
2. Mở `configs/experiments.json`: TF-IDF lexical, MiniLM + pgvector dense, hybrid
   RRF. Cấu hình cải thiện cuối tăng context 1,600 → 6,000 ký tự, top-3 → top-6,
   số lượt tìm 1 → 3. Nêu rõ cấu hình cuối đổi nhiều tham số cùng lúc, chưa tách
   được tác động riêng của từng tham số.
3. Demo câu có evidence: hỏi về vulnerability scans ngoài lịch định kỳ.
   Đọc câu trả lời, mở trace thấy query tiếng Anh, chunk trang 45 và citation.
4. Demo thiếu evidence: hỏi số vụ ransomware Los Angeles năm 2035. Agent phải
   tìm kiếm rồi từ chối; không dùng kiến thức ngoài tài liệu để đoán.
5. Trình bày lỗi thật: q24 có đúng trang nhưng baseline chỉ giữ đoạn đầu, thiếu
   phần governance/risk management/capacity-building/operational processes.
   Context lớn giúp giữ đoạn tiếp theo; xem trace dev của baseline và hybrid.
6. Mở báo cáo và kết quả cuối: tách ranking, context, câu trả lời và citation.
   Evidence Hit không tự chứng minh câu trả lời đúng. Nhãn Codex hỗ trợ cần học
   viên xác nhận. Không tuyên bố bonus đa phương thức từ PDF 107 trang.

Lệnh và cách chạy trong [runbook](DAY07_RUNBOOK.md). Các trace demo được lưu
trong `results/demo-*.json` khi chạy lệnh; không trình bày trace giả như model thật.
