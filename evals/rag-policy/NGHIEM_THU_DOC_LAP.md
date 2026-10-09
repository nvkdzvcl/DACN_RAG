# Nghiệm thu RAG độc lập

Trạng thái: **chưa có người duyệt hoặc tập kín độc lập**. Tài liệu này chuẩn bị quy trình, không chứng nhận độ chính xác. Các bộ `bt20`, `rag-context`, `rag-documents`, `rag`, `rag-policy` đã được dùng để sửa hệ thống, chỉ còn giá trị hồi quy. Chính sách mẫu không dùng cho khách thật.

## 1. Duyệt nguồn và nhãn hồi quy

Người duyệt sao chép `human-review.jsonl` từ từng thư mục lượt chạy được ghi trong `XU_LY_TON_DONG_20261009.md`. Không sửa phiếu gốc hoặc điền tên người thật bằng công cụ tự động.

Đối chiếu từng câu với tài liệu gốc, vị trí nguồn và toàn bộ điều kiện; không dùng `fact_pattern_pass` hoặc kết luận của model làm nhãn người duyệt. Khi duyệt câu nối tiếp, đọc cả lịch sử khách hàng.

- `gold_label_approved`: nhãn kỳ vọng có đúng với nguồn và câu hỏi không?
- Đáp án có nguồn: chấm `answer_correct`, `all_claims_supported`, `citation_entailment_correct`; để `abstention_correct=null`.
- Đáp án từ chối/hỏi lại: chấm `abstention_correct`; để ba trường đáp án có nguồn là `null`.
- Lỗi provider: không chấm đúng/sai đáp án; lưu ghi chú và đo lại trong lượt mới.
- Ghi tên người duyệt thật trong `reviewer`, giải thích nhãn bị bác bỏ trong `notes`.

Ưu tiên bảy ca tồn đọng ban đầu, mọi ca hồi quy mới, mâu thuẫn, injection và hỏi nối tiếp. Muốn báo tỷ lệ toàn tập phải duyệt toàn bộ, không chỉ ca lỗi.

### Bất đồng cần phân xử: `rag/test-026`

Khách hỏi Chủ nhật có nhận giao hỏa tốc không. Gold trích: “Dịch vụ giao hỏa tốc của cửa hàng mẫu chỉ nhận đơn tại quận 1 từ 8 giờ đến 15 giờ, từ thứ Hai đến thứ Bảy.” Rubric đòi từ `không`, nhưng câu nguồn không có từ đó. Luồng trích nguyên văn có thể trả đúng phạm vi hoạt động mà vẫn trượt rubric. Đây là nhận xét của trợ lý, **chưa phải kết luận người duyệt**.

Không chèn thêm từ `không` ngoài nguồn hoặc trích câu phủ định không liên quan chỉ để đạt điểm. Nếu người duyệt chấp thuận nhãn ngữ nghĩa khác, tạo phiên bản dataset mới, ghi người duyệt/lý do và chạy baseline cùng runtime mới trên cùng phiên bản mới. Giữ nguyên điểm, corpus và nhãn của lượt cũ.

Chạy từ thư mục gốc; thay các đường dẫn ví dụ bằng phiếu đã được người thật chấm:

```powershell
python -m app.review_rag --run evals/rag/runs/TEN_LUOT --reviews output/rag-human-reviewed.jsonl --output output/rag-human-report.json
```

## 2. Đóng băng trước khi nhận tập kín

1. Chọn đúng lượt hồi quy cuối trong báo cáo tồn đọng. Lưu `manifest.json`, các snapshot mã, digest model và kết quả. Commit nền không đủ vì có thể còn thay đổi chưa commit; phải đối chiếu SHA-256.
2. Người soạn tập kín độc lập với người chỉnh prompt. Không gửi câu hỏi/đáp án cho người phát triển trước khi đóng băng. Không tái diễn đạt câu đã dùng để chỉnh hệ thống rồi gọi đó là tập độc lập.
3. Người soạn chọn chính sách mới, có quyền sử dụng và không chứa dữ liệu khách thật. Chuẩn bị các nhóm có đáp án, hỏi nối tiếp, thiếu thông tin, ngoài nguồn, mâu thuẫn và injection; gồm cả đáp án phủ định và mốc thời gian theo sự kiện.
4. Người thứ hai duyệt nguồn, nhãn và điều kiện. Chốt số lượng từng nhóm và tiêu chí đạt trước khi chạy. Ghi ngày, tên người soạn/người duyệt, SHA-256 corpus/cases và bằng chứng đóng băng; trường chưa có bằng chứng giữ trạng thái chờ.
5. Sau đóng băng mới đưa dataset vào `evals/independent-v1/`: `cases.jsonl` và `corpus/test-*`. Schema theo `evals/rag-policy/cases.jsonl`; các câu dùng `split=test`, ID/nhóm riêng, gold quote có nguồn/vị trí chính xác. Với câu buộc hỏi lại, đặt `should_answer=false`, `should_clarify=true`.
6. Chạy một lần với runtime/model/config đã đóng băng. Không chỉnh prompt khi đang đo; không nạp corpus kiểm thử vào kho tri thức sản xuất.

```powershell
python -m app.evaluate_rag --split test --dataset evals/independent-v1 --output evals/independent-v1/runs/frozen-v1
python -m app.review_rag --run evals/independent-v1/runs/frozen-v1 --reviews output/independent-v1-human-reviewed.jsonl --output output/independent-v1-human-report.json
```

`app.evaluate_rag` kiểm tra gold với corpus, ghi hash/digest và chạy DB/Qdrant tạm. Nó không xác minh danh tính người soạn hoặc chứng minh tập đã được giữ kín. Phải lưu bằng chứng độc lập ngoài kết quả công cụ.

## 3. Điều kiện kết thúc

- Không lỗi vận hành; không có hồi quy an toàn chưa xử lý. Xem từng nhóm và mẫu số, không chỉ tổng điểm.
- Mọi ca chưa đạt/bất đồng có kết luận người duyệt và hành động rõ ràng; không sửa ngầm nhãn sau đo.
- Người thật duyệt toàn bộ tập kín; báo cáo tên, số ca được duyệt, phạm vi và giới hạn. Không suy từ bộ mẫu sang độ chính xác khách thật.
- Nếu dùng lỗi tập kín để sửa hệ thống, tập đó trở thành hồi quy. Muốn nghiệm thu độc lập phiên bản tiếp theo cần tập kín mới.

Phần viết/duyệt tập kín và ký kết luận vẫn cần người độc lập. Trợ lý không tự điền thay.
