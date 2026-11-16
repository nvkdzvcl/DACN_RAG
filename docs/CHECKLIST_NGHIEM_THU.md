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
| A1 | Đăng ký bằng email thật, nhập mã 6 số nhận qua email | Vào được màn hình chat |Đạt |
| A2 | Nhập sai mã 5 lần ở một lần đăng ký khác | Báo mã bị hủy, yêu cầu gửi mã mới |Chưa đạt. Nhập sai bao nhiêu lần vẫn không thấy hiện mã bị hủy, sau > 5 lần nhập, lần nhập đúng mã sau đó vẫn hiện "Mã xác minh không đúng hoặc đã hết hạn. Bạn cần nhập đúng mã xác minh để hoàn tất đăng ký tài khoản. Nhưng reload lại thì thấy đã đăng nhập vào tài khoản đang đăng ký đó - Lỗi nghiêm trọng"|
| A3 | Hỏi "Mua điện thoại mới bị lỗi phần cứng trong 30 ngày có được đổi không?" | Trả lời có trích nguồn (tên file, dòng) và nội dung đúng với nguồn |Đạt |
| A4 | Hỏi tiếp "Còn laptop thì sao?" | Hiểu là câu nối tiếp, trả lời về laptop, có nguồn |Phân vân, cần xem xét lại - trả lời tương tự ở A2, nhưng cũng chưa sai lắm |
| A5 | Hỏi một câu không có trong chính sách, ví dụ "Shop có bán xe máy không?" | Từ chối, gợi ý gặp nhân viên; không bịa |Đạt |
| A6 | Hỏi "Hoàn tiền về thẻ mất mấy ngày?" | AI trả lời (5 đến 7 ngày...), không chuyển nhân viên |Chưa đạt - câu trả lời của AI "Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên." |
| A7 | Nhắn "cảm ơn" | Lời cảm ơn cố định, không lặp lại câu trả lời cũ |Đạt |
| A8 | Bấm một câu gợi ý trong Hỏi đáp | Gửi câu hỏi và nhận trả lời có nguồn |Đạt |
| A9 | Tắt mạng (hoặc tắt backend) rồi gửi tin | Báo lỗi tiếng Việt, nội dung đang soạn vẫn còn |Đạt |
| A10 | Mở Lịch sử, Tài khoản, rồi Đăng xuất | Thấy hội thoại cũ; đăng xuất quay về màn hình đăng nhập |Đạt |
Lỗi nghiêm trọng phát hiện ở phần đăng ký tài khoản là chưa nhập mã xác thực nhưng reload trang thì đã đăng nhập vào được
## B. Chuyển nhân viên và Inbox (`http://localhost:5173/`, tài khoản agent)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| B1 | Khách nhắn "Tôi muốn khiếu nại vì giao hàng quá chậm" | Khách thấy thông báo đã chuyển nhân viên; AI không trả lời tiếp |Đạt |
| B2 | Agent mở Inbox | Hội thoại hiện ở trạng thái Chờ nhân viên, có ticket ưu tiên và hạn SLA |Đạt |
| B3 | Agent bấm Tiếp nhận rồi trả lời | Khách nhận được tin trong vòng vài giây |Đạt |
| B4 | Agent nhập ghi chú nội bộ, chọn Giải quyết | Ticket Đã giải quyết; khách không thấy ghi chú nội bộ |Đạt |
| B5 | Khách hỏi tra đơn bằng một mã đơn không thuộc mình | Không lộ thông tin đơn, chuyển nhân viên |Đạt |
| B6 | Agent mở Kho tri thức | Xem được tài liệu; không có nút xóa/lập chỉ mục lại (chỉ admin) |Đạt - nhưng cần làm giao diện tốt hơn. |

## C. Quản trị (tài khoản admin)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| C1 | Kho tri thức: tải một file TXT/Markdown nhỏ | Trạng thái chuyển sang indexed; hỏi thử trả lời theo file mới |Tạm đạt 2/3 câu test |
| C2 | Xóa file vừa tải | Câu hỏi về nội dung đó không còn được trả lời từ file này |Đạt |
| C3 | Cài đặt: xem danh sách nhân viên | Thấy admin và agent |Đạt |
| C4 | Tổng quan và Phân tích | Số liệu hội thoại/SLA hiển thị, không lỗi |Đạt |

## D. Telegram (nếu bật `TELEGRAM_ENABLED`)

| # | Thao tác | Kỳ vọng | Kết quả |
|---|---|---|---|
| D1 | Nhắn bot một câu chính sách | Trả lời có dòng "Nguồn:", không có dấu `**` |Đạt |
| D2 | Nhắn "tôi cần gặp nhân viên" | Hội thoại hiện trong Inbox kênh Telegram |Đạt |
| D3 | Agent trả lời và Đóng hội thoại | Điện thoại nhận tin trả lời và thông báo đóng |Đạt |

## E. Kết luận

- Số mục Đạt / tổng: 20 / 23
- Lỗi chặn demo (nếu có): ...........................................
- Đồng ý gắn tag phiên bản nộp: ☐ Có ☐ Không

Ghi chú: nhóm còn một quyết định nghiệp vụ chưa làm — khách quay lại hội thoại đang chờ nhân viên thì không nhận được phản hồi nào (xem [nghiệm thu 15/11](ACCEPTANCE_20261115.md#ghi-nhận-chưa-sửa)).

## F. Xử lý sau nghiệm thu (16/11/2026)

| Mục | Nguyên nhân | Xử lý |
|---|---|---|
| A2 (lỗi nghiêm trọng) | `/register` cấp phiên đăng nhập ngay, bước nhập mã chỉ là màn hình frontend; tải lại trang là vào được chat dù chưa xác minh. Cơ chế hủy mã sau 5 lần sai vẫn chạy (DB: mã `used`, tài khoản chưa xác minh), nhưng thông báo hủy chỉ hiện ở lần sai thứ 5 | Backend chặn mọi API trò chuyện (gửi tin, gặp nhân viên, chat mới, tra đơn, lịch sử) với tài khoản chưa xác minh (403). Tải lại trang hoặc đăng nhập tài khoản chưa xác minh đều quay về màn hình nhập mã, có nút "Dùng tài khoản khác". Mọi lần nhập sau khi mã bị hủy/hết hạn đều báo rõ cần gửi lại mã. Có test backend và kiểm tra giao diện |
| A4 | Dòng chính sách đổi trả 30 ngày áp dụng chung cho điện thoại, máy tính bảng, laptop, PC; trả lời giống A3 là đúng | Không sửa |
| A6 | Model hiểu "thẻ mất mấy ngày" là "thẻ bị mất". Truy hồi đúng (nguồn đứng đầu, điểm 0,59); cách hỏi "hoàn tiền về thẻ thì mất mấy ngày?" hoặc "bao lâu thì tiền được hoàn về thẻ?" được trả lời đúng | **Ghi nhận là giới hạn của qwen3:4b, không sửa.** Đã thử ba hướng tổng quát, mỗi câu chạy 3 lần: (1) thêm quy tắc đọc "mất + khoảng thời gian" vào prompt chọn nguồn và kiểm định: vẫn từ chối 6/6, và câu "thẻ thì mất mấy ngày" vốn đúng có 1/3 lần thành "nguồn mâu thuẫn"; (2) diễn đạt lại dòng chính sách thành "thẻ hoặc ví đã dùng để thanh toán": "thẻ mất bao lâu" đúng 3/3 nhưng "thẻ mất mấy ngày" vẫn từ chối 3/3, "ví mất mấy ngày" hỏi lại 2/3; (3) bước viết lại câu hỏi giữ nguyên câu. Không giữ thay đổi nào nên không cần đo lại. Hệ thống vẫn an toàn (từ chối, không trả lời sai) |
| C1 | Câu không đạt: "Vệ sinh máy mất bao lâu?" (08:09, sau câu hỏi số lần vệ sinh). Truy hồi đúng: dòng "thời gian thực hiện" đứng đầu, điểm 0,665. Chạy lại toàn bộ pipeline với đúng nguồn và lịch sử: trả lời đúng 2/3, lần còn lại bước chọn nguồn trả "không có trong nguồn" | Ghi nhận là dao động của model (eval đo được ±2–3 câu mỗi bộ); hệ thống từ chối chứ không trả lời sai. Không sửa |
| B6 | Danh sách tài liệu chưa phân trang; "Xem nội dung" hiện ở cuối trang nên phải cuộn xuống mới thấy | Phân trang 10 tài liệu/trang (tìm kiếm, lọc quay về trang 1). Nội dung mở ngay dưới tài liệu được chọn, tự cuộn vào tầm nhìn, bấm "Ẩn nội dung" để đóng; nhãn phạm vi hiển thị in đậm thay vì dấu `**`. Kiểm tra trình duyệt (agent, desktop và mobile): 14/14 |

Ghi nhận thêm: "Tôi cần gập nhân viên" (gõ sai "gặp") không chuyển nhân viên; AI hỏi lại. Nút Gặp nhân viên vẫn dùng được. Chưa sửa vì nhận diện lỗi chính tả cần đánh giá riêng.
