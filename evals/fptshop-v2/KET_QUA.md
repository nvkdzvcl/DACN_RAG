# Kết quả fptshop-v2: sửa tài liệu, không sửa code (15/11/2026)

Cùng 40 câu và nhãn đã duyệt của v1; chỉ sửa 6 dòng tài liệu để ghi rõ phạm vi (xem `README.md`). Pipeline, model và ngưỡng giữ nguyên.

| Chỉ số | v1 (`first-20261115`) | v2 (`docfix-20261115`) |
|---|---:|---:|
| Quyết định đúng | 36/40 | 36/40 |
| Đạt mẫu dữ kiện và trích đúng nguồn gold | 34/40 | **36/40** |
| Recall@5 | 93,3% | **96,7%** |
| Citation khớp nguồn gold | 64,3% | **67,4%** |
| Từ chối sai câu có đáp án | 2/30 | 2/30 |
| Trả lời khi phải từ chối hoặc hỏi lại | 2/10 | 2/10 |
| p50 | 6,5 giây | 5,2 giây |

## Thay đổi theo ca

| ID | v1 | v2 | Ghi chú |
|---|---|---|---|
| fpt-004 | Trích dòng FPT Play box | **Đúng**, trích thêm dòng phí thiếu hộp của điện thoại, laptop | Nhờ ghi rõ phạm vi dòng phí |
| fpt-013 | Hỏi lại khách | **Đúng** | Nhờ ghi rõ "thanh toán khi nhận hàng (COD)" |
| fpt-005 | Trích sai quy định | Từ chối | Dòng máy cũ vẫn không vào top 5 retrieval. Không sửa tiếp, vì sửa theo câu chữ của câu hỏi là tinh chỉnh theo bộ test |
| fpt-039 | Báo mâu thuẫn | Hỏi lại "ốp lưng mua lẻ hay mua kèm máy" | Theo nhãn là sai; nhưng câu hỏi không nói rõ nên hỏi lại là hợp lý. Ghi nhận là nhãn còn tranh luận được |
| fpt-032, fpt-033 | Liệt kê đủ trường hợp | Không đổi | Như v1 |

## Kết luận

- Ghi rõ phạm vi trong tài liệu là cách cải thiện hiệu quả và không đụng code; nên viết tài liệu mới theo cùng quy ước.
- Vì sửa đổi được chọn sau khi xem lỗi v1 trên cùng 40 câu, kết quả v2 là regression, không phải bằng chứng tổng quát hóa.
- Kho tri thức runtime đã được lập chỉ mục lại với hai file đã sửa (`doi-tra.md`, `giao-hang.md`); vẫn 12 tài liệu ở trạng thái indexed.
