# Nghiệm thu tích hợp toàn hệ thống (15/11/2026)

Bản kiểm tra: `main` sau khi merge PR #11–#15, cộng hai sửa nhỏ trong lượt này (dấu `**` gửi sang Telegram và tóm tắt ticket). Môi trường local Windows 11, Ollama `qwen3:4b` + `embeddinggemma:300m`, Kho tri thức là 12 file chính sách FPT Shop, SMTP Gmail và bot Telegram thật.

## Kết quả

| Hạng mục | Cách kiểm tra | Kết quả |
|---|---|---|
| Unit/integration test backend | `python -m unittest discover -s app/tests` | 245/245 đạt |
| Build frontend | `npm run build --prefix frontend` | Đạt |
| Test giao diện có sẵn | `frontend/tests/*.cjs` (Playwright, Edge) | 4/4 đạt |
| RAG với Ollama thật | `python -m app.tests.smoke_ollama` | Đạt: trả lời có nguồn, hiểu câu nối tiếp, từ chối yêu cầu bịa mã giảm giá |
| Tool tra đơn | `python -m app.tests.smoke_tools` | 7/7 ca đạt (tra đơn, đơn không thuộc khách, hủy → nhân viên, injection, câu chính sách, nhiều mã đơn) |
| Luồng API M4 | `python -m app.tests.smoke_m4` | Đạt |
| Website: khiếu nại → nhân viên → giải quyết | Playwright, khách (mobile) và agent (desktop) song song | 7/7 bước đạt (xem dưới) |
| Phân quyền và phiên | Gọi API theo từng vai trò | 23/23 đạt (xem dưới) |
| Telegram | Người dùng dự án nhắn từ điện thoại; agent trả lời từ Inbox | Đạt (xem dưới) |
| Đăng ký email thật | Giai đoạn 2, PR #14 | Đạt |

### Luồng Website (ảnh trong `docs/images/acceptance/`)

1. Khách gửi "Tôi muốn khiếu nại vì giao hàng quá chậm" → hội thoại chuyển `handoff_requested`.
2. AI không trả lời sau khi đã chuyển nhân viên.
3. Agent thấy khiếu nại trong Inbox.
4. Ticket tạo với ưu tiên Cao, có hạn SLA phản hồi đầu.
5. Agent bấm Tiếp nhận và trả lời; khách nhận được qua polling trong khoảng 16 giây.
6. Agent nhập ghi chú nội bộ và chọn Giải quyết → ticket "Đã giải quyết", "Đã phản hồi đúng hạn".
7. Ghi chú nội bộ không hiển thị cho khách.

### Phân quyền (23 mục)

- Chưa đăng nhập: Inbox, Kho tri thức, danh sách nhân viên → 401.
- Agent: xem Inbox và Kho tri thức được; danh sách nhân viên, lập chỉ mục lại/xóa tài liệu, cấp/thu hồi mã truy cập đơn → 403; POST thiếu header CSRF → 403.
- Admin: xem danh sách nhân viên được; lập chỉ mục tài liệu không tồn tại → 404 (tức là qua được kiểm tra quyền).
- Cookie khách không dùng được cho API nhân viên (401). Sau khi đăng xuất, phiên khách và phiên agent đều trả 401.

### Telegram

| Bước | Kết quả |
|---|---|
| Bot | Trạng thái `connected` (polling, chỉ chat riêng và văn bản) |
| Tin khách gửi khi hội thoại cũ (05/11) vẫn đang chờ nhân viên | Lưu vào DB, hiện trong Inbox; AI im lặng đúng thiết kế; khách không nhận được phản hồi nào |
| Agent tiếp nhận, trả lời, đóng hội thoại từ Inbox | Cả tin trả lời và thông báo đóng đều `sent`; người dùng xác nhận đã thấy trên điện thoại |
| Hỏi lại "Hoàn tiền về thẻ đã thanh toán mất mấy ngày?" | Mở hội thoại mới; AI trả lời đúng (5 đến 7 ngày, không tính thứ Bảy, Chủ nhật, lễ) sau khoảng 14 giây, có nguồn; không bị chuyển nhân viên nhờ sửa quy tắc handoff (PR #15) |
| Dấu `**` trong tin Telegram | Có trong lần gửi trên; đã sửa `outgoing_text` bỏ dấu (test mới). Kiểm tra lại sau sửa: tin AI gửi lúc 23:43 không còn dấu `**`, người dùng xác nhận trên điện thoại |
| Tin đến khi backend tắt | Bot nhận lại khi chạy lại backend; câu trả lời cho tin cũ ("kết thúc") bị bỏ qua (`stale_ai`) vì khách đã gửi câu mới, chỉ câu trả lời mới nhất được gửi |

## Lỗi tìm thấy trong lượt này và cách xử lý

| Lỗi | Xử lý |
|---|---|
| Tin Telegram chứa dấu `**` của tiền tố phạm vi | `app/telegram.py`: bỏ dấu trước khi gửi văn bản thuần; thêm test |
| Tóm tắt ticket trong Inbox hiện dấu `**` | `main.jsx`: hiển thị qua `plainText` |

## Ghi nhận, chưa sửa

- **Khách quay lại hội thoại đang chờ nhân viên không nhận được phản hồi** (ví dụ Telegram sau 10 ngày). Cân nhắc gửi lời nhắc "yêu cầu của bạn đang chờ nhân viên" hoặc tự đóng ticket quá hạn; đây là thay đổi nghiệp vụ, cần quyết định của nhóm.
- Trong lượt test, merge PR #14 kèm xóa nhánh đã làm GitHub tự đóng PR #15 (nhánh gốc bị xóa); đã khôi phục nhánh tạm, mở lại và merge #15. Lần sau với PR xếp chồng: không xóa nhánh gốc trước khi chuyển base.
- Khách chỉ nhắn câu kết thúc như "kết thúc" (không kèm câu hỏi) thì AI có thể lặp lại câu trả lời trước, vì câu được viết lại theo lịch sử hội thoại. Xem xét ở giai đoạn 5.
- Dữ liệu test còn trong DB local: khách `e2e-test@example.com` và các hội thoại "Khach E2E", tài khoản `e2e-admin` và `e2e-agent`. Cần dọn trước khi demo.
