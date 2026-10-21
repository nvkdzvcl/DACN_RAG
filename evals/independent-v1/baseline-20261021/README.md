# Chốt phiên bản trước nghiệm thu RAG độc lập

Ngày lập: 21/10/2026 (Asia/Bangkok).

**Đã chốt runtime và corpus hồi quy. Chưa có corpus/câu hỏi kín, người duyệt hoặc kết quả nghiệm thu độc lập.** Không gọi bước này là hoàn tất nghiệm thu.

## Phiên bản đã lưu

- Commit nền: `62d27d7b680e8d22e88b1d8836cbc451bc081428`.
- Workspace có thay đổi sẵn ở `frontend/package-lock.json`; giữ nguyên, ngoài phạm vi RAG. Không tạo commit hoặc push ở bước này.
- Chat model: `qwen3:4b`; embedding: `embeddinggemma:300m`. Digest đầy đủ nằm trong `manifest.json`, không chỉ dựa vào tên model.
- Ollama đang chạy: `0.40.6`; temperature `0`, think `false`, num_ctx `8192`, num_predict `700`, keep_alive `5m`.
- Qdrant local; lấy tối đa 5 nguồn, ngưỡng `0.35`, chunk 180 từ và overlap 30 từ. Quy tắc thực tế được chốt bằng bản sao mã, không chỉ mô tả này.
- `snapshot.zip` lưu 122 tệp: toàn bộ Python trong app (gồm prompt/schema, runner và test), requirements, corpus/nhãn của năm bộ RAG, bằng chứng hồi quy cuối có sẵn.
- `manifest.json` lưu SHA-256 từng tệp, SHA-256 ZIP, cấu hình cho phép công bố, phiên bản Python/thư viện, digest model và kết quả đối chiếu lịch sử.

Prompt nằm trong mã `app/rag/`, được lưu nguyên trạng, không viết lại. Không sửa nhãn `rag/test-003`; vấn đề câu hỏi giờ ngừng nhận so với nhãn cả khung giờ được ghi để người thật duyệt.

## Đối chiếu với hồi quy cũ

Đối chiếu SHA-256 với lượt `refund-schema-v1-20261009` của cả năm bộ: các tệp RAG, xử lý tài liệu, evaluator, corpus và cases được đối chiếu đều khớp. Manifest ghi cụ thể số tệp và danh sách sai khác cho từng bộ.

Điểm 180/180 là bằng chứng lịch sử, không phải lần chạy mới hôm nay hoặc điểm trên bộ độc lập. Không suy ra độ trễ hay chất lượng hiện tại chỉ từ hash mã/model. Không suy ra toàn bộ backend không thay đổi từ phép so sánh phạm vi RAG này.

## Phạm vi kho tài liệu

- Corpus giả lập của năm bộ hồi quy được sao chép và băm; bao gồm cả ca phát triển của bộ TXT để lưu lịch sử đầy đủ.
- Kho vận hành hiện có 1 tệp: chỉ lưu hash nội dung trong manifest; không sao chép nội dung, không mở DB/Qdrant đang phục vụ. Hash tệp không chứng minh trạng thái lập chỉ mục, không thay thế backup nhất quán.
- Nghiệm thu độc lập sẽ dùng corpus riêng trong DB/vector tạm theo evaluator hiện có, không lấy kho vận hành làm corpus nghiệm thu mặc định.
- Corpus và nhãn độc lập chưa được cung cấp nên **chưa thể đóng băng**. Không tạo câu hỏi mới thay người soạn độc lập ở bước này.
- Không lưu `.env`, mật khẩu SMTP, token Telegram, DB khách hàng hoặc model weights vào gói này. Phiên bản thư viện được ghi lại, chưa có bộ cài offline tái tạo toàn bộ môi trường.

## Kiểm tra trước khi đo

Chạy từ thư mục gốc dự án, với Ollama đang hoạt động:

```powershell
cd E:\DACN_RAG
python -m evals.independent-v1.baseline-20261021.verify
```

Lệnh chỉ đọc: kiểm tra ZIP, hash tệp trong workspace, danh sách Python trong app, cấu hình RAG, phiên bản các thư viện đã ghi và digest/version Ollama. Không gửi câu hỏi tới model, không sửa DB hoặc vector. Biến môi trường hiện có được ưu tiên hơn `.env`, giống cách nạp cấu hình đã dùng lúc chốt; đây không phải phép đọc cấu hình của tiến trình backend đang chạy.

Nếu có `BASELINE MISMATCH` hoặc lỗi kiểm tra, dừng đo và xác định thay đổi. Không cập nhật hash trong bản này để che sai khác; tạo baseline mới khi chủ động đổi code/model/cấu hình. Gói snapshot giúp đối chiếu, không khóa quyền sửa repository.

## Bước tiếp theo

1. Người độc lập soạn chính sách/câu hỏi mới; người thứ hai duyệt nguồn, nhãn và điều kiện. Chốt tiêu chí đạt trước khi đo.
2. Bàn giao dataset có phiên bản riêng; lưu SHA-256 corpus/cases, tên người soạn/người duyệt và thời điểm. Không sửa manifest runtime này; liên kết baseline này trong biên bản dataset mới.
3. Kiểm tra baseline, sau đó chạy evaluator trên dataset mới vào thư mục kết quả mới. Đối chiếu manifest lượt chạy với baseline này và manifest dataset.

Chỉ sau bước 2 mới có đủ cả runtime lẫn dataset đóng băng cho nghiệm thu. Chưa sửa lỗi theo câu hỏi kín, chưa chấm thay người duyệt.
