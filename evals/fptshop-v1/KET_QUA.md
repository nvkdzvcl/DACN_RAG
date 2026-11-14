# Kết quả cập nhật Kho tri thức FPT Shop (15/11/2026)

## Việc đã làm

1. Người dùng dự án duyệt 40 nhãn trong `REVIEW.md`; bộ câu được đóng băng bằng SHA-256 trong `README.md` trước lượt chạy đầu tiên.
2. Sao lưu dữ liệu runtime bằng `python -m app.backup create --offline` (đã `verify: OK`); bản sao lưu nằm ngoài repo.
3. Hỏi 10 câu cố định trên Kho tri thức thật của ứng dụng (`before_after.py --label before`).
4. Gỡ tài liệu giả lập `chinh-sach-mau-binh-giu-nhiet-BT20.md`, nạp 12 file `knowledge/fptshop/*.md`: 12 tài liệu ở trạng thái indexed, 201 chunk.
5. Hỏi lại đúng 10 câu đó (`--label after`), rồi chạy đủ 40 câu bằng `app.evaluate_rag` trên SQL/vector tạm.

Pipeline giữ nguyên bản đã merge ở PR #10 (qwen3:4b, embeddinggemma:300m, ngưỡng 0,35), không đổi code.

## 10 câu trước và sau cập nhật

| ID | Câu hỏi | Trước (kho BT20) | Sau (kho FPT Shop) |
|---|---|---|---|
| fpt-001 | Mua iPhone mới về được một tuần thì máy bị lỗi phần cứng, có được đổi máy mới không? | **Trả lời sai** bằng chính sách BT20 của cửa hàng giả lập | Trả lời, nguồn: doi-tra dòng 9 |
| fpt-007 | Máy chống nước IP68 mà bị vào nước thì có được bảo hành không? | Từ chối | Trả lời, nguồn: bao-hanh dòng 13, 16 |
| fpt-010 | Đơn đặt online giao từ kho, mở ra thấy máy bị móp thì phải báo trong bao lâu? | **Trả lời sai**, trích định nghĩa ngày làm việc của BT20 | Trả lời, nguồn: kiem-hang dòng 7, 9 |
| fpt-011 | Nhà mình cách cửa hàng 40km, giao tủ lạnh có mất phí không? | Từ chối | Trả lời, nguồn: giao-hang dòng 11, 13 |
| fpt-015 | Hoàn tiền về lại thẻ đã thanh toán thì mất mấy ngày? | Từ chối (báo mâu thuẫn) | Trả lời, nguồn: thanh-toan dòng 13, doi-tra dòng 34 |
| fpt-016 | Thẻ Visa debit có mua trả góp được không? | Từ chối | Trả lời, nguồn: tra-gop dòng 5, 8, 9 |
| fpt-018 | Mua hết 400 nghìn thì được bao nhiêu điểm thành viên? | Từ chối | Trả lời, nguồn: khach-hang-than-thiet dòng 6 |
| fpt-020 | Muốn khiếu nại thì gọi số nào? | Từ chối | Trả lời, nguồn: khieu-nai dòng 4, lien-he-va-mua-hang dòng 5 |
| fpt-022 | Mang iPhone cũ đi thu cũ đổi mới thì trước đó phải làm gì với iCloud? | Từ chối | Trả lời, nguồn: thu-cu-doi-moi dòng 10 |
| fpt-023 | Giá niêm yết trên web đã có VAT chưa? | Từ chối | Trả lời, nguồn: thanh-toan dòng 14 (kèm một dòng mã giảm giá không liên quan) |

Trước cập nhật: 2/10 câu bị trả lời bằng chính sách của cửa hàng khác, 8/10 bị từ chối. Sau cập nhật: 10/10 có trích nguồn. Chi tiết: `before-after/before.json`, `before-after/after.json`.

## Bộ 40 câu (`runs/first-20261115`)

| Chỉ số | Kết quả |
|---|---:|
| Quyết định trả lời/từ chối đúng | **36/40 (90%)** |
| Đạt mẫu dữ kiện và trích đúng nguồn gold (proxy) | 34/40 (85%) |
| Recall@1 / @5 | 81,7% / 93,3% |
| Từ chối đúng (10 câu phải từ chối/hỏi lại) | 8/10 |
| Từ chối sai câu có đáp án (30 câu) | 2/30 |
| Citation khớp nguồn gold | 64,3% |
| Độ trễ p50 / p95 | 6,5 / 8,9 giây |

| Nhóm | Đúng |
|---|---:|
| answerable | 23/24 |
| followup | 5/5 |
| unanswerable | 4/4 |
| ambiguous | 2/4 |
| injection | 2/3 |

## Các ca chưa đạt

| ID | Hiện tượng | Nhận xét |
|---|---|---|
| fpt-004 | Hỏi "mất hộp khi trả máy bị trừ bao nhiêu" thì trích dòng FPT Play box (cũng ghi thiếu hộp 2%) | Con số đúng nhưng sai phạm vi sản phẩm |
| fpt-005 | Hỏi máy cũ đổi ý thì trích quy định "bảo hành hãng trên 365 ngày" | Sai |
| fpt-013 | Đơn 60 triệu muốn trả tiền khi nhận: hệ thống hỏi lại thay vì trả lời | Từ chối sai |
| fpt-032 | "Hoàn tiền mất mấy ngày": trả lời liệt kê cả hai cách (5–7 ngày và 2–3 ngày) thay vì hỏi lại | Sai theo nhãn, nhưng câu trả lời đúng dữ kiện và đủ điều kiện; nhãn còn tranh luận được |
| fpt-033 | "Trả góp tối thiểu bao nhiêu": trích bảng mức tối thiểu theo từng ngân hàng thay vì hỏi lại | Như fpt-032 |
| fpt-039 | Ốp lưng: báo "mâu thuẫn" | Tài liệu có hai quy định khác phạm vi: ốp mua lẻ không đổi trả; ốp mua kèm máy được nhận lại khi trả máy do lỗi. Model coi là mâu thuẫn |

Citation khớp gold chỉ 64,3% vì nhiều câu trả lời kèm thêm 1–2 dòng cùng chủ đề (ví dụ fpt-016 trích 3 dòng trả góp). Các dòng thêm không sai nhưng làm câu trả lời dài hơn cần thiết.

## Đề xuất (không làm trong lượt này)

- **Sửa tài liệu, không sửa code:** ghi rõ "mua lẻ" trong dòng ốp lưng, bao da; ghi rõ "máy đã qua sử dụng" ở đầu dòng máy cũ. Sau khi sửa phải tạo bộ `fptshop-v2` (corpus mới, nhãn giữ nguyên), không ghi đè v1.
- Quyết định nhãn cho câu kiểu fpt-032/033: hỏi lại hay liệt kê đủ các trường hợp đều chấp nhận được; nên chốt một quy ước trong báo cáo.

## Giới hạn

- Câu hỏi và nhãn do trợ lý AI soạn, người dùng dự án duyệt; không phải người kiểm thử độc lập. 40 câu nên chênh 1–2 câu không có ý nghĩa thống kê.
- Nội dung chính sách là bản diễn đạt lại; độ đúng so với văn bản gốc phụ thuộc bước duyệt nội dung.
- Mỗi cấu hình chỉ chạy một lần.
