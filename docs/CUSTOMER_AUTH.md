# Tài khoản khách hàng

Triển khai ngày 03/10/2026. Tài khoản khách dùng email + mật khẩu, tách khỏi tài khoản nhân viên/admin. Không cần nhà cung cấp xác thực hoặc gửi email.

## Sử dụng

1. Khởi động backend như hiện tại để tự tạo bảng schema v8. Với bản giao diện do backend phục vụ, chạy `npm --prefix frontend run build` sau khi cập nhật mã nguồn.
2. Mở `/chat`, chọn **Đăng ký**. Nhập tên hiển thị, email và mật khẩu 15–128 ký tự, rồi nhập lại mật khẩu.
3. Đăng nhập cùng tài khoản trên thiết bị khác để mở hội thoại đang hoạt động gần nhất. **Lịch sử** cho phép đọc các hội thoại trước đó, phân trang danh sách và tin nhắn.
4. **Chat mới** kết thúc hội thoại hiện tại và tạo hội thoại mới. Lịch sử cũ vẫn giữ. Thiết bị đang mở hội thoại cũ vẫn xem được; đăng nhập lại để chuyển sang hội thoại mới nhất.
5. **Đăng xuất** chỉ thu hồi phiên hiện tại. **Tài khoản → Đổi mật khẩu** yêu cầu mật khẩu hiện tại và thu hồi tất cả phiên đăng nhập của tài khoản.

## Giới hạn hiện tại

- Email chỉ là định danh đăng nhập, chưa xác minh quyền sở hữu. Chưa có quên mật khẩu hoặc khôi phục qua email; giao diện thông báo trước khi đăng ký.
- Đăng ký không nhận hồ sơ Customer cũ chỉ vì trùng email. Không tự ghép lịch sử khách vãng lai vào tài khoản.
- Đơn hàng vẫn cần mã truy cập riêng. Email và tên hiển thị không đủ để chứng minh quyền xem đơn.
- Tài khoản không cấp quyền staff/admin; CLI `app.create_user` vẫn dành cho nhân viên.
- Phiên có hạn 24 giờ; hết phiên không xóa tài khoản hoặc lịch sử. Widget nhúng cùng origin hỗ trợ các lựa chọn đăng nhập tương tự.

## Dữ liệu và vận hành

Schema v8 thêm `customer_accounts` và `customer_sessions`, giữ dữ liệu khách vãng lai và các bảng cũ. Email được bỏ khoảng trắng hai đầu và chuyển chữ thường; hỗ trợ email ASCII, không bỏ dấu chấm hoặc phần sau dấu cộng.

Mật khẩu lưu bằng PBKDF2-SHA256, 600.000 vòng với salt riêng; token phiên chỉ lưu hash. Cookie HttpOnly, SameSite Strict, path `/api/v1/widget`, Secure khi APP_ENV khác development. Môi trường ngoài development cần HTTPS. Thay đổi dữ liệu kiểm tra CSRF; đăng ký/đăng nhập/đổi mật khẩu có giới hạn theo IP. Giới hạn hiện giữ trong bộ nhớ, chỉ phù hợp một API worker.

Sao lưu nhận schema v7 và v8. Khôi phục v8 thu hồi cả phiên khách có tài khoản; người dùng đăng nhập lại. Bản sao v7 được nâng schema khi backend khởi động. Không hạ mã nguồn về phiên bản chỉ hiểu v7 sau khi nâng dữ liệu lên v8.

## Kiểm thử

`python -m unittest app.tests.test_customer_auth -v` kiểm tra đăng ký, xác thực, phiên nhiều thiết bị, thu hồi phiên, lịch sử và quyền đơn hàng; có trường hợp login đang chờ không vượt qua lần đổi mật khẩu.
