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


## Bổ sung thao tác và điều hướng — 09/10/2026

- Inbox thêm **Chỉ tin khách chưa đọc**, lọc SQL theo nhân viên trước phân trang. Khi mở danh sách chưa đọc bằng URL, không tự chọn/đánh dấu hội thoại đầu tiên. Sau xác nhận đọc, hội thoại rời danh sách nhưng khung chat/bản nháp đang mở vẫn được giữ; có hướng dẫn ngay dưới bộ lọc. Không thêm thao tác đánh dấu chưa đọc.
- Gộp trạng thái/kênh vào một dòng, tăng chữ preview; danh sách chỉ nhấn mạnh SLA trễ/quá hạn. SLA đầy đủ vẫn có ở khung chat/hồ sơ, không thay cách tính SLA.
- URL lưu trang, hội thoại, bộ lọc và phân trang Inbox; lưu tìm kiếm/trạng thái/phân trang/bản ghi khách hàng và đơn hàng. Back/Forward khôi phục trạng thái. Ví dụ `/?page=inbox&selectedId=ID&mobileConversation=1&unreadOnly=1`. Giá trị URL được kiểm tra danh sách hợp lệ, giới hạn chiều dài và khoảng số; API tiếp tục kiểm tra quyền. Bộ lọc dùng replaceState để không tạo lịch sử theo mỗi ký tự; đổi trang/chọn hội thoại dùng pushState. Không lưu bản nháp, mật khẩu hoặc mã truy cập vào URL/storage.
- Bản nháp và ghi chú Inbox giữ trong phiên khi đổi trang/Back; beforeunload cảnh báo khi còn nội dung chưa gửi. Trình duyệt có thể không hiện cảnh báo trên một số thiết bị; tải lại/đóng trang vẫn không phải lưu bền bản nháp.
- Bảng khách/đơn dùng CSS thành thẻ có nhãn trên mobile, giữ bảng desktop và ngữ nghĩa table/row/cell cho công cụ hỗ trợ. Bộ lọc xếp dọc để ô tìm/trạng thái không bị ép hẹp. Không thêm dependency.
- Sáng/tối dùng chung giữa admin, đăng nhập, khách và widget; theo hệ thống khi chưa chọn, lưu lựa chọn hiện có, đồng bộ thay đổi qua tab. Tên hiển thị thống nhất **RAG Support**. Khi storage bị chặn vẫn đổi trong phiên.
- Chat theo chiều cao/độ lệch visual viewport, lắng nghe resize/scroll; ô nhập mobile 16 px và có safe-area. Sửa ResizeObserver của ô nhập bằng requestAnimationFrame để tránh đổi kích thước ngay trong vòng quan sát.

Kiểm chứng bổ sung: unittest bao phủ lọc trước phân trang, phối hợp search/trạng thái/ưu tiên/SLA, tách nhân viên, tin AI không tính chưa đọc, tin đến cùng thời gian sau cursor và HTTP 401/422. Kiểm thử trình duyệt nằm ở `frontend/tests/navigation.cjs`; chạy cùng `theme.cjs` và `message-input.cjs` với Playwright có sẵn qua NODE_PATH. QA dùng API giả lập trong trình duyệt; kiểm thử backend dùng DB tạm, không gửi Telegram/email hoặc gọi model thật.

QA đã kiểm tra Back, reload/bộ lọc, giữ chat/bản nháp sau đọc, cảnh báo rời trang, thẻ mobile, bảng desktop, theme đăng nhập/khách và URL sai. Viewport 320×700, 390×500, 390×844, 768×900, 1366×900 không tràn ngang trong luồng đã thử; ô nhập chat nằm trong viewport. Ảnh QA tại `output/ui-followup/`. Chưa thử bàn phím điện thoại vật lý, audit khả năng truy cập toàn diện, tải lớn hoặc RAG thật; không dùng lượt này nghiệm thu M3/M6/M7.

Kết quả cuối đợt bổ sung: **223 kiểm thử backend đạt** (141,515 giây); `message-input.cjs`, `theme.cjs`, `navigation.cjs` đạt. Frontend production build và `git diff --check` đạt. Không cộng các kết quả này vào điểm chất lượng RAG.

## Bổ sung lưu nháp và hiệu quả thao tác — 09/10/2026

- Nháp nhân viên, ghi chú hoàn tất và UUID của tin chưa xác nhận lưu bằng sessionStorage theo ID nhân viên/hội thoại. Widget lưu theo ID hội thoại từ snapshot đã xác thực; không khôi phục nháp sang danh tính/hội thoại khác. Reload hoặc hết phiên rồi đăng nhập lại cùng tài khoản/hội thoại trong tab có thể khôi phục. Hết hạn sau 24 giờ từ lần lưu cuối, tối đa 200 mục mỗi loại; kiểm tra cấu trúc, chiều dài và UUID khi đọc. Storage hỏng/bị chặn/đầy báo rõ, vẫn giữ nội dung trong bộ nhớ. Không lưu mật khẩu, token hoặc mã truy cập.
- Đăng xuất chủ động thành công xóa nháp của phạm vi hiện tại; kết thúc/chat mới xóa nháp hội thoại khách vừa kết thúc. sessionStorage không đồng bộ qua thiết bị và không cam kết giữ sau đóng tab. Phiên khách hết hạn không được dùng nháp cũ cho hội thoại mới. UUID gửi lại dùng cùng nội dung cũ; nháp mới vẫn giữ. Mỗi hội thoại giữ một lần gửi chưa xác nhận gần nhất; gửi nội dung mới thay lần chờ cũ, cần xem lịch sử trước khi gửi tiếp nếu chưa rõ kết quả.
- Khách soạn tin khi AI xử lý, nút gửi và Enter vẫn khóa tới khi xử lý xong. Phản hồi thành công chỉ xóa nội dung đã gửi nếu nháp chưa đổi. Nút gửi lại tin chưa xác nhận giữ UUID qua reload để backend chống gửi trùng; không tự gửi nháp khi khôi phục.
- POST `/inbox/conversations/{conversation_id}/unread` chỉ nhận tin khách thuộc hội thoại và dùng nhân viên từ phiên. Cursor lùi về tin khách ngay trước theo thời gian/ID, hoặc xóa cursor nếu đây là tin khách đầu. Những tin khách mới hơn vẫn chưa đọc; không đổi schema v10. UI dừng tự ghi đọc và chờ request đọc đang chạy trong cùng tab, rồi đánh dấu chưa đọc và về hàng chờ. Mở lại sẽ đánh dấu đọc theo điều kiện hiện có. Tab khác đang đọc cùng tài khoản vẫn có thể cập nhật cursor sau đó.
- Dashboard/Phân tích tự tải khi tab hiện lại hoặc cửa sổ có focus; gộp hai sự kiện gần nhau. Không polling nền liên tục. Làm mới giữ số liệu hiện có; lỗi ghi rõ số liệu có thể cũ. Thời điểm hiển thị là thời điểm cũ nhất của các lần tải thành công liên quan, không phải thời điểm sửa dữ liệu trên server. Màn sửa bản ghi không tự tải lại khi focus.
- Hồ sơ ở viewport dưới 1280 px dùng dialog native, có tên truy cập, giữ Tab/Shift+Tab bên trong, Escape đóng và trả focus. Thu hẹp desktop tự đóng sidebar hồ sơ, tránh bật modal bất ngờ. Log nhân viên thông báo phần thêm mới, tắt live khi xem lịch sử cũ. Chỉnh màu chữ avatar/người gửi/thời gian trong theme sáng để các mẫu đo đạt 4,5:1; không coi đây là audit WCAG toàn bộ.
- Widget giữ ô soạn ngoài vùng cuộn phụ trợ. Cảnh báo dài, quyền tra đơn mở rộng vẫn cuộn được bằng bàn phím; ô soạn không bị đẩy khỏi viewport thấp đã thử.

Kiểm chứng backend: **225 kiểm thử đạt** trong **146,750 giây**. Test mới bao phủ lùi cursor, thời gian trùng, tách nhân viên, ID sai/tin AI, auth/CSRF và payload giả. Log: `output/ui-productivity-backend-tests.log`.

Runner mới `frontend/tests/productivity.cjs` dùng Playwright có sẵn và API giả lập: nháp/ghi chú qua reload, tách tài khoản, hết phiên/đăng nhập lại, xóa khi đăng xuất/chat mới, UUID retry, soạn trong lúc AI xử lý, phản hồi cũ giữ nháp mới, thứ tự read/unread, focus dialog, mẫu tương phản sáng/tối, focus refresh/dashboard lỗi giữ số liệu, nháp hết hạn/storage hỏng/bị chặn và viewport 320×700, 390×500, 768×900, 1366×900. Ảnh và tỷ lệ màu: `output/ui-productivity/`.

Kết quả cuối: `productivity.cjs`, `navigation.cjs`, `theme.cjs`, `message-input.cjs` đạt; production build và `git diff --check` đạt. Đã xem ảnh hồ sơ mobile, Inbox sáng/tối và ô nhập khách khi storage lỗi.

Giới hạn: chưa thử bàn phím điện thoại vật lý, VoiceOver/NVDA thật hoặc audit khả năng truy cập toàn diện. Kiểm thử trình duyệt dùng API giả lập; không gọi model/Telegram/email thật, không dùng kết quả này nghiệm thu RAG/M3/M6/M7.
