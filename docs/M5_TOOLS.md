# Chọn công cụ đơn hàng có kiểm soát quyền

Ngày kiểm chứng gần nhất: 26/09/2026. Mốc con M5 dùng qwen3:4b chọn hành động có cấu trúc, backend điều phối. Không dùng agent tự lập kế hoạch nhiều bước, không cho model sửa đơn hoặc quyết định danh tính. Chưa nghiệm thu trọn M5, đánh giá sentiment/tóm tắt hoặc chất lượng M3.

## Đánh giá điều phối ngày 26/09/2026

Kết quả mới nhất sau sửa ngữ cảnh handoff và NFC: 24/24 bộ gốc, 8/8 bộ nối tiếp, 10/12 bộ ngữ cảnh mới. Ba lượt bản cuối có 25 lời gọi selector thật, không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. 144 unittest đạt trong 49,188 giây với transport mock. Hai ca policy-free-form và negation-prefixed vẫn chuyển nhầm vì ngoài mẫu; không coi điểm bộ gốc là nghiệm thu M5. Lưu các lượt trước/sau tại evals/tools/runs/handoff-*; chi tiết mẫu và giới hạn ở mục nhận diện handoff.

CLI `python -m app.evaluate_tools --output evals/tools/runs/my-new-run` đo 24 ca giả lập có nhãn nháp, chưa người duyệt. Chạy điều phối, Ollama selector và kiểm tra quyền thật trên SQLite trong bộ nhớ; riêng RAG được thay bằng kết quả đánh dấu, không đọc DB/vector người dùng. Baseline đạt 17/24; thêm một câu system prompt ưu tiên chuyển nhân viên khi vừa hỏi trạng thái vừa yêu cầu hủy/đổi đơn, kể cả có điều kiện, đạt 18/24. Ca cancel-and-track được sửa, không thực hiện hủy đơn.

Mỗi lượt có 15 lời gọi selector thật, không lỗi provider, không quan sát lộ marker mã vận đơn bị cấm hoặc thay đổi đơn. Đây là kiểm tra giới hạn trên fixture, không bảo đảm mọi dạng rò rỉ. Sáu ca chưa đạt: refund-policy, no-human-needed, currency-policy do từ khóa handoff; implicit-followup, ambiguous-followup, expired-followup do tin hiện tại thiếu mã và chưa suy ra đơn từ lịch sử. Nhãn hỏi nối tiếp mô tả khả năng mong muốn vượt giới hạn hiện tại. Tập đã dùng chỉnh prompt nên chỉ là phát triển/regression; không suy ra chất lượng RAG, tóm tắt hoặc cải thiện độ trễ toàn luồng.

Ba test runner mới; 137 unittest đạt trước chỉnh prompt, 10 test liên quan chạy lại đạt trên prompt cuối với transport mock. Đã kiểm tra snapshot nguồn/model/dataset và từ chối ghi đè kết quả. Bằng chứng, cách chấm và giới hạn tại [evals/tools/README.md](../evals/tools/README.md).

## Hợp đồng thực thi

Lượt bổ sung history-reference-20260926 đạt 21/24 với 17 lời gọi selector thật: cả bốn ca followup đạt, còn refund-policy, no-human-needed, currency-policy. Tám ca mới tại followups.jsonl đạt trong history-boundaries-20260926 với năm lời gọi selector; bao gồm chính sách/hủy đơn, mã hiện tại ưu tiên, mã AI, mã sai và tin dài. Không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. Bốn test mới và mở rộng tranh chấp cho nối tiếp; toàn bộ 141 unittest đạt trong 49,555 giây. Các ca mới vẫn là nhãn nháp phục vụ phát triển, không phải nghiệm thu độc lập.

Khi hội thoại open, phân loại yêu cầu gặp nhân viên theo quy tắc trước. Nếu có đúng một mã DH/ORD theo ORDER_PATTERN, lưu tin khách và tool_trace pending rồi commit trước khi gọi model. Nhiều mã khác nhau yêu cầu khách chọn một mã và không gọi model. Mã hợp lệ trong tin hiện tại ưu tiên hơn lịch sử.

Từ 26/09/2026, nếu tin hiện tại không có mã nhưng nhắc rõ “đơn đó”, “đơn này”, “đơn ấy”, “đơn vừa nêu”, “đơn ở trên” (có thể thêm “hàng” sau “đơn”), lấy các mã khách đã gửi trong bốn tin khách/AI gần nhất của cùng hội thoại. Chuẩn hóa NFC/hoa thường/khoảng trắng chỉ cho cụm tham chiếu. Không lấy mã do AI hoặc nhân viên nêu, không lấy hội thoại khác; quét tin khách đầy đủ, không cắt ở 500 ký tự như lịch sử RAG. Một mã đi bộ chọn; nhiều mã yêu cầu làm rõ; không có mã vẫn đi RAG. Nếu tin hiện tại chứa DH/ORD mà không tạo mã hợp lệ, không dùng mã cũ để thay thế âm thầm. Các cách nói khác hoặc mã đã ra ngoài cửa sổ chưa được suy ra.

Trace nội bộ có order_id_source=history khi mã đến từ lịch sử, gồm pending/clarification và kết quả cuối; widget tiếp tục không nhận trace. Bộ chọn chỉ nhận yêu cầu hiện tại và một mã đã giải quyết, không nhận lịch sử hoặc dữ liệu đơn. Mọi kiểm tra chủ đơn/quyền phiên/hết hạn và chặn tool muộn vẫn thực hiện ngay trước thực thi; mã trong lịch sử không cấp quyền.

Từ 22/09/2026, nhận mã DH/ORD bằng chữ/số ASCII, cho phép một dấu - hoặc _ ngay sau tiền tố, ít nhất bốn ký tự chữ/số phía sau, tổng không quá 64 ký tự. Hoa/thường ASCII tương đương; không chuyển chữ Unicode giống hình thành mã khác. Không lấy một phần mã trong chuỗi chữ/số/gạch nối/gạch dưới dài hơn: DH12345-EXTRA hoặc x-DH12345 không được hiểu là DH12345. Ngoặc, dấu phẩy và dấu câu thông thường vẫn phân cách mã. Nếu không còn mã hợp lệ, đi RAG như nhánh không có mã; chưa thêm thông báo riêng cho mã sai. Quyền chủ đơn và quyền widget vẫn kiểm tra tại lúc thực thi.

Schema chỉ nhận name thuộc lookup_order/handoff/rag và arguments chứa đúng order_id backend lấy từ tin hiện tại hoặc lịch sử trong phạm vi trên. Không cho thêm customer_id, agent_id, URL, tên tool khác hoặc trường ngoài schema; backend xác thực lại kể cả khi provider không tuân thủ grammar. rag là nhánh chuyển sang dịch vụ RAG hiện có, không phải công cụ đọc đơn. Văn bản tự do từ bộ chọn không được dùng làm câu trả lời.

Sau chọn tool, backend khóa lại hội thoại. Chỉ tra đơn/chuyển nhân viên nếu hội thoại còn open và tin khách cuối vẫn là tin đang xử lý. lookup_order lấy customer_id từ hội thoại trong DB và kiểm tra chủ đơn tại thời điểm thực thi. Đơn không tồn tại hoặc không thuộc khách dùng cùng kết quả, chuyển hàng chờ, không lộ trạng thái hay mã vận đơn. Kết quả hợp lệ được backend ghép theo mẫu cố định, không đưa dữ liệu đơn cho model viết lại.

handoff tạo hoặc tái sử dụng ticket bằng cùng quy tắc hiện có. Model chọn handoff vì khách yêu cầu hủy chỉ có nghĩa chuyển nhân viên; đơn không bị hủy. Tin/handoff/đóng trong lúc model chờ vẫn ghi được, tool muộn bị skipped. Tên widget tự nhập không xác minh chủ đơn; tra thành công cần chủ đơn nội bộ hoặc quyền đúng đơn do admin cấp cho phiên sau xác minh thủ công.

## Nhật ký và lỗi

Migration v5 cộng cột JSON nullable Message.tool_trace, không thay dữ liệu cũ; kiểm thử xác nhận chạy lại giữ trace đã có. API chi tiết Inbox trả trace cho staff. Từ 22/09/2026, nhân viên mở **Nhật ký công cụ** dưới tin khách để xem trạng thái, mã đơn, hành động và kết quả đã lưu. Snapshot widget không trả trace, quyền hoặc retrieval thô.

Nhật ký mặc định thu gọn, dùng details/summary có hỗ trợ bàn phím và giữ trạng thái mở qua polling. Pending được ghi là Chưa có kết quả vì có thể là lượt bị gián đoạn; rag chỉ xác nhận chọn luồng chính sách, không khẳng định đáp án thành công. Executed phản ánh lượt xử lý cũ, không phải trạng thái đơn hiện tại; kết quả không thấy/không có quyền giữ chung một nhãn. Tin không có trace không hiển thị mục này. Trạng thái lạ dùng nhãn Chưa xác định; không xuất JSON thô hoặc trường ngoài danh sách hiển thị. Không có nút chạy lại tool.

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

## Nhận diện handoff bằng từ khóa

Từ 22/09/2026, phần so khớp chuyển nhân viên chuẩn hóa Unicode NFC, không phân biệt hoa/thường và gộp khoảng trắng (xuống dòng, tab, khoảng trắng không ngắt). Chỉ nhận từ/cụm từ nguyên vẹn: tệp PDF không còn khớp nhầm tệ; gặp xuống dòng nhân viên và dấu tiếng Việt dạng tách rời vẫn được nhận. Chuẩn hóa chỉ phục vụ so khớp; tin nhắn đã lưu và trích đoạn ticket giữ văn bản gốc.

Từ 26/09/2026, bỏ qua riêng cụm “tiền tệ”, phủ định rõ yêu cầu gặp người ở đầu mệnh đề và một số mẫu hỏi chính sách hoàn tiền. Phủ định hỗ trợ không/chưa cần/muốn, có thể mở đầu bằng tôi/mình/em; mệnh đề bắt đầu ở đầu tin hoặc sau dấu câu. Câu hỏi chính sách cần cụm điều kiện/chính sách/quy định/quy trình/thủ tục hoàn tiền, tiếp bằng dấu hỏi hoặc là gì/như thế nào/thế nào/ra sao, có thể kèm một cụm theo chính sách/quy định hoặc của cửa hàng/shop. Đây là mẫu có giới hạn, không phải hiểu ý định tự do.

Chỉ che cụm khớp để so từ khóa; khiếu nại hoặc yêu cầu xử lý khác trong cùng tin vẫn kích hoạt handoff. Ví dụ hỏi chính sách rồi yêu cầu hoàn tiền ngay vẫn chuyển nhân viên. Phủ định chuyển giao không cấp quyền xem đơn: khách không có quyền vẫn chuyển hàng chờ sau tra cứu bị từ chối. Nhãn negative/neutral là kết quả quy tắc định tuyến, chưa được chấm như bộ phân tích cảm xúc.

Widget dùng chung bộ phân loại khi kiểm tra AI bận và xử lý nghiệp vụ. Tin trung tính cần suất AI, nhận 429 trước lưu nếu bận; yêu cầu handoff thật vẫn đi ngay. Nút Gặp nhân viên giữ hành vi trực tiếp. Telegram dùng chung dịch vụ sau lưu update. Đầu vào bộ chọn công cụ được chuẩn hóa NFC để tránh model hiểu khác giữa dấu ghép/tách; tin lưu và trích đoạn ticket giữ nguyên. Chưa hiểu phủ định/phát ngôn trích dẫn tùy ý hoặc tiếng Việt không dấu.

## Phạm vi tiếp theo

CLI `--merge` gộp phiếu theo ID được chia cho từng thành viên trong cùng lượt đo. Giữ tên/ghi chú, kể cả ca chờ; nếu cùng ca có nội dung duyệt khác nhau thì chặn output để đối chiếu. Không biểu quyết hoặc tự chọn bản cuối. Chín test CLI/HTML đạt sau bổ sung; cách gộp và tính điểm tại [hướng dẫn gộp phiếu](../evals/tools/README.md#gộp-phần-duyệt-của-các-thành-viên).

Đã có CLI `app.review_tools` và ba biểu mẫu HTML offline cho 44 ca gần nhất: lưu nháp, kiểm tra tên/lý do, xuất JSON giữ bằng chứng và tiếp tục từ JSON qua `--html --reviews`. Cả 44 ca chưa có quyết định của người chấm. Bác nhãn phải ghi lý do, điểm chỉ tính trên nhãn được duyệt và vẫn tính lỗi xử lý trong mẫu số. Đây là duyệt sau khi xem kết quả, không phải đánh giá độc lập hay chất lượng câu trả lời. Bảy test CLI/HTML đạt; QA desktop/mobile và JSON xuất từ giao diện đã kiểm chứng trên ca giả lập. Hướng dẫn cùng giới hạn tải file tại [evals/tools](../evals/tools/README.md#duyệt-bằng-trình-duyệt-offline).

Cần người duyệt nhãn và tập kiểm tra độc lập về cách viết mã, yêu cầu hỗn hợp và hỏi nối tiếp sau bộ 24 ca phát triển; sửa nhận nhầm ý định và chốt hành vi dùng lịch sử trước mở rộng. Đã có quyền từng đơn cho widget sau xác minh thủ công; xác minh tự động còn thiếu. Nhận diện khiếu nại và tóm tắt vẫn chủ yếu theo quy tắc/trích lịch sử, chưa được chấm chất lượng. Adapter Telegram có chống sự kiện trùng và kiểm thử local; kênh thứ hai vẫn cần tích hợp thật. Không để thiếu tài khoản kênh thứ hai biến thành tuyên bố đã hoàn tất đa kênh.

## Quyền tra đơn widget ngày 21/09/2026

Widget đã có cơ chế nhập mã do admin cấp sau xác minh ngoài hệ thống. Tool chấp nhận đúng đơn đã cấp quyền cho phiên, ngoài nhánh khách nội bộ đã gắn chủ đơn; kiểm tra lại thời hạn, phiên và chủ đơn ngay trước tra cứu. Không gộp Customer, không mở các đơn khác cùng chủ. Xem [ORDER_ACCESS.md](ORDER_ACCESS.md). Chưa có OTP tự động hoặc đăng nhập khách; đánh giá M5 độc lập và kênh thứ hai vẫn còn thiếu.
