# Các trang quản lý và báo cáo

Ngày 18/09/2026, năm mục menu Tổng quan, Khách hàng, Đơn hàng, Phân tích và Cài đặt đã nối API thật. Màu xanh đậm/teal, nền sáng, bảng và khung chi tiết dựa trên mockup người dùng cung cấp; giữ Inbox, Kho tri thức và widget hiện có.

## Chức năng và quyền

| Trang | Nhân viên và admin | Riêng admin |
|---|---|---|
| Tổng quan | Tổng số khách/đơn/hội thoại/tài liệu, trạng thái hiện tại, liên kết thao tác | Không có quyền bổ sung |
| Khách hàng | Tìm tên/email/mã, phân trang, xem tối đa 20 hội thoại gần nhất, mở Inbox và lọc đơn của khách | Tạo và sửa tên/email |
| Đơn hàng | Tìm mã đơn/tên khách/vận đơn, lọc trạng thái/khách, xem thông tin | Tạo đơn nội bộ, sửa trạng thái/vận đơn; không đổi chủ đơn |
| Phân tích | Khoảng 7/30/90 ngày, hội thoại theo ngày/kênh, số tin/ticket, SLA phản hồi đầu | Không có quyền bổ sung |
| Cài đặt | Xem tài khoản, tự đổi mật khẩu, xem kênh và chính sách SLA | Danh sách tài khoản và cấp tài khoản mới qua API hiện có |

Danh sách mặc định 25 bản ghi, tối đa 100 qua API. Các thao tác ghi kiểm tra cookie và CSRF; backend chặn agent tạo/sửa khách/đơn hoặc đọc danh sách tài khoản. Không gửi password_hash, token phiên hoặc cấu hình bí mật. Mật khẩu mới 12–128 ký tự, phải khác mật khẩu cũ; xác thực mật khẩu hiện tại và thu hồi mọi phiên của chính người đổi trong cùng transaction. Tài khoản khác giữ phiên. Đăng nhập kiểm tra lại hash/active dưới khóa ghi sau xác thực để mật khẩu cũ đang được xử lý không cấp phiên muộn.

Sửa khách/đơn phải gửi expected chứa giá trị cũ; UPDATE có điều kiện trả 409 nếu bản ghi đã đổi/mất, tránh ghi đè. UI giữ form khi lỗi để người dùng đối chiếu và chủ động tải lại. ID khách do server sinh; mã đơn phải khớp DH/ORD, trùng mã trả 409, khách không tồn tại trả 404. Không có xóa khách/đơn hoặc gộp danh tính. Tên/email không phải bằng chứng xác minh khách widget.

## Cách đọc số liệu

Tổng quan đếm toàn bộ dữ liệu và trạng thái hiện tại. Phần thống kê theo kỳ dùng từ 00:00 UTC của ngày đầu đến lúc gọi API, gồm ngày hiện tại. Hội thoại theo ngày/kênh dựa trên thời điểm tạo hội thoại; tin nhắn đếm riêng theo thời điểm tạo tin. Ticket thuộc kỳ dựa trên thời điểm tạo ticket, dù hội thoại bắt đầu từ trước kỳ.

Tỷ lệ đúng hạn = ticket phản hồi đúng hạn / ticket đã có phản hồi nhân viên. Ticket đang chờ trong hạn, quá hạn và kết thúc chưa phản hồi được tách riêng; không đưa vào mẫu số này. Thời gian trung bình tính từ tạo ticket đến phản hồi đầu của các ticket đã được phản hồi. Khi chưa có mẫu, API trả null, UI hiện Chưa có. Ticket đã kết thúc dùng first_response_at đã chốt; lượt hỗ trợ sau không sửa số liệu lịch sử. Chỉ số này không phải chất lượng RAG hoặc tỷ lệ giải quyết tự động.

Số liệu tải khi mở trang, đổi bộ lọc hoặc nhấn Làm mới. Chỉ Inbox/widget giữ polling 3 giây. SLA vẫn cố định 24/7, chưa chỉnh trong Cài đặt. Cài đặt hiển thị trạng thái worker Telegram và chi tiết lỗi đã lọc bí mật; mặc định Chưa kết nối. Cấu hình ngoài UI theo TELEGRAM.md, chưa kiểm chứng bot thật. SLA Telegram dùng thời điểm API Telegram xác nhận gửi. Đơn nội bộ là dữ liệu mô phỏng phục vụ đồ án, chưa tích hợp vận chuyển/thanh toán, chưa có sản phẩm/giá trị đơn. Chưa có reset mật khẩu người khác, khóa tài khoản qua UI, audit thay đổi quản trị hoặc tổng hợp phù hợp dữ liệu lớn.

## Kiểm chứng

- 66 unittest đạt trong 23,627 giây; bảy ca mới bao phủ auth/role/CSRF, dữ liệu riêng tư, phân trang/tìm ký tự %, validation, xung đột, bất biến chủ đơn, mẫu số SLA/kỳ thống kê/snapshot, dữ liệu trống và thu hồi phiên khi đổi mật khẩu và tranh chấp với đăng nhập đang xử lý.
- Vite build đạt. QA trình duyệt trên bản build với SQLite/vector riêng: tìm kiếm/phân trang, tạo/sửa khách và đơn, mở đúng hội thoại, lọc đơn theo khách, báo cáo 30 ngày, tạo nhân viên rồi đăng nhập, ẩn quyền ghi cho agent, đổi mật khẩu và đăng nhập lại bằng mật khẩu mới.
- Desktop và mobile 390px đã kiểm tra trực quan. Mobile đủ bảy mục điều hướng, bảng cuộn ngang trong khung, chi tiết đưa lên trước bảng và nhận focus. Không tràn ngang toàn trang, không lỗi console quan sát được.
- Không đổi pipeline/model/prompt RAG hoặc dữ liệu người dùng; không chạy lại benchmark M3. M3 và nghiệm thu người dùng vẫn chờ duyệt.

Chạy kiểm thử: `python -m unittest discover -s app/tests -v`; build: `npm --prefix frontend run build`. Mở Cài đặt bằng admin để tạo nhân viên, sau đó dùng cửa sổ ẩn danh kiểm tra quyền agent.

## Cấp quyền tra đơn ngày 21/09/2026

Chi tiết đơn của admin có xác nhận đã kiểm tra người nhận, nút Cấp mã mới và Thu hồi quyền. Mã mới thay toàn bộ quyền widget cũ của đơn, hết hạn sau 15 phút và chỉ hiển thị lúc cấp. Staff không có điều khiển này; backend cũng kiểm tra quyền admin và CSRF. Không gửi mã vào chính hội thoại chưa xác minh. Xem [ORDER_ACCESS.md](ORDER_ACCESS.md) về phạm vi và demo.
