# Chính sách mẫu Mộc Demo

Chỉ dùng kiểm thử, không tải tự động vào kho tri thức người dùng. Các con số và sản phẩm hoàn toàn giả lập.

24 câu và nhãn được chốt trước khi sửa runtime ngày 09/10/2026: giao trễ, dịch vụ giao, mốc hoàn tiền theo thanh toán, lý do đổi trả, bảo hành, hóa đơn, khắc tên, thiếu dữ kiện, chỉ dẫn giả và xung đột. Không bổ sung số điện thoại/tài khoản thật; thiếu bằng chứng vẫn phải từ chối.

Nhãn do trợ lý soạn, cần người duyệt độc lập. Sau khi xem kết quả, bộ này chỉ là tập phát triển/hồi quy, không phải đánh giá mù. Không sửa các corpus/nhãn cũ.

`CHINH_SACH_MAU.md` là bản chính sách giả lập sạch để đọc hoặc dùng trong môi trường demo riêng. `corpus/` có thêm chỉ dẫn giả và tài liệu mâu thuẫn để kiểm thử khả năng từ chối; không đưa vào kho tri thức vận hành.

Chạy đánh giá với DB/vector tạm, không sửa dữ liệu đang dùng:

```powershell
python -m app.evaluate_rag --split test --dataset evals/rag-policy --output evals/rag-policy/runs/ten-luot-moi
```
