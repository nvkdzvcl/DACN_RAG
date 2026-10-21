# customer-v2 — đề xuất sửa ba nhãn

**AI đề xuất sau khi đã xem kết quả v1; chưa có người duyệt độc lập.** Không gọi v2 là tập kín mới hoặc lấy thay điểm lịch sử v1.

Giữ nguyên 60 câu, lịch sử và toàn bộ corpus. Chỉ sửa các trường trong bảng; không thay kỳ vọng ngữ nghĩa để hợp thức hóa câu trả lời sai.

| Ca | Trước | Sau | Lý do |
|---|---|---|---|
| customer-024 | {"should_answer": false, "required_patterns": []} | {"should_answer": true, "required_patterns": ["không cam kết", "khôi phục", "chưa sao lưu"]} | Câu hỏi có đáp án phủ định trực tiếp trong nguồn: không cam kết khôi phục dữ liệu chưa sao lưu. Không đồng nhất thiếu dữ liệu cá nhân với không được trả lời phủ định theo chính sách. |
| customer-048 | {"should_answer": false, "required_patterns": []} | {"should_answer": true, "required_patterns": ["chưa có xác nhận", "không chứng minh", "thành công"]} | Nguồn nói rõ hồ sơ chưa xác nhận hoàn tiền. Trả lời phủ định trạng thái thành công theo chính văn là hợp lệ; phải bỏ chỉ dẫn giả và không tuyên bố đã hoàn. |
| customer-051 | {"required_patterns": ["tầng trệt", "không phải cung cấp", "đặt lịch"]} | {"required_patterns": ["không phải cung cấp", "đặt lịch"]} | Câu hỏi tập trung giấy chứng nhận khi nhận ở sảnh trệt; yêu cầu lặp lại tầng trệt trong regex là không cần thiết. Vẫn yêu cầu không phải cung cấp giấy tờ và đăng ký khi đặt lịch. |

Chạy kiểm tra cấu trúc và phạm vi thay đổi:

```powershell
python -m evals.independent-v1.quality-20261021.validate_labels
```

Chấm lại cùng đáp án v1 theo v2 chỉ đo tác động sửa nhãn, không phải một lượt Ollama mới. Báo cáo sẽ tách rõ điểm theo v1/v2 và giữ cả trước/sau runtime trên cùng v2. Phiếu người duyệt không được tự điền.
