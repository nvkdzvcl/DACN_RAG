# Tài khoản khách hàng

Cập nhật ngày 07/10/2026. Tài khoản khách dùng email + mật khẩu tự quản lý, tách khỏi tài khoản nhân viên/admin. Đã có xác minh email và khôi phục mật khẩu qua SMTP; gửi thư thật cần cấu hình hộp thư của cửa hàng.

## Sử dụng

1. Khởi động backend để tự nâng schema lên v9. Chạy `npm --prefix frontend run build` khi phục vụ giao diện từ backend.
2. Mở `/chat`, chọn **Đăng ký**, nhập tên, email và mật khẩu 15–128 ký tự. Khách vãng lai và tài khoản chưa xác minh vẫn trò chuyện được.
3. Vào **Tài khoản → Gửi email xác minh**. Mở thư, bấm liên kết rồi nhập mật khẩu hiện tại. Liên kết có hạn 60 phút, dùng một lần; mở trang chưa tự xác minh.
4. Khi quên mật khẩu, chọn **Quên mật khẩu?** trên trang đăng nhập. Nhập email đã xác minh, mở liên kết trong thư và nhập lại mật khẩu mới hai lần. Liên kết có hạn 15 phút. Đặt lại thành công thu hồi mọi phiên và mọi liên kết cũ; đăng nhập lại bằng mật khẩu mới.
5. **Đăng xuất** chỉ thu hồi phiên hiện tại; **Tài khoản → Đổi mật khẩu** yêu cầu mật khẩu hiện tại và thu hồi tất cả phiên, liên kết của tài khoản.
6. **Lịch sử** lưu theo tài khoản trên nhiều thiết bị. **Chat mới** kết thúc hội thoại hiện tại nhưng giữ lịch sử; thiết bị đang xem chat cũ có thể đăng nhập lại để chọn hội thoại đang hoạt động mới nhất.

Email chưa xác minh không nhận được thư khôi phục. Tài khoản đã tạo trước cập nhật này cần đăng nhập và xác minh trước; không tự tin cậy email cũ. Nếu đã quên mật khẩu trước khi xác minh thì luồng email này không thể khôi phục tài khoản. Không tự ghép hồ sơ/lịch sử/đơn hàng theo email, kể cả email đã xác minh. Tra đơn vẫn cần mã truy cập riêng.

## Cấu hình SMTP

Sao chép các biến sau vào `.env` và điền thông tin SMTP do nhà cung cấp hộp thư cấp. Không dùng giá trị minh họa để gửi thật.

```dotenv
CUSTOMER_PUBLIC_URL=http://localhost:5173
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_FROM=support@example.com
SMTP_USERNAME=support@example.com
SMTP_PASSWORD=replace-with-smtp-credential
```

- `CUSTOMER_PUBLIC_URL` là origin giao diện khách, không có đường dẫn, query hoặc fragment. Khi backend phục vụ luôn giao diện, dùng origin backend. Khi triển khai, dùng HTTPS; HTTP chỉ cho localhost/127.0.0.1/::1 trong development. Mở thư trên điện thoại cần origin mà điện thoại truy cập được; localhost của máy phát triển không dùng được trên điện thoại khác.
- Dùng `SMTP_SECURITY=starttls` với cổng do nhà cung cấp chỉ định (thường 587), hoặc `ssl` (thường 465). Cấm SMTP không TLS; luôn kiểm tra chứng chỉ. USERNAME/PASSWORD phải có cùng nhau hoặc cùng để trống cho relay đã cho phép, không đưa thông tin này vào frontend.
- `SMTP_FROM` phải là địa chỉ được nhà cung cấp cho phép gửi. Dùng thông tin đăng nhập SMTP/mật khẩu ứng dụng theo hướng dẫn hộp thư, không gửi bí mật qua chat hoặc commit vào Git.
- Khởi động với `python -m uvicorn app.main:app --reload --env-file .env` để nạp cấu hình. Biến môi trường có sẵn được ưu tiên.
- Chưa cấu hình hợp lệ: giao diện báo gửi email chưa sẵn sàng; đăng nhập, đăng ký và đổi mật khẩu hiện tại vẫn dùng được. `email-status` chỉ kiểm tra cấu hình, không chứng minh kết nối SMTP hay thư đã tới hộp thư.
- Không thêm dịch vụ xác thực trả phí hoặc dependency mới. Chi phí và hạn mức gửi thư phụ thuộc hộp thư SMTP được chọn.

## Vận hành và giới hạn

API tiếp nhận yêu cầu gửi bằng HTTP 202, không trả token hoặc xác nhận email có tồn tại. Chỉ gửi khôi phục cho tài khoản đã xác minh. Token ngẫu nhiên 32 byte, DB chỉ lưu SHA-256; token xuất hiện trong fragment của liên kết, không nằm trong query/access log. Frontend lấy vào bộ nhớ và xóa fragment khỏi thanh địa chỉ. Tải lại trang trước khi hoàn tất cần mở lại liên kết gốc.

Mỗi IP: yêu cầu xác minh 3/phút, quên mật khẩu 5/phút, xác minh/đặt lại 10/phút. Mỗi tài khoản và loại thư: cách nhau ít nhất 60 giây, tối đa 3 thư/giờ, lưu giới hạn trong DB kể cả khi gửi lỗi. Các liên kết trước vẫn dùng được đến khi hết hạn hoặc một liên kết hoàn tất; gửi lại không làm hỏng liên kết cũ chỉ vì SMTP lỗi. Đổi/đặt lại mật khẩu vô hiệu hóa tất cả token. Lỗi SMTP chỉ ghi thông báo chung, không ghi địa chỉ người nhận, mật khẩu hoặc nội dung thư; token của thư gửi lỗi bị vô hiệu hóa.

Gửi thư bằng tác vụ nền trong tiến trình API, chưa có hàng gửi bền hoặc retry tự động. Nếu API dừng hoặc SMTP gián đoạn, khách chờ rồi yêu cầu lại. Cần outbox/worker bền trước khi cam kết giao thư hoặc chạy nhiều worker. Giới hạn theo IP còn ở bộ nhớ, phù hợp một API worker.

Mật khẩu PBKDF2-SHA256 600.000 vòng, salt riêng. Cookie HttpOnly, SameSite Strict, hạn 24 giờ, Secure ngoài development. POST yêu cầu CSRF. Schema v9 thêm cờ email_verified (tài khoản cũ mặc định false) và customer_email_tokens; giữ dữ liệu cũ. Sao lưu nhận v7/v8/v9, khôi phục thu hồi cả phiên và token email. Không hạ mã nguồn về bản chỉ hỗ trợ schema cũ sau nâng cấp.

## Kiểm chứng ngày 07/10/2026

172 kiểm thử backend đạt; frontend build đạt. Kiểm thử bao gồm xác minh với mật khẩu, token hết hạn/đã dùng/sai mục đích, phản hồi đồng nhất cho email lạ/chưa xác minh, giới hạn gửi, lỗi SMTP không lộ bí mật, TLS, reset đồng thời, migration giữ tài khoản cũ và backup thu hồi token.

Trình duyệt với DB và hộp thư thử cục bộ: đăng ký, nhận liên kết xác minh, mở trên phiên trình duyệt khác, mật khẩu sai/đúng, quên mật khẩu, xác nhận mật khẩu mới, thu hồi thiết bị cũ, đăng nhập mới và chặn dùng lại liên kết. Giao diện điện thoại 390px không tràn ngang. Chưa cấu hình hoặc gửi thử SMTP tới hộp thư thật.
