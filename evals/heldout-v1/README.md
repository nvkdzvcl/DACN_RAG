# heldout-v1 — bộ kiểm tra chưa dùng để tinh chỉnh

Tạo ngày 14/11/2026, **trước khi** viết lại pipeline RAG (gỡ regex đặc thù theo ca). Cửa hàng, sản phẩm, corpus và cách hỏi đều mới, không lấy từ các bộ eval cũ.

Giới hạn trung thực:
- Câu hỏi và nhãn do trợ lý AI soạn, chưa có người duyệt độc lập. Người soạn đã biết hướng thiết kế mới, nên đây chỉ là bộ "chưa tinh chỉnh", không phải bộ kín chuẩn.
- 41 câu, khoảng tin cậy rộng; chênh lệch 1–2 câu không có ý nghĩa thống kê.
- **Quy tắc:** không sửa code để vá riêng một ca trong bộ này. Sau khi dùng làm báo cáo, bộ này trở thành regression; cần bộ mới để đo tổng quát hóa.

Chạy: `python -m app.evaluate_rag --split test --dataset evals/heldout-v1 --output evals/heldout-v1/runs/<tên-mới>`

SHA-256 khi đóng băng:
```
4ccf5407b7dc7a95b72ded59c9b1cb3487ea84786c735a2e610725174833e003 *cases.jsonl
b696e48a63ff13852073473f5a90fffa1f8b94c1103187d903412bac860dc87b *corpus/test-chinh-sach.md
3af863093ffc2e9f800d53566aee32000bc4945b9cee24bc9eed59f198f61113 *corpus/test-dh9-a.txt
639cd4a7e3ca8197159e4f282717317919b6ef0b89c7ee3526daad0a0031a497 *corpus/test-dh9-b.txt
da64356eb6b2f98422bc4733b405331ae3491d46dc4d00b2d52e452cbb89c383 *corpus/test-lk3-a.txt
ebb80d4c10ac0e0e85a21168e4ad210c25d30950882bf219e166dea6a3159ca9 *corpus/test-lk3-b.txt
```
