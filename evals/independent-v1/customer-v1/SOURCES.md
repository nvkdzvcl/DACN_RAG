# Nguồn tham khảo và ranh giới dữ liệu

Ngày tra cứu: 21/10/2026. Nguồn chính thức, chỉ dùng lấy ý tưởng tình huống; không sao chép nguyên bài hoặc lời khách. URL không được nạp vào retriever; runtime chỉ đọc corpus đã đóng băng.

| Nguồn | URL | Ý tưởng dùng |
|---|---|---|
| IKEA US — Can someone else pick up my order? | https://www.ikea.com/us/en/customer-service/knowledge/articles/bce0e1d2-f533-4341-9606-25b38d8f4932.html | Nhận hộ, xác nhận nhận hàng và giấy tờ người nhận. |
| Apple Việt Nam — Thanh toán & Bảo mật | https://www.apple.com/vn/shop/help/payments | Thanh toán không thành công, đổi phương thức, phân biệt dữ liệu thanh toán với xác nhận đơn. |
| Samsung Việt Nam — Thay đổi phương thức thanh toán | https://www.samsung.com/vn/shop-faq/payment-and-financing/can-i-change-my-payment-method/ | Không sửa trực tiếp phương thức của đơn đã xác nhận; yêu cầu hủy và đặt lại. |
| Samsung Việt Nam — Hủy giao dịch thu cũ đổi mới | https://www.samsung.com/vn/shop-faq/trade-in/how-do-i-cancel-a-trade-in/ | Giữ thiết bị cũ ảnh hưởng ưu đãi thu cũ; cần xác nhận lại thanh toán. |
| Samsung Việt Nam — Hoàn điểm khi hủy đơn | https://www.samsung.com/vn/shop-faq/samsung-rewards/can-i-get-a-refund-on-points/ | Gợi ý phân biệt tiền, điểm và mã ưu đãi; không đưa thời hạn/điểm Samsung vào nhãn. |

Tất cả quy tắc cụ thể trong corpus do AI thiết kế cho An Nhiên Lab. Những khác biệt với nguồn thật là chủ ý giả lập, không phải mô tả chính sách hiện hành của các hãng. Các nhóm giao tách kiện, giỏ hàng, quà tặng, bảo dưỡng định kỳ, tiếp cận điểm nhận, hóa đơn, đầu sạc và phần còn lại là tình huống do AI tự soạn; không có chứng cứ về tần suất xuất hiện ở khách thật.

Các thông báo A/B mâu thuẫn và các đoạn chỉ dẫn giả đều do AI tạo để thử hệ thống; không gán chúng cho hãng hoặc nhân viên thật. Không đưa tài khoản, OTP, số điện thoại hoặc dữ liệu khách hàng thật vào corpus.

Bộ này mở rộng chủ đề so với 248 ca cũ nhưng vẫn có thể chồng lấn nghiệp vụ (đổi trả, phí, bảo hành, hoàn tiền). `novelty-check.json` chỉ loại trùng nguyên câu và chỉ ra câu gần về ký tự. Người duyệt cần xác nhận độ mới tình huống trước khi gọi là tập nghiệm thu độc lập.
