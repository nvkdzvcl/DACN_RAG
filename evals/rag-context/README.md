# Kiểm chứng ngoài bộ BT20

24 câu về tai nghe TN8 và loa LS2, soạn ngày 08/10/2026 trước lượt chạy đầu tiên trên bộ này. Chính sách và số liệu là dữ liệu giả lập; không phải thông tin sản phẩm thật.

Bộ này kiểm tra giấy tờ, phủ định bảo hành, phí theo từng lý do, mốc hoàn tiền, câu nối tiếp, chỉ dẫn giả, thiếu dữ kiện, câu mơ hồ và nguồn mâu thuẫn. Hai câu mơ hồ có `should_clarify=true`: từ chối chung không được chấm đạt thay cho hỏi làm rõ.

Đây là bộ do cùng trợ lý soạn, chưa được người duyệt độc lập. Không coi kết quả là nghiệm thu chất lượng hay tập kiểm thử độc lập về tác giả. Không thay nhãn sau khi xem đầu ra.

## Chạy lại

```powershell
python -m app.evaluate_rag --split test --dataset evals/rag-context --output evals/rag-context/runs/ten-luot-moi
```

Runner dùng DB, Qdrant và kho tài liệu tạm riêng; cần Ollama cùng hai model đã cấu hình. Không ghi đè thư mục kết quả đã tồn tại. Manifest lưu hash corpus, ca kiểm thử và mã Python; kết quả lưu đáp án, nguồn, đầu ra model và độ trễ của từng ca.

## Giới hạn bản sửa

- Câu trả lời vẫn trích nguyên văn, không cho model tự viết chính sách mới.
- Câu có tiêu đề phạm vi Markdown hoặc liên kết “trường hợp này/đó” giữ phần trước trong cùng đoạn; không suy ra điều kiện từ đoạn ngoài phạm vi truy hồi.
- Hai mẫu mơ hồ tiếng Việt được phát hiện trước khi chọn câu nguồn; kiểm định model còn có thể yêu cầu làm rõ các trường hợp khác. Chưa có bộ phân giải ngữ cảnh đa ngôn ngữ tổng quát.
- Nếu kiểm định đề xuất ID câu khác, server kiểm tra ID, trích lại và kiểm định lần nữa. Chỉ sửa một lần, tối đa ba lần gọi chat; mâu thuẫn nguồn không được vượt qua bằng sửa đáp án.
- Bộ BT20 được dùng để chẩn đoán và chỉnh sửa, nên điểm BT20 sau sửa là điểm hồi quy, không phải điểm tổng quát hóa trên dữ liệu chưa thấy.
