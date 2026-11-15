# Checklist nghiệm thu người dùng

Dùng thay cho bước review chéo giữa các thành viên. Người kiểm tra tự thao tác và ghi kết quả; không cần đọc code. Ghi **Đạt**, **Không đạt** (kèm mô tả và ảnh) hoặc **Bỏ qua** (kèm lý do).

**Chuẩn bị:**
- Chạy Ollama, backend (`python -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000`) và frontend (`npm run dev --prefix frontend`).
- Có một tài khoản admin, một tài khoản agent và một email thật để đăng ký khách.
- Mở khách và nhân viên ở hai trình duyệt khác nhau (hoặc một cửa sổ ẩn danh), vì cookie dùng chung origin.

Người kiểm tra: ............ Ngày: ............ Commit/tag: ............

## A. Khách hàng trên Website (`http://localhost:5173/chat`)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| A1 | Đăng ký bằng email thật, nhập mã 6 số nhận qua email | Vào được màn hình chat | |
| A2 | Nhập sai mã 5 lần ở một lần đăng ký khác | Báo mã bị hủy, yêu cầu gửi mã mới | |
| A3 | Hỏi "Mua điện thoại mới bị lỗi phần cứng trong 30 ngày có được đổi không?" | Trả lời có trích nguồn (tên file, dòng) và nội dung đúng với nguồn | |
| A4 | Hỏi tiếp "Còn laptop thì sao?" | Hiểu là câu nối tiếp, trả lời về laptop, có nguồn | |
| A5 | Hỏi một câu không có trong chính sách, ví dụ "Shop có bán xe máy không?" | Từ chối, gợi ý gặp nhân viên; không bịa | |
| A6 | Hỏi "Hoàn tiền về thẻ mất mấy ngày?" | AI trả lời (5 đến 7 ngày...), không chuyển nhân viên | |
| A7 | Nhắn "cảm ơn" | Lời cảm ơn cố định, không lặp lại câu trả lời cũ | |
| A8 | Bấm một câu gợi ý trong Hỏi đáp | Gửi câu hỏi và nhận trả lời có nguồn | |
| A9 | Tắt mạng (hoặc tắt backend) rồi gửi tin | Báo lỗi tiếng Việt, nội dung đang soạn vẫn còn | |
| A10 | Mở Lịch sử, Tài khoản, rồi Đăng xuất | Thấy hội thoại cũ; đăng xuất quay về màn hình đăng nhập | |

## B. Chuyển nhân viên và Inbox (`http://localhost:5173/`, tài khoản agent)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| B1 | Khách nhắn "Tôi muốn khiếu nại vì giao hàng quá chậm" | Khách thấy thông báo đã chuyển nhân viên; AI không trả lời tiếp | |
| B2 | Agent mở Inbox | Hội thoại hiện ở trạng thái Chờ nhân viên, có ticket ưu tiên và hạn SLA | |
| B3 | Agent bấm Tiếp nhận rồi trả lời | Khách nhận được tin trong vòng vài giây | |
| B4 | Agent nhập ghi chú nội bộ, chọn Giải quyết | Ticket Đã giải quyết; khách không thấy ghi chú nội bộ | |
| B5 | Khách hỏi tra đơn bằng một mã đơn không thuộc mình | Không lộ thông tin đơn, chuyển nhân viên | |
| B6 | Agent mở Kho tri thức | Xem được tài liệu; không có nút xóa/lập chỉ mục lại (chỉ admin) | |

## C. Quản trị (tài khoản admin)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| C1 | Kho tri thức: tải một file TXT/Markdown nhỏ | Trạng thái chuyển sang indexed; hỏi thử trả lời theo file mới | |
| C2 | Xóa file vừa tải | Câu hỏi về nội dung đó không còn được trả lời từ file này | |
| C3 | Cài đặt: xem danh sách nhân viên | Thấy admin và agent | |
| C4 | Tổng quan và Phân tích | Số liệu hội thoại/SLA hiển thị, không lỗi | |

## D. Telegram (nếu bật `TELEGRAM_ENABLED`)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| D1 | Nhắn bot một câu chính sách | Trả lời có dòng "Nguồn:", không có dấu `**` | |
| D2 | Nhắn "tôi cần gặp nhân viên" | Hội thoại hiện trong Inbox kênh Telegram | |
| D3 | Agent trả lời và Đóng hội thoại | Điện thoại nhận tin trả lời và thông báo đóng | |

## E. Kết luận

- Số mục Đạt / tổng: ...... / 23
- Lỗi chặn demo (nếu có): ...........................................
- Đồng ý gắn tag phiên bản nộp: ☐ Có ☐ Không

Ghi chú: nhóm còn một quyết định nghiệp vụ chưa làm — khách quay lại hội thoại đang chờ nhân viên thì không nhận được phản hồi nào (xem [nghiệm thu 15/11](ACCEPTANCE_20261115.md#ghi-nhận-chưa-sửa)).
