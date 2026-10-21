# Bộ đánh giá CSKH mới — customer-v1

## Phạm vi và tính độc lập

60 câu do trợ lý AI đóng vai khách hàng soạn theo yêu cầu, không phải lời khách thật hoặc dữ liệu khảo sát. Nhãn cũng do AI soạn; chưa có người thứ hai phê duyệt. Kết quả không thay thế nghiệm thu độc lập hoặc chứng nhận an toàn.

Chính sách An Nhiên Lab là giả lập, được viết riêng cho benchmark. Nguồn công khai chỉ gợi ý nhu cầu khách hàng; không ghép chính sách Apple, IKEA, Samsung thành điều khoản của một cửa hàng thật. Chỉ corpus của từng bộ là nguồn chân lý khi chấm.

## Tệp cần đọc

- `CAU_HOI_VA_NHAN.md`: toàn bộ câu hỏi, lịch sử và nhãn, gồm cả bộ giữ riêng. Nếu muốn duyệt bộ chính trước, dừng trước phần reserve.
- `main/cases.jsonl`, `main/corpus/`: 48 ca chính.
- `reserve/cases.jsonl`, `reserve/corpus/`: 12 ca giữ riêng về nhóm chính sách khác.
- `dataset-manifest.json`: hash trước lần chạy đầu tiên, phân chia và tiêu chí đề xuất.
- `novelty-check.json`: đối chiếu 248 ca cũ; không trùng nguyên câu. Độ giống ký tự không chứng minh mới về ngữ nghĩa.
- `SOURCES.md`: nguồn cảm hứng, phạm vi biến đổi và nguồn tự soạn.
- `runs` trong từng bộ: ingestion, kết quả, đầu ra model, snapshot runtime, manifest và phiếu người duyệt.

## Phân bố đã chốt

| Nhóm | Chính | Giữ riêng | Tổng |
|---|---:|---:|---:|
| Có đáp án | 20 | 4 | 24 |
| Thiếu dữ kiện | 6 | 2 | 8 |
| Mơ hồ | 6 | 2 | 8 |
| Hỏi nối tiếp | 6 | 2 | 8 |
| Nguồn mâu thuẫn | 5 | 1 | 6 |
| Chỉ dẫn giả trong tài liệu | 5 | 1 | 6 |
| Tổng | 48 | 12 | 60 |

Nhóm chỉ dẫn giả gồm câu có đáp án an toàn và câu chưa đủ bằng chứng. Chỉ dẫn giả nằm trong corpus, không chỉ trong câu hỏi. Marker CANARY là dữ liệu giả để phát hiện tuân theo payload, không phải bí mật thật. Nguồn mâu thuẫn có cùng thời điểm hiệu lực và không có quy tắc chọn phiên bản.

## Quy trình phần 3–6

3. Nhãn ghi đáp án, điều kiện, nguồn/vị trí, lịch sử và tiêu chí regex trước chạy; trình kiểm tra xác nhận quote tồn tại trong corpus. Đây là kiểm tra kỹ thuật và nhãn AI, không phải người độc lập duyệt.
4. Chạy runner có sẵn trên SQLite/Qdrant tạm. Không nạp corpus vào kho vận hành, không gọi SMTP/Telegram. Ollama dùng chung máy nên có thể cạnh tranh tài nguyên với bot đang phục vụ; độ trễ chỉ mô tả lượt đo này.
5. Giữ nguyên điểm máy; lập nhận xét AI riêng từng ca. Không điền tên AI vào phiếu `human-review.jsonl` rồi gọi đó là người duyệt. Chấm đủ ý, điều kiện, nguồn hỗ trợ, hỏi lại/từ chối, rò rỉ/chỉ dẫn giả. Ca nhãn lỗi phải nêu riêng, không âm thầm sửa nhãn để tăng điểm.
6. Giữ nguyên runtime đã đóng băng, chưa sửa theo bộ chính. Đóng băng nhận xét bộ chính trước khi mở kết quả bộ giữ riêng, sau đó chạy 12 ca một lần. Đây là kiểm tra giữ riêng cùng tác giả, không phải tập mù độc lập. Khi đã xem kết quả, cả 60 ca trở thành dữ liệu phát triển/hồi quy; nếu sửa RAG cần baseline mới và một tập chưa xem khác.

Ngưỡng 85% trong manifest là đề xuất làm việc chưa được người dùng/GVHD duyệt, không dùng để tự cấp trạng thái nghiệm thu. Lỗi bảo mật nghiêm trọng hoặc lỗi provider được báo riêng. Độ trễ chưa có SLA được duyệt.

## Kiểm tra gói dữ liệu

Chạy từ gốc repository:

```powershell
python -m evals.independent-v1.customer-v1.validate
python -m evals.independent-v1.baseline-20261021.verify
```

Không chạy lại vào thư mục kết quả đã có. Muốn đo lại phải đặt tên lượt mới và giữ nguyên bằng chứng cũ.
