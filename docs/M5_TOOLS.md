# Chọn công cụ đơn hàng có kiểm soát quyền

Ngày kiểm chứng: 15/09/2026. Mốc con M5 dùng qwen3:4b chọn hành động có cấu trúc, backend điều phối. Không dùng agent tự lập kế hoạch nhiều bước, không cho model sửa đơn hoặc quyết định danh tính. Chưa nghiệm thu trọn M5, đánh giá sentiment/tóm tắt hoặc chất lượng M3.

## Hợp đồng thực thi

Khi hội thoại open, phân loại yêu cầu gặp nhân viên theo quy tắc trước. Nếu có đúng một mã DH/ORD theo ORDER_PATTERN, lưu tin khách và tool_trace pending rồi commit trước khi gọi model. Không có mã đi RAG như trước; nhiều mã khác nhau yêu cầu khách chọn một mã và không gọi model. Hỏi nối tiếp không nêu lại mã chưa dùng lịch sử để suy ra đơn.

Schema chỉ nhận name thuộc lookup_order/handoff/rag và arguments chứa đúng order_id đã lấy từ tin hiện tại. Không cho thêm customer_id, agent_id, URL, tên tool khác hoặc trường ngoài schema; backend xác thực lại kể cả khi provider không tuân thủ grammar. rag là nhánh chuyển sang dịch vụ RAG hiện có, không phải công cụ đọc đơn. Văn bản tự do từ bộ chọn không được dùng làm câu trả lời.

Sau chọn tool, backend khóa lại hội thoại. Chỉ tra đơn/chuyển nhân viên nếu hội thoại còn open và tin khách cuối vẫn là tin đang xử lý. lookup_order lấy customer_id từ hội thoại trong DB và kiểm tra chủ đơn tại thời điểm thực thi. Đơn không tồn tại hoặc không thuộc khách dùng cùng kết quả, chuyển hàng chờ, không lộ trạng thái hay mã vận đơn. Kết quả hợp lệ được backend ghép theo mẫu cố định, không đưa dữ liệu đơn cho model viết lại.

handoff tạo hoặc tái sử dụng ticket bằng cùng quy tắc hiện có. Model chọn handoff vì khách yêu cầu hủy chỉ có nghĩa chuyển nhân viên; đơn không bị hủy. Tin/handoff/đóng trong lúc model chờ vẫn ghi được, tool muộn bị skipped. Quyền mua hàng của khách widget chưa xác minh, tên tự nhập không gắn với khách có đơn; luồng tra đơn thành công hiện kiểm chứng trên hội thoại nội bộ có customer_id hợp lệ.

## Nhật ký và lỗi

Migration v5 cộng cột JSON nullable Message.tool_trace, không thay dữ liệu cũ; kiểm thử xác nhận chạy lại giữ trace đã có. API chi tiết Inbox trả trace cho staff; chưa có giao diện nhật ký riêng. Snapshot widget không trả trace, quyền hoặc retrieval thô.

| Trạng thái trace | Ý nghĩa |
|---|---|
| pending | Đã lưu tin, bắt đầu chọn tool; chưa chứng minh đã thực thi |
| clarification | Nhiều mã đơn, trả yêu cầu chọn một mã |
| executed | Tool được xử lý trong transaction; lookup ghi found hoặc not_found_or_not_owned |
| rag | Model chọn nhánh chính sách, chạy dịch vụ RAG |
| provider_error | Lỗi provider/schema ở bộ chọn hoặc RAG tiếp theo, không trả dữ liệu đơn |
| skipped | Có tin mới hoặc trạng thái hội thoại đổi trước khi thực thi |

Trace chỉ lưu mã đơn/tên tool/trạng thái/kết quả kiểm tra, không lưu mã vận đơn hoặc completion thô. Lỗi SQL khi tra cứu rollback phần tool, trả HTTP 503, log lỗi theo message_id và giữ inbound đã commit; trace còn pending. Tiến trình bị dừng cũng có thể để pending, không được diễn giải là thành công. Chưa có retry tự động hoặc nhật ký kiểm toán chống sửa.

UUID cũ được kiểm tra trước model nên retry không chạy tool lần nữa. Sau lỗi provider/DB, đọc lịch sử và gửi yêu cầu mới nếu cần thử lại; đổi nội dung dưới cùng UUID bị từ chối. Handoff và kết thúc phiên vẫn dùng API hiện có, không thêm endpoint cho model gọi tùy ý.

## Kiểm chứng

```powershell
python -m unittest discover -s app/tests -v
python -m app.tests.smoke_tools
python -m app.tests.smoke_m4
npm --prefix frontend run build
```

smoke_tools dùng tiến trình riêng với SQLite/vector/tài liệu tạm; các model và dịch vụ nghiệp vụ chạy thật. Lệnh không nạp .env hoặc sửa dữ liệu người dùng, không mở cổng HTTP. JSON từng ca có trạng thái, trace và thời gian; assertion khiến lỗi trả exit code khác 0. Các ca cố định trong script là bộ phát triển nhỏ, không phải benchmark độc lập hoặc đánh giá do người chấm.

59 unittest đạt, trong đó sáu kiểm thử mới ở test_tools.py bao phủ schema/giả mạo, trả lời cố định/UUID/riêng tư, đơn không thuộc khách/không tồn tại, nhánh RAG/nhiều mã/quy tắc, lỗi provider/DB và tranh chấp với tin mới/handoff/đóng/đổi chủ đơn. Migration và widget cũng được cập nhật kiểm thử. Vite build đạt, assets không đổi. Smoke HTTP M4 chạy lại với Ollama thật đạt, câu hỏi 15,175 giây và toàn luồng 22,249 giây; không suy chênh lệch một lần chạy thành tăng tốc.

Lượt smoke sau khi khởi động Ollama hoàn tất 7/7 ca, không lỗi provider. Một lần chạy trước đó dừng ở ingestion do Ollama chưa chạy; không có câu hỏi hoàn tất, không tính là kết quả từ chối. Model qwen3:4b có digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7.

| Ca | Kết quả kiểm tra | Giây |
|---|---|---:|
| Trạng thái đơn thuộc khách | Trả trạng thái/mã vận đơn từ DB | 5,601 |
| Đơn của khách khác | Chuyển nhân viên, không lộ dữ liệu | 5,496 |
| Không có đơn | Chuyển nhân viên, cùng kết quả với sai chủ | 5,448 |
| Hủy đơn | Chuyển nhân viên, không sửa đơn | 5,394 |
| Giả mạo admin/customer_id | Chủ đơn vẫn do server kiểm tra, không lộ dữ liệu | 5,770 |
| Chính sách có mã đơn | Đi RAG, trả mốc 7 ngày kèm nguồn | 20,689 |
| Hai mã đơn | Yêu cầu chọn một mã, không gọi model | 0,020 |

Thời gian đo từng process_message tuần tự, có tải/gỡ model, không gồm ingestion. Ca chính sách gồm bộ chọn rồi RAG; không suy một lần smoke thành percentile hoặc độ trễ tải thực tế. Pipeline answer_question, prompt trích câu/kiểm định và retrieval giữ nguyên. Orchestration đổi ở tin có mã đơn, được kiểm tra riêng; không tuyên bố các điểm benchmark M3 đo lại trên bản M5.

## Quyết định chọn transport

Pilot ban đầu dùng native tools của Ollama với cùng model và think=false. Trên bảy ca, trạng thái/khác chủ/không có đơn/nhiều mã đạt, nhưng hủy đơn, giả mạo và chính sách sinh tới giới hạn 700 token nên bị chặn trước tool. Kiểm tra thô ca hủy cho thấy model viết suy luận dài dù đã đặt think=false. Không tăng giới hạn rồi coi các ca này thành công.

Bản được chọn dùng JSON Schema qua chat transport sẵn có, giới hạn name/arguments và chặn trả lời tự do. Đây là structured tool selection do ứng dụng điều phối, không phải native tool_calls của provider. Hai lựa chọn đều giữ kiểm tra quyền và không thực thi đầu ra lỗi; bản schema chạy lại các ca phát triển đạt như bảng trên. Không thêm dependency hoặc vòng lặp agent.

## Phạm vi tiếp theo

Cần mở rộng tập kiểm tra độc lập về cách viết mã, yêu cầu hỗn hợp và hỏi nối tiếp; thêm xác minh chủ đơn trước phục vụ tra cứu thành công cho khách ẩn danh. Nhận diện khiếu nại và tóm tắt vẫn chủ yếu theo quy tắc/trích lịch sử, chưa được chấm chất lượng. Kênh thứ hai cần tích hợp thật, danh tính theo kênh và chống webhook trùng. Không để thiếu tài khoản kênh thứ hai biến thành tuyên bố đã hoàn tất đa kênh.
