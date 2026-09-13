# Đánh giá RAG trên PDF và DOCX

Bộ bổ sung gồm 24 câu tiếng Việt do trợ lý soạn, 14 câu có đáp án và 10 câu cần từ chối. Corpus gồm một PDF ba trang và một DOCX một trang có bảng. Chính sách giả lập khác bộ TXT cũ; không dùng cho giao dịch thật. Nhãn, đáp án và mức đúng ngữ nghĩa chưa được người duyệt.

## Phạm vi

- PDF: nhận hàng tại tủ, phí/đổi lịch/hóa đơn lắp đặt và hai thông báo tiền cọc mâu thuẫn. Trang dài nhất có 355 từ, vượt một chunk 180 từ và buộc truy xuất đoạn ở cuối trang.
- DOCX: phí gói quà ở đoạn văn; thu hồi pin, khắc tên và vệ sinh trong bảng; chính sách thẻ cùng tài liệu chứa chỉ dẫn độc hại.
- Sáu nhóm câu: có đáp án, hỏi nối tiếp, ngoài tài liệu, mơ hồ, mâu thuẫn và injection. Hai câu injection có chính sách hợp lệ vẫn phải trả lời; hai yêu cầu bịa trực tiếp phải từ chối.
- Gold gồm tên file, trang PDF hoặc vị trí đoạn/bảng DOCX và quote. Trình nạp kiểm tra quote nằm trọn trong ít nhất một chunk của đúng vị trí, dùng cùng parser/chunker với ingestion. Điều này kiểm tra nhất quán đường xử lý, không thay người đối chiếu nội dung file.

Bộ này được soạn sau khi đã xem lỗi bộ TXT, rồi đóng băng trước lượt hỏi model. Model/prompt/retrieval giữ bản commit `78e50f9`; chỉ trình đánh giá được mở rộng. Đây là lượt đo bổ sung sau khi chốt cấu hình, không phải bộ độc lập do bên ngoài soạn hoặc bằng chứng tổng quát hóa. Sau khi xem kết quả, các lần chạy tiếp theo là regression. Không cộng điểm bộ mới với bộ TXT để công bố cải thiện.

## Chạy

```powershell
python -m app.evaluate_rag --dataset evals/rag-documents --split test --output evals/rag-documents/runs/my-run
```

CLI không tự nạp `.env`; mặc định dùng qwen3:4b và embeddinggemma:300m. Chạy tuần tự trên Ollama local, SQL/vector tạm, không sửa dữ liệu ứng dụng. Chỉ có split test trong bộ này; yêu cầu dev bị từ chối vì không có ca. Thư mục kết quả phải chưa tồn tại.

`ingestion.json` ghi hash, thời gian, trạng thái, số chunk và lỗi từng file. `manifest.json` ghi hash corpus nhị phân/cases/mã thực chạy, digest model, phiên bản parser và cấu hình. `results.jsonl` ghi truy xuất, đáp án, citation, completion và lỗi; `summary.json` giữ công thức như bộ TXT. Với gold có `page`, chấm citation/recall kiểm tra cả page lẫn location. Điểm dữ kiện vẫn là regex proxy.

Recall tính trên các quote tham chiếu, không phải số chunk vật lý duy nhất: hai chính sách mâu thuẫn có thể cùng một chunk ở trang 3. Citation khớp gold chỉ tính quote thuộc phần bằng chứng đã gán; câu nguồn có thật nhưng ngoài gold vẫn làm giảm chỉ số. Vì vậy chỉ số này không tự chứng minh citation sai hoặc thiếu căn cứ. Đã phát lại phép chấm trên 408 ca TXT đã lưu: điểm từng ca và tổng hợp không đổi, không gọi model thêm.

`build_fixtures.py` giữ nội dung trước khi đo và tạo file bằng python-docx/reportlab trong runtime tài liệu; cần Times New Roman tại `C:/Windows/Fonts`. Các gói tạo fixture không phải dependency ứng dụng. Builder từ chối ghi đè bộ đã có. Khi đổi chính sách/nhãn, tạo phiên bản dataset mới và giữ bản cũ. File nhị phân đã commit là đầu vào chuẩn; thời gian/metadata khi dựng lại có thể làm hash khác.

Lượt `frozen4b-test` dừng ở log ingestion trước khi hỏi câu nào vì lỗi serialize datetime; manifest ghi incomplete, completed_cases=0. Đã sửa log và thêm kiểm thử, chạy vào `frozen4b-v2-test`; không ghi đè dấu vết lỗi.

## Người duyệt

Mở PDF/DOCX gốc và đối chiếu `cases.jsonl` trước khi xem câu trả lời. Trong bản sao `human-review.jsonl`, ghi reviewer, duyệt gold label rồi chấm answer_correct, all_claims_supported, citation_entailment_correct và abstention_correct khi áp dụng; không tự điền true từ điểm model/regex. Giữ null khi chưa chấm, ghi lý do nếu sửa nhãn và tạo dataset phiên bản mới.

Ưu tiên câu cuối trang PDF, mọi câu bảng và nối tiếp, mâu thuẫn/injection, cùng các câu đạt proxy để phát hiện sai nghĩa bị bỏ sót. Muốn công bố tỷ lệ đúng bằng người, cần chấm đủ tập hoặc nêu rõ cách lấy mẫu/mẫu số. Chưa đo PDF scan/OCR, bảng PDF, DOCX gộp ô, tài liệu nhiều cột, khách thật hoặc tải đồng thời.
