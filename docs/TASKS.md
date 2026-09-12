# Công việc

## Đang làm

- [ ] Chốt mô hình dữ liệu nền tảng: User, Customer, Conversation, Message, Ticket, Order, KnowledgeDocument.
- [x] Khởi tạo FastAPI và cấu hình môi trường Windows.

## Tiếp theo

- [ ] Tạo migrations và schema cơ bản.
- [ ] Xây API health và API hội thoại tối thiểu.
- [x] Xây ingestion PDF/DOCX.
- [x] Xây chunking, metadata và vector search local.
- [x] Xây RAG query có citation và từ chối khi thiếu bằng chứng.
- [x] Phân tích cảm xúc tối thiểu và tự động tạo handoff ticket.
- [x] Order Tool có kiểm tra quyền truy cập theo khách hàng.
- [x] Dữ liệu demo đơn hàng và endpoint seed/reset tối thiểu.
- [x] Orchestration endpoint xử lý tin nhắn: RAG, Order Tool và handoff.
- [x] API Unified Inbox: danh sách, lọc và chi tiết hội thoại/ticket.
- [ ] Xây order tool và handoff.
- [ ] Xây widget và inbox.

## Unified Inbox - 12/09/2026

- [x] Nối danh sách và chi tiết hội thoại với API thật; chọn đúng conversation ID.
- [x] Hiển thị tên/email khách hàng, tin nhắn theo thời gian, người gửi, trạng thái và ticket.
- [x] Lọc trạng thái/ưu tiên, tìm khách hàng/kênh và làm mới danh sách.
- [x] Trạng thái tải/lỗi/rỗng và thử lại; hủy request cũ khi chuyển hội thoại; bỏ dữ liệu mẫu tự động.
- [x] Proxy Vite cho backend local; sửa HTTP 404; kiểm tra backend và giao diện desktop/mobile.
- [ ] Tiếp theo: xác thực/phân quyền nhân viên, tiếp nhận ticket và gửi tin nhắn nhân viên; AI dừng khi người thật tiếp quản.
- [ ] Sau khi hoàn thành luồng tiếp nhận và trả lời xuyên suốt: cập nhật mốc Unified Inbox/handoff trong DeCuong.md và báo cáo Word.

Inbox hiện chỉ đọc. Chưa nghiệm thu toàn bộ mốc widget/inbox; chưa có số liệu SLA, đơn hàng hoặc nhân viên đăng nhập để hiển thị như dữ liệu thật.
