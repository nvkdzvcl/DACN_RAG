# Đánh giá RAG tiếng Việt

Phiên bản đầu gồm 72 câu do trợ lý soạn trên chính sách **cửa hàng giả lập**, chưa được người dùng duyệt nhãn. Không dùng các chính sách này cho khách thật. Đây là baseline kỹ thuật cho retrieval và trả lời có nguồn; không đại diện lưu lượng thực tế hoặc chứng minh hệ thống không hallucination.

## Dữ liệu và cách tách tập

- `cases.jsonl`: câu hỏi, lịch sử ngắn, nhóm nội dung, đáp án kỳ vọng, nguồn/vị trí/quote, biểu thức kiểm tra dữ kiện và trạng thái duyệt.
- `corpus/`: sáu tài liệu TXT cố định. Mỗi lần chạy chỉ nhập tài liệu có tiền tố đúng tập; tài liệu sản xuất không được đọc hay sửa.
- `dev`: 24 câu để phân tích lỗi/hiệu chỉnh; `test`: 48 câu cố định. Câu diễn đạt lại/hỏi nối tiếp của cùng một chính sách có đáp án nằm cùng tập. Nguồn của hai tập khác nhau. Mẫu ý định chung vẫn giống nhau, đặc biệt câu thiếu tên sản phẩm hoặc yêu cầu bịa; chưa loại trùng ngữ nghĩa bằng người. Không coi đây là tập kiểm tra độc lập ngoài miền.
- Sáu loại câu: có đáp án, hỏi nối tiếp, ngoài tài liệu, thiếu thông tin, nguồn mâu thuẫn và prompt injection. Các chỉ dẫn độc hại trong corpus là dữ liệu thử nghiệm.
- Câu thiếu thông tin yêu cầu từ chối kết luận cụ thể và đề nghị làm rõ; câu mâu thuẫn yêu cầu không tự chọn một văn bản khi chưa có thứ tự hiệu lực. Người duyệt có thể chấp nhận câu trả lời nêu rõ các phương án thay vì từ chối hoàn toàn; khi đó phải sửa nhãn trong phiên bản dữ liệu mới.

Không sửa câu hỏi/nhãn của một baseline đã chạy. Nếu cần sửa, giữ kết quả cũ, ghi lý do và chạy vào thư mục mới. Sau khi đã xem lỗi ở tập test, tập này trở thành regression cho phiên bản sau; cần thêm tập kiểm tra chưa xem để tuyên bố khả năng tổng quát hóa.

## Chạy

Từ thư mục gốc dự án, cài `requirements-dev.txt` và khởi động Ollama có `qwen3:4b` cùng `embeddinggemma:300m` (các baseline cũ dùng `qwen3:1.7b`):

```powershell
python -m unittest app.tests.test_evaluate_rag -v
python -m app.evaluate_rag --split dev --output evals/rag/runs/my-dev-run
python -m app.evaluate_rag --split test --output evals/rag/runs/my-test-run
```

Trình chạy đọc biến môi trường hiện tại, không tự nạp `.env`. Mặc định model/ngưỡng giống ứng dụng. Muốn so cấu hình khác, đặt `LLM_MODEL`, `EMBEDDING_MODEL`, `RAG_MIN_SCORE` trong terminal chạy benchmark. Chạy tuần tự, tránh hỏi AI hoặc upload tài liệu ở ứng dụng trong lúc đo để giảm tranh chấp GPU. Không cần dừng ứng dụng.

Tùy chọn `--dataset` chọn thư mục bộ dữ liệu khác trong repo; mặc định giữ bộ TXT này. Bộ PDF/DOCX bổ sung ở `../rag-documents/`, chạy với `--dataset evals/rag-documents --split test`. CLI hỗ trợ các định dạng ingestion hiện có; gold được đối chiếu vị trí bằng cùng parser/chunker, phải nằm trọn trong một chunk. Với gold có `page`, chấm cả page và location. Các lượt mới có `ingestion.json` ghi thời gian/trạng thái/số chunk và hash mỗi file; corpus/nhãn và kết quả TXT cũ giữ nguyên.

Mỗi lần chạy tạo SQL DB và Qdrant trong thư mục tạm; đóng/mở kho vector sau ingestion trước khi hỏi. Thư mục kết quả bắt buộc chưa tồn tại để tránh ghi đè. Khi lỗi provider, ghi lỗi và tiếp tục; lỗi không được tính là từ chối đúng. Mã thoát khác 0 nếu có lỗi vận hành; chất lượng thấp vẫn xuất báo cáo đầy đủ, chưa có ngưỡng nghiệm thu tự động.

## Kết quả và thước đo

`manifest.json` lưu commit nền, SHA-256 corpus/cases/mã Python thực chạy (kể cả thay đổi chưa commit), digest model, tham số và phiên bản thư viện. `results.jsonl` lưu từng đáp án, kết quả truy xuất, citation, completion thô, thời gian và điểm. `summary.json` tổng hợp cả tập và từng loại câu. `human-review.jsonl` là phiếu chấm để trống; số ca được người duyệt hiện là 0.

Luồng hiện tại gọi chat tối đa hai lần: chọn câu nguồn bằng ID, rồi kiểm định đáp án do backend ghép nguyên văn nếu lựa chọn hợp lệ. Baseline cũ dùng sinh đáp án tự do. `raw_completions` lưu đúng thứ tự gọi, kể cả kết quả kiểm định từ chối; thời gian tính cả hai lượt. Manifest ghi luồng thực chạy; snapshot `answer_service.py.txt` lưu prompt/schema của từng thử nghiệm. Kết quả model kiểm định là quyết định nội bộ ứng dụng, không phải nhãn người chấm hoặc thước đo entailment độc lập.

Lượt bật suy luận còn lưu `ollama.py.txt`; manifest lấy `think`, `temperature`, `num_ctx` và `num_predict` trực tiếp từ cấu hình transport đang chạy. Giới hạn sinh tính cả token suy luận và câu trả lời. Phản hồi bị cắt do hết giới hạn (`done_reason=length`), chưa hoàn tất hoặc không có nội dung cuối được tính là lỗi provider, không tính là từ chối đúng. `raw_completions` chỉ chứa nội dung cuối; không xuất trường suy luận nội bộ của Ollama vào câu trả lời, citation hoặc lịch sử hội thoại.

| Chỉ số | Cách tính và giới hạn |
|---|---|
| Recall@1/3/5 | Trung bình số đoạn gold có trong top-k chia tổng đoạn gold của từng câu; chỉ câu có gold, bao gồm câu nguồn mâu thuẫn. So filename, vị trí và quote. Lỗi vận hành có recall 0. Đây là kết quả truy xuất trước ngưỡng score lọc cho LLM. |
| Gold-source citation precision | Số citation khớp vị trí nguồn gold và quote nguyên văn chia tổng citation được trả ra. Không có citation thì null; không đo entailment của từng mệnh đề. |
| Answerable citation coverage | Số câu có đáp án với ít nhất một citation khớp gold chia tổng câu phải trả lời, kể cả câu lỗi. |
| Correct abstention rate | Số câu phải từ chối trả `grounded=false` và citation rỗng, không lỗi provider, chia tổng câu phải từ chối. Không thay người duyệt chất lượng lời giải thích. |
| False abstention rate | Số câu phải trả lời nhưng từ chối chia tổng câu phải trả lời. Lỗi vận hành tách riêng, không tính là từ chối. |
| Decision accuracy | Tỷ lệ quyết định trả lời/từ chối khớp nhãn; lỗi provider tính sai. |
| Fact-pattern pass | Câu có đáp án: grounded, đủ mẫu dữ kiện, có nguồn gold, không có chuỗi cấm. Câu phải từ chối: abstain không lỗi/chuỗi cấm. Chỉ là proxy tự động, có thể bỏ sót sai nghĩa, phủ định hoặc thông tin thừa. |
| p50/p95 | Nội suy tuyến tính trên thời gian end-to-end từng câu thành công, gồm embedding truy vấn và tải/gỡ model, không gồm ingestion. Lưu số mẫu; lỗi/timed out tách riêng. Chưa phải SLA hay tải đồng thời. |

## Duyệt bằng người

Đối chiếu từng dòng `results.jsonl` với corpus gốc, không chỉ nhìn `grounded` hoặc điểm tự động. Trong `human-review.jsonl`, ghi người duyệt và ghi chú, duyệt nhãn trước rồi chấm: đáp án đúng câu hỏi, mọi mệnh đề có bằng chứng, citation chứng minh mệnh đề và quyết định từ chối phù hợp. Trường không áp dụng giữ null. Kết quả tự động không tự cập nhật thành điểm người chấm.

Ưu tiên duyệt mọi ca không đạt proxy, mọi câu mơ hồ/mâu thuẫn/injection và một mẫu câu đạt. Muốn công bố tỷ lệ đúng hoặc có căn cứ bằng người, cần chấm đủ tập hoặc nêu rõ cách lấy mẫu và mẫu số. Chưa dùng model tự chấm làm ground truth; chưa có dữ liệu người dùng thật hay kiểm tra PDF/OCR chất lượng cao trong benchmark TXT này.
