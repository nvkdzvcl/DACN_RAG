# RAG quality regression - 2026-10-21

240 real Ollama cases in temporary DB/Qdrant stores, not customer data. Labels v2 are AI proposals awaiting human approval.
Regression only, not independent acceptance. Model unchanged; answer review remains mandatory.

## Same-label comparison

| Dataset | Safety (rescored on same labels) | This run | Service errors | p50 / p95 (s) |
|---|---:|---:|---:|---:|
| evals/independent-v1/customer-v2/main | 38/48 | 47/48 | 0 | 5.899 / 8.958 |
| evals/independent-v1/customer-v2/reserve | 9/12 | 11/12 | 0 | 5.335 / 7.827 |
| evals/rag | 48/48 | 48/48 | 0 | 5.259 / 7.253 |
| evals/bt20 | 58/60 | 60/60 | 0 | 6.534 / 9.337 |
| evals/rag-context | 22/24 | 22/24 | 0 | 5.335 / 10.146 |
| evals/rag-documents | 24/24 | 24/24 | 0 | 5.76 / 8.659 |
| evals/rag-policy | 24/24 | 24/24 | 0 | 5.713 / 9.873 |

## Label changes versus runtime changes

OFFLINE rescoring of saved answers, not additional Ollama calls. V1/v2 differ only in labels 024/048/051.

| Runtime | Labels v1 /60 | Labels v2 /60 |
|---|---:|---:|
| baseline-20261021 | 43 | 46 |
| safety-final-20261021 | 44 | 47 |
| quality-final-20261021 | 56 | 58 |

## Gains, regressions and failures

### evals/independent-v1/customer-v2/main

Gained: customer-003, customer-014, customer-021, customer-027, customer-028, customer-029, customer-030, customer-031, customer-035.
Regressed: none.
Quotes missing from retrieved chunks: none.

#### customer-022 (missing_information)

Củ sạc hãng khác nhà em không còn nhãn, xác nhận giúp nó có Power Delivery để chạy QI-M nhé?

Expected: Không xác định được chuẩn củ sạc chưa có thông số; cần model/thông số, không đoán tương thích.

Actual:

Sạc đế QI-M: Đế QI-M dùng đầu vào USB-C Power Delivery tối thiểu 18 W; cáp chuyển đầu chỉ thay hình dạng đầu cắm, không bổ sung chuẩn Power Delivery. Không khẳng định tương thích với mọi điện thoại hoặc mọi củ sạc chỉ dựa vào việc cắm vừa.

### evals/independent-v1/customer-v2/reserve

Gained: customer-055, customer-056.
Regressed: none.
Quotes missing from retrieved chunks: none.

#### customer-053 (missing_information)

Mã quà em gửi nhầm đã bị người khác dùng chưa, kiểm tra và xác nhận ngay giúp em?

Expected: Không có dữ liệu sử dụng mã trực tiếp; nhân viên kiểm tra sau xác thực, không đoán trạng thái.

Actual:

Mã quà điện tử gửi nhầm email: Nếu mã chưa được sử dụng, chủ đơn đã xác thực yêu cầu nhân viên vô hiệu hóa mã cũ rồi phát lại tới email đúng. Nếu mã đã được sử dụng, chuyển kiểm tra riêng và không hứa phát lại. Chỉ biết email nhận không đủ quyền đổi mã.

### evals/rag

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/bt20

Gained: bt20-008, bt20-045.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag-context

Gained: context-013.
Regressed: context-005.
Quotes missing from retrieved chunks: none.

#### context-005 (answerable)

Nếu lỗi TN8 nằm ngoài bảo hành thì có sửa ngay không báo giá không?

Expected: Nhân viên báo chi phí trước khi khách quyết định.

Actual:

Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

#### context-008 (answerable)

Đổi TN8 vì chọn sai màu có được hoàn tiền ship ban đầu không?

Expected: Không hoàn phí giao ban đầu.

Actual:

Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên.

### evals/rag-documents

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag-policy

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

## Limits and next steps

- Human review is still required for failures and three proposed labels; human-review.jsonl remains blank.
- Freeze code/model/corpus and thresholds before another team authors a new held-out set; these 60 cases are development data.
- Regex and role-block filters cover tested patterns, not arbitrary prompt injection.
- Verbatim quotes do not prove semantic correctness/completeness. One run does not prove model stability.
- Interrupted quality-v1-20261021 results are excluded from final counts.
