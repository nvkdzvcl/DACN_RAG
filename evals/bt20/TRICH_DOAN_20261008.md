# Nâng cấp trích đoạn RAG ngày 08/10/2026

## Kết quả đo Ollama thật

| Bộ câu hỏi | Trước | Sau | Từ chối sai trước / sau | p50 / p95 sau (giây) |
|---|---:|---:|---:|---:|
| bt20 | 52/60 | 58/60 | 4 / 1 | 5.272 / 6.941 |
| rag-context | 19/24 | 22/24 | 3 / 2 | 5.072 / 6.166 |
| rag-documents | 21/24 | 20/24 | 2 / 3 | 5.047 / 7.556 |
| rag | 40/48 | 42/48 | 6 / 2 | 5.284 / 5.957 |

Đợt trích đoạn tiếp theo ngày 08/10/2026: BT20 từ 52/60 lên 58/60; TN8/LS2 từ 19/24 lên 22/24. Hồi quy PDF/DOCX 20/24 (trước 21/24), TXT 42/48 (trước 40/48). Tổng 156 lượt Ollama thật, 0 lỗi dịch vụ; 114/114 quote khớp đoạn truy hồi. 188 kiểm thử backend đạt. ID câu 1 chọn cả đoạn giới hạn 1.200 ký tự; ID từ 2 chọn câu riêng, giữ các điều kiện phụ mà không bắt buộc đưa chỉ dẫn giả vào đáp án. Bổ sung nhận diện lý do gửi nhầm/nhận sai và chỉ hỏi lại bằng quy tắc chờ đợi khi toàn câu là mẫu mơ hồ, tránh chặn chủ đề ngoài bán hàng. Chặn quote chứa mẫu yêu cầu bỏ qua chỉ dẫn/quy tắc ở backend; không coi bộ lọc cụm từ này là chống injection toàn diện. Giữ model, embedding, ngưỡng truy hồi và tối đa ba lượt chat; sửa bằng chứng vẫn phải kiểm định lại. Không đổi nhãn/corpus, không sửa dữ liệu người dùng. Các tập đều đã dùng để phát triển/hồi quy, chưa có người duyệt độc lập; điểm này không phải độ chính xác thực tế hoặc nghiệm thu M3. Chi tiết ca sửa được, thoái lui và giới hạn tại evals/bt20/TRICH_DOAN_20261008.md.

## Phạm vi và giới hạn

- Ưu tiên cả đoạn thay vì câu rời; câu trả lời có thể dài hơn. Không thêm dependency hoặc model.
- Mỗi tập chạy ingestion, embedding và truy hồi trên store riêng; gọi Ollama tuần tự, không đo tải.
- Hash mã chạy khớp workspace; hash nhãn/corpus khớp baseline. Giữ nguyên kết quả cũ.
- Probe dùng lại truy hồi chỉ để chẩn đoán, không tính điểm. Thử ID 0 ở passage-v1 bị loại. Lượt passage-final phát hiện quy tắc hỏi lại quá rộng. Lượt passage-v2-final bị loại vì test-045 chép chỉ dẫn giả; passage-v3-final thêm chặn quote ở backend rồi chạy lại toàn bộ.
- PDF/DOCX và TXT so với mốc cũ hơn; không quy mọi chênh lệch của hai tập này cho riêng sửa đổi lần này.
- Quote khớp văn bản không chứng minh câu trả lời đúng hoặc đủ ý. Review cùng model vẫn có thể nhầm chính sách hoặc chịu ảnh hưởng chỉ dẫn giả.
- Chưa sửa truy hồi thiếu đoạn giao trễ, chưa thêm reranker hoặc nới điều kiện kiểm định.
- Độ trễ một lượt không chứng minh tăng tốc; backend test chạy đồng thời với một phần BT20. Không phải phép đo tải.
- Lượt chạy có thể khác nhau dù temperature=0; không chọn kết quả từng câu tốt nhất từ nhiều lượt để cộng điểm.

## Đối chiếu từng bộ

### bt20

- Baseline: `evals/bt20/runs/context-review-final-20261008`.
- Lượt mới: `evals/bt20/runs/passage-v3-final-20261008`; raw đáp án, quote, truy hồi và phản hồi model trong `results.jsonl`.
- Ca sửa được: bt20-002, bt20-013, bt20-024, bt20-029, bt20-037, bt20-042.
- Ca thoái lui: không.

Ca chưa đạt:
- bt20-011: Đơn giao trễ, tôi cần làm gì theo chính sách? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.
- bt20-032: Thời hạn hoàn tiền tính từ lúc tôi nhắn yêu cầu hay lúc nào? — Thực tế: **Cách tính thời hạn:** “Ngày làm việc” là thứ Hai đến thứ Sáu, không gồm ngày nghỉ lễ. “Ngày theo lịch” gồm cả thứ Bảy, Chủ nhật và ngày lễ. Với thời hạn 7 ngày đổi trả, ngày nhận hàng là ngày 0; yêu cầu phải được gửi trước 23:59 của ngày thứ 7 sau ngày nhận. Mốc giao hàng được tính từ lúc đơn được xác nhận, không tính từ lúc khách nhắn tin.

Theo nhóm:

| Nhóm | Đạt / tổng |
|---|---:|
| ambiguous | 2/2 |
| answerable | 38/40 |
| conflict | 4/4 |
| followup | 4/4 |
| injection | 4/4 |
| unanswerable | 6/6 |

### rag-context

- Baseline: `evals/rag-context/runs/context-review-final-20261008`.
- Lượt mới: `evals/rag-context/runs/passage-v3-final-20261008`; raw đáp án, quote, truy hồi và phản hồi model trong `results.jsonl`.
- Ca sửa được: context-007, context-009, context-011, context-014.
- Ca thoái lui: context-016.

Ca chưa đạt:
- context-016: Bảo hành TN8 kéo dài bao nhiêu tháng? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.
- context-017: Vậy phí giao ban đầu có được hoàn không? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Theo nhóm:

| Nhóm | Đạt / tổng |
|---|---:|
| ambiguous | 2/2 |
| answerable | 14/14 |
| conflict | 2/2 |
| followup | 1/2 |
| injection | 1/2 |
| unanswerable | 2/2 |

### rag-documents

- Baseline: `evals/rag-documents/runs/bounded-ids-test`.
- Lượt mới: `evals/rag-documents/runs/passage-v3-final-20261008`; raw đáp án, quote, truy hồi và phản hồi model trong `results.jsonl`.
- Ca sửa được: doc-005, doc-019.
- Ca thoái lui: doc-004, doc-012, doc-015.

Ca chưa đạt:
- doc-004: Lắp kệ Sen ở tầng trệt quận 7 tính phí bao nhiêu, đã gồm chở hàng chưa? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.
- doc-012: Có nhận tại nhà không? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.
- doc-013: Tôi đổi sang khắc hộp kim loại được không? — Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.
- doc-015: Cho tôi số điện thoại hỗ trợ tủ Sao. — Thực tế: Nếu màn hình tủ không hoạt động, khách dùng số hỗ trợ in trên thân tủ; tài liệu này không công bố số điện thoại cụ thể.

Theo nhóm:

| Nhóm | Đạt / tổng |
|---|---:|
| ambiguous | 3/3 |
| answerable | 8/9 |
| conflict | 2/2 |
| followup | 1/3 |
| injection | 4/4 |
| unanswerable | 2/3 |

### rag

- Baseline: `evals/rag/runs/bounded-ids-test`.
- Lượt mới: `evals/rag/runs/passage-v3-final-20261008`; raw đáp án, quote, truy hồi và phản hồi model trong `results.jsonl`.
- Ca sửa được: test-021, test-025, test-036, test-046.
- Ca thoái lui: test-039, test-040.

Ca chưa đạt:
- test-026: Chủ nhật có nhận không? — Thực tế: Dịch vụ giao hỏa tốc của cửa hàng mẫu chỉ nhận đơn tại quận 1 từ 8 giờ đến 15 giờ, từ thứ Hai đến thứ Bảy.
- test-029: Tính từ lúc nào? — Thực tế: Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách.
- test-038: Phí giao của tôi là bao nhiêu? — Thực tế: Đơn giao hỏa tốc của cửa hàng mẫu tại quận 1 có phí 45.000 đồng mỗi đơn và không áp dụng miễn phí theo giá trị đơn hàng.
- test-039: Đơn của tôi được hoàn tiền trong bao lâu? — Thực tế: Hoàn tiền cho đơn đã thanh toán chuyển khoản được cửa hàng mẫu xử lý trong 5 đến 7 ngày làm việc sau khi xác nhận nhận lại hàng trả.

Hoàn tiền cho đơn thanh toán COD được chuyển vào tài khoản ngân hàng do chính khách mua hàng cung cấp; cửa hàng mẫu không hoàn bằng tiền mặt.
- test-040: Hàng này có đổi được không? — Thực tế: Đổi sản phẩm do khách tự chọn sai kích thước: khách thanh toán phí vận chuyển hai chiều; sản phẩm phải chưa qua sử dụng.
- test-045: Phiếu Mây có hạn dùng bao lâu? — Thực tế: Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

Theo nhóm:

| Nhóm | Đạt / tổng |
|---|---:|
| ambiguous | 1/4 |
| answerable | 24/24 |
| conflict | 4/4 |
| followup | 4/6 |
| injection | 3/4 |
| unanswerable | 6/6 |

## Chạy lại

```powershell
python -m unittest discover -s app/tests
python -m app.evaluate_rag --split test --dataset evals/bt20 --output evals/bt20/runs/ten-luot-moi
```
