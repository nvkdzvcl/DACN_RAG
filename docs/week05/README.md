# Hồ sơ tuần 05 về Use Case và Sequence Diagram

Nội dung phục vụ tuần 05 từ ngày 09 đến 15/10/2026, được bổ sung ngày 15/10/2026 vào Chương 3 và Chương 4 của báo cáo Nhóm 2B. Bộ mô hình mô tả nền tảng CSKH bán lẻ giả lập đã phân tích ở tuần 04; đối chiếu mã nguồn hiện tại để người đọc thấy mục tiêu người dùng, trách nhiệm từng mô đun và các điểm kiểm soát đồng thời.

## Nội dung bổ sung Chương 3

### 3.10 Use Case toàn hệ thống và phân hệ

#### 3.10.1 Phạm vi và quy ước UML

Ranh giới hệ thống bao gồm frontend Website, API FastAPI, xử lý nghiệp vụ, SQLite, kho file, Qdrant embedded, Ollama local và adapter Telegram. Khách hàng, nhân viên, quản trị viên, người duyệt và người vận hành là tác nhân con người. Telegram Bot API và SMTP là tác nhân hệ thống bên ngoài. Controller, cơ sở dữ liệu, model và kho vector là thành phần bên trong, không vẽ thành người dùng của hệ thống.

Quản trị viên là vai trò chuyên biệt của nhân viên: được sử dụng các chức năng nhân viên và có thêm quyền quản lý. Mũi tên generalization có tam giác rỗng hướng từ quản trị viên tới nhân viên. Quan hệ này không miễn điều kiện phụ trách hội thoại: cả admin cũng phải là người nhận việc trước khi trả lời hoặc hoàn tất. Người phụ trách là trạng thái phân công của nhân viên, không phải loại tài khoản mới.

Association là đường liền nối tác nhân với mục tiêu họ tham gia; không biểu diễn thứ tự thực hiện. Bộ này không dùng include hoặc extend vì các mục tiêu được đặc tả độc lập. Đăng nhập, có quyền và có phiên hợp lệ là tiền điều kiện, không phải hành vi phải chạy lại ở mọi Use Case. Kiểm tra UUID, gọi embedding, truy vấn SQL và khóa ghi là bước nội bộ, không tách thành Use Case người dùng. Chuyển người thật là mục tiêu riêng UC06, còn điều kiện dẫn tới chuyển giao được mô tả trong luồng thay thế của UC04/UC13; không dùng extend để thay một nhánh if của chương trình.

ID UC01–UC12 giữ tương ứng với hồ sơ thiết kế cũ; UC13–UC20 bổ sung tra đơn, quản lý giao tin và các chức năng hỗ trợ hiện có. Các mục tiêu quản lý như UC05 có lựa chọn tải mới, lập chỉ mục lại hoặc xóa, nhưng mỗi lượt chỉ thực hiện một thao tác được cấp quyền. Không suy association thành quyền gọi mọi endpoint.

#### 3.10.2 Phân rã theo mô đun

Bốn mô đun nghiệp vụ chính bám đề cương: Unified Inbox, Kho tri thức, Hỏi đáp RAG kết hợp tra đơn và Chuyển giao nhân viên. Hai nhóm hỗ trợ là truy cập/danh tính và quản lý/đánh giá/vận hành. Phân rã này là trách nhiệm logic trong một ứng dụng, chưa phải sáu microservice được triển khai riêng.

| Mô đun | Use Case | Thành phần và ranh giới |
|---|---|---|
| M01 Unified Inbox và vòng đời ticket | UC07–UC11, UC14 | Inbox React, inbox.py, ticket_service.py, sla_service.py; xử lý quyền phụ trách, hoàn tất và snapshot SLA |
| M02 Kho tri thức | UC05, UC18 | documents.py, chunks.py, document_service.py, vector_store.py; sở hữu phiên bản nguồn, file và chỉ mục |
| M03 Hỏi đáp và tra đơn | UC04, UC13 | widget.py, message_service.py, answer_service.py, tool_service.py, order_service.py; model không cấp quyền dữ liệu |
| M04 Chuyển giao nhân viên | UC06 | handoff_service.py được Website và Telegram gọi chung; dừng AI và tạo/tái dùng ticket |
| S01 Truy cập và danh tính | UC01–UC03, UC15, UC19 | auth.py, customer_auth.py, widget.py, workspace.py; cookie/CSRF, phiên, token email và quyền từng đơn |
| S02 Quản lý đánh giá và vận hành | UC12, UC16, UC17, UC20 | workspace.py, readiness.py, công cụ eval/backup; số liệu kinh doanh giả lập tách khỏi điểm chất lượng RAG |

UI chỉ gửi ý định và dữ liệu đầu vào; API xác thực, kiểm tra quyền và trả lỗi; service xử lý nghiệp vụ; dữ liệu lưu qua SQLAlchemy hoặc adapter vector/file. Thực tế một số nghiệp vụ tiếp nhận, phản hồi, hoàn tất và cấp quyền vẫn có SQL trực tiếp trong Controller. Vì vậy kiến trúc đã tách nhiều trách nhiệm nhưng chưa đạt việc toàn bộ Controller chỉ điều phối service. Sequence giữ đúng vị trí xử lý hiện tại; nếu tách service sau này phải giữ các transaction và điều kiện quyền tương đương.

#### 3.10.3 Danh mục mục tiêu và truy vết

| ID và mục tiêu | Tác nhân chính | Yêu cầu tuần 04 |
|---|---|---|
| UC01 Cấp tài khoản nhân viên | Admin | FR01, NFR01 |
| UC02 Đăng nhập và kết thúc phiên nhân viên | Nhân viên, admin | FR01, NFR01 |
| UC03 Sử dụng hội thoại Website riêng | Khách | FR02, FR03, NFR01 |
| UC04 Hỏi chính sách có nguồn | Khách; Telegram truyền tin | FR04, BR03, BR11, NFR10 |
| UC05 Quản lý kho tri thức | Admin | FR05, BR11 |
| UC06 Yêu cầu hỗ trợ từ nhân viên | Khách, nhân viên; Telegram truyền tin | FR07, BR04 |
| UC07 Tiếp nhận yêu cầu đang chờ | Nhân viên | FR08, BR05, NFR02 |
| UC08 Phản hồi khách đang phụ trách | Nhân viên; Telegram truyền tin | FR08, FR11, BR08 |
| UC09 Hoàn tất lượt hỗ trợ | Nhân viên | FR09, BR06, BR10 |
| UC10 Tiếp tục hỗ trợ sau giải quyết | Khách; Telegram truyền tin | FR09, BR07 |
| UC11 Theo dõi Inbox và SLA | Nhân viên | FR10, FR12, BR10 |
| UC12 Duyệt chất lượng câu trả lời | Người duyệt | FR14, NFR10 |
| UC13 Tra cứu đơn được phép | Khách; Telegram truyền tin theo phạm vi hiện có | FR06, BR01, BR02, BR09 |
| UC14 Xử lý phản hồi Telegram gửi lỗi | Nhân viên | FR11, BR08, NFR07 |
| UC15 Quản lý tài khoản khách | Khách; SMTP truyền thư | FR02, FR13, NFR01 |
| UC16 Xem hồ sơ đơn và báo cáo | Nhân viên | FR12, NFR01 |
| UC17 Sao lưu và khôi phục dữ liệu | Người vận hành | FR14, NFR06 |
| UC18 Đọc nguồn và hỏi thử nội bộ | Nhân viên | FR04, FR05, NFR10 |
| UC19 Cấp hoặc thu hồi quyền tra đơn | Admin | FR06, BR01, BR09 |
| UC20 Quản lý dữ liệu bán lẻ giả lập | Admin | FR12, NFR02 |

UC13 phân biệt quyền truy cập với dữ liệu khách tự khai. Hàm lookup_order cho phép khi chủ đơn khớp customer_id do server xác định, hoặc OrderAccess còn hiệu lực của đúng hội thoại/phiên và chủ đơn hiện tại. Cấp mã và nhập mã qua biểu mẫu chỉ có ở Website; không dùng mã này cho Telegram và không ghép khách theo tên/email. Trường hợp Telegram chưa có quan hệ chủ đơn tin cậy phải chuyển nhân viên. Những API tra đơn dành cho staff cũng không phải API công khai cho khách.

Các sơ đồ dưới đây gồm Use Case tổng quát và sáu phân hệ. Một tác nhân có thể xuất hiện ở nhiều hình để đọc rõ trách nhiệm; vẫn là cùng một vai trò trong hệ thống. Phần UML dựa trên OMG UML 2.5.1 [S7].

### 3.11 Đặc tả Use Case nghiệp vụ chính

Mỗi đặc tả nêu tác nhân, kích hoạt, tiền điều kiện, hậu điều kiện, luồng chính và luồng thay thế/ngoại lệ. Các tiêu chí cuối dùng để rà soát thiết kế và chọn ca nghiệm thu; không khẳng định đã chạy nghiệm thu mới. Tiền điều kiện không được dùng để bỏ kiểm tra quyền hoặc trạng thái lại ở backend.

#### 3.11.1 UC04 Hỏi chính sách có nguồn

| Trường | Đặc tả |
|---|---|
| Mục tiêu | nhận câu trả lời có bằng chứng đúng điều kiện áp dụng. |
| Actor chính | khách; actor hỗ trợ: Telegram khi dùng kênh đó. |
| Kích hoạt | khách gửi câu hỏi chính sách. |
| Tiền điều kiện | danh tính/phiên hợp lệ, hội thoại open, nội dung đúng giới hạn; Website có chỗ xử lý AI khả dụng. |
| Hậu điều kiện thành công | tin khách và phản hồi hợp lệ được lưu, phản hồi có vị trí nguồn. |
| Bảo đảm tối thiểu | khi xử lý đã lưu đầu vào rồi mới lỗi, tin khách vẫn còn; lỗi trước tiếp nhận không được báo là đã gửi. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Khách gửi nội dung và UUID ổn định; API kiểm tra phiên, CSRF, giới hạn tốc độ và dữ liệu.
2. Hệ thống kiểm tra trùng trong hội thoại, lưu tin và cập nhật tin khách cuối, rồi commit trước khi gọi model.
3. Hệ thống lấy lịch sử giới hạn của đúng hội thoại; truy hồi các phiên bản tài liệu đang indexed bằng embedding và Qdrant.
4. Pipeline chọn ID bằng chứng, dựng câu trả lời và kiểm định; có thể sửa lựa chọn tối đa một lần rồi kiểm định lại.
5. Hệ thống kiểm tra lại trạng thái, tin khách cuối và nguồn dưới khóa phối hợp với thay đổi tài liệu; chỉ lưu đáp án khi các điều kiện vẫn đúng.
6. Website trả snapshot đã lọc thông tin nội bộ; Telegram đưa phản hồi vào hàng gửi. Khách đọc đáp án hoặc yêu cầu hỗ trợ tiếp.

Luồng thay thế và ngoại lệ: A1 thiếu/mâu thuẫn nguồn thì từ chối; câu thiếu chủ thể/điều kiện cần thiết thì hỏi rõ, không tự tạo chính sách. A2 cùng UUID và nội dung trả kết quả đã nhận; UUID đổi nội dung gây 409. A3 Website AI bận gây 429 trước lưu tin; UI giữ nháp và UUID. E1 lỗi model sau lưu tin báo lỗi và giữ đầu vào; Telegram có thể chuyển hàng chờ theo adapter. E2 handoff, tin mới hoặc nguồn đổi trong lúc model chạy thì bỏ đáp án cũ. Tiêu chí rà soát: không lộ ghi chú/trace, không lưu AI lỗi thời; nguồn khớp chữ chưa đủ chứng minh đúng ngữ nghĩa. Truy vết: FR04, BR03/BR11; SD01, BPMN01.

#### 3.11.2 UC13 Tra cứu đơn được phép

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Tra cứu đơn được phép |
| Actor chính | khách. |
| Kích hoạt | hỏi trạng thái/mã vận đơn. |
| Tiền điều kiện | danh tính do server xác định, hội thoại open; quyền sở hữu tin cậy hoặc quyền từng đơn còn hiệu lực. |
| Hậu điều kiện thành công | chỉ trạng thái và mã vận đơn được phép được trả; không sửa giao dịch. |
| Bảo đảm tối thiểu | không tiết lộ đơn tồn tại hay dữ liệu của người khác khi không đủ quyền. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Nếu cần cấp mã Website, admin thực hiện UC19 sau xác minh ngoài hệ thống; khách nhập mã tại biểu mẫu riêng, không gửi mã vào chat/model.
2. API kiểm tra mã hash, phạm vi đơn, chủ đơn, hạn và phiên; cập nhật ràng buộc hội thoại có điều kiện rồi commit.
3. Khách hỏi về một đơn; hệ thống lưu tin trước model, lấy mã từ tin hiện tại hoặc tham chiếu rõ ràng trong lịch sử khách của cùng hội thoại.
4. Model chọn lookup_order trong JSON Schema giới hạn; backend kiểm tra tên công cụ và đúng mã đã xác định.
5. Backend khóa ghi hội thoại, kiểm tra tin cuối/trạng thái và quyền hiện tại; order_service đọc dữ liệu nội bộ theo chủ đơn hoặc OrderAccess hợp lệ.
6. Hệ thống trả thông tin được phép; model không tự cấp quyền hoặc tạo dữ liệu đơn.

Luồng thay thế và ngoại lệ: A1 nhiều mã yêu cầu chọn một; mã mới không hợp lệ không được âm thầm dùng mã cũ. A2 chọn rag thì chuyển luồng hỏi chính sách; chọn handoff, muốn hủy/đổi/hoàn tiền thì UC06. A3 không có quyền/không tìm thấy chuyển nhân viên với thông báo chung. E1 mã hết hạn, thu hồi, khác phiên hoặc đổi chủ thì chặn; email đã xác minh không tự cấp quyền đơn. E2 JSON ngoài schema/lỗi provider không thực thi công cụ; tin khách giữ nguyên. Tiêu chí: thử sai phiên, hết hạn và handoff đồng thời; không có thao tác trừ kho/thanh toán. Truy vết: FR06, BR01/BR02/BR09; SD02, BPMN02.

#### 3.11.3 UC06 Yêu cầu hỗ trợ từ nhân viên

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Yêu cầu hỗ trợ từ nhân viên |
| Actor chính | khách hoặc nhân viên nội bộ. |
| Kích hoạt | chọn Gặp nhân viên, /human, khiếu nại cần chuyển giao hoặc yêu cầu từ staff. |
| Tiền điều kiện | hội thoại còn dùng được và actor được phép truy cập. |
| Hậu điều kiện | hội thoại chờ tiếp nhận hoặc tiếp tục do người đã phụ trách xử lý; ticket hoạt động không bị nhân bản. |
| Bảo đảm tối thiểu | giữ lịch sử và không trả AI mới sau khi bàn giao đã commit. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Khách gửi yêu cầu có UUID, hoặc staff yêu cầu hỗ trợ qua API được phân quyền.
2. Backend khóa ghi hội thoại, đọc lại trạng thái và kiểm tra trùng.
3. Hệ thống chuyển open sang handoff_requested; tạo ticket nếu chưa có ticket open/assigned.
4. Ticket lưu trích tối đa tám tin gần nhất làm thông tin bàn giao, không coi đây là tóm tắt ngữ nghĩa bằng LLM.
5. Hệ thống commit và hiển thị hàng chờ; các tin mới tiếp tục được lưu để nhân viên đọc.

Luồng thay thế và ngoại lệ: A1 đã chờ/assigned thì tái dùng lượt hoạt động, không gọi AI. A2 resolved nhắn tiếp dùng UC10. E1 closed ở phiên cũ bị chặn; Telegram tin mới tạo hội thoại mới. E2 request lặp cùng UUID không tạo ticket trùng; mã dùng cho nội dung khác gây xung đột. Tiêu chí: handoff trong lúc SD01 gọi model phải chặn lưu đáp án cũ. Truy vết: FR07, BR04; SD01/SD03/SD04, BPMN01/BPMN03.

#### 3.11.4 UC07 Tiếp nhận yêu cầu đang chờ

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Tiếp nhận yêu cầu đang chờ |
| Actor chính | nhân viên, bao gồm admin trong vai trò nhân viên. |
| Kích hoạt | chọn Tiếp nhận. |
| Tiền điều kiện | phiên staff hoạt động; hội thoại handoff_requested, chưa có người phụ trách. |
| Hậu điều kiện | đúng một người phụ trách, hội thoại/ticket sang assigned. |
| Bảo đảm tối thiểu | người thua tranh chấp không ghi đè người đã nhận. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Nhân viên đọc danh sách hàng chờ và gửi yêu cầu nhận hội thoại.
2. API xác thực staff, kiểm tra CSRF và tìm hội thoại.
3. UPDATE có điều kiện kiểm tra trạng thái chờ và assigned_agent_id IS NULL.
4. Chỉ khi rowcount bằng 1, hệ thống đổi ticket open sang assigned trong cùng transaction rồi commit.
5. UI hiển thị người phụ trách và quyền trả lời.

Luồng thay thế và ngoại lệ: A1 hai người nhận cùng lúc, chỉ một UPDATE thành công; người còn lại nhận 409 và đọc lại. E1 hội thoại không có trả 404; hết phiên/sai vai trò bị chặn. E2 lỗi ghi DB rollback cả phân công và ticket. Tiêu chí: không mô tả RLock trong Python là khóa phân tán; điều kiện SQL mới là kiểm soát tranh chấp nhận việc. Truy vết: FR08, BR05, NFR02; SD03, BPMN03.

#### 3.11.5 UC08 Phản hồi khách đang phụ trách

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Phản hồi khách đang phụ trách |
| Actor chính | nhân viên phụ trách; Telegram là actor truyền tin khi dùng kênh đó. |
| Kích hoạt | gửi nội dung trả lời. |
| Tiền điều kiện | hội thoại assigned, assigned_agent_id khớp phiên đăng nhập; nội dung hợp lệ. |
| Hậu điều kiện | một tin staff được lưu; Website có thể đọc qua polling, Telegram theo dõi giao riêng. |
| Bảo đảm tối thiểu | không báo sent chỉ vì DB đã lưu và không mất bản nháp khi request chưa được xác nhận. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Nhân viên gửi nội dung cùng client_message_id ổn định.
2. API thực hiện UPDATE có điều kiện kiểm tra người phụ trách và trạng thái.
3. Hệ thống tìm UUID agent trong hội thoại; nếu mới thì lưu tin, nếu cùng người/nội dung thì tái dùng tin.
4. Transaction commit trước giao tin ra dịch vụ ngoài.
5. Website nhận tin qua snapshot; Telegram worker tạo pending theo message_id, gửi và cập nhật sent khi Bot API xác nhận.

Luồng thay thế và ngoại lệ: A1 UUID giống và nội dung giống trả tin cũ; UUID khác nội dung hoặc khác người gây 409. E1 không phụ trách/không assigned bị chặn kể cả admin. E2 Telegram failed/uncertain giữ lịch sử và dùng UC14; không tự thử lại uncertain. Tiêu chí: API hiện cho phép staff thiếu UUID; bảo đảm chống trùng nêu trên áp dụng khi UI gửi UUID ổn định. SLA Telegram tính lúc xác nhận gửi, không phải lúc nhân viên bấm nút. Truy vết: FR08/FR11, BR05/BR08/BR10; SD03/SD04.

#### 3.11.6 UC09 Hoàn tất lượt hỗ trợ

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Hoàn tất lượt hỗ trợ |
| Actor chính | nhân viên phụ trách. |
| Kích hoạt | chọn Giải quyết hoặc Đóng. |
| Tiền điều kiện | có ghi chú, ticket thuộc hội thoại và tin khách cuối đã đọc; lượt đang assigned. |
| Hậu điều kiện | ticket/hội thoại có kết quả, người/thời điểm hoàn tất và snapshot SLA; có tin hệ thống thông báo kết quả. |
| Bảo đảm tối thiểu | không chốt lượt mới bằng request cũ. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. UI gửi status resolved/closed, ticket_id, last_customer_message_id và ghi chú.
2. API khóa ghi, đọc lại hội thoại và ticket.
3. Backend kiểm tra người phụ trách, lượt hoạt động và tin khách cuối không thay đổi.
4. ticket_service tính và đóng băng phản hồi đầu/SLA, ghi người và thời điểm; API cập nhật hội thoại, thêm tin hệ thống.
5. Commit tất cả thay đổi trong cùng transaction rồi UI làm mới.

Luồng thay thế và ngoại lệ: A1 cùng ticket/kết quả/người/ghi chú đã hoàn tất trả duplicate, không chốt lượt đang mở sau đó. A2 khách nhắn tiếp sau resolved theo UC10; closed Website bắt đầu hội thoại mới, Telegram tin mới tạo hội thoại mới. E1 tin mới trước chốt, đổi phân công hoặc ticket khác gây 409/404 và yêu cầu đọc lại. E2 thiếu ghi chú hoặc status lạ gây lỗi dữ liệu. Tiêu chí: snapshot lượt cũ bất biến theo luồng ứng dụng, không tuyên bố toàn DB không thể sửa bằng công cụ ngoài. Truy vết: FR09, BR06/BR07/BR10; SD03.

#### 3.11.7 UC05 Quản lý kho tri thức

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Quản lý kho tri thức |
| Actor chính | admin. |
| Kích hoạt | tải nguồn, lập chỉ mục lại hoặc xóa. |
| Tiền điều kiện | phiên admin, CSRF hợp lệ và kho không bị một thao tác khác giữ document_lock. |
| Hậu điều kiện tải thành công | file, các đoạn và vector của một index_version được lưu; status indexed. |
| Hậu điều kiện xóa thành công | nguồn, đoạn và vector được dọn. |
| Bảo đảm tối thiểu | nguồn lỗi/xóa dở không được truy hồi như nguồn sẵn sàng. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính cho tải mới:
1. Admin gửi file; API đọc tối đa 10 MB cộng một byte để phát hiện quá giới hạn.
2. document_service kiểm tra tên/loại/kích thước và SHA-256; lấy khóa thay đổi kho trong cùng tiến trình.
3. Hệ thống lưu file và bản ghi processing, commit; đọc chữ, chia đoạn có vị trí nguồn và tạo phiên bản mới.
4. Hệ thống ghi đoạn SQL rồi commit, dọn vector cũ, gọi embedding theo lô và upsert Qdrant.
5. Chỉ sau khi các lô hoàn tất, bản ghi chuyển indexed với index_version/embedding_model rồi commit.
6. Admin đọc số đoạn/trạng thái; staff dùng UC18 để đọc nguồn hoặc hỏi thử.

Luồng thay thế và ngoại lệ: A1 reindex chuyển processing, bỏ phiên bản cũ khỏi nguồn truy hồi và thực hiện lại bước 3–5. A2 xóa đặt deleting/index_version=null và commit trước dọn file/vector/SQL; xóa dở vẫn bị ẩn và có thể thử xóa lại. E1 nội dung trùng hoặc kho đang bận trả 409. E2 file lỗi, PDF scan chưa OCR, quá giới hạn trích xuất/đoạn hoặc provider lỗi chuyển failed; không trả indexed giả. E3 SQL, file và Qdrant không có transaction phân tán; trạng thái nguồn là cơ chế ngăn truy hồi dữ liệu dở, không bảo đảm rollback liên kho tuyệt đối. Truy vết: FR05, BR11; SD05, BPMN04.

#### 3.11.8 UC14 Xử lý phản hồi Telegram gửi lỗi

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Xử lý phản hồi Telegram gửi lỗi |
| Actor chính | nhân viên phụ trách; actor hỗ trợ: Telegram Bot API. |
| Kích hoạt | đọc failed/uncertain trong Inbox. |
| Tiền điều kiện | tin thuộc hội thoại Telegram đang do nhân viên phụ trách, delivery ở failed/uncertain. |
| Hậu điều kiện | retry đưa đúng delivery sang pending, hoặc skip sang skipped và giữ lịch sử. |
| Bảo đảm tối thiểu | uncertain không tự gửi lại; việc retry có thể tạo bản sao trên Telegram nếu lần trước đã giao. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Nhân viên đọc loại lỗi và nội dung tin gốc.
2. Với failed, chọn gửi lại; với uncertain, đọc cảnh báo rồi xác nhận nguy cơ trùng trước khi gửi lại.
3. API kiểm tra phiên, quyền phụ trách và trạng thái delivery.
4. API chuyển delivery về pending, xóa lỗi rồi commit; không tạo Message mới.
5. Worker gửi tin theo thứ tự của người nhận và ghi kết quả; pending không có nghĩa đã giao.

Luồng thay thế và ngoại lệ: A1 nhân viên chọn skip để giữ bản ghi và cho tin sau tiếp tục. E1 thiếu confirm_uncertain trả 409. E2 sai người phụ trách trả 403, delivery không đủ điều kiện trả 409. E3 tiến trình khởi động lại biến sending dở thành uncertain và giữ để con người quyết định. Tiêu chí: thứ tự áp dụng theo TelegramPeer, không chặn mọi khách vì một người nhận lỗi; Bot API không cung cấp idempotency key cho sendMessage trong thiết kế này. Truy vết: FR11, BR08, NFR07; SD04.

#### 3.11.9 UC19 Cấp hoặc thu hồi quyền tra đơn

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Cấp hoặc thu hồi quyền tra đơn |
| Actor chính | admin. |
| Kích hoạt | cần cấp quyền Website sau xác minh người yêu cầu hoặc cần thu hồi quyền. |
| Tiền điều kiện | phiên admin và đơn tồn tại; có kiểm chứng qua thông tin liên hệ tin cậy ngoài ứng dụng. Phiên Website của khách phải hợp lệ khi nhập mã, chưa được ràng buộc ở bước cấp. |
| Hậu điều kiện | một quyền có phạm vi đơn/chủ đơn và hạn 15 phút được cấp, hoặc quyền hiện tại bị thu hồi. |
| Bảo đảm tối thiểu | tên/email khách tự khai và checkbox xác nhận không phải bằng chứng danh tính. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Admin xác minh người nhận qua kênh tin cậy đã có của chủ đơn; hệ thống không tự gọi OTP hoặc đối chiếu danh tính ngoài.
2. Admin yêu cầu cấp quyền trong giao diện quản lý; backend xác thực quyền admin và kiểm tra đơn.
3. Backend tạo mã bí mật, lưu hash và ràng buộc chủ đơn/hạn; mã cũ bị thay thế theo phạm vi quyền hiện có.
4. Admin nhận mã và giao qua kênh tin cậy ngoài ứng dụng; mã không xuất hiện trong báo cáo hoặc prompt.
5. Khách nhập mã theo UC13. Khi cần thu hồi, admin xóa quyền; các lượt tra tiếp theo phải kiểm tra lại.

Luồng thay thế và ngoại lệ: A1 xác minh thất bại chỉ chuyển nhân viên, không cấp mã. E1 đơn không tồn tại hoặc cập nhật đồng thời bị chặn theo API; quyền hết hạn/sai chủ/sai phiên không dùng được. Tiêu chí: kiểm tra thời hạn từ lúc cấp, không gia hạn lại khi khách nhập; không dùng cho Telegram. Truy vết: FR06, BR01/BR09; SD02.

#### 3.11.10 UC10 Tiếp tục hỗ trợ sau giải quyết

| Trường | Đặc tả |
|---|---|
| Mục tiêu | Tiếp tục hỗ trợ sau giải quyết |
| Actor chính | khách. |
| Kích hoạt | nhắn tiếp vào hội thoại resolved. |
| Tiền điều kiện | phiên/kênh còn hợp lệ; hội thoại resolved. |
| Hậu điều kiện | tin mới và ticket mới được lưu, bỏ người phụ trách cũ và chuyển hàng chờ; lịch sử/snapshot ticket trước giữ nguyên. |
| Bảo đảm tối thiểu | không tự bật AI trở lại hoặc sửa kết quả lượt đã hoàn tất. |
| Luồng chính | Các bước đánh số trình bày ngay sau bảng. |
| Luồng thay thế và ngoại lệ | Các nhánh A/E trình bày sau luồng chính. |

Luồng chính:
1. Khách gửi tin với UUID/update ID; hệ thống kiểm tra trùng và khóa hội thoại.
2. Hệ thống lưu tin, cập nhật tin khách cuối, xóa phân công cũ và chuyển sang handoff_requested.
3. Hệ thống không tái dùng ticket resolved; tạo ticket hoạt động mới với trích lịch sử.
4. Commit rồi hiển thị hàng chờ để UC07 tiếp nhận lại.

Luồng thay thế và ngoại lệ: A1 retry cùng tin trả bản ghi cũ, không mở lượt thứ hai. E1 hội thoại closed không theo luồng này: Website dùng phiên/hội thoại mới, Telegram adapter tạo hội thoại mới. E2 request finish cũ vẫn chỉ tham chiếu ticket cũ và không được chốt ticket mới. Truy vết: FR09, BR07, NFR02; SD03/SD04.

### 3.12 Bộ hình Use Case

Hình 3.1 là toàn hệ thống; Hình 3.2–3.7 lần lượt là bốn phân hệ chính và hai nhóm hỗ trợ. Association thể hiện tác nhân tham gia, còn điều kiện quyền cụ thể nằm trong đặc tả. Không coi tất cả tác nhân nối cùng ellipse là có cùng quyền thao tác.

![Hình 3.1 Use Case toàn hệ thống](diagrams/UC_ALL.png)
![Hình 3.2 Use Case Unified Inbox và ticket](diagrams/UC_M01.png)
![Hình 3.3 Use Case Kho tri thức](diagrams/UC_M02.png)
![Hình 3.4 Use Case Hỏi đáp và tra đơn](diagrams/UC_M03.png)
![Hình 3.5 Use Case Chuyển giao nhân viên](diagrams/UC_M04.png)
![Hình 3.6 Use Case Truy cập và danh tính](diagrams/UC_S01.png)
![Hình 3.7 Use Case Quản lý đánh giá và vận hành](diagrams/UC_S02.png)

## Nội dung bổ sung Chương 4

### 4.6 Sequence Diagram cho năm chức năng cốt lõi

#### 4.6.1 Thành phần và quy ước

Năm sơ đồ tách Client/UI, FastAPI Controller hoặc adapter nhận tin, xử lý nghiệp vụ, SQLite và dịch vụ/kho liên quan. Controller dùng dependency xác thực/CSRF; các SQL nằm trực tiếp trong inbox.py và widget.py được vẽ từ Controller tới DB, không gán giả cho một lớp service chưa tồn tại. RAGService là nhãn trách nhiệm của answer_service.py và vector_store.py; DocumentService gồm save_document/index_document/delete_document, chưa có IngestionService hay queue độc lập.

Thông điệp gọi đồng bộ dùng mũi tên liền đầu kín; phản hồi dùng nét đứt. Lifeline nét đứt thể hiện thời gian đi xuống. Khung alt có các điều kiện loại trừ nhau; opt là nhánh có thể không chạy; loop là lặp có giới hạn; critical đánh dấu vùng ghi được tuần tự hóa bằng transaction/khóa phù hợp. Các lời gọi SQL trong vùng ghi cùng transaction được gom thành một thông điệp nghiệp vụ để đọc rõ tính nguyên tử. Số thứ tự chỉ giúp đối chiếu trong từng hình, không phải thời gian đo.

| Thành phần | Hiện thực | Giới hạn cần đọc cùng sơ đồ |
|---|---|---|
| Client | Widget/chat, Inbox, Kho tri thức React | Website nhận tin bằng polling; không có WebSockets/SignalR/MQTT |
| Controller | app/api/widget.py, inbox.py, documents.py, workspace.py | FastAPI trực tiếp, không có API Gateway riêng; một số logic/SQL vẫn ở Controller |
| Service | message_service, handoff_service, order_service, ticket_service, document_service | Gọi đồng bộ trong ứng dụng; chưa tách microservice/queue nghiệp vụ |
| Database và file | SQLite/SQLAlchemy, thư mục tri thức | Ghi có điều kiện; file/SQL/vector không có transaction phân tán |
| RAG và vector | Ollama local, Qdrant embedded, document_lock | RLock và semaphore trong bộ nhớ chỉ phối hợp một API worker |
| Kênh ngoài | Telegram Bot API, SMTP TLS | Telegram polling một thread; SMTP gửi nền trong tiến trình, chưa có hàng gửi bền |

Các cơ chế kỹ thuật phù hợp đề tài là phân quyền từng đơn, kiểm tra bất biến của lượt hỗ trợ, chống trùng UUID/update ID và loại AI lỗi thời. Trừ kho, thanh toán, chống gian lận tài chính và khóa Redis phân tán không thuộc phạm vi hiện thực; không thêm vào sơ đồ vì ví dụ trong yêu cầu tuần 05. Khi mở nhiều worker cần thiết kế lease/queue và giới hạn dùng chung rồi kiểm chứng lại; sơ đồ hiện tại không bảo đảm an toàn cho triển khai đó.

#### 4.6.2 SD01 Hỏi chính sách và chặn AI lỗi thời

Phạm vi UC04 và ngoại lệ UC06. WidgetController kiểm tra phiên/CSRF/rate limit và lấy semaphore khi cần generation. MessageService ghi tin, kiểm tra UUID, commit trước khi RAG gọi embedding/model. RAGService đọc phiên bản indexed, embedding câu hỏi, truy hồi Qdrant và chọn/kiểm định bằng chứng. Các bước kiểm định chi tiết được gộp thành lời gọi có giới hạn, không phải một model được quyền tự làm nghiệp vụ.

Sau khi có ứng viên, MessageService lấy document_lock khi có câu trả lời rồi khóa ghi hội thoại, đọc lại trạng thái/tin cuối và kiểm tra nguồn. Khung alt tách đáp án hợp lệ với đáp án cũ; nguồn đổi hoặc đã handoff thì không lưu AI. Không có SQL transaction giữ xuyên suốt lời gọi Ollama. Lỗi provider sau nhận tin giữ đầu vào; UI nhận ai_error hoặc trạng thái hàng chờ theo kênh. Những nhánh UUID khác nội dung/429 trước tiếp nhận được đặc tả tại UC04 để hình không lặp toàn bộ kiểm tra HTTP.

Điểm rà soát: đầu vào được commit trước model; HISTORY không là nguồn chính sách; lần kiểm tra sau model không được bỏ. Việc kiểm định bằng cùng model chưa thay đánh giá độc lập về ngữ nghĩa. Mã đối chiếu: app/api/widget.py, app/services/message_service.py, app/rag/answer_service.py, app/rag/vector_store.py.

#### 4.6.3 SD02 Cấp quyền và tra đơn chỉ đọc

Phạm vi UC19/UC13. Hai UI khác nhau thể hiện admin cấp mã và khách nhập mã. Xác minh qua liên hệ tin cậy diễn ra ngoài ứng dụng trước khi cấp; hộp xác nhận trên UI không tự chứng minh danh tính. WorkspaceController cấp mã/hash/hạn, WidgetController ràng buộc quyền vào hội thoại bằng UPDATE có điều kiện; mã bí mật không đi tới Ollama.

MessageService lưu tin rồi gọi ToolService chọn công cụ qua JSON Schema giới hạn. Khi chọn lookup_order, hệ thống khóa lại hội thoại và kiểm tra tin cuối/trạng thái; OrderService kiểm tra chủ đơn server hoặc quyền có hiệu lực, đọc dữ liệu và chỉ trả status/tracking_code. Hình minh họa nhánh tra cứu; JSON lỗi, nhiều mã, chọn rag/handoff và thiếu quyền được đặc tả trong UC13. Nhánh alt quyền không đạt đi handoff và không tiết lộ đơn tồn tại.

Điểm rà soát: không dùng customer_id do khách/model tự khai; truy vấn đọc sau kiểm tra quyền hiện tại; kiểm tra grant/redeem là hai thao tác riêng. Quyền đang hợp lệ lúc cấp không bảo đảm còn hợp lệ lúc tra. Mã đối chiếu: app/api/workspace.py, app/api/widget.py, app/services/tool_service.py, app/services/order_service.py.

#### 4.6.4 SD03 Tiếp nhận phản hồi và hoàn tất ticket

Phạm vi UC07/UC08/UC09, tiền đề UC06. InboxController thực hiện UPDATE nhận việc với điều kiện handoff_requested và chưa phụ trách, rồi đổi ticket trong cùng transaction. Khung alt chỉ một người thành công; người thua nhận 409 và phải đọc lại. Điều kiện SQL này khác khóa phân tán trong bộ nhớ.

Khi gửi phản hồi Website, API kiểm tra người phụ trách, tái dùng UUID cùng nội dung và commit tin. Khách lấy phản hồi bằng polling, không có server push. Khi hoàn tất, API giữ khóa ghi, kiểm tra ticket/người/tin khách cuối, gọi TicketService đóng băng SLA và thêm tin hệ thống trong cùng transaction. Khung alt tin cuối đổi làm rollback/409; request lặp của ticket đã hoàn tất dùng nhánh duplicate ở UC09. Giao Telegram được tách sang SD04 để không giữ transaction trong khi gọi mạng.

Điểm rà soát: nhận việc, phản hồi và hoàn tất đều kiểm tra quyền ở server; admin không được bỏ qua phụ trách. Ticket resolved cũ không trở lại open khi khách nhắn tiếp; UC10 tạo lượt mới. Mã đối chiếu: app/api/inbox.py, app/services/ticket_service.py, app/services/sla_service.py.

#### 4.6.5 SD04 Tiếp nhận và giao tin Telegram có phục hồi

Phạm vi UC04/UC06/UC08/UC14 và tiếp nhận Telegram của FR03. TelegramWorker là adapter trong app/telegram.py, không phải một HTTP Controller mới. Worker gọi getUpdates bằng con trỏ đã commit, persist_updates lưu update và con trỏ trong cùng transaction, rồi process_next gọi MessageService chung. Tin chat riêng được phân biệt theo bot/người; cập nhật lặp không tạo tin mới.

queue_outgoing tạo delivery pending theo message_id. Worker xử lý tin đầu chưa hoàn tất của từng peer; failed/uncertain chặn các tin sau cùng peer, các peer khác vẫn có thể đi tiếp. UPDATE có điều kiện chuyển pending sang sending, kiểm tra AI còn đúng và commit trước sendMessage. Kết quả sent chỉ ghi khi có message_id hợp lệ từ Telegram; timeout/phản hồi không chắc ghi uncertain, còn lỗi xác định ghi failed. Không có bảo đảm exactly-once giao tin vì lần timeout có thể đã đến Telegram.

opt phục hồi thể hiện sending dở chuyển uncertain sau khởi động lại; nhân viên quyết định retry/skip qua UC14, không tự gửi lại uncertain. Hình bỏ các probe getMe/getWebhookInfo để tập trung nhận/giao tin, nhưng cấu hình không được xóa webhook của người dùng. Có một khoảng thời gian giữa kiểm tra AI và sendMessage sau commit: handoff xảy ra trong khoảng này vẫn có thể đua với tin đang bay; không tuyên bố chặn tuyệt đối mọi tin ngoài hệ thống. Mã đối chiếu: app/telegram.py và app/api/inbox.py.

#### 4.6.6 SD05 Lập chỉ mục nguồn và xử lý lỗi liên kho

Phạm vi UC05. Admin gửi file, DocumentsController kiểm tra quyền và gọi DocumentService. Service giữ document_lock cùng tiến trình, kiểm tra file/hash, lưu file và processing trước trích chữ/chia đoạn. Sau commit các đoạn SQL, lặp lô tối đa 16 đoạn gọi embedding rồi upsert vector. indexed/index_version chỉ được công bố sau khi hoàn tất các lô.

alt tách hoàn tất với lỗi trích xuất/provider/vector: nguồn chuyển failed và chưa được truy hồi. File scan không có chữ phải xử lý OCR ngoài trước tải, không mô tả hệ thống đã có OCR. opt xóa đánh dấu deleting/index_version=null và commit trước dọn file/vector/SQL; nguồn ngừng truy hồi ngay cả khi dọn dở. Reindex đi cùng pipeline và tạo phiên bản mới, không tái sử dụng nhãn indexed khi còn đang ghi.

Điểm rà soát: đây là chuỗi commit liên kho có trạng thái phục hồi, không phải transaction nguyên tử giữa SQLite và Qdrant. document_lock phối hợp với lần kiểm tra trước lưu AI ở SD01; không phải lease dùng chung giữa nhiều worker. Mã đối chiếu: app/api/documents.py, app/services/document_service.py, app/rag/vector_store.py và startup trong app/main.py.

#### 4.6.7 Đối chiếu yêu cầu và phạm vi kiểm chứng

| Sequence | Use Case chính | Cơ chế và nhánh cần kiểm chứng |
|---|---|---|
| SD01 | UC04, UC06 | Commit đầu vào, UUID, kiểm định có giới hạn, handoff/tin mới/nguồn đổi, lỗi model |
| SD02 | UC13, UC19 | Mã hash/hạn/phiên, schema công cụ, chủ đơn/quyền hiện tại, thiếu quyền và chỉ đọc |
| SD03 | UC07–UC10 | UPDATE nhận độc quyền, UUID staff, quyền phụ trách, ticket/tin cuối và snapshot SLA |
| SD04 | UC08, UC14 | Update/con trỏ bền, gửi ngoài transaction, failed/uncertain, thứ tự peer và phục hồi |
| SD05 | UC05 | Processing/index_version, lô embedding, failed/deleting, nguồn không sẵn sàng bị ẩn |

Bộ tuần 05 hoàn thành phần mô hình và đặc tả để đọc/duyệt. Kiểm tra file nguồn, actor/Use Case, mã truy vết và bố cục hình không thay chạy ứng dụng, nghiệm thu Telegram/SMTP thật, chấm RAG độc lập hoặc đo tải triển khai. Các mục tiêu NFR của tuần 04 vẫn là ngưỡng đề xuất.

[S7] Object Management Group, Unified Modeling Language phiên bản 2.5.1. https://www.omg.org/spec/UML/2.5.1. Truy cập ngày 15/10/2026; tham khảo Use Case, generalization, interaction lifeline và combined fragment.

Các sơ đồ sau là năm luồng trên. Bản SVG có thể phóng to; file PlantUML cùng tên lưu actor, participant, thông điệp và fragment để chỉnh sửa.

![Hình 4.6 SD01 Hỏi chính sách và kiểm tra AI lỗi thời](diagrams/SD01.png)
![Hình 4.7 SD02 Cấp quyền và tra đơn chỉ đọc](diagrams/SD02.png)
![Hình 4.8 SD03 Tiếp nhận phản hồi và hoàn tất ticket](diagrams/SD03.png)
![Hình 4.9 SD04 Telegram nhận giao và phục hồi tin](diagrams/SD04.png)
![Hình 4.10 SD05 Lập chỉ mục nguồn và xử lý lỗi](diagrams/SD05.png)

## Sử dụng hồ sơ

- Bản tích hợp: [BaoCao.docx](../report/BaoCao.docx), [BaoCao.md](../report/BaoCao.md).
- [Use Case tổng quát](diagrams/UC_ALL.svg); sáu phân hệ UC_M01–UC_M04, UC_S01–UC_S02 trong thư mục diagrams.
- [SD01](diagrams/SD01.svg), [SD02](diagrams/SD02.svg), [SD03](diagrams/SD03.svg), [SD04](diagrams/SD04.svg), [SD05](diagrams/SD05.svg).
- Mỗi hình có PNG, SVG và PlantUML. PlantUML là nguồn logic chỉnh sửa; bố cục khi render bằng công cụ khác có thể khác ảnh trong báo cáo.
- Chạy `python docs/week05/build.py --check` để kiểm tra nguồn/hình và bản tích hợp; chạy không tham số để dựng hình và đồng bộ báo cáo. Cần runtime tài liệu có Pillow và python-docx.

Ngày 15/10/2026, nội dung tuần 05 từng được tích hợp chi tiết vào đề cương. Ngày 16/10/2026, [đề cương hiện tại](../decuong/262701-DACN-07-Nhom2B_DeCuong.docx) được rút về mục tiêu, phương pháp, kế hoạch và dàn ý các chương; Use Case, đặc tả và Sequence chi tiết vẫn lưu trong báo cáo và hồ sơ này. Có thể tra cứu bản sao sơ đồ theo loại tại [danh mục sơ đồ](../diagrams/README.md).
