# Nâng cấp thao tác giao diện — 09/10/2026

## Phạm vi

- Inbox hiển thị tin cuối (tối đa 160 ký tự), người gửi, thời điểm hoạt động gần nhất; sắp xếp hoạt động mới trước rồi ID hội thoại để phân trang xác định. Hội thoại chưa có tin dùng thời điểm tạo.
- Bộ đếm chỉ tính **tin khách chưa đọc của nhân viên đang đăng nhập**. Bảng `conversation_reads` lưu cặp thời gian/ID tin đã xem; API GET không đánh dấu đã đọc. POST `/api/v1/inbox/conversations/{id}/read` nhận đúng `message_id`, kiểm tra tin thuộc hội thoại, yêu cầu staff + CSRF, không nhận `user_id` từ client. Ghi tuần tự theo khóa hội thoại, cursor không lùi khi có request cũ hoặc đồng thời.
- Frontend chỉ xác nhận đọc trang tin mới nhất khi tab hiện, vùng chat hiện và cuộn sát cuối. Không đánh dấu khi chỉ xem danh sách mobile, lịch sử cũ, hoặc hồ sơ đang che chat trên màn hình hẹp. Chỉ xác nhận ID đã render, không tự đánh dấu tin đến sau đó. Lỗi lưu trạng thái được báo và thử lại; không tô đã đọc giả. Nhấn “Về tin mới nhất” để tới cuối mà không tự kéo người đang đọc lịch sử.
- Mobile đang mở chat ẩn thanh điều hướng tổng và tiêu đề lặp, giữ nút về danh sách. SLA chi tiết nằm trong hồ sơ. Chiều cao Inbox theo visual viewport; ô nhập chữ 16 px, có safe-area và giữ bản nháp khi đổi hội thoại/giao diện.
- Kho tri thức có ba tab thực, hỗ trợ phím trái/phải/Home/End; lọc theo tên và trạng thái, thông báo không có kết quả, nút xóa lọc. Agent không có tab tải tài liệu. Tệp đã chọn giữ khi lỗi, chỉ reset sau tải và refresh danh sách thành công.
- Thử hỏi AI tách “Cần làm rõ câu hỏi”, “Chưa đủ bằng chứng”, “Có trích nguồn — cần đối chiếu” và lỗi xử lý. Giữ câu hỏi khi lỗi, thử lại qua nút, thông báo chờ sau 15 giây, không dựng phần trăm tiến độ. Hủy nhận phản hồi cũ khi rời trang/đổi tài liệu; không khẳng định đã hủy suy luận phía server.
- Nguồn đóng mặc định, có tên/trang, nhãn riêng cho quote và toàn đoạn. Chỉ đánh dấu đoạn khớp nguyên văn sau chuẩn hóa khoảng trắng bằng React text/mark, không render HTML từ tài liệu. Dùng cả document/chunk/version khi nhận phản hồi; lỗi nguồn cũ hoặc đã xóa vẫn hiển thị và có thử lại.
- Tổng quan đưa “Cần xử lý hiện tại” lên trên thống kê: chờ tiếp nhận, quá hạn, đang phụ trách. Số liệu lấy API thật; khi chưa tải không hiển thị số 0 giả. Nút mở Inbox với đúng bộ lọc. Hàng chờ không bị hiểu nhầm là thống kê 7/30/90 ngày.

## Dữ liệu và vận hành

Schema **v10** thêm bảng trạng thái đọc, không sửa nội dung hội thoại cũ. Trước triển khai thật, sao lưu offline theo `OPERATIONS.md`; không hạ code về bản chỉ nhận v9. Backend tự migrate khi khởi động. Readiness yêu cầu v10; backup hỗ trợ v7–v10, khôi phục giữ trạng thái đọc và vẫn thu hồi các phiên/token như trước.

Lịch sử trước khi có cursor được coi là chưa đọc, không tự suy đoán nhân viên đã xem. Không gửi read receipt cho khách. Bộ đếm phản ánh phần mềm đã xác nhận vùng tin hiển thị, không chứng minh người dùng đã đọc hiểu. Chưa có thao tác “đánh dấu chưa đọc”.

Không thêm dependency, không đổi pipeline/model/prompt RAG, không gửi Telegram/email thật. Phần tải danh sách tài liệu vẫn là API hiện có; lọc tên/trạng thái ở frontend phù hợp quy mô đồ án. Truy vấn SLA/hàng chờ và sắp xếp hoạt động chưa được đo tải lớn.

## Kiểm chứng

Kết quả cuối: **221 kiểm thử backend đạt** (165,357 giây), trong đó 33 kiểm thử Inbox/xác thực và 16 kiểm thử backup/readiness đã chạy riêng. Frontend production build đạt; không thêm dependency. `git diff --check` không có lỗi khoảng trắng.

Chạy từ gốc repo:

```powershell
python -m unittest app.tests.test_inbox app.tests.test_auth_handoff
python -m unittest app.tests.test_backup app.tests.test_serving
python -m unittest discover -s app/tests
npm --prefix frontend run build
```

Test bổ sung bao phủ preview và hoạt động cuối, không ghi đọc qua GET, tách nhân viên, lưu bền cursor, thời gian trùng, request cũ, tin đến giữa đọc và xác nhận, ID tin khác hội thoại, CSRF, user_id giả, ghi đồng thời, migration lặp và backup/restore giữ trạng thái đọc.

QA trình duyệt dùng server/DB tạm với API thật cho đăng nhập, Inbox, trạng thái đọc, danh sách tài liệu, nguồn và dashboard. Phản hồi RAG và trạng thái model được giả lập riêng để kiểm tra UI; không dùng QA này làm bằng chứng chất lượng model.

- Đã kiểm tra preview, dấu chưa đọc, trạng thái đọc còn sau reload, bản nháp còn khi chuyển màn hình, nút về tin mới, hồ sơ/SLA đóng mở, sáng/tối.
- Đã kiểm tra lọc tài liệu lỗi, không có kết quả, xóa lọc, chuyển tab bằng End, hỏi làm rõ/thiếu nguồn/lỗi dịch vụ, giữ câu hỏi và trả lời có nguồn có đoạn đánh dấu.
- Dashboard mở đúng “Của tôi” và “Quá hạn”; phân biệt số hội thoại hiện tại với ticket trong kỳ.
- Không tràn ngang ở các viewport 320×700, 390×500, 390×844, 768×900, 1366×900. Ô nhập nằm trong viewport; riêng 390×500 còn vùng tin 140 px. Đây là mô phỏng viewport thấp, **chưa thử bàn phím trên điện thoại vật lý**.
- Không thấy lỗi console trong phiên QA. Ảnh và số đo cục bộ: `output/ui-upgrade/`. Dữ liệu QA không đưa vào DB thật.

Giới hạn nghiệm thu: chưa chạy audit khả năng truy cập toàn diện, kiểm thử tải lớn hoặc RAG thật trong lượt giao diện này. Chưa tự đánh dấu M3/M6/M7 hoàn tất.
