# Xử lý ưu tiên cao còn lại — 09/10/2026

## Phạm vi

Giữ nguyên corpus và nhãn của 180 ca; không thêm từ ngoài nguồn để đạt regex. Không đổi model `qwen3:4b`, embedding `embeddinggemma:300m`, ngưỡng truy hồi 0,35 hoặc bật chế độ suy luận dài. Không nạp chính sách thử vào kho tri thức người dùng.

- Hỏi lại câu bảo hành cá nhân thiếu sản phẩm trước truy hồi; lịch sử do bot gợi ý không chứng minh sản phẩm của khách.
- Giữ lịch sử khách hàng ở truy hồi, bộ chọn và kiểm định ban đầu. Lượt kiểm định ngữ nghĩa lại tách câu hiện tại khỏi lịch sử để tránh nhầm câu hỏi cũ; lịch sử vẫn giải nghĩa câu nối tiếp, không làm nguồn chính sách.
- Nếu chunk đứng đầu truy hồi có dấu hiệu bắt đầu giữa câu (ký tự đầu viết thường), bộ chọn nêu mệnh đề trọng tâm trước ID. Không kích hoạt vì đoạn phụ không liên quan. Chỉ thu hẹp vào câu **khớp nguyên văn toàn câu** trong nguồn đã chọn, sau khi kiểm tra toàn bộ ID. Đây là heuristic giới hạn, không phải bộ tách câu tổng quát. Mệnh đề tự sinh không bao giờ trở thành đáp án. Câu phụ thuộc vẫn được mở rộng ngữ cảnh rồi kiểm định lại.
- Câu “không đủ” giữ điều kiện xác minh ở các câu trước, tránh chỉ trả phủ định mà thiếu cách cấp quyền.
- Cho phép tối đa một lần sửa trích dẫn hoặc kiểm định ngữ nghĩa lại trên bằng chứng nguyên văn. Lượt đầu có thể từ chối do thiếu ý/hiểu sai câu; lượt cuối vẫn phải xác nhận đủ ý, claim có nguồn, không xung đột và không cần hỏi lại. Không lấy đa số hoặc tự đổi cờ kiểm định. Xung đột, JSON sai hoặc cờ mâu thuẫn thì dừng, không thử lại. Tổng tối đa ba lần chat, vẫn kiểm tra phiên bản tất cả nguồn trước khi trả lời. Cùng model tự kiểm định không chứng minh đáp án đúng.
- Với yêu cầu rõ “hoàn tiền”, chỉ cho bộ chọn lấy câu có từ chỉ hoàn/refund; bộ kiểm định vẫn thấy toàn bộ nguồn, kể cả nguồn không được chọn. Đây là kiểm tra chủ đề giới hạn, chưa bao phủ mọi cách diễn đạt tiếng Việt hoặc ngôn ngữ khác.
- Yêu cầu số tài khoản phải có chuỗi số cạnh nhãn tài khoản trong nguồn và trong trích dẫn cuối. Lời khuyên không gửi thông tin cá nhân không thay thế số tài khoản còn thiếu. Định dạng lạ có thể bị từ chối thận trọng; không đoán hoặc tự tạo thông tin thanh toán.

## Bằng chứng

- `python -m unittest discover -s app/tests`: **209 kiểm thử đạt** trên bản cuối, log cục bộ `output/priority-followup-final-unittest-v10.log`. Riêng RAG: 49 kiểm thử. `git diff --check` đạt.
- Các kiểm thử mới bao gồm thiếu sản phẩm, giữ lịch sử khách hàng, giữ bước xác minh, không ghép qua injection, thu hẹp câu nguyên văn, không dùng câu tự sinh, không che ID sai và giới hạn kiểm định lại.
- Lượt thử `bt20/runs/priority-followup-v1-20261009` dừng ở 31 ca, 27 đạt, do phát hiện hồi quy. Manifest đánh dấu `incomplete`, không dùng làm lượt nghiệm thu. Raw completions và snapshot giữ nguyên.
- Lượt `priority-followup-v2-20261009`: BT20 55/60, context 22/24, PDF/DOCX dừng sau 4 ca. Không chọn bản này vì thay đổi bộ chọn quá rộng và dùng kiểm định ngữ nghĩa ngắn cả khi sửa bằng chứng gây hồi quy. Bản cuối giữ prompt/schema cũ trên chunk không có dấu hiệu cắt đầu câu; sửa ID vẫn dùng kiểm định cũ, không tự chuyển sang kiểm định ngữ nghĩa lại.
- Lượt trung gian tên `priority-followup-final-20261009` hoàn tất đủ 180 ca: BT20 58/60, context 23/24, PDF/DOCX 24/24, TXT 47/48, policy 24/24, tổng 176/180. Tên thư mục không có nghĩa đã nghiệm thu. Lượt này phát hiện trả nhầm mốc giao hàng cho hoàn tiền và trả lời chung thay số tài khoản; vì vậy bổ sung chặn chủ đề và số tài khoản rồi đo lại vào `priority-followup-verified-20261009`.
- Thử bật suy luận dài chỉ trên một số ca không được chọn: chậm hơn rõ rệt và vẫn có ca bị từ chối sai. Cấu hình vận hành giữ `think=false`.

Lượt `priority-followup-verified-20261009` đạt 177/180 nhưng `doc-013` bị hỏi lại vì một chunk phụ bị cắt đầu câu kích hoạt chế độ chọn trọng tâm. Bản sau chỉ kích hoạt theo chunk đầu truy hồi; test schema có nguồn phụ viết thường để kiểm tra điều kiện này.

Lượt được chọn là `priority-followup-verified-v2-20261009`; các lượt khác chỉ phục vụ thử nghiệm. Kiểm tra riêng ca lỗi không thay thế kiểm thử hồi quy. Các log kiểm thử có cảnh báo deprecation từ thư viện hiện có; không cài thêm dependency hoặc sửa phần không liên quan.

## Kết quả hồi quy đóng băng

Lượt: `priority-followup-verified-v2-20261009`. So với `priority-final-20261009` trên cùng corpus/nhãn.

| Bộ | Trước | Sau | Ca mới lỗi | p50 / p95 (giây) |
|---|---:|---:|---|---:|
| bt20 | 58/60 | 59/60 | bt20-032 | 5.652 / 9.437 |
| rag-context | 24/24 | 24/24 | Không | 5.306 / 7.18 |
| rag-documents | 23/24 | 24/24 | Không | 5.687 / 8.449 |
| rag | 45/48 | 47/48 | Không | 5.354 / 8.02 |
| rag-policy | 23/24 | 24/24 | Không | 5.947 / 7.92 |

Tổng **178/180** đạt rubric tự động; 0 lỗi provider; 0 ca chứa chuỗi cấm.
**164/164** quote khớp nguyên văn chunk; không đồng nghĩa đủ ý hoặc đúng ngữ nghĩa.
Mâu thuẫn 13/13; injection 17/17 trên bộ thử này, không bảo đảm toàn diện.
Đã đối chiếu hash corpus/nhãn với baseline và hash mọi file trong manifest với workspace; không đổi dữ liệu đánh giá sau đo.
Chưa có nhãn người thật duyệt hoặc tập kín độc lập. Không công bố số này là độ chính xác thực tế.

### bt20

- Sửa được: bt20-006, bt20-037.
- Recall@5 trên ca có gold: 1.0.
- Kết quả: `evals/bt20/runs/priority-followup-verified-v2-20261009/results.jsonl`.

**bt20-032** — Thời hạn hoàn tiền tính từ lúc tôi nhắn yêu cầu hay lúc nào?

Kỳ vọng: Tính sau khi nhận và kiểm tra hàng trả, với yêu cầu được chấp thuận.

Đáp án:

Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.

### rag-context

- Sửa được: Không.
- Recall@5 trên ca có gold: 1.0.
- Kết quả: `evals/rag-context/runs/priority-followup-verified-v2-20261009/results.jsonl`.

### rag-documents

- Sửa được: doc-006.
- Recall@5 trên ca có gold: 1.0.
- Kết quả: `evals/rag-documents/runs/priority-followup-verified-v2-20261009/results.jsonl`.

### rag

- Sửa được: test-029, test-037.
- Recall@5 trên ca có gold: 1.0.
- Kết quả: `evals/rag/runs/priority-followup-verified-v2-20261009/results.jsonl`.

**test-026** — Chủ nhật có nhận không?

Kỳ vọng: Không, chỉ nhận thứ Hai đến thứ Bảy.

Đáp án:

Dịch vụ giao hỏa tốc của cửa hàng mẫu chỉ nhận đơn tại quận 1 từ 8 giờ đến 15 giờ, từ thứ Hai đến thứ Bảy.

### rag-policy

- Sửa được: policy-013.
- Recall@5 trên ca có gold: 1.0.
- Kết quả: `evals/rag-policy/runs/priority-followup-verified-v2-20261009/results.jsonl`.

## Phần cần người độc lập

### Đối chiếu thủ công bởi trợ lý, không phải nhãn người thật

| Ca tồn đọng ban đầu | Đối chiếu bản cuối |
|---|---|
| bt20-006 | Trả đúng mốc trước đóng gói, giữ bước liên hệ sau đóng gói. |
| bt20-037 | Giữ đủ xác minh, mã truy cập đúng đơn và giới hạn tên/mã đơn. |
| doc-006 | Chỉ trích câu hóa đơn, đủ 4 ngày làm việc và mốc xác nhận biên bản. |
| test-026 | Trả đúng nguyên văn phạm vi thứ Hai–thứ Bảy; rubric vẫn đòi từ “không”. |
| test-029 | Giữ mốc xác nhận nhận lại hàng trả trong câu hoàn tiền. |
| test-037 | Hỏi lại, không tự chọn thời hạn bảo hành khi khách chưa nêu sản phẩm. |
| policy-013 | Có phủ định không khắc kim loại; vẫn kèm đoạn đổi sai màu không cần thiết. Rubric đạt không đồng nghĩa đáp án đã gọn hoặc tối ưu. |

**Chưa hoàn tất toàn bộ ưu tiên cao.** Ca mới chưa đạt `bt20-032`: nguồn và bộ chọn đã đúng thời điểm hoàn tiền, nhưng kiểm định cùng model vẫn hỏi lại sai. Bản cuối không còn lấy mốc giao hàng làm đáp án. Giữ từ chối thận trọng, không bypass review hoặc đổi nhãn để lấy điểm. Cần cải thiện độ ổn định ngữ nghĩa và duyệt độc lập trước nghiệm thu; các lượt thử cho thấy ngay cả nhiệt độ 0 cũng không nên suy từ một lượt đạt thành bảo đảm ổn định.

`rag/test-026` đòi từ `không`, dù gold nguyên văn chỉ nói nhận từ thứ Hai đến thứ Bảy. Trợ lý đã đối chiếu nguồn và ghi bất đồng; chưa có người duyệt kết luận. Không sửa nhãn cũ hay đổi số liệu hồi quy.

Phiếu `human-review.jsonl` của từng lượt giữ trống. Quy trình duyệt toàn tập, xử lý nhãn bất đồng, đóng băng runtime và nhận tập kín mới nằm trong `NGHIEM_THU_DOC_LAP.md`. Không coi tài liệu hướng dẫn là bộ đánh giá độc lập đã hoàn thành.
