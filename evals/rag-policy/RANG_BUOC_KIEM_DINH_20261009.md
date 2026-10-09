# Ràng buộc ID cho kiểm định RAG — 09/10/2026

## Nguyên nhân và thay đổi

Bản trước có grammar JSON ràng buộc cặp `source_id`/`sentence_id` khi chọn nguồn, nhưng kiểm định chỉ yêu cầu hai số nguyên dương. Vì vậy kiểm định có thể đề xuất câu giao hàng đã bị loại khỏi tập bằng chứng cho câu hỏi hoàn tiền. Backend chặn ID đó là đúng về an toàn, nhưng gây từ chối sai ở `bt20-032`.

`review_answer` nay nhận lại đúng grammar của bước chọn nguồn, áp dụng cho `repair_citations` ở cả lần kiểm định đầu và lần kiểm định lại. Không tạo bộ lọc nguồn thứ hai, không gắn quy tắc với ID ca kiểm thử. Backend vẫn kiểm tra mọi ID; không tin riêng grammar của provider. Kiểm định vẫn đọc tất cả nguồn để phát hiện mâu thuẫn, kể cả nguồn không được phép chọn làm đáp án.

Không đổi prompt cuối cùng, model, ngưỡng truy hồi, corpus, nhãn hoặc giới hạn ba lần chat. Không bỏ kiểm định, không cho dùng câu giao hàng làm mốc hoàn tiền và không ghi dữ liệu mẫu vào kho thật.

## Kiểm thử và chẩn đoán

- Test mới tái hiện thiếu ràng buộc trước sửa: một trong hai test mới thất bại vì schema kiểm định không khớp schema chọn nguồn. Sau sửa, **58 test RAG** và **218 test backend** đạt.
- Test kiểm tra hai lần kiểm định đều dùng đúng cặp ID hợp lệ, vẫn nhìn thấy nguồn giao hàng; phản hồi giả mạo chứa ID bị loại vẫn bị backend chặn, kể cả khi các cờ kiểm định báo chấp thuận.
- Thử riêng tám lượt trên `bt20-032`: baseline 2/2, chỉ sửa prompt 1/2, chỉ ràng buộc grammar 2/2, kết hợp 2/2. Không chọn sửa prompt vì thêm thay đổi nhưng vẫn có lỗi. Baseline cũng có lúc đạt, nên không kết luận mọi dao động đã biến mất hoặc mọi lỗi trước đây chỉ do schema.
- Sau sửa, chạy năm vòng xen kẽ sáu ca `bt20-011`, `bt20-018`, `bt20-032`, `bt20-047`, `test-026`, `policy-013`: **30/30 đạt rubric**, riêng `bt20-032` **5/5** thay vì 0/3 trong chẩn đoán trước. `policy-013` giữ đúng một citation cả năm vòng. Không quá ba lần chat/câu.
- Hai phép thử trên gọi Ollama thật nhưng phát lại truy hồi đã lưu từ `precision-final-20261009`; DB và kiểm tra phiên bản nguồn được giả lập. Không cộng vào điểm end-to-end hoặc gọi là tập kín độc lập. Kết quả mới lưu hash runtime và hash đầu vào để đối chiếu.

Bằng chứng chẩn đoán: `evals/rag-policy/refund-schema-prompt-probes-20261009.jsonl` và `evals/rag-policy/refund-schema-stability-20261009.jsonl`. Bằng chứng 15/18 của bản trước giữ nguyên tại `evals/rag-policy/precision-stability-20261009.jsonl`.

## Hồi quy end-to-end đóng băng

Lượt `refund-schema-v1-20261009`, so với `precision-final-20261009` trên cùng corpus/nhãn:

| Bộ | Trước | Sau | Ca mới lỗi | p50 / p95 (giây) |
|---|---:|---:|---|---:|
| bt20 | 60/60 | 60/60 | Không | 6.542 / 9.731 |
| rag-context | 24/24 | 24/24 | Không | 5.459 / 9.783 |
| rag-documents | 24/24 | 24/24 | Không | 5.592 / 8.728 |
| rag | 48/48 | 48/48 | Không | 5.322 / 8.131 |
| rag-policy | 24/24 | 24/24 | Không | 5.870 / 9.552 |

- **180/180** đạt rubric, 0 lỗi provider, 0 ca chứa chuỗi cấm theo rubric. `bt20-032` đạt trong lượt đầy đủ và 5/5 lượt chẩn đoán xen kẽ.
- **154/154 quote** khớp chuỗi con của chunk truy hồi sau chuẩn hóa khoảng trắng; không đồng nghĩa toàn bộ đáp án đủ ý hoặc đúng ngữ nghĩa. Mâu thuẫn **13/13**, injection **17/17** đạt trên bộ này, không phải bảo đảm an toàn toàn diện.
- Hash runtime trong manifest khớp workspace và snapshot mã; hash corpus/nhãn khớp baseline. Không đổi mã sau khi chạy **218 kiểm thử** và đóng băng lượt đo. Các phiếu `human-review.jsonl` chưa được điền.
- Kết quả, phản hồi model, manifest, snapshot và phiếu duyệt nằm tại `evals/<bộ>/runs/refund-schema-v1-20261009/`. Chạy tuần tự bằng `python -m app.evaluate_rag --split test --dataset evals/<bộ> --output evals/<bộ>/runs/<tên-mới>`; không ghi đè lượt đã có. Kiểm thử: `python -m unittest discover -s app/tests`.
- Độ trễ quan sát cao hơn lượt trước trên cả năm bộ. Chưa đo cô lập chi phí grammar so với trạng thái tải model/hệ thống, không tuyên bố bản này tăng tốc.

## Giới hạn

Grammar chỉ ngăn chọn cặp ID ngoài tập hợp lệ, không chứng minh model hiểu đúng mọi mốc thời gian. Năm vòng lặp chưa bảo đảm độ ổn định trong mọi trạng thái chạy hoặc với câu hỏi mới. Câu mở vẫn có thể kèm đoạn dư; phản hồi từ chối yêu cầu thực thi có thể còn chung chung.

Các bộ đã được dùng để phát triển/hồi quy. Chưa có người thật duyệt toàn tập hoặc tập kín do người khác soạn; chưa nghiệm thu M3/toàn bộ ưu tiên cao. Không điền thay phiếu người duyệt và không gọi điểm hồi quy là độ chính xác thực tế.
