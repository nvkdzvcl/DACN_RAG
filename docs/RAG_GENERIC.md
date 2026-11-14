# Gỡ quy tắc đặc thù khỏi pipeline RAG (14/11/2026)

## Vì sao làm

Bản ngày 21/10 (`four-fixes-verified`) đạt **240/240 câu đúng quyết định** trên 7 bộ eval cũ. Đó không phải chất lượng thật: `answer_service.py` chứa nhiều regex tiếng Việt viết theo đúng cách hỏi của từng ca eval (ví dụ "gửi nhầm", "làm hộ", "gói này", "khoản bị trừ"), cùng các câu prompt vá riêng từng lỗi. Các bộ eval cũ vì vậy không còn đo được khả năng trả lời câu hỏi mới.

Để kiểm tra, nhóm tạo bộ [heldout-v1](../evals/heldout-v1/README.md) **trước khi** sửa code: cửa hàng, sản phẩm và cách hỏi mới, 41 câu, đóng băng bằng SHA-256.

| Bản | Bộ cũ (240 câu, đã dùng để tinh chỉnh) | heldout-v1 (41 câu, chưa thấy) |
|---|---:|---:|
| Regex cũ (`four-fixes-verified`) | 240/240 (100%) | 33/41 (80,5%) |

Khoảng cách 100% → 80,5% là mức overfit. Nhóm câu mơ hồ trên held-out chỉ đạt 1/5: regex không nhận ra cách hỏi mới.

## Thay đổi thiết kế

Nguyên tắc: **model chỉ chọn ID câu, backend chép nguyên văn** (giữ nguyên). Các quyết định ngữ nghĩa chuyển từ regex sang model, dựa trên nguồn truy hồi được.

| Bước | Trước | Sau |
|---|---|---|
| Câu hỏi nối tiếp | Ghép thô các tin khách trước vào query | LLM viết lại thành câu độc lập (chỉ khi có lịch sử khách); kết quả lỗi, không đổi hoặc chứa chỉ dẫn → quay về cách ghép cũ |
| Hỏi lại khách | ~15 regex theo cách hỏi cụ thể, chạy trước retrieval | Bước chọn câu trả `decision`: `answer` / `ask_customer` / `sources_disagree` / `not_in_sources`, dựa trên việc nguồn có nhiều quy định tùy điều kiện khách chưa nêu |
| Trạng thái riêng (voucher, giao dịch) | Regex chặn trước | `not_in_sources` khi khách yêu cầu kiểm tra trạng thái hoặc thực hiện hành động |
| Định dạng đáp án | Regex thêm "Không. Chủ nhật nằm ngoài lịch…", "Mốc bắt đầu: …" | Chỉ ghép nguyên văn câu nguồn |
| Lọc câu "hoàn tiền" | Bỏ mọi câu không chứa "hoàn/refund" | Bỏ |
| Prompt kiểm định | Hai biến thể + câu vá riêng (phí ship, số tài khoản, câu có/không) | Một prompt chung |
| Retry | Repair, prune, semantic retry | Chỉ một lần repair theo ID reviewer chỉ ra, review lại |

Giữ lại (quy tắc an toàn hoặc cấu trúc, không phụ thuộc cách hỏi): lọc chỉ dẫn/role tag trong nguồn và lịch sử, kiểm tra ID câu, kiểm tra số điện thoại/số tài khoản phải nằm cạnh nhãn, phát hiện điều khoản bị phủ định ngược (`opposing_policy`) và thông báo cạnh tranh không rõ hiệu lực (`unresolved_notices`), kiểm tra lại phiên bản nguồn.

Số lần gọi model: 2 (chọn + kiểm định), +1 khi có lịch sử khách, +1 khi repair.

## Cấu trúc module (ưu tiên 3)

| Module | Vai trò | Gọi model? |
|---|---|---|
| `app/rag/safety.py` | Lọc chỉ dẫn/role tag, làm sạch lịch sử, quy tắc số điện thoại/số tài khoản, kiểm tra mâu thuẫn cấu trúc | Không |
| `app/rag/evidence.py` | Tách câu, dựng danh sách câu chọn được, JSON Schema ràng buộc ID, ghép nguyên văn | Không |
| `app/rag/prompts.py` | Ba system prompt (viết lại, chọn câu, kiểm định) | Không |
| `app/rag/answer_service.py` | Điều phối và ba lượt gọi model qua `ask_model` | Có |

Unit test riêng từng bước: `app/tests/test_rag_stages.py` (không cần DB, vector hay Ollama). Eval runner giờ snapshot mọi file trong `app/rag/`.

## Kết quả

### Lặp prompt trên dev (bộ cũ, đã dùng để tinh chỉnh regex nên regex có lợi thế)

| Bộ | Regex cũ | v2 | v3 | v4 (chọn) |
|---|---:|---:|---:|---:|
| rag (test) | 48/48 | 41/48 | 46/48 | 45/48 |
| rag-policy | 24/24 | 21/24 | 21/24 | 20/24 |
| rag-context | 24/24 | 19/24 | 21/24 | 20/24 |
| **Tổng** | 96/96 | 81/96 | **88/96** | 85/96 |
| Trả lời khi phải từ chối | 0 | 4 | 6 | **3** |
| Câu mâu thuẫn chặn đúng | 7/7 | 7/7 | 4/7 | **7/7** |

- v3: thêm quy tắc suy ra câu trả lời ngầm ("chỉ thứ Hai–thứ Bảy" trả lời "Chủ nhật có không"; "sau khi X" trả lời mốc bắt đầu), hỏi lại khi câu trả lời khác nhau tùy trường hợp chưa nêu, prompt kiểm định viết bằng tiếng Việt. Câu nối tiếp tăng từ 7/12 lên 12/12, nhưng câu mâu thuẫn bắt đầu lọt.
- v4: so nguồn để phát hiện mâu thuẫn trước khi chọn `answer`.
- **Tiêu chí chọn, chốt trước khi chạy held-out:** ít câu trả lời sai tự tin nhất, sau đó mới tới độ chính xác. Đề tài yêu cầu không bịa đặt; từ chối rồi chuyển nhân viên an toàn hơn khẳng định sai. Vì vậy chọn v4 dù v3 cao hơn 3 câu trên dev.

### Held-out (đo một lần với bản đã chọn)

| | Regex cũ | Generic v4 |
|---|---:|---:|
| Quyết định đúng | 33/41 | **35/41** |
| Đạt mẫu dữ kiện (proxy) | 33/41 | 34/41 |
| Trả lời khi phải từ chối (15 câu) | 4 | **1** |
| Từ chối sai câu có đáp án (26 câu) | 4 | 5 |
| Câu mơ hồ hỏi lại đúng | 1/5 | **4/5** |
| p50 (giây) | 7,2 | 6,1 |

So với bản regex, bản tổng quát đạt điểm ngang hoặc hơn trên dữ liệu chưa thấy, giảm câu trả lời sai tự tin từ 4 xuống 1, và **không chứa quy tắc nào viết theo câu hỏi cụ thể**. Chênh lệch 2 câu trên 41 không có ý nghĩa thống kê; kết luận đúng là "không tệ hơn trên dữ liệu mới, an toàn hơn, dễ bảo trì hơn", không phải "tốt hơn rõ rệt".

Lỗi còn lại của v4 trên held-out:
- 004, 018: điểm retrieval dưới 0,35, không gọi model (cả hai bản đều sai). Thuộc ưu tiên 4.
- 005 ("không ưng"): hỏi lại thay vì hiểu là đổi ý.
- 023 (câu nối tiếp "Thứ bảy có nhận không?"): từ chối.
- 029: câu mơ hồ về lý do trả hàng nhưng vẫn trả lời bằng trường hợp đổi ý.
- 040: lịch sử chứa câu ép trả lời "miễn phí hết" khiến pipeline từ chối thay vì trả lời phí đúng (an toàn nhưng là từ chối sai).

## Giới hạn

- Bộ held-out do trợ lý AI soạn, chưa có người duyệt; người soạn biết hướng thiết kế mới. 41 câu cho khoảng tin cậy rộng.
- Bản generic-v1 đã chạy một lần trên held-out và lỗi của nó được xem trước khi sửa prompt (v2). Sửa đổi chỉ là quy tắc chung (tên `decision` rõ nghĩa, câu phủ định là đáp án, áp ngưỡng "từ X"), không nhắc nội dung câu held-out nào; v3, v4 chỉ lặp trên bộ cũ. Dù vậy held-out không còn hoàn toàn "sạch"; sau báo cáo này nó trở thành bộ regression và cần bộ mới để đo tổng quát hóa.
- Mỗi cấu hình chỉ chạy một lần; temperature 0 nhưng Ollama vẫn có thể dao động 1–2 câu giữa các lần chạy.
- Hai ca held-out (004, 018) bị từ chối ở cả hai bản vì điểm retrieval dưới 0,35. Đây là việc của ưu tiên 4 (hybrid retrieval).
