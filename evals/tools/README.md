# Đánh giá điều phối công cụ M5

Ngày đo: 26/09/2026. Bộ 24 ca giả lập, tám ca biên nối tiếp và 12 ca ngữ cảnh có nhãn nháp, chưa được người duyệt. Đây là tập phát triển/regression đã dùng chỉnh prompt và luồng điều phối, không phải tập đánh giá độc lập hoặc nghiệm thu M5. Kết quả mới nhất: 24/24, 8/8 và 10/12; hai cách nói tự do vẫn chuyển nhân viên nhầm.

## Chạy phép đo

Từ root repo, bật Ollama và cài model cấu hình (mặc định qwen3:4b):

```powershell
python -m app.evaluate_tools --output evals/tools/runs/my-new-run
```

Thư mục output phải chưa tồn tại; lệnh từ chối ghi đè. Có thể truyền `--dataset path/to/cases.jsonl`. CLI dùng biến môi trường của tiến trình, không tự đọc `.env`. Nếu kiểm tra Ollama thất bại, thư mục rỗng có thể đã được tạo; lần sau chọn tên mới.

Mỗi ca dùng SQLite trong bộ nhớ và migration thật. Chạy `process_message`, quy tắc handoff, bộ chọn Ollama và kiểm tra quyền thật; riêng `answer_question` trả `EVAL_RAG_BRANCH_ONLY`. Không đọc DB/vector người dùng hoặc gửi Telegram. Phép đo xác nhận chọn nhánh, không chấm câu trả lời RAG, tóm tắt handoff hoặc độ trễ toàn luồng.

## Dữ liệu và cách chấm

Hai đơn giả: DH78216 thuộc owner, ORD-93427 thuộc other. Phạm vi owner được tra đơn của mình; anonymous không có quyền; granted có quyền DH78216 gắn với phiên widget còn hiệu lực; expired có quyền đã hết hạn. Mỗi ca tạo dữ liệu mới. Ca hỏi nối tiếp có tối đa bốn tin lịch sử; nhãn mô tả hành vi sản phẩm mong muốn, gồm khả năng suy ra đơn chưa được triển khai.

Một ca đạt khi đúng nhánh mong đợi, thỏa expected_lookup, không lỗi, không lộ marker mã vận đơn bị cấm và không đổi dữ liệu đơn được theo dõi. Kiểm tra marker chỉ bao phủ hai mã vận đơn fixture, không chứng minh mọi dạng rò rỉ đều bị chặn. Quyền từ chối tra đơn dẫn tới handoff; nhãn any chấp nhận cả chuyển nhân viên trực tiếp và tra rồi từ chối, không bắt buộc gọi lookup. Lỗi provider vẫn nằm trong mẫu số; không loại ca thất bại khỏi tỷ lệ.

`manifest.json` lưu dataset/hash, model/digest/options và mã nguồn tại lúc chạy; `results.jsonl` lưu từng ca ngay sau xử lý; `summary.json` chỉ xuất khi chạy hết. Exit 0 nghĩa là hoàn tất phép đo, không có nghĩa mọi ca đạt; đọc `passed`, `cases` và `errors` để quyết định. Exit 1 báo lỗi đầu vào hoặc khởi chạy. Các kết quả đã lưu không sửa lại khi thay mã nguồn.

## Kết quả thực đo

| Chỉ số | baseline-20260926 | mixed-priority-20260926 |
|---|---:|---:|
| Đạt so với nhãn nháp | 17/24 (70,83%) | 18/24 (75%) |
| Lời gọi bộ chọn Ollama thật | 15 | 15 |
| Lỗi provider | 0 | 0 |
| Lộ marker bị cấm / sửa đơn quan sát được | 0 / 0 | 0 / 0 |
| Trung vị thời gian điều phối | 1,38 giây | 1,24 giây |
| Ca được người duyệt | 0 | 0 |

Cùng dataset, model/digest/options; chỉ thay một câu trong system prompt để ưu tiên handoff khi vừa tra trạng thái vừa yêu cầu hủy/đổi đơn, kể cả có điều kiện. Ca `cancel-and-track` chuyển từ lookup sang handoff và đạt; không tự hủy đơn. 23 ca còn lại giữ kết quả đạt/không đạt. Thứ tự cố định, trạng thái model/cache khác nhau và nhánh RAG giả lập nên không suy ra cải thiện tốc độ từ hai trung vị.

Sau sửa: access 8/8, mixed 3/3, format 3/3, handoff 1/1, negation 1/3, policy 1/2, followup 1/4.

| Ca chưa đạt | Giới hạn quan sát được |
|---|---|
| refund-policy | Quy tắc hoàn tiền chuyển nhân viên dù hỏi chính sách |
| no-human-needed | Quy tắc gặp nhân viên chưa hiểu phủ định |
| currency-policy | Từ khóa tệ khớp trong cụm tiền tệ |
| implicit-followup | Thiếu mã ở tin hiện tại nên đi RAG, chưa suy ra đơn từ lịch sử |
| ambiguous-followup | Chưa dùng lịch sử để yêu cầu làm rõ đơn đang nhắc tới |
| expired-followup | Chưa suy ra mã từ lịch sử để kiểm tra lại quyền hết hạn |

## Bổ sung hỏi nối tiếp

Lượt `runs/history-reference-20260926` giữ nguyên 24 ca/model/options, đạt 21/24 (87,5%), với 17 lời gọi selector thật; trung vị điều phối 0,767 giây. Ba ca implicit-followup, ambiguous-followup, expired-followup chuyển sang đạt; các ca khác giữ kết quả đạt/không đạt. Còn refund-policy, no-human-needed, currency-policy. Không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được; không dùng trung vị này để kết luận cải thiện tốc độ.

Backend nhận tham chiếu rõ đơn đó/này/ấy/vừa nêu/ở trên, lấy mã khách đã gửi trong bốn tin khách/AI gần nhất cùng hội thoại. Không dùng mã AI nêu; mã hiện tại ưu tiên; nhiều mã lịch sử hỏi lại; mã hiện tại sai không âm thầm thay bằng mã cũ. Không có mã/ngữ cảnh phù hợp vẫn đi RAG. Đây là giới hạn chủ động, chưa suy luận tham chiếu tự do. Quyền đơn được kiểm tra lại sau model, trace nội bộ ghi order_id_source=history.

```powershell
python -m app.evaluate_tools --dataset evals/tools/followups.jsonl --output evals/tools/runs/my-new-followup-run
```

Lượt `runs/history-boundaries-20260926` đo tám ca mới trong followups.jsonl, đạt 8/8, năm lời gọi selector thật, không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. Các ca gồm quyền phiên, chính sách, hủy đơn, mã hiện tại ưu tiên, mã AI, mã sai, nhiều mã ở hai tin và mã nằm sau ký tự 500. Nhãn ca không đủ ngữ cảnh phản ánh nhánh RAG hiện tại, không chứng minh bot hỏi làm rõ đúng hoặc trả lời hữu ích. Tám ca chưa người duyệt, viết theo giới hạn đã chọn; không coi là tập độc lập để khẳng định chất lượng tổng quát.

## Ngữ cảnh handoff và Unicode

Backend bỏ qua riêng tiền tệ, phủ định rõ gặp người ở đầu mệnh đề và mẫu hỏi chính sách hoàn tiền; vẫn xét các từ khóa khác trong cùng tin. Widget dùng cùng quy tắc khi AI bận: tin trung tính nhận 429 trước lưu, yêu cầu handoff thật đi ngay. Bộ mới handoff-context.jsonl có cả mẫu rõ, yêu cầu hỗn hợp, phủ định kép, quyền tra đơn và hai cách nói tự do ngoài mẫu.

```powershell
python -m app.evaluate_tools --dataset evals/tools/handoff-context.jsonl --output evals/tools/runs/my-new-context-run
```

| Lượt đo | Bộ ca | Đạt | Lời gọi selector thật |
|---|---|---:|---:|
| handoff-context-20260926 | cases.jsonl | 24/24 | 18 |
| handoff-boundaries-20260926 | handoff-context.jsonl, trước NFC | 9/12 | 2 |
| handoff-nfc-20260926 | cases.jsonl, bản cuối | 24/24 | 18 |
| handoff-nfc-boundaries-20260926 | handoff-context.jsonl, bản cuối | 10/12 | 2 |
| handoff-nfc-followups-20260926 | followups.jsonl, bản cuối | 8/8 | 5 |

Ca unicode-negated-human qua bộ quy tắc nhưng selector hiểu sai văn bản dấu tách. Chuẩn hóa NFC riêng nội dung đưa vào model giúp ca này đạt; tin lưu/ticket giữ nguyên. Hai bộ trước/sau giữ dataset/model/options; không sửa lại kết quả cũ. Mọi lượt trong bảng không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. Phần lớn ca handoff-context đi quy tắc và không gọi model; nhánh RAG vẫn giả lập. Điểm số phản ánh điều phối toàn luồng giới hạn này, không phải độ chính xác riêng của model hoặc chất lượng câu trả lời.

Hai ca còn lỗi: policy-free-form (Mình chỉ hỏi về chính sách hoàn tiền của cửa hàng thôi) và negation-prefixed (Hiện tại tôi chưa cần gặp nhân viên, tra DH78216 giúp tôi). Quy tắc chưa nhận câu hỏi không theo mẫu hoặc phủ định có lời dẫn tùy ý. Không mở rộng mẫu chỉ để làm đẹp điểm; cần người duyệt và bộ câu độc lập để chốt bước xử lý ý định tiếp theo. Bộ mới chưa độc lập với phát triển; không gộp các tỷ lệ thành bằng chứng nghiệm thu tổng quát.

## Duyệt nhãn đã đóng băng

CLI `app.review_tools` tạo phiếu JSON hoặc tổng hợp nhãn được duyệt từ lượt đo hoàn tất. Không gọi model, không sửa benchmark, không tự ghi nhận ai đã duyệt. Đã chuẩn bị 44 phiếu trống: [24 ca gốc](reviews/core-20260926.json), [8 ca nối tiếp](reviews/followups-20260926.json), [12 ca ngữ cảnh](reviews/context-20260926.json). Mỗi phiếu kèm câu hỏi, lịch sử, phạm vi quyền, nhãn nháp và kết quả để đối chiếu. Đây là duyệt sau khi xem kết quả, không phải chấm mù hoặc bộ đánh giá độc lập.

Chỉ sửa `reviewer`, `gold_label_approved`, `notes`. Đặt true khi đồng ý cả expected_route và expected_lookup của ca; false khi bác nhãn, kèm lý do; null nếu chưa quyết định. Reviewer bắt buộc khi có quyết định, là tên tự khai, chưa xác thực tài khoản. Không dùng true để đánh dấu bot trả lời đúng: CLI tự so bằng chứng định tuyến với nhãn được duyệt. Nếu cần sửa nhãn, ghi đề xuất trong notes rồi tạo phiên bản dataset mới; không sửa case hoặc kết quả gốc.

```powershell
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --output evals/tools/reviews/context-new-review.json
```

Sau khi thành viên điền phiếu, tổng hợp vào file mới:

```powershell
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --reviews evals/tools/reviews/context-new-review.json --output evals/tools/reviews/context-review-summary.json
```

Output phải chưa tồn tại; thư mục cha phải có sẵn. CLI kiểm tra manifest, đủ kết quả, summary, điểm đạt lưu sẵn và hash của lượt đo; bác ID trùng/khác lượt, sửa case, kiểu giá trị sai và quyết định không có người chấm. Hash ràng buộc đúng dữ liệu và tránh nhầm bản, không phải chữ ký chống giả mạo. Báo cáo lưu hash đầu vào, phiếu và mã nguồn bộ chấm.

`accuracy_against_approved_labels` chỉ tính các ca có nhãn được duyệt; lỗi xử lý vẫn ở mẫu số của nhóm này. Ca bác nhãn và ca chưa duyệt được liệt kê riêng, không coi là đã đạt. Chưa có nhãn được duyệt thì tỷ lệ là null. `all_labels_approved` chỉ mô tả đủ nhãn được chấp thuận, không xác nhận chất lượng sản phẩm. Duyệt một phần có thể gây thiên lệch lựa chọn; không suy rộng tỷ lệ sang cả tập. Phép chấm không đánh giá đáp án RAG, tóm tắt hoặc mọi kiểu rò rỉ dữ liệu.

Năm unittest mới đạt (0,078 giây), gồm phiếu trống/duyệt một phần, lỗi trong mẫu số, sai hash/nội dung/ID/kiểu quyết định, lượt đo không hoàn tất và CLI không ghi đè/gọi model. Đã kiểm tra ba phiếu hiện có: 44 ca vẫn chờ duyệt, không có điểm do người chấm. Mã runtime khớp snapshot phép đo trước, không chạy lại Ollama hoặc toàn bộ test runtime cho CLI độc lập này.

## Duyệt bằng trình duyệt offline

Mở trực tiếp file HTML trong trình duyệt: [24 ca gốc](reviews/core-20260926.html), [8 ca nối tiếp](reviews/followups-20260926.html), [12 ca ngữ cảnh](reviews/context-20260926.html). Không cần chạy API hoặc Ollama. Cả 44 ca khởi tạo chưa quyết định.

1. Đọc câu hỏi, quyền truy cập, lịch sử và hai nhãn mong đợi; mở kết quả đã lưu khi cần đối chiếu.
2. Điền tên, chọn đồng ý/bác nhãn/chưa quyết định. Bác nhãn phải ghi lý do; trang chặn xuất quyết định thiếu thông tin.
3. Chọn **Tải JSON để tổng hợp**, kiểm tra file trong mục Tải xuống. Nếu trình duyệt không tải được, mở **Sao chép JSON nếu không tải được**, sao chép toàn bộ và lưu `.json` UTF-8.
4. Khánh dùng lệnh tổng hợp ở mục trước với đúng thư mục lượt đo và đường dẫn JSON đã nhận. Nếu chia ca cho nhiều thành viên, dùng `--merge` như mục sau; giữ phiếu nguồn riêng từng người.

Nháp lưu trong localStorage khi trình duyệt hỗ trợ, riêng từng biểu mẫu. Đổi máy/trình duyệt, xóa dữ liệu hoặc đổi đường dẫn file có thể mất nháp; JSON là bản để chuyển giao. Tên tự khai, không xác thực người chấm. Muốn tạo biểu mẫu mới hoặc tiếp tục từ JSON hợp lệ:

```powershell
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --html --output evals/tools/reviews/context-new.html
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --html --reviews evals/tools/reviews/context-filled.json --output evals/tools/reviews/context-resumed.html
```

Output phải chưa tồn tại. Trang giữ nguyên bằng chứng JSON, kể cả số như `1.0`, chỉ xuất thay đổi ở ba trường cho phép. Nội dung ca hiển thị như văn bản; CSP chặn kết nối mạng. Duyệt sau khi xem kết quả vẫn có thiên lệch, không thay đánh giá độc lập.

Kiểm chứng giao diện: bảy test CLI/HTML đạt; QA trên ba ca giả lập kiểm tra tên/lý do bắt buộc, đổi ca, khôi phục nháp, nội dung HTML không thực thi, desktop và mobile 390px không tràn ngang. JSON lấy từ ô xuất của trình duyệt được CLI chấp nhận: một đồng ý, một bác, một chờ. Tải Blob trực tiếp trong trình duyệt tích hợp chưa xác nhận được; đã kiểm chứng đường sao chép JSON dự phòng. Không điền quyết định vào 44 ca thật, không gọi model hoặc đổi runtime.

## Gộp phần duyệt của các thành viên

Khánh chia ID ca trong cùng bộ cho từng thành viên. Mỗi người chỉ điền phần được giao, để nguyên phần còn lại; gửi file JSON đã xuất. Gộp riêng từng lượt đo, không trộn ba bộ có hash khác nhau:

```powershell
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --merge evals/tools/reviews/context-member-a.json evals/tools/reviews/context-member-b.json --output evals/tools/reviews/context-merged.json
python -m app.review_tools --run evals/tools/runs/handoff-nfc-boundaries-20260926 --reviews evals/tools/reviews/context-merged.json --output evals/tools/reviews/context-merged-summary.json
```

Tên file thành viên là ví dụ, cần thay bằng file thực nhận. `--merge` tạo phiếu JSON đủ mọi ca theo thứ tự gốc, chưa phải báo cáo điểm; thêm `--html` và chọn output `.html` nếu muốn tiếp tục duyệt bằng trình duyệt. `--merge` và `--reviews` không dùng cùng lúc. Mọi output phải chưa tồn tại.

Phiếu hoàn toàn trống không ghi đè phần đã điền. Tên và ghi chú ở ca chưa quyết định vẫn được giữ; bản trùng đúng cả ba trường sau bỏ khoảng trắng đầu/cuối được gộp một lần. Nếu cùng ID có tên, quyết định hoặc ghi chú khác nhau, CLI liệt kê ID xung đột và không tạo output, kể cả hai người cùng đồng ý nhãn. Khánh đối chiếu với người duyệt rồi chuẩn bị bản đầu vào đã thống nhất; giữ file nguồn để truy vết. Công cụ không chọn theo thứ tự file, không lấy đa số, không tự giải quyết bất đồng hoặc giả định người thứ hai đã duyệt.

Chín test CLI/HTML đạt, gồm gộp phần riêng, ghi chú chờ, tính bất biến theo thứ tự file, trùng bản, xung đột, sai hash/ID và không ghi đè/gọi model. Ca test dùng người duyệt giả lập; cả 44 ca thật vẫn chờ duyệt. Gộp phiếu không biến tập phát triển thành đánh giá độc lập.

## Kiểm chứng và bước tiếp theo

```powershell
python -m unittest app.tests.test_tools app.tests.test_evaluate_tools -v
```

Mốc sửa yêu cầu hỗn hợp: 10 test đạt, bộ đầy đủ 137 test đạt trước chỉnh prompt; hai lượt đo có 30 lời gọi model thật. Mốc nối tiếp: thêm bốn test và mở rộng tranh chấp khi chờ model (tin mới, handoff, đóng, đổi chủ); bộ đầy đủ 141 test đạt trong 49,555 giây. Ollama transport được mock trong unittest. Hai lượt đo mới có 22 lời gọi model thật là bằng chứng riêng; nhánh RAG vẫn giả lập. Đã đối chiếu snapshot nguồn với kết quả và kiểm tra từ chối ghi đè mà hash kết quả không đổi.

Bản cuối ngữ cảnh/NFC đạt 144 unittest trong 49,188 giây, gồm ba test mới và mở rộng kiểm tra đầu vào NFC/văn bản gốc. Các test xác nhận cụm trung tính không che yêu cầu khác, Unicode/khoảng trắng, giới hạn AI và ticket khi handoff; model/transport mock. Ba phép đo bản cuối trong bảng có 25 lời gọi model thật là bằng chứng riêng. Source snapshot bản cuối đối chiếu với mã hiện tại; summary tính lại khớp từng result.

Khánh phụ trách sửa luồng chính, tích hợp và đo lại. Nhóm kiểm thử duyệt nhãn/rationale, bổ sung câu chưa dùng để chỉnh prompt, đối chiếu hai ca mới chưa đạt; nhóm báo cáo cập nhật số liệu và giới hạn. Chỉ chốt chất lượng M5 sau khi có người duyệt và đánh giá độc lập; chất lượng RAG, bot thật và triển khai đo riêng.
