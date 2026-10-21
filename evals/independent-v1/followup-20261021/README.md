# Sửa bốn ca còn lỗi — 21/10/2026

## Kết quả cuối

Lượt `four-fixes-verified-20261021` hoàn tất **240/240 ca đạt rubric, không lỗi dịch vụ**: 60/60 ca theo nhãn v2 đã được người dùng duyệt ba chỉnh sửa và 180/180 ca hồi quy cũ. So với `quality-final-20261021`, đúng bốn ca mục tiêu chuyển từ trượt sang đạt, không có ca thoái lui trong lượt này. **236 test backend và một test báo cáo đạt.**

| Ca | Hành vi quan sát được |
|---|---|
| customer-022 | Hỏi model/ảnh thông số; nói chưa xác nhận tương thích được; không viện dẫn yêu cầu sản phẩm thay thông số củ sạc riêng. |
| customer-053 | Nói chưa có dữ liệu sử dụng mã, chưa tra cứu; đề nghị nhân viên kiểm tra sau xác thực. |
| context-005 | Trả chính sách nhân viên báo chi phí trước khi khách quyết định sửa, không từ chối thiếu nguồn. |
| context-008 | Trả quy định khách chọn sai màu không được hoàn phí giao ban đầu, giữ điều kiện riêng của từng đoạn. |

198/198 quote khớp đoạn truy hồi; hash mã/dữ liệu trong cả bảy manifest được kiểm tra lại. Cùng đáp án mới chấm offline theo nhãn gốc v1 đạt 58/60, theo v2 đạt 60/60; không trộn tác động đổi nhãn với sửa runtime. Phiếu human-review vẫn trống: phê duyệt ba nhãn không phải phê duyệt toàn bộ đáp án. Đây vẫn là bộ phát triển/hồi quy đã xem, chưa phải nghiệm thu độc lập. Đáp án có thể dài do giữ nguyên điều kiện/trích đoạn; khớp quote và đạt regex không chứng minh hoàn hảo về ngữ nghĩa.

Kết quả từng bộ, đối chiếu bốn lượt và thống kê máy đọc được tại `KET_QUA.md`, `report.json`; bản chạy dở và các phép kiểm tra có lỗi vẫn được giữ riêng, không gộp vào số 240/240.

## Phạm vi và phê duyệt nhãn

Tiếp tục từ commit `a8edc5b`. Người dùng đã đồng ý ba thay đổi nhãn customer-024/048/051; bằng chứng phạm vi phê duyệt nằm ở `../customer-v2/label-approval.json`. Không coi phê duyệt này là duyệt độc lập đáp án hay nghiệm thu hệ thống. Giữ nguyên manifest đề xuất, 60 câu, lịch sử, corpus và kết quả các lượt trước.

## Thay đổi runtime

- Khi khách nói rõ thiếu nhãn/model/thông số và yêu cầu xác nhận tương thích, hỏi model hoặc thông số thay vì dùng yêu cầu chung của sản phẩm để xác nhận thiết bị riêng. Thông số/model khách đã cung cấp vẫn được dùng cho truy hồi; lời trợ lý không tự cấp dữ kiện.
- Với yêu cầu kiểm tra/xác nhận mã quà, voucher hoặc mã giảm giá đã dùng chưa, nhánh RAG nói rõ chưa có dữ liệu sử dụng mã và chưa thực hiện tra cứu, hướng dẫn nhân viên kiểm tra sau xác thực. Cùng hàng rào áp dụng cho yêu cầu xác nhận giao dịch đã về/đã thành công chưa, tránh dùng chính sách đối soát thay dữ liệu giao dịch riêng. Không tự chuyển trạng thái hội thoại hoặc giả vờ gọi công cụ. Câu hỏi về cách kiểm tra/quy trình/điều kiện vẫn đi truy hồi bình thường; câu hỏi đọc hồ sơ REF-M không bị chặn như một yêu cầu thực thi tra cứu.
- Chỉ với câu hỏi báo giá/phí hoàn: bước chọn nguồn nhấn mạnh đúng lý do/điều kiện khách nêu; review phân biệt điều kiện bắt buộc trước thao tác với thời lượng thao tác và công nhận quy định không hoàn phí cho đúng lý do. Không lẫn khách chọn sai với cửa hàng giao sai. Các câu hỏi khác giữ prompt gốc, tránh làm lệch hành vi giấy tờ/nhận hộ.
- Giữ giới hạn ba cuộc gọi chat, mọi bản sửa bằng chứng vẫn phải được review lại. Không đổi model, ngưỡng truy hồi, corpus, quyền tra cứu hoặc lớp chặn chỉ dẫn giả/mâu thuẫn.

## Kiểm tra mục tiêu

`check_targets.py` chạy customer-022, customer-053, context-005 và context-008 ba lượt liên tiếp, dùng pipeline thật với DB/Qdrant tạm và corpus đầy đủ. Chỉ giới hạn danh sách ca qua loader của evaluator; manifest ghi đúng ID đã chạy và hash toàn bộ dữ liệu/mã. Hai ca hỏi rõ/giới hạn tra cứu được chặn trước truy hồi, nên không gọi model; hai ca context gọi Ollama thật. Không gọi Telegram/SMTP hay đọc DB khách.

Lượt `four-fixes-smoke-20261021-r1/r2/r3`: **12/12 đạt, không lỗi dịch vụ**. Đây là kiểm tra lặp trên ca đã biết, không phải tập kín hoặc bảo đảm ổn định tổng quát. Raw completions và câu trả lời nằm trong thư mục runs của từng bộ.

Lượt hồi quy `four-fixes-final-20261021` với hướng dẫn prompt toàn cục quan sát thêm ba ca trượt customer-021/026/035; dừng sau khi phát hiện và giữ trạng thái incomplete cho phần chưa chạy hết, không dùng làm kết quả cuối. Đối chứng thu hẹp `four-fixes-scoped-smoke-20261021` giữ đạt 026/035 nhưng 021 trượt cả ba lượt. Ca 021 cùng lỗi xác nhận trạng thái riêng bằng chính sách chung, nên mở rộng hàng rào không giả vờ tra cứu sang trạng thái giao dịch. Không diễn giải những lượt này thành chứng minh nhân quả hoặc tính ổn định tổng quát.

Lượt `four-fixes-verified-smoke-20261021-r1/r2/r3` trên bản mã cuối: **21/21 đạt, không lỗi dịch vụ**, gồm bốn ca mục tiêu và ba ca kiểm soát 021/026/035, mỗi ca ba lần. Không thay nhãn để hợp thức hóa kết quả; hai lượt chẩn đoán trước được giữ nguyên dù có ca trượt.

```powershell
python -m unittest app.tests.test_rag
python -m unittest discover -s app/tests
python -m unittest evals.independent-v1.quality-20261021.test_report
python -m evals.independent-v1.quality-20261021.validate_labels
python -m evals.independent-v1.followup-20261021.check_targets --name four-fixes-verified-smoke-20261021 --include-controls
python -m evals.independent-v1.quality-20261021.run_regression --name four-fixes-verified-20261021
python -m evals.independent-v1.quality-20261021.report --name four-fixes-verified-20261021 --baseline quality-final-20261021 --output evals/independent-v1/followup-20261021
```

Tên lượt phải mới khi chạy lại, không ghi đè bằng chứng. `KET_QUA.md` và `report.json` chỉ được tạo khi cả bảy bộ đã hoàn tất; so sánh trên cùng nhãn với lượt quality-final, tách riêng chấm lại nhãn v1/v2.

## Giới hạn

Các quy tắc hỏi rõ/giới hạn tra cứu mới chỉ bao phủ mẫu tiếng Việt đã thử; chưa phải bộ phân tích đầy đủ mọi cách diễn đạt. Cần công cụ được phân quyền và xác thực riêng nếu bổ sung tra trạng thái mã thật. Prompt tốt hơn không thay được người duyệt và bộ kín mới. Backend đang chạy không có reload phải khởi động lại mới nhận mã; không tự khởi động lại trong lượt sửa này.
