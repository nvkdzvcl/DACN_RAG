# Quyền tra cứu từng đơn trong widget

Ngày 21/09/2026. Khách widget có thể nhận quyền xem trạng thái và mã vận đơn của một đơn cụ thể bằng mã truy cập do admin cấp. Đây là cấp quyền sau xác minh thủ công qua kênh tin cậy, chưa phải đăng nhập khách hoặc OTP email/SMS tự động.

## Cách dùng

1. Admin xác minh người nhận qua kênh liên hệ tin cậy đã có của chủ đơn. Không dùng tên, email do người đang chat tự khai hoặc việc biết mã đơn làm bằng chứng.
2. Trong **Đơn hàng**, mở đơn, đánh dấu đã xác minh và chọn **Cấp mã mới**. Mã mới thu hồi mọi mã và quyền widget cũ của chính đơn đó. Mã chỉ được trả về lúc cấp, không có API đọc lại.
3. Giao mã qua kênh tin cậy đã xác minh. Không gửi mã vào chính hội thoại chưa xác minh. Ứng dụng không tự gửi email, SMS hoặc tin nhắn ngoài hệ thống.
4. Khách nhập mã đơn và mã truy cập ở mục **Tra đơn** trên `/chat` hoặc **Quyền tra cứu đơn** trong widget nhúng. Sau khi được cấp quyền, trang `/chat` xem được trạng thái và mã vận đơn; widget nhúng có thể gửi câu hỏi chứa mã đơn. Mã truy cập nhập ở biểu mẫu riêng không được thêm vào Message hay gửi tới model.
5. Admin chọn **Thu hồi quyền** để chặn các lần tra tiếp theo. Thu hồi không xóa câu trả lời đã được phép xem trước đó.

## Phạm vi và thời hạn

- Mã có 256 bit ngẫu nhiên, dạng URL-safe dài 43 ký tự; DB chỉ lưu SHA-256. Không đặt mã trong URL, localStorage hay log ứng dụng.
- Mỗi đơn giữ tối đa một mã/quyền hiện tại, hết hạn sau 15 phút tính từ lúc cấp, không gia hạn lúc nhập. Phiên widget hết hạn hoặc kết thúc thì quyền cũng không dùng được.
- Lần nhập thành công ràng buộc mã vào một hội thoại có phiên widget còn hiệu lực. Gửi lại cùng mã từ cùng phiên được chấp nhận để phục hồi khi mất phản hồi; phiên khác bị từ chối.
- Chỉ cho xem đúng đơn được cấp quyền. Không đổi Customer của hội thoại, không mở các đơn khác cùng chủ, không gộp hồ sơ, không cấp quyền sửa/hủy đơn.
- Kiểm tra chủ đơn tại lúc cấp, nhập mã và tra cứu. Thay chủ đơn làm quyền cũ không còn hợp lệ.
- Không đổi trạng thái handoff khi nhập mã: AI vẫn dừng nếu đã chuyển nhân viên. Hội thoại đóng không nhận mã.
- Quyền được kiểm tra lại sau khi model chọn tool. Thu hồi, hết hạn hoặc kết thúc phiên trong lúc model chạy chặn phản hồi tra đơn mới.

## API và dữ liệu

| Method và path | Quyền | Kết quả |
|---|---|---|
| POST /api/v1/workspace/orders/{order_id}/access-code | Admin + CSRF | 201: order_id, code, expires_at; Cache-Control: no-store; đơn không tồn tại 404 |
| DELETE /api/v1/workspace/orders/{order_id}/access-code | Admin + CSRF | Thu hồi mã/quyền hiện tại; gọi lại vẫn thành công |
| POST /api/v1/widget/order-access | Phiên widget + CSRF | Payload order_id và code, cấm trường thừa; trả snapshot của chính phiên |
| GET /api/v1/widget/orders/{order_id} | Phiên widget đã cấp quyền đúng đơn | Chỉ trả order_id, status, tracking_code; không có quyền, hết hạn, đổi chủ hoặc thu hồi trả 404; no-store |

Nhập sai, hết hạn, sai chủ hoặc mã đã được dùng ở phiên khác cùng trả 400 với thông báo chung; thiếu/hết phiên trả 401, hội thoại đóng trả 409, sai định dạng trả 422. Giới hạn nhập mã 6 lần/phút/IP, vượt trả 429. GET /api/v1/widget/session bổ sung order_access gồm mã đơn và thời điểm hết quyền, không trả mã truy cập hoặc hash.

Migration v6 thêm bảng OrderAccess: order_id duy nhất, customer_id lúc cấp, token_hash, issued_by_id, expires_at và conversation_id sau khi sử dụng. Migration cộng thêm, giữ dữ liệu cũ, chạy lại không xóa quyền đã cấp. Việc cấp lại/thu hồi thay quyền hiện tại; chưa có lịch sử audit đầy đủ.

## Kiểm chứng và giới hạn

Chạy `python -m unittest app.tests.test_order_access -v`: bảy test bao phủ quyền admin/CSRF, validation/rate limit, phạm vi một đơn, cách ly phiên, retry, rotation, hết hạn, đổi chủ, kết thúc phiên, handoff, hai phiên tranh chấp, thu hồi khi model đang chờ và migration lặp lại. Bộ đầy đủ có 73 unittest đạt; frontend build đạt.

Khóa ghi và giới hạn bộ nhớ được kiểm chứng trên SQLite một API worker. Cần thiết kế lại giới hạn phân tán và kiểm chứng transaction trên PostgreSQL trước chạy nhiều worker. Việc giao mã phụ thuộc quy trình xác minh ngoài hệ thống; checkbox chỉ là nhắc admin, không phải bằng chứng kỹ thuật xác minh danh tính. M3 vẫn chờ người chấm, kênh thứ hai và cloud vẫn chưa hoàn tất.

QA trình duyệt trên DB riêng: admin cấp mã, widget nhập mã, câu hỏi có mã đơn gọi qwen3:4b thật và nhận đúng trạng thái/vận đơn. Sau thu hồi, lượt hỏi tiếp chuyển nhân viên, không tạo câu trả lời tra đơn mới; lịch sử trả lời hợp lệ trước đó vẫn giữ. Kiểm tra trực quan desktop và khung iframe 390 pixel cho admin/widget; không chạy lại benchmark RAG.
