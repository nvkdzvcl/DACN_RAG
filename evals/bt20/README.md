# Kiểm chứng RAG trên chính sách BT20

Bộ 60 câu được soạn và kiểm tra nguồn trước khi chạy ngày 08/10/2026. Đây là tập kiểm tra tổng hợp do trợ lý soạn, chưa có người duyệt độc lập; không đại diện phân bố câu hỏi khách hàng thật.

## Phạm vi

- 40 câu chính sách trực tiếp: sản phẩm, thanh toán, giao hàng, đổi trả, bảo hành, hoàn tiền, quyền tra cứu đơn.
- 4 câu nối tiếp có lịch sử; 4 câu thử chống chỉ dẫn giả trong câu hỏi/lịch sử.
- 6 câu thiếu dữ liệu, 2 câu thiếu ngữ cảnh và 4 câu nguồn mâu thuẫn.
- 46 câu dự kiến có thể trả lời từ nguồn, 14 câu dự kiến cần từ chối/làm rõ/chuyển nhân viên.

`corpus/test-bt20.md` là bản sao nguyên nội dung `docs/chinh-sach-mau-binh-giu-nhiet-BT20.md` tại thời điểm đo. Hai tài liệu CX10 là dữ liệu mâu thuẫn chủ động tạo cho kiểm thử, không phải chính sách cửa hàng. Không nhập các tài liệu kiểm thử này vào kho tri thức đang dùng.

Câu hỏi, đáp án đối chiếu, vị trí nguồn và mẫu từ khóa nằm trong `cases.jsonl`. Không sửa nhãn hoặc prompt RAG sau khi xem kết quả của lượt `current-20261008`. Nếu nhãn chưa hợp lý, ghi nhận riêng trong phần đọc đánh giá; giữ kết quả máy ban đầu.

## Chạy lại

Từ root repo, với Ollama và hai model đã có:

```powershell
$env:TELEGRAM_ENABLED='false'
$env:OLLAMA_HOST='http://127.0.0.1:11434'
$env:LLM_MODEL='qwen3:4b'
$env:EMBEDDING_MODEL='embeddinggemma:300m'
python -m app.evaluate_rag --dataset evals/bt20 --split test --output evals/bt20/runs/new-run
```

Thư mục kết quả phải chưa tồn tại. Runner dùng SQLite/Qdrant/tài liệu tạm; ingestion, embedding và generation gọi Ollama thật. Wrapper chỉ ghi lại đầu ra model, không thay đáp án bằng mock. Không đo trình duyệt, điều phối đơn hàng, Telegram hoặc tải đồng thời.

## Cách đọc kết quả

- `manifest.json`: hash dữ liệu/mã nguồn, model digest, cấu hình và trạng thái hoàn tất. Mã ứng dụng có thay đổi chưa commit được ghi bằng hash từng file.
- `ingestion.json`: trạng thái nạp tài liệu và số chunk.
- `results.jsonl`: câu hỏi, đáp án, nguồn truy hồi, trích dẫn, đầu ra chọn/kiểm định và thời gian từng ca.
- `summary.json`: chỉ số tự động; mẫu từ khóa không thay chấm ngữ nghĩa. `gold_source_citation_precision` chỉ đo khớp tập đoạn nguồn đã gán nhãn, không đồng nghĩa tỷ lệ bịa nội dung.
- `human-review.jsonl`: phiếu trống cho người duyệt thật; không điền tên người hoặc giả là đánh giá độc lập.

Nhãn `grounded=true` là quyết định của pipeline có kiểm định bằng cùng model. Cần đọc nội dung và điều kiện để kết luận đúng; trích dẫn khớp nguồn chưa đủ chứng minh câu trả lời phù hợp câu hỏi. p50/p95 chỉ áp dụng cho tập này chạy tuần tự trên máy đo, không phải SLO production.

## Kết quả lượt 08/10/2026

Hoàn tất 60/60 câu, không lỗi dịch vụ; 43/60 đạt rubric tự động. Đọc KET_QUA.md trước khi diễn giải các chỉ số và xem CHI_TIET_60_CAU.md để đối chiếu từng câu. Pipeline chưa được sửa theo kết quả này.
