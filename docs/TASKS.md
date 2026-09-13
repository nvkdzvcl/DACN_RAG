# Công việc

## Đang làm

- [x] Mô hình dữ liệu cơ bản: User, AuthSession, Customer, Conversation, Message, Ticket, Order, KnowledgeDocument.
- [x] Khởi tạo FastAPI và cấu hình môi trường Windows.

## Tiếp theo

- [x] Migration cộng thêm cột, có phiên bản và chạy lại được trên SQLite; PostgreSQL chưa kiểm chứng.
- [x] API health và API hội thoại tối thiểu; sửa schema response tạo hội thoại.
- [x] Xây ingestion PDF/DOCX.
- [x] Xây chunking, metadata và vector search local.
- [x] Xây RAG query có citation và từ chối khi thiếu bằng chứng.
- [x] Phân tích cảm xúc tối thiểu và tự động tạo handoff ticket.
- [x] Order Tool có kiểm tra quyền truy cập theo khách hàng.
- [x] Dữ liệu demo đơn hàng và endpoint seed lặp lại an toàn; chưa có reset.
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
- [x] API tiếp nhận conversation: đổi trạng thái handoff sang `assigned`, cập nhật ticket mở sang `assigned`.
- [x] API trả lời nhân viên: chỉ cho gửi khi conversation đã `assigned`; lưu `sender_type=agent`.
- [x] Test luồng tiếp nhận, trả lời và chặn trả lời trước khi tiếp nhận.
- [x] Nối nút `Tiếp nhận`, ô trả lời và nút `Gửi` vào API; khóa ô trả lời trước khi conversation được nhận.
- [x] Sau thao tác thành công, tải lại danh sách/chi tiết để phản ánh trạng thái và tin nhắn mới.
- [x] Hiển thị lỗi thao tác và giới hạn nội dung gửi 4.000 ký tự.
- [x] Xác thực/phân quyền nhân viên; thay `agent-demo` bằng ID từ phiên đăng nhập.
- [ ] Bổ sung realtime/widget.
- [x] Cập nhật DeCuong.md và phần báo cáo cho xác thực/tiếp nhận/trả lời; chưa nghiệm thu toàn bộ M4/M5.

## Xác thực và handoff có người phụ trách - 13/09/2026

- [x] Đăng nhập/đăng xuất, phiên 8 giờ trong DB; cookie HttpOnly/SameSite, header chống CSRF, giới hạn thử đăng nhập.
- [x] Vai trò admin/agent; CLI tạo tài khoản và API tạo nhân viên dành cho admin; bảo vệ API nội bộ.
- [x] Ghi người phụ trách và tác giả tin nhân viên; cập nhật có điều kiện để chỉ một nhân viên nhận được hội thoại.
- [x] Chỉ người phụ trách được trả lời; chặn nội dung trắng và giả mạo agent_id trong body.
- [x] Luồng /messages và /process dùng chung; lưu phản hồi AI/citation, dừng RAG/order tool khi chờ hoặc đã nhận handoff.
- [x] Giữ trạng thái assigned khi khách khiếu nại tiếp; không tạo ticket trùng; trích các tin gần nhất làm ngữ cảnh chuyển giao.
- [x] Bản nháp riêng từng hội thoại; đăng nhập lại khi phiên hết hạn; thông báo AI dừng và quyền phụ trách.
- [x] Kiểm tra trình duyệt: đăng nhập, tiếp nhận/gửi, giữ bản nháp, tải lại phiên, đăng xuất; desktop và mobile 390px.
- [x] 15 kiểm thử unittest đạt; frontend build đạt. Báo cáo Word ba trang đã xuất PDF bằng Word và kiểm tra ảnh bằng Poppler (renderer đóng gói thiếu LibreOffice trên Windows).

Phạm vi hiện tại: MVP local một API worker, SQLite; API khách hàng tạm là API nội bộ có xác thực, chờ widget có phiên khách riêng. Embedding vẫn là hash 256 chiều trong RAM; chưa có LLM thật, vector DB bền, SLA hay kênh xã hội thật. Tóm tắt handoff là trích đoạn, chưa phải tóm tắt bằng LLM.

Task tiếp theo: embedding ngữ nghĩa + vector DB lưu bền + LLM có trích dẫn; trước khi gọi LLM qua mạng cần tách xử lý chậm khỏi transaction và kiểm tra lại trạng thái trước khi lưu/gửi AI.
