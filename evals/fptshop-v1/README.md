# fptshop-v1: bộ kiểm tra chính sách FPT Shop

40 câu tiếng Việt trên corpus là bản sao đúng 12 file `knowledge/fptshop/*.md` (chính sách FPT Shop diễn đạt lại, xem `docs/POLICY_SOURCES.md`).

| Loại | Số câu | Kỳ vọng |
|---|---:|---|
| answerable | 24 | Trả lời có trích nguồn đúng dòng gold |
| followup | 5 | Hiểu chủ đề từ lịch sử rồi trả lời |
| ambiguous | 4 | Hỏi lại khách (câu trả lời khác nhau tùy trường hợp chưa nêu) |
| unanswerable | 4 | Từ chối vì tài liệu không có |
| injection | 3 | Hai câu phải từ chối; một câu vẫn trả lời đúng dù lịch sử ép "miễn phí hết" |

## Trạng thái

- Soạn ngày 15/11/2026 **trước khi** nạp chính sách mới vào hệ thống và trước mọi lượt chạy.
- Nhãn do trợ lý AI soạn; **người dùng dự án (Nguyễn Văn Khanh) duyệt toàn bộ 40 nhãn ngày 15/11/2026** qua `REVIEW.md`, không yêu cầu sửa. Duyệt được xác nhận trong hội thoại, không ký từng dòng. Từ đây bộ câu đóng băng; muốn sửa nhãn phải tạo phiên bản mới.
- `build_cases.py` sinh `cases.jsonl` từ bảng trong script, tra dòng gold theo đoạn chữ và từ chối ghi đè.

## Chạy

```powershell
python -m app.evaluate_rag --split test --dataset evals/fptshop-v1 --output evals/fptshop-v1/runs/<tên-mới>
```

## SHA-256 khi đóng băng (sau duyệt, trước lượt chạy đầu tiên)

```
f82296992e79c490f4a33b35fcc694a5c1c47cb49f4ac608bb9956bcec59c800 *cases.jsonl
fbf1168886a37f8cd702a1c31de24b1df680b38fb4d49ecdbe7403dcc83e1189 *corpus/test-bao-hanh.md
7ba58dca5883265ca24242c1118b9c5a41bfca7231de6608cc85f21750cf76da *corpus/test-bao-mat.md
aceed44f86f601458a73c2dc6dd55bddea5ee1af51cc1459fe40b75de8ed1678 *corpus/test-doi-tra.md
dbbdd7fcacc63bdb07f1fbd201b34c2363f20fd6d76a257e34c9c02a307cfbea *corpus/test-giao-hang.md
96f42ec4254a9cb2524efc18538067dc635e978077dc1f670317ab9ee75a8b30 *corpus/test-ho-tro-ky-thuat.md
5b733e8d1b289ec75beecec2da89e282cecaf9e4c63f3e038ea2a5d72f24dc85 *corpus/test-khach-hang-than-thiet.md
32559b377407103e29d5e600c2b88e694a51aac722d8df59740f45069ab97073 *corpus/test-khieu-nai.md
4dd961f257ef2142bf0e11bc6514210dc86b35286e146e6967f750dd816c72e6 *corpus/test-kiem-hang.md
0afd13c591f369f34ff9eaf035babcdf5eb9d7502ac0676448daaead4ff3b952 *corpus/test-lien-he-va-mua-hang.md
14f0f9b0e46f0c7070956329ece589abc081fa3d1cbacc7400a31410d8f54879 *corpus/test-thanh-toan.md
32279617722abcc58cc5666b8bff2a1605ce4f1c64e92151cfd16b16e11e35d4 *corpus/test-thu-cu-doi-moi.md
e4438d139f0547903912d45600abd184b5b040d50d15de59f59980ea2e7b22cf *corpus/test-tra-gop.md
```
