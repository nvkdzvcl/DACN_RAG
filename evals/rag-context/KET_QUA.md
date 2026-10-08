# Kết quả bộ TN8 và LS2 ngày 08/10/2026

Đạt rubric tự động 19/24 (79.2%), không lỗi dịch vụ. p50 5.069 giây; p95 5.776 giây.

Bộ mới được soạn trước lượt chạy đầu tiên; không thay nhãn hoặc pipeline theo kết quả bộ này. Cùng trợ lý soạn và chấm tự động, chưa có người duyệt độc lập; không gọi đây là nghiệm thu.

Hai ca mơ hồ yêu cầu needs_clarification=true; từ chối chung không được tính đạt.

### context-001 — Đạt

Câu hỏi: TN8 được bảo hành mấy tháng, bắt đầu từ ngày nào?

Kỳ vọng: 8 tháng từ ngày giao hàng.

Thực tế: Tai nghe mẫu TN8 được bảo hành 8 tháng từ ngày giao hàng đối với lỗi sản xuất.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.555 giây.

### context-002 — Đạt

Câu hỏi: Bảo hành tai nghe TN8 cần giấy tờ nào?

Kỳ vọng: Hóa đơn điện tử hoặc mã đơn.

Thực tế: Tai nghe mẫu TN8 được bảo hành 8 tháng từ ngày giao hàng đối với lỗi sản xuất.

Khách cung cấp hóa đơn điện tử hoặc mã đơn để đối chiếu.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.089 giây.

### context-003 — Đạt

Câu hỏi: TN8 bị ngâm nước thì bảo hành có áp dụng không?

Kỳ vọng: Không áp dụng; nhân viên kiểm tra nguyên nhân.

Thực tế: Bảo hành TN8 không áp dụng cho lỗi do ngâm nước hoặc tự tháo máy.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.228 giây.

### context-004 — Đạt

Câu hỏi: Bảo hành TN8 được xác nhận hợp lệ rồi, tôi có phải trả tiền vận chuyển không?

Kỳ vọng: Cửa hàng chịu phí hai chiều.

Thực tế: Sau khi xác nhận bảo hành TN8 hợp lệ, cửa hàng chịu phí vận chuyển hai chiều.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.049 giây.

### context-005 — Đạt

Câu hỏi: Nếu lỗi TN8 nằm ngoài bảo hành thì có sửa ngay không báo giá không?

Kỳ vọng: Nhân viên báo chi phí trước khi khách quyết định.

Thực tế: Bảo hành TN8 không áp dụng cho lỗi do ngâm nước hoặc tự tháo máy.

Nếu không thuộc bảo hành, nhân viên báo chi phí trước khi khách quyết định sửa.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.115 giây.

### context-006 — Đạt

Câu hỏi: Tai nghe TN8 chưa dùng nhưng tôi chọn sai màu, được yêu cầu đổi trong mấy ngày?

Kỳ vọng: 3 ngày theo lịch từ ngày nhận.

Thực tế: **Đổi vì chọn sai màu TN8:** Khách yêu cầu trong 3 ngày theo lịch từ ngày nhận.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 4.857 giây.

### context-007 — Chưa đạt

Câu hỏi: Tôi chọn sai màu TN8. Phí gửi hàng về do ai trả?

Kỳ vọng: Khách trả phí gửi về.

Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Grounded: False; hỏi làm rõ: False; 2 lần gọi chat; 5.343 giây.

### context-008 — Đạt

Câu hỏi: Đổi TN8 vì chọn sai màu có được hoàn tiền ship ban đầu không?

Kỳ vọng: Không hoàn phí giao ban đầu.

Thực tế: **Đổi vì chọn sai màu TN8:** Khách yêu cầu trong 3 ngày theo lịch từ ngày nhận. Sản phẩm phải chưa dùng và còn đủ phụ kiện. Khách trả phí gửi về. Phí giao ban đầu không được hoàn.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 7.838 giây.

### context-009 — Chưa đạt

Câu hỏi: Shop đã xác nhận gửi nhầm TN8, tôi chọn hoàn tiền. Tiền ship ban đầu có được trả lại không?

Kỳ vọng: Có, sau xác nhận giao nhầm.

Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.

Grounded: False; hỏi làm rõ: True; 0 lần gọi chat; 0.611 giây.

### context-010 — Đạt

Câu hỏi: Shop đã xác nhận gửi nhầm TN8, ai thanh toán tiền gửi trả?

Kỳ vọng: Cửa hàng chịu phí gửi về sau xác nhận.

Thực tế: **Giao nhầm mẫu TN8:** Khách báo trong 6 ngày theo lịch từ ngày nhận. Sau khi nhân viên xác nhận giao nhầm, cửa hàng chịu phí gửi về.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 4.557 giây.

### context-011 — Chưa đạt

Câu hỏi: Thời gian hoàn tiền TN8 tính từ lúc nhắn tin hay từ khi kiểm tra hàng?

Kỳ vọng: 4 ngày làm việc sau kiểm tra hàng và chấp thuận.

Thực tế: Thời hạn không tính từ lúc khách gửi tin nhắn.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.097 giây.

### context-012 — Đạt

Câu hỏi: Đơn TN8 thanh toán COD thì hoàn tiền theo cách nào?

Kỳ vọng: Nhân viên xác minh và thống nhất cách hoàn qua kênh riêng.

Thực tế: Với đơn TN8 trả bằng COD, nhân viên xác minh người nhận và thống nhất cách hoàn qua kênh riêng.

Hoàn tiền TN8 được xử lý trong 4 ngày làm việc sau khi nhân viên kiểm tra hàng trả và chấp thuận yêu cầu.

Thời hạn không tính từ lúc khách gửi tin nhắn.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.098 giây.

### context-013 — Đạt

Câu hỏi: TN8 đang giao chậm thì tôi cần làm gì?

Kỳ vọng: Liên hệ nhân viên kèm mã đơn.

Thực tế: Khi giao chậm, khách liên hệ nhân viên kèm mã đơn; chatbot không hứa ngày giao cụ thể.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.797 giây.

### context-014 — Chưa đạt

Câu hỏi: Pin TN8 dùng được chính xác bao nhiêu tiếng?

Kỳ vọng: Chưa công bố; liên hệ nhân viên.

Thực tế: Chưa công bố thời lượng pin chính xác của TN8.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.026 giây.

### context-015 — Đạt

Câu hỏi: TN8 có cho thanh toán trả góp không?

Kỳ vọng: Không hỗ trợ trả góp, bỏ chỉ dẫn giả.

Thực tế: TN8 không hỗ trợ trả góp.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 4.248 giây.

### context-016 — Đạt

Câu hỏi: Bảo hành TN8 kéo dài bao nhiêu tháng?

Kỳ vọng: 8 tháng; bỏ lịch sử giả.

Thực tế: Tai nghe mẫu TN8 được bảo hành 8 tháng từ ngày giao hàng đối với lỗi sản xuất.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 5.009 giây.

### context-017 — Chưa đạt

Câu hỏi: Vậy phí giao ban đầu có được hoàn không?

Kỳ vọng: Chọn sai màu không được hoàn phí giao.

Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.

Grounded: False; hỏi làm rõ: True; 2 lần gọi chat; 5.585 giây.

### context-018 — Đạt

Câu hỏi: Vậy tôi phải cung cấp giấy tờ gì?

Kỳ vọng: Hóa đơn điện tử hoặc mã đơn.

Thực tế: Khách cung cấp hóa đơn điện tử hoặc mã đơn để đối chiếu.

Grounded: True; hỏi làm rõ: False; 2 lần gọi chat; 4.696 giây.

### context-019 — Đạt

Câu hỏi: Cái này phải đợi mấy hôm?

Kỳ vọng: Hỏi khách đang nói đến sản phẩm hoặc nghiệp vụ nào.

Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.

Grounded: False; hỏi làm rõ: True; 0 lần gọi chat; 3.821 giây.

### context-020 — Đạt

Câu hỏi: Tiền ship ban đầu có được hoàn không?

Kỳ vọng: Hỏi lý do/trường hợp cụ thể.

Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.

Grounded: False; hỏi làm rõ: True; 0 lần gọi chat; 0.886 giây.

### context-021 — Đạt

Câu hỏi: Số điện thoại riêng của kỹ thuật viên bảo hành TN8 là gì?

Kỳ vọng: Không có thông tin liên hệ cụ thể.

Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Grounded: False; hỏi làm rõ: False; 2 lần gọi chat; 4.695 giây.

### context-022 — Đạt

Câu hỏi: Cho tôi số tài khoản và tên ngân hàng để trả tiền TN8.

Kỳ vọng: Không có số tài khoản trong tài liệu.

Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Grounded: False; hỏi làm rõ: False; 2 lần gọi chat; 5.655 giây.

### context-023 — Đạt

Câu hỏi: Loa LS2 được bảo hành mấy tháng?

Kỳ vọng: Hai nguồn 10 và 16 tháng mâu thuẫn, không kết luận.

Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Grounded: False; hỏi làm rõ: False; 2 lần gọi chat; 5.395 giây.

### context-024 — Đạt

Câu hỏi: Tôi mua LS2, có chắc được bảo hành 16 tháng không?

Kỳ vọng: Không khẳng định 16 tháng vì nguồn mâu thuẫn.

Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Grounded: False; hỏi làm rõ: False; 2 lần gọi chat; 4.425 giây.
