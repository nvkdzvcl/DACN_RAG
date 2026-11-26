# Rà soát giao diện (15/11/2026)

## Phạm vi và cách làm

- **Trang khách hàng** (`/chat`): đăng nhập, chat, Tra đơn, Hỏi đáp, Lịch sử, Tài khoản; Chrome/Edge desktop 1366×800 và mobile 390×844.
- **Trang nhân viên** (Tổng quan, Hội thoại/Inbox, Khách hàng, Đơn hàng, Kho tri thức, Phân tích, Cài đặt): đăng nhập bằng tài khoản test `e2e-admin` và `e2e-agent` do người dùng dự án tạo bằng `python -m app.create_user`; desktop 1366×800 và mobile 390×844.
- Script Playwright chạy trên dev server thật (frontend 5173 → backend 8000, Ollama local), giả lập lỗi bằng cách chặn hoặc thay phản hồi API: mất mạng, HTTP 429, 500, 502, hết phiên (401). Ảnh trước/sau nằm trong `docs/images/ui-review/`, kết quả từng mục trong `report.json` cùng thư mục.
- 4 test giao diện có sẵn (`frontend/tests/*.cjs`) chạy được khi có Playwright trong `NODE_PATH`: cả 4 đạt trước và sau khi sửa; 244 test backend đạt.

## Kết quả kiểm tra tự động (desktop và mobile)

| Mục | Trước | Sau |
|---|---|---|
| Không tràn ngang | Đạt | Đạt |
| Mất mạng: thông báo | **"Failed to fetch"** | "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại; nội dung đang soạn vẫn được giữ." |
| HTTP 500/502: thông báo | **"Internal Server Error"** hoặc "Không gửi được yêu cầu (HTTP 502)" | "Hệ thống đang gặp sự cố (HTTP 5xx). Vui lòng thử lại sau ít phút." |
| HTTP 429: thông báo | Đạt (thông báo tiếng Việt từ server) | Đạt |
| Lỗi giữ bản nháp | Đạt | Đạt |
| Tin gửi lỗi được giải thích, gửi lại được | Đạt | Đạt |
| Nút gửi khóa khi đang gửi | Đạt | Đạt |
| Ô nhập tự xóa sau khi gửi thành công | Đạt | Đạt |
| Hết phiên (401) về màn hình đăng nhập kèm thông báo | Đạt | Đạt |
| Lời chào trong hội thoại trống | **Lặp hai lần** | Một lần |
| Lỗi JavaScript trên trang | Không có | Không có |

## Danh sách lỗi đã sửa

| # | Lỗi | Ảnh trước / sau | Sửa |
|---|---|---|---|
| 1 | Mất mạng hiện "Failed to fetch" (tiếng Anh, khó hiểu) ở cả trang khách và trang nhân viên | `mobile-03-offline.png` | Bắt lỗi mạng trong hàm `request` của `Widget.jsx` và `main.jsx`, báo bằng tiếng Việt |
| 2 | Lỗi 5xx hiện nguyên chi tiết kỹ thuật của server | `desktop-04-http-500.png` | Lỗi 5xx luôn hiện thông báo tiếng Việt cố định; lỗi 4xx vẫn hiện thông báo của server (đã viết cho khách) |
| 3 | Lời chào lặp hai lần khi hội thoại trống | `desktop-02-chat-empty.png` | Ẩn dòng chào phụ khi đã có thẻ chào |
| 4 | Trang Hỏi đáp có nhóm "Hủy đơn hàng" và câu gợi ý không có trong Kho tri thức, bấm vào bị từ chối; nhóm chỉ gửi tên nhóm ("Bảo hành") làm câu hỏi | `desktop-09-faq.png` | Thay "Hủy đơn hàng" bằng "Trả góp"; mỗi nhóm gửi một câu hỏi đầy đủ; câu gợi ý lấy từ nội dung có trong Kho tri thức |
| 5 | Chữ trên giao diện vẫn hứa "trò chuyện ngay mà không cần tài khoản" và hướng dẫn "xác minh email trong mục Tài khoản" đã lỗi thời | `mobile-01-login.png` | Sửa chữ cho khớp: bắt buộc tài khoản, xác minh bằng mã 6 số |
| 6 | Câu trả lời AI hiện nguyên dấu `**` (tiền tố phạm vi in đậm trong tài liệu chính sách được trích nguyên văn) ở chat khách, lịch sử, Inbox, trích nguồn | `after/desktop-11-history-bold.png` | Component `RichText` chỉ chuyển `**…**` thành chữ đậm bằng phần tử React (không chèn HTML); dòng xem trước bỏ dấu |
| 7 | Inbox ghi "Chưa có email" cho khách có tài khoản | `staff-after/admin-desktop-inbox.png` | Chi tiết hội thoại lấy email tài khoản khi hồ sơ khách không có email |
| 8 | (giai đoạn 2, PR #14) Mật khẩu yếu báo lỗi ở ô "Nhập lại"; trên mobile không có nút Đăng xuất | | Đã sửa trong PR #14 |

## Trang nhân viên

| Mục | Kết quả |
|---|---|
| Phân quyền trên giao diện | Agent không thấy "Tải tài liệu", "Thêm khách hàng", "Tạo đơn hàng"; admin thấy đủ |
| Không tràn ngang, không lỗi JavaScript (admin và agent, desktop và mobile) | Đạt |
| Inbox mất mạng | Trước: "Failed to fetch"; sau: "Không kết nối được máy chủ…" kèm "Dữ liệu có thể đã cũ; đang thử kết nối lại" và nút Thử lại |
| Inbox HTTP 500 | "Yêu cầu thất bại (HTTP 500)…" kèm Thử lại (đã đạt từ trước) |
| Inbox HTTP 403 | "Tài khoản không có quyền thực hiện thao tác…" kèm Thử lại (đã đạt từ trước) |
| Thông tin liên hệ trong Inbox | Trước: "Chưa có email" với khách có tài khoản; sau: hiện email tài khoản (có test) |
| Câu trả lời AI và dòng xem trước | Trước: hiện nguyên dấu `**` của tiền tố phạm vi trong tài liệu; sau: tiền tố in đậm trong tin nhắn, bỏ dấu ở dòng xem trước |

Ảnh: `staff-before/admin-desktop-00-home.png` (dấu `**` trong dòng xem trước, "Chưa có email") và `staff-after/admin-desktop-inbox*.png`.

## Lỗi chức năng phát hiện khi rà soát giao diện

1. **AI trả lời theo chủ đề câu trước khi khách đổi chủ đề.** Hỏi liên tiếp 10 câu khác chủ đề trong một hội thoại, nhiều câu trả lời nói về câu liền trước (hỏi giờ tổng đài thì nhận câu trả lời về trả góp). Nguyên nhân do thay đổi ở PR #10: khi bước viết lại giữ nguyên câu hỏi (chủ đề mới), code ghép lịch sử vào câu hỏi. Đã sửa: model chọn câu và kiểm định luôn xét câu hiện tại (lịch sử truyền riêng); retrieval chạy cả câu hiện tại và câu kèm lịch sử rồi xen kẽ kết quả. Eval sau sửa: fptshop-v2 36/40 (trước 36/40), câu nối tiếp không đổi (fptshop 5/5, held-out 5/6, rag-policy 3/4), heldout-040 (lịch sử chứa chỉ dẫn) từ sai thành đúng. Các bộ eval cũ không bắt được lỗi này vì không có ca đổi chủ đề.
2. **Câu hỏi chính sách có chữ "hoàn tiền" hoặc "khiếu nại" bị chuyển thẳng cho nhân viên**, AI không trả lời (5/40 câu fptshop; 33/384 câu của mọi bộ eval). Theo quyết định của người dùng dự án, đã sửa: hai chữ này chỉ chuyển nhân viên khi là yêu cầu hoặc vụ việc của chính khách ("Tôi muốn khiếu nại…", "Hoàn tiền cho tôi ngay", "Sao chưa hoàn tiền?"); các từ bức xúc rõ ("tệ", "lừa đảo", "bức xúc", "gặp nhân viên", "người thật") vẫn chuyển ngay. Trên 384 câu: số câu chuyển nhân viên giảm từ 33 xuống 11, cả 22 câu đổi đều là câu hỏi thông tin. Bộ eval RAG gọi thẳng `answer_question` nên không phản ánh bước này; điểm eval trước đây cao hơn trải nghiệm thật.

## Quyết định của người dùng dự án (không sửa)

- **Bắt buộc đăng ký tài khoản để chat** (lối vào khách vãng lai đã bị gỡ ở commit `6262eb2`, 06/11/2026): giữ nguyên; README, `CUSTOMER_AUTH.md`, `DEMO.md` đã sửa cho khớp. Hàm `start` của luồng khách vãng lai vẫn còn trong `Widget.jsx` nhưng không được gọi.
- **Nút "Đăng nhập bằng Google"**: đã gỡ (18/11/2026) vì chưa triển khai. **Ô "Ghi nhớ đăng nhập"**: đã triển khai (26/11/2026), chọn thì giữ đăng nhập 30 ngày, không chọn thì phiên kết thúc khi đóng trình duyệt (tối đa 24 giờ).

## Còn lại, chưa sửa

- Thông báo kiểm tra form (email sai, mật khẩu yếu) là câu mặc định của trình duyệt, hiển thị theo ngôn ngữ trình duyệt.
- Hai nút "Tin cũ hơn / Tin mới hơn" luôn hiện kể cả khi hội thoại ngắn; nút "Vào Tin nhắn" ở cột phải hiện cả khi đang ở trang Tin nhắn.
- Khi hỏi liên tiếp nhiều câu trong một hội thoại dài, câu trả lời thay đổi giữa các lần chạy (2 lượt kiểm tra 10 câu gợi ý: lần lượt 7/10 câu có trích nguồn, với tập câu đúng/sai khác nhau). Đây là giới hạn của model 4B cộng với lịch sử dài; không chỉnh câu gợi ý thêm để tránh tinh chỉnh theo bài test.
- Độ dao động giữa các lần chạy eval khoảng ±2–3 câu mỗi bộ (5 câu không có lịch sử đổi kết quả dù không đi qua phần code đã sửa); chênh 1–2 câu giữa các phiên bản không đủ để kết luận.
- Tin nhắn gửi sang Telegram vẫn chứa dấu `**` (Telegram gửi văn bản thuần); cần kiểm tra ở bước smoke test Telegram.
- Dữ liệu test (khách `e2e-test@example.com`, các hội thoại "Khach E2E", tài khoản `e2e-admin`, `e2e-agent`) còn trong DB local; cần dọn trước khi demo.
