# Nâng cấp diễn đạt có nguồn và độ liên quan — 09/10/2026

Cập nhật tiếp theo: `RANG_BUOC_KIEM_DINH_20261009.md` ghi bản ràng buộc ID kiểm định, giữ 180/180 hồi quy và đạt 30/30 chẩn đoán lặp. Các kết quả và giới hạn dưới đây mô tả bản trước, không bị ghi đè.

## Thay đổi

- Câu hỏi mốc bắt đầu: nếu trích dẫn chỉ có một mốc rõ sau thời lượng, đưa mệnh đề nguyên văn lên đầu với nhãn “Mốc bắt đầu”. Giữ nguyên đoạn nguồn và điều kiện phía dưới. Không suy ra ngày, không chọn giữa nhiều mốc, không diễn giải mệnh đề phủ định. Dạng không nhận diện được giữ nguyên trích dẫn.
- Câu hỏi có nhận/giao/mở cửa trong ngày: chỉ diễn đạt “Không” khi nguồn duy nhất có lịch **chỉ** làm đúng hành động đó từ ngày A đến ngày B, ngày được hỏi nằm ngoài khoảng, không có phủ định hoặc ngoại lệ rõ. Hỗ trợ khoảng qua Chủ nhật. Không suy từ lịch thông thường sang cấm tuyệt đối; không khẳng định “Có” khi ngày nằm trong lịch vì có thể còn điều kiện khác.
- Mọi câu diễn đạt thêm đều xuất hiện trong CANDIDATE trước kiểm định; không thêm sau khi model đã duyệt. Citations vẫn giữ nguyên văn nguồn. Bộ kiểm định vẫn thấy các nguồn không được trích dẫn để phát hiện xung đột.
- Với câu có/không kèm nhiều đoạn, kiểm định xác định nguồn thừa. Chỉ bỏ nguồn nếu danh sách sửa là tập con thực sự của nguồn đang trích; giữ nguyên toàn bộ trích dẫn/điều kiện thuộc nguồn được giữ, không dùng câu sửa ngắn hơn để làm mất điều kiện. Kiểm định lại kết quả tối đa một lần; từ chối nếu vẫn cần sửa. ID sửa sai, nguồn mâu thuẫn hoặc kiểm định sau sửa không đạt thì không trả đáp án có nguồn. Câu mở giữ prompt cũ để tránh thay cách hiểu yêu cầu hành động.
- Giữ model, cấu hình và giới hạn tối đa ba lần chat. Không thêm dependency; không nạp tài liệu mẫu vào dữ liệu thật.

## Phạm vi kiểm chứng

Giữ nguyên mọi corpus/nhãn của 180 ca. Baseline: `priority-followup-verified-v2-20261009` (178/180). Lượt nâng cấp và các snapshot được lưu ở thư mục mới; không ghi đè bằng chứng cũ.

Các thử riêng `bt20-032`, `test-026`, `doc-006`, `test-029`, `policy-013` dùng truy hồi đã lưu để chẩn đoán, không thay thế đo end-to-end. Test tự động bổ sung lịch qua cuối tuần, ngày biên, ngoại lệ, không độc quyền, phủ định, hành động khác, nhiều nguồn/mốc, giữ điều kiện và kiểm định bắt buộc sau sửa.

Lượt `precision-v1-20261009` đạt 178/180: sửa các ca đích nhưng phát sinh `bt20-011` (hỏi giao trễ bị từ chối) và `bt20-047` (yêu cầu chấp thuận đổi trả được trả chính sách thay vì từ chối). Không chọn bản này. Prompt kiểm định độ liên quan áp dụng cho mọi câu nhiều đoạn gây thay đổi quá rộng; bản v2 giới hạn cho câu có/không. Giữ toàn bộ kết quả v1, không sửa nhãn hoặc xóa ca lỗi.

Lượt `precision-v2-20261009` đạt 179/180; `bt20-018` bị từ chối dù lần kiểm định cuối xác nhận đúng vì gợi ý rút gọn nguồn tới quá muộn. Bản cuối giới hạn cả prompt và việc áp dụng rút gọn cho câu có/không; câu mở đã được kiểm định chấp thuận giữ nguyên bằng chứng theo cơ chế cũ. Không thêm lượt model hoặc bỏ bước kiểm định đáp án rút gọn.

## Kết quả hồi quy đóng băng

Lượt `precision-final-20261009`, so với `priority-followup-verified-v2-20261009` trên cùng corpus/nhãn:

| Bộ | Trước | Sau | Ca mới lỗi | p50 / p95 (giây) |
|---|---:|---:|---|---:|
| bt20 | 59/60 | 60/60 | Không | 5.957 / 8.790 |
| rag-context | 24/24 | 24/24 | Không | 4.606 / 8.898 |
| rag-documents | 24/24 | 24/24 | Không | 5.042 / 7.971 |
| rag | 47/48 | 48/48 | Không | 4.392 / 6.961 |
| rag-policy | 24/24 | 24/24 | Không | 5.151 / 8.912 |

- Tổng **180/180** đạt rubric tự động, từ 178/180; không có ca mới lỗi trên lượt này. 0 lỗi provider và 0 ca chứa chuỗi cấm theo rubric.
- **216 kiểm thử backend đạt** bằng `python -m unittest discover -s app/tests`. Không đổi runtime sau khi chạy kiểm thử và đóng băng các lượt đo.
- **153/153 citation quote** là chuỗi con của chunk truy hồi sau chuẩn hóa khoảng trắng. Kiểm tra này chỉ xác nhận trích nguồn, không xác nhận suy luận trong phần diễn đạt thêm hoặc mức đầy đủ của đáp án.
- Mâu thuẫn **13/13**, injection **17/17** đạt rubric trên bộ thử này; không phải chứng nhận chống injection toàn diện.
- Hash mọi file trong manifest khớp workspace; hash corpus/nhãn khớp baseline. Mỗi câu dùng không quá ba lần chat. Không đổi nhãn để đạt điểm, không tự điền phiếu người duyệt.
- Mỗi bộ có `manifest.json`, `results.jsonl`, `summary.json`, `ingestion.json` và `human-review.jsonl` tại `evals/<bộ>/runs/precision-final-20261009/`. Kết quả chứa lịch sử, nguồn, đáp án và phản hồi model để đối chiếu; phiếu người duyệt vẫn trống.

### Các ca trọng tâm

- `bt20-032`: trả “Mốc bắt đầu: sau khi nhận và kiểm tra hàng trả.”, sau đó giữ cả điều kiện yêu cầu được chấp thuận và thời hạn 5 ngày làm việc. Không hỏi lại dư ở lượt cuối.
- `rag/test-026`: trả “Không. Chủ nhật nằm ngoài lịch thứ Hai đến thứ Bảy trong chính sách được trích dẫn.” rồi giữ nguyên quote. Đây là diễn đạt được kiểm định từ lịch **chỉ nhận**, không giả làm câu nguyên văn hoặc sửa gold.
- `policy-013`: chỉ giữ chính sách khắc chữ, bỏ đoạn đổi trả không liên quan. Đây là cải thiện độ liên quan dù baseline đã đạt rubric.
- `bt20-011`, `bt20-018`, `bt20-047`: không còn trượt rubric như các lượt thử v1/v2. Riêng `bt20-047` vẫn hỏi làm rõ chung thay vì giải thích rõ không thể tự phê duyệt; không coi điểm từ chối đạt là trải nghiệm hoàn hảo.

## Kiểm tra lặp sau lượt đầy đủ

Chạy thêm ba lần cho mỗi ca `bt20-011`, `bt20-018`, `bt20-032`, `bt20-047`, `test-026`, `policy-013`: **15/18** đạt rubric. Bằng chứng giữ tại `evals/rag-policy/precision-stability-20261009.jsonl`, gồm số lần lặp, hash kết quả đầu vào, đáp án và phản hồi model.

Đây là chẩn đoán gọi Ollama thật nhưng phát lại kết quả truy hồi đã lưu; DB và kiểm tra phiên bản nguồn được giả lập. Không cộng 18 lượt này vào điểm 180 ca end-to-end và không coi là tập kín độc lập.

`bt20-032` bị từ chối sai cả ba lần lặp: bộ kiểm định nhầm mốc giao hàng với mốc hoàn tiền, đề xuất ID câu giao hàng đã bị loại khỏi lựa chọn hợp lệ. Kiểm tra ID chặn đáp án thay vì trả mốc sai. Chưa xác định nguyên nhân khác biệt với lượt end-to-end; không sửa bằng cách bỏ kiểm định, cho phép ID ngoài tập hoặc chỉ giữ lượt đạt. Ca này **đạt trong lượt đầy đủ nhưng chưa ổn định**, còn ưu tiên xử lý. Năm ca khác đạt cả ba lần; `policy-013` giữ đúng một citation cả ba lần.

## Giới hạn còn lại

Quy tắc diễn đạt chỉ bao phủ các mẫu tiếng Việt nêu trên, không phải bộ hiểu lịch hoặc thời gian tổng quát. `bt20-032` chưa ổn định theo kiểm tra lặp phía trên. Rút gọn độ liên quan chỉ áp dụng dạng có/không; câu mở như `bt20-011` vẫn có thể kèm đoạn đổi trả dư. Model chọn và kiểm định cùng họ nên chưa loại được sai sót tương quan.

Không dùng điểm hồi quy để khẳng định tỷ lệ đúng thực tế. Phiếu người duyệt vẫn để trống; nghiệm thu độc lập theo `NGHIEM_THU_DOC_LAP.md` vẫn cần người khác soạn tập kín và duyệt toàn bộ. Chưa đánh dấu M3 hoặc toàn bộ ưu tiên cao hoàn tất.
