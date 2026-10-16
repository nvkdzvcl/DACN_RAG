# Hồ sơ tuần 04 về hiện trạng yêu cầu và quy trình nghiệp vụ

Hồ sơ phục vụ yêu cầu tuần 04 từ ngày 02 đến 08/10/2026, được bổ sung ngày 15/10/2026 cho Nhóm 2B. Nội dung dưới đây được đưa vào Chương 3 và Chương 4 của báo cáo. Phạm vi là nền tảng trợ lý AI hỗ trợ khách hàng đa kênh cho cửa hàng bán lẻ trực tuyến giả lập, sử dụng Website Chat Widget và Telegram.

Người thực hiện chưa khảo sát trực tiếp doanh nghiệp hoặc phỏng vấn nhân viên. Theo xác nhận của người dùng ngày 15/10/2026, hồ sơ sử dụng mô hình giả lập có tham khảo quy trình công khai. Không có số lượng khách, thời gian xử lý, tỷ lệ thất thoát hoặc kết quả phỏng vấn được xem là số liệu thực tế. Hồ sơ hoàn thiện mô tả và mô hình; chưa thay nghiệm thu nghiệp vụ, chất lượng RAG hoặc kết nối Telegram thật.

## Chương 3 Phân tích yêu cầu hệ thống

### 3.1 Phạm vi và phương pháp khảo sát

Đơn vị giả lập là một cửa hàng bán lẻ trực tuyến quy mô nhỏ, tiếp nhận câu hỏi về chính sách, giao hàng, đơn hàng và đổi trả. Khách liên hệ qua website hoặc Telegram; nhân viên CSKH xử lý yêu cầu, quản trị viên quản lý tài khoản và tài liệu. Kiểm tra hàng, duyệt đổi trả, hủy đơn, hoàn tiền và làm việc với đơn vị vận chuyển diễn ra ngoài nền tảng của đồ án. Hệ thống chỉ hỗ trợ tra cứu, lưu trao đổi và chuyển yêu cầu cho người có trách nhiệm.

Khảo sát bàn gồm ba nguồn: quy trình đổi trả công khai của FPT Shop [S1], tài liệu kỹ thuật và mã nguồn của đồ án [S5], cùng tiêu chuẩn BPMN và tài liệu bảo mật/tích hợp [S2–S4]. Quy trình FPT Shop chỉ được tham khảo ở cấu trúc tiếp nhận, kiểm tra điều kiện, thông báo phương án và sự đồng ý của khách; không sao chép thời hạn, phí hoặc chính sách sản phẩm vào cửa hàng giả lập. Không khẳng định cửa hàng giả lập là FPT Shop hoặc đã được doanh nghiệp xác nhận.

| Loại thông tin | Căn cứ | Cách sử dụng |
|---|---|---|
| Quy trình đổi trả công khai | S1, mục III Quy trình đổi trả | Tham khảo bước kiểm tra và phê duyệt bởi con người |
| Hành vi hệ thống hiện có | S5, API, dịch vụ và kiểm thử trong repo | Xác định chức năng, quyền và giới hạn đã triển khai |
| Hiện trạng trước khi áp dụng hệ thống | Kịch bản giả lập được người dùng cho phép | Giả định phân tích; cần đối chiếu khi có cửa hàng thực tế |
| Độ trễ và tải local | S6, dữ liệu đo có phạm vi riêng | Bằng chứng kỹ thuật local; không suy thành năng lực doanh nghiệp |
| Khối lượng khách và tổn thất kinh doanh | Chưa có dữ liệu | Không đặt số liệu hoặc tỷ lệ giả làm kết quả khảo sát |

### 3.2 Quy trình hiện trạng giả lập

Trước khi sử dụng nền tảng, nhân viên mở từng kênh để đọc tin, tra chính sách trong các file riêng và tra đơn trong sổ/bảng quản lý giả lập. Danh sách việc cần theo dõi và người phụ trách được ghi thủ công. Đây là mô hình tham chiếu để phân tích nhu cầu, không phải mô tả quan sát tại một doanh nghiệp cụ thể.

| Bước | Người xử lý | Đầu vào và thao tác | Đầu ra và ngoại lệ |
|---|---|---|---|
| AS01 Tiếp nhận | Khách, nhân viên CSKH | Khách gửi câu hỏi; nhân viên đọc tin tại từng kênh, ghi thời điểm và nội dung | Có yêu cầu cần xử lý; tin thiếu thông tin được hỏi lại |
| AS02 Phân loại | Nhân viên CSKH | Phân biệt hỏi chính sách, tra đơn, khiếu nại hoặc yêu cầu đổi/hủy | Chọn nguồn tra cứu; yêu cầu mơ hồ chưa được kết luận |
| AS03 Hỏi chính sách | Nhân viên CSKH | Mở tài liệu tương ứng với sản phẩm, thời điểm và điều kiện áp dụng | Trả lời theo tài liệu; tài liệu thiếu hoặc mâu thuẫn chuyển quản trị viên xác nhận |
| AS04 Tra đơn | Nhân viên CSKH, quản trị viên | Thu mã đơn; xác minh người yêu cầu qua thông tin liên hệ tin cậy đã có của chủ đơn | Chỉ cung cấp dữ liệu được phép; biết mã đơn hoặc tự khai email chưa đủ để cấp quyền |
| AS05 Khiếu nại và đổi trả | Nhân viên CSKH, người có thẩm quyền ngoài hệ thống | Thu thông tin mua hàng, lý do và tình trạng hàng; đối chiếu chính sách, yêu cầu kiểm tra nếu cần | Thông báo phương án và điều kiện; không hứa hoàn tiền/đổi hàng trước khi được duyệt |
| AS06 Bàn giao | Nhân viên CSKH | Chuyển nội dung, bằng chứng và việc đang chờ cho người xử lý | Có người phụ trách; nếu chưa nhận phải giữ yêu cầu ở danh sách chờ |
| AS07 Theo dõi và kết thúc | Nhân viên phụ trách, khách | Phản hồi, xác nhận kết quả, ghi việc còn chờ và lý do kết thúc | Giữ lịch sử; khách hỏi tiếp sau giải quyết cần mở lượt xử lý mới |

Tại AS05, mô hình tham khảo S1 yêu cầu kiểm tra tình trạng sản phẩm và điều kiện áp dụng trước khi thông báo phương án. Một số trường hợp phải có kết luận từ trung tâm bảo hành; phí phát sinh được thông báo trước khi thực hiện. Trong đồ án, các hoạt động này được nhân viên xử lý ngoài hệ thống, còn chatbot chỉ giải thích chính sách có nguồn và ghi nhận yêu cầu. Thời hạn đổi trả của cửa hàng giả lập phải lấy từ tài liệu đã được quản trị viên cung cấp, không tự suy theo chính sách của nhà bán lẻ khác.

### 3.3 Nút thắt và rủi ro của hiện trạng

Các vấn đề dưới đây là rủi ro dự kiến của kịch bản giả lập, chưa được đo bằng nhật ký hoặc phỏng vấn. Mỗi vấn đề gắn với một biện pháp và một cách xác minh để tránh trình bày suy đoán thành kết quả khảo sát.

| Mã | Điểm nghẽn hoặc rủi ro | Hậu quả dự kiến | Biện pháp mục tiêu và cách xác minh |
|---|---|---|---|
| BN01 | Mở nhiều kênh và ghi việc thủ công | Bỏ sót tin hoặc trả lời lặp | Inbox tập trung; đối chiếu số tin gốc với số tin đã lưu trong kịch bản thử |
| BN02 | Chính sách nằm trong nhiều file hoặc phiên bản | Trả lời theo tài liệu cũ, mất điều kiện áp dụng | Kho tri thức có phiên bản và citation; thử cập nhật nguồn trong lúc AI đang xử lý |
| BN03 | Tra đơn theo tên hoặc mã khách tự khai | Lộ dữ liệu của người khác | Quyền xem từng đơn sau xác minh; thử sai phiên, hết hạn và thu hồi |
| BN04 | Không có thao tác nhận việc độc quyền | Hai nhân viên xử lý cùng yêu cầu hoặc không ai nhận | Gán người phụ trách có điều kiện; thử hai người tiếp nhận đồng thời |
| BN05 | Theo dõi thời gian bằng ghi chú riêng | Không biết yêu cầu nào quá hạn | SLA phản hồi đầu; đối chiếu thời điểm tạo ticket và phản hồi đầu |
| BN06 | Mất mạng khi gửi hoặc tải lại trang | Khách gửi lại, trùng tin hoặc mất bản nháp | UUID và giữ bản nháp; thử mất phản hồi rồi gửi lại cùng ID |
| BN07 | Không ghi lý do và trạng thái kết thúc | Khó bàn giao hoặc đánh giá kết quả | Ghi chú nội bộ và lịch sử ticket; thử khách nhắn lại sau giải quyết |

Khi khảo sát thật, cần thu thập thời điểm nhận/phản hồi của một tập yêu cầu có sự đồng ý sử dụng, số lần đổi người xử lý, tỷ lệ yêu cầu thiếu thông tin và các phiên bản chính sách đang dùng. Không ghi tên khách, số điện thoại hoặc nội dung riêng tư vào báo cáo công khai. Số mẫu, khoảng thời gian và người xác nhận phải được ghi cùng kết quả; hiện các dữ liệu này chưa có.

### 3.4 Tác nhân và ranh giới trách nhiệm

| Tác nhân | Trách nhiệm | Giới hạn |
|---|---|---|
| Khách hàng | Gửi yêu cầu, đọc nguồn, cung cấp thông tin xác minh, yêu cầu người thật | Không đọc API nội bộ, ghi chú hoặc đơn chưa được cấp quyền |
| Nhân viên CSKH | Đọc Inbox, nhận việc, trả lời, ghi kết quả, xử lý lỗi giao tin | Chỉ trả lời/hoàn tất hội thoại do mình phụ trách |
| Quản trị viên | Cấp tài khoản, quản lý nguồn, hồ sơ/đơn giả lập, xác minh và cấp quyền đơn | Quyền quản trị không bỏ qua điều kiện phụ trách khi trả lời ticket |
| Ứng dụng FastAPI | Xác thực, phân quyền, lưu tin, điều phối, kiểm tra trạng thái và chống trùng | Quyết định của model không thay kiểm tra quyền tại backend |
| Ollama và Qdrant local | Embedding, truy hồi, chọn bằng chứng và kiểm định | Dịch vụ nội bộ; không có quyền tự sửa đơn hoặc cấp danh tính |
| Telegram Bot API | Nhận update và truyền phản hồi trong chat riêng | Dịch vụ bên ngoài; gửi thành công không chứng minh khách đã đọc |
| SMTP | Truyền thư xác minh và khôi phục mật khẩu | HTTP 202 chỉ là tiếp nhận yêu cầu, chưa chứng minh thư đã giao |
| Người duyệt | Đọc nguồn, duyệt nhãn và đánh giá câu trả lời | Điểm regression tự động không thay đánh giá độc lập |

### 3.5 Quy tắc nghiệp vụ

| Mã | Quy tắc |
|---|---|
| BR01 | Danh tính do phiên hoặc Telegram cung cấp; tên/email tự khai không xác minh quyền sở hữu đơn. Email đã xác minh cũng không tự ghép đơn hàng. |
| BR02 | Tra đơn chỉ đọc trạng thái và mã vận đơn được phép. Hủy đơn, đổi trả, hoàn tiền chuyển người thật; không tự thực hiện giao dịch. |
| BR03 | Chính sách phải có bằng chứng và giữ điều kiện áp dụng. Thiếu, mâu thuẫn hoặc không đủ căn cứ thì hỏi lại hoặc từ chối, không tạo câu trả lời khẳng định. |
| BR04 | Chuyển nhân viên dừng AI. Tin khách mới khi đang chờ/đã nhận vẫn được lưu; không tạo ticket trùng cho cùng lượt hỗ trợ. |
| BR05 | Tiếp nhận phải độc quyền. Chỉ người phụ trách được trả lời, giải quyết hoặc đóng, kể cả admin. |
| BR06 | Hoàn tất phải có ghi chú nội bộ và đúng ticket/tin khách cuối đã xem; thay đổi đồng thời trả xung đột để đọc lại. |
| BR07 | Nhắn sau resolved tạo lượt ticket mới, bỏ phân công cũ và tiếp tục chờ người thật. Widget closed phải tạo phiên/hội thoại mới; Telegram nhận tin mới sau closed tạo hội thoại mới. |
| BR08 | Retry cùng UUID/nội dung không tạo tin mới. Gửi Telegram uncertain không tự thử lại; nhân viên phụ trách xác nhận nguy cơ trùng trước khi gửi lại. |
| BR09 | Quyền widget giới hạn một đơn, một phiên và 15 phút từ lúc cấp; kiểm tra lại quyền khi tra. Mã này không dùng cho Telegram. |
| BR10 | SLA demo tính 24/7 từ tạo ticket tới phản hồi đầu: urgent 5, high 15, normal 60, low 240 phút. Website dùng thời điểm lưu tin nhân viên; Telegram dùng lúc API xác nhận gửi. Đây không phải SLA giải quyết. |
| BR11 | Chỉ đưa tài liệu sẵn sàng, đúng phiên bản vào truy hồi. Xóa hoặc đổi nguồn trong lúc model chạy phải chặn đáp án dựa trên phiên bản cũ. |
| BR12 | Đổi trả theo mô hình tham khảo cần kiểm tra chứng từ/thông tin mua hàng, tình trạng hàng và chính sách áp dụng; người có thẩm quyền thông báo phương án trước khi thực hiện. Việc kiểm tra và giao dịch nằm ngoài nền tảng. |

### 3.6 Yêu cầu chức năng

Mức ưu tiên P1 là yêu cầu bắt buộc của phạm vi đồ án; P2 là hỗ trợ vận hành/đánh giá. Trạng thái “có local” chỉ xác nhận đã có mã và bằng chứng kiểm chứng cục bộ trong S5, không xác nhận nghiệm thu thực tế. Các luồng nghiệm thu sau dùng dữ liệu tạm, không sửa dữ liệu khách hoặc gửi tin thật khi chưa cấu hình kênh.

| Mã | Yêu cầu và ưu tiên | Điều kiện và kết quả mong đợi | Ngoại lệ và tiêu chí kiểm chứng |
|---|---|---|---|
| FR01 | Xác thực nhân viên, P1; có local | Tài khoản hoạt động đăng nhập; admin cấp tài khoản; đổi mật khẩu thu hồi phiên | Chưa đăng nhập/sai quyền bị chặn; mật khẩu cũ không cấp phiên sau khi đổi |
| FR02 | Tài khoản và phiên khách, P1; có local | Cho phép vãng lai, đăng ký, đăng nhập, khôi phục lịch sử theo tài khoản | Hai tài khoản không đọc lịch sử nhau; hết phiên báo lỗi, không tự đổi danh tính |
| FR03 | Tiếp nhận đa kênh, P1; Website có local, Telegram chờ bot thật | Lưu tin cùng hội thoại/kênh; update Telegram chống trùng theo bot và update ID | Retry không tăng số tin; nhóm/tệp Telegram không đi luồng hỏi đáp văn bản thông thường |
| FR04 | Hỏi chính sách có nguồn, P1; có local, chất lượng chờ duyệt | Hội thoại open, nguồn sẵn sàng; trả bằng chứng có vị trí hoặc thông báo thiếu căn cứ | Lỗi model giữ tin khách; handoff/tin mới/nguồn đổi chặn đáp án cũ; nội dung đúng ngữ nghĩa cần người duyệt |
| FR05 | Quản lý kho tri thức, P1; có local | Admin tải PDF/DOCX/TXT/Markdown tối đa 10 MB, lập chỉ mục lại/xóa; staff xem nguồn | File lỗi không được báo sẵn sàng; PDF scan chưa OCR; tài liệu xóa không còn được truy hồi |
| FR06 | Tra đơn theo quyền, P1; có local trên dữ liệu giả lập | Widget đã được cấp quyền đúng đơn/phiên; chỉ trả trạng thái và vận đơn | Sai phiên, hết hạn, thu hồi hoặc đổi chủ chặn kết quả; không gửi mã bí mật vào model |
| FR07 | Chuyển nhân viên, P1; có local | Khách yêu cầu hoặc hệ thống phát hiện cần người thật; tạo/tái dùng ticket và dừng AI | Retry không trùng ticket; AI đang chờ không được trả sau handoff |
| FR08 | Tiếp nhận và trả lời, P1; có local | Nhân viên nhận hàng chờ; người phụ trách gửi phản hồi | Hai người nhận cùng lúc chỉ một người thành công; người khác không gửi/hoàn tất được |
| FR09 | Giải quyết, đóng và mở lượt mới, P1; có local | Người phụ trách gửi ghi chú, ticket và tin cuối; kết thúc đúng lượt | Tin khách mới trước hoàn tất gây 409; retry hoàn tất cũ không đóng lượt mới |
| FR10 | Inbox, tìm kiếm và SLA, P1; có local | Lọc/phân trang hội thoại, lịch sử, trạng thái đọc và bản nháp; hiển thị SLA phản hồi đầu | Giữ đúng khách/bản nháp khi đổi trang; mẫu số SLA không tính ticket chưa phản hồi |
| FR11 | Theo dõi giao tin Telegram, P1; có local, chờ kênh thật | Hiển thị pending, sending, sent, failed, uncertain, skipped; người phụ trách retry hoặc skip | Uncertain cần xác nhận; lỗi chặn tin sau cùng người nhận; không gửi ghi chú/trace nội bộ |
| FR12 | Quản lý hồ sơ, đơn và báo cáo, P2; có local | Staff xem, admin tạo/sửa dữ liệu giả lập; thống kê theo kỳ | Kiểm tra expected để chặn ghi đè; không đổi chủ đơn hoặc coi thống kê SLA là chất lượng AI |
| FR13 | Xác minh email và khôi phục mật khẩu, P2; có local, chờ SMTP thật | SMTP TLS, token đúng mục đích/hạn; reset thu hồi mọi phiên/token của tài khoản | Liên kết hết hạn/đã dùng bị chặn; phản hồi yêu cầu không tiết lộ email tồn tại; chưa bảo đảm giao thư bền |
| FR14 | Đánh giá và vận hành, P2; có công cụ local | Phiếu người duyệt, probe sẵn sàng, backup/restore vào thư mục mới | Chưa có nhãn duyệt thì tỷ lệ để null; restore kiểm tra hash và thu hồi phiên/token; không ghi đè dữ liệu |

#### 3.6.1 Luồng hỏi đáp và chuyển giao

Điều kiện đầu là phiên hợp lệ và tin đúng giới hạn. Hệ thống kiểm tra UUID, lưu tin trước lời gọi model, xác định trạng thái và loại yêu cầu. Hội thoại open có thể đi hỏi chính sách hoặc tra đơn; yêu cầu gặp nhân viên/khiếu nại cần chuyển giao đi hàng chờ. Hội thoại đang chờ hoặc assigned chỉ lưu tin và chuyển cho nhân viên, không gọi AI.

Kết quả RAG chỉ được lưu sau kiểm tra lại trạng thái, tin khách cuối và phiên bản nguồn. Thiếu bằng chứng dẫn tới từ chối hoặc hỏi làm rõ; lỗi dịch vụ giữ tin khách và báo lỗi, không giả làm câu trả lời thành công. Trả lời cũ bị bỏ khi điều kiện đã đổi. BPMN01 mô tả nhánh hỏi chính sách, còn BPMN02 và BPMN03 mô tả tra đơn và xử lý bởi nhân viên.

#### 3.6.2 Luồng tra đơn

Admin xác minh người nhận qua kênh tin cậy đã có rồi cấp mã cho đúng đơn. Khách nhập mã tại biểu mẫu riêng, hệ thống ràng buộc vào phiên và thời hạn. Khi nhận yêu cầu tra cứu, backend kiểm tra quyền còn hiệu lực và chủ đơn hiện tại; model không được cấp quyền bằng nội dung chat. Nhiều mã đơn cần hỏi chọn một mã. Không đủ quyền, yêu cầu hủy/đổi trả hoặc kênh Telegram chưa có cơ chế cấp quyền thì chuyển người thật, không tiết lộ đơn tồn tại hay dữ liệu chủ đơn.

#### 3.6.3 Luồng xử lý và kết thúc ticket

Nhân viên tiếp nhận có điều kiện, đọc tin và phản hồi. Với Website, tin đã lưu có thể được khách lấy bằng polling; với Telegram, tin chờ worker gửi và trạng thái giao được theo dõi riêng. Khi cần hoàn tất, người phụ trách gửi ghi chú cùng ticket và ID tin khách cuối đã xem. Xung đột yêu cầu đọc lại trước khi chốt. Giải quyết/đóng lưu người, thời điểm và snapshot SLA; không sửa kết quả lượt cũ khi khách mở lượt mới.

### 3.7 Yêu cầu phi chức năng

Các ngưỡng hiệu năng và phục hồi dưới đây là mục tiêu đề xuất cho nghiệm thu đồ án, chưa phải cam kết vận hành đã đạt. Chốt lại với GVHD khi xác định máy triển khai và tải thực tế. Độ trễ tính từ lúc gửi HTTP đến nhận đủ phản hồi; p95 tính riêng từng nhóm API, không gộp API đọc dữ liệu với API gọi model.

| Mã | Yêu cầu | Mục tiêu và cách kiểm chứng | Trạng thái |
|---|---|---|---|
| NFR01 | Bảo mật và riêng tư | 100% ca kiểm thử quyền từ chối truy cập sai vai trò/phiên/đơn; cookie HttpOnly/SameSite Strict, Secure và HTTPS khi triển khai; không lộ mật khẩu/token/ghi chú trong API khách | Có cơ chế local; HTTPS và rà soát triển khai còn chờ |
| NFR02 | Toàn vẹn khi đồng thời | Retry cùng UUID tạo đúng một tin; hai người nhận chỉ một người thành công; cập nhật stale gây xung đột; handoff chặn AI muộn trong mọi ca thử định trước | Có kiểm thử local; cần lặp trên môi trường triển khai |
| NFR03 | Độ trễ API không gọi model | Đề xuất p95 ≤ 1 giây cho đọc danh sách/chi tiết và ≤ 2 giây cho ghi tin staff, với 10 client, 500 hội thoại, trang Inbox 25; lỗi bất ngờ ≤ 1% trong lượt 15 phút | Có baseline local cũ; cần đo lại workload hiện tại |
| NFR04 | Độ trễ hỏi chính sách | Đề xuất p95 ≤ 15 giây ở lượt tuần tự tối thiểu 60 câu có nguồn/thiếu nguồn trên cấu hình model đã chốt và máy GPU ghi rõ; ghi riêng thời gian chờ/gọi model và lỗi | Có số đo regression; chưa nghiệm thu theo kịch bản này |
| NFR05 | Chịu tải và mở rộng | Đề xuất 10 client HTTP đồng thời trong 15 phút không mất/trùng tin; tải RAG đồng thời phải đo riêng, không suy 10 client HTTP thành 10 lượt generation; tăng worker chỉ sau thiết kế queue/lease và giới hạn dùng chung | Hiện một API worker với SQLite/Qdrant embedded; chưa nghiệm thu tải bền |
| NFR06 | Phục hồi dữ liệu | Đề xuất backup offline hằng ngày, RPO ≤ 24 giờ và RTO ≤ 60 phút trong buổi diễn tập; đối chiếu hash nguồn, số tin/ticket và việc thu hồi phiên sau restore | Có công cụ local; lịch backup và mục tiêu RPO/RTO chưa kiểm chứng |
| NFR07 | Độ bền kênh ngoài | Lỗi Telegram phải phân biệt failed/uncertain, không tự gửi lại uncertain; khởi động lại không trùng update/ticket; SMTP TLS và lỗi không lộ bí mật | Có mock/local; bot/hộp thư thật và hàng gửi SMTP bền còn chờ |
| NFR08 | Khả dụng giao diện | Đề xuất dùng được ở 320–1536 px, không tràn ngang trang; mọi thao tác chính bằng bàn phím, focus rõ, trạng thái tải/lỗi/rỗng và giữ bản nháp khi mất mạng | Có QA trình duyệt; điện thoại thật và trình đọc màn hình còn chờ |
| NFR09 | Quan sát và khả năng bảo trì | Ghi lỗi theo ID tin/yêu cầu, chỉ báo sẵn sàng có quyền staff; migration v1–v10 chạy lặp giữ dữ liệu; tài liệu quy trình có mã yêu cầu và phiên bản | Có local; chưa có audit quản trị đầy đủ hoặc giám sát production |
| NFR10 | Chất lượng và truy xuất nguồn | Đề xuất tối thiểu 60 câu độc lập được người duyệt chốt nhãn trước đo; tỷ lệ đáp án đúng ≥ 85%, từ chối đúng ≥ 90%, citation hỗ trợ đủ ≥ 95%; lỗi provider tính riêng, không bỏ khỏi báo cáo | Ngưỡng đề xuất chưa được duyệt; regression hiện có không thay bộ độc lập |

RPO là lượng dữ liệu có thể mất tính theo thời gian kể từ bản sao gần nhất; RTO là thời gian khôi phục để dịch vụ dùng được. Đáp án đúng được tính trên câu có đủ thông tin trả lời và bao gồm từ chối sai trong các ca không đạt. Từ chối đúng tính trên câu được duyệt là không đủ căn cứ; citation hỗ trợ đủ tính trên câu có đáp án nội dung được người duyệt đọc cả nguồn và điều kiện. Mỗi chỉ số phải có mẫu số, trường hợp lỗi/chưa chấm và cấu hình đầu vào; chưa có mẫu thì để null.

### 3.8 Phạm vi nghiệm thu và truy vết

| Vấn đề | Yêu cầu liên quan | Mô hình và bằng chứng |
|---|---|---|
| BN01, BN06 | FR03, FR10, FR11; NFR02, NFR07 | BFD03, BPMN01/BPMN03; kiểm thử widget/Telegram và API |
| BN02 | FR04, FR05; NFR10 | BFD02, BPMN01/BPMN04; kiểm thử nguồn đổi và phiếu người duyệt |
| BN03 | FR01, FR02, FR06; NFR01 | BFD01, BPMN02; kiểm thử quyền đơn và tài khoản |
| BN04, BN07 | FR07–FR09; NFR02 | BFD04, BPMN03; kiểm thử nhận việc, xung đột, lượt mới |
| BN05 | FR10, FR12; BR10 | BFD05, BPMN03; kiểm thử snapshot SLA và mẫu số báo cáo |
| Vận hành và mở rộng | FR13, FR14; NFR03–NFR09 | BFD06; đo HTTP/RAG riêng, diễn tập restore và kiểm chứng SMTP |

Hồ sơ tuần 04 hoàn thành phần phân tích và mô hình trong phạm vi giả lập. Những việc chưa xác nhận gồm khảo sát doanh nghiệp thật, duyệt ngưỡng NFR, nhãn/đáp án độc lập, bot Telegram thật, SMTP thật và tải bền tại máy triển khai. Các việc này được ghi nhận riêng; không gắn nhãn đã hoàn thành chỉ vì tài liệu hoặc mã nguồn đã tồn tại.

### 3.9 Nguồn tham chiếu

[S1] FPT Shop, Chính sách đổi trả, mục III Quy trình đổi trả. Truy cập ngày 15/10/2026: https://fptshop.com.vn/ho-tro/chinh-sach-doi-san-pham. Tham khảo quy trình kiểm tra và thông báo phương án; không sử dụng điều kiện/phí của FPT Shop làm chính sách cửa hàng giả lập.

[S2] Object Management Group, Business Process Model and Notation phiên bản 2.0.2: https://www.omg.org/spec/BPMN/2.0.2. Schema BPMN 2.0: https://www.omg.org/spec/BPMN/20100501/BPMN20.xsd. Truy cập/schema kiểm tra ngày 15/10/2026.

[S3] Telegram, Bot API, các mục getUpdates, getWebhookInfo và sendMessage: https://core.telegram.org/bots/api. Truy cập ngày 15/10/2026; tham khảo ranh giới nhận/gửi và dịch vụ bên ngoài.

[S4] OWASP, Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html. Truy cập ngày 15/10/2026; tham khảo kiểm tra quyền trên mọi request và nguyên tắc quyền tối thiểu.

[S5] Hồ sơ dự án: docs/API.md, docs/CUSTOMER_AUTH.md, docs/ORDER_ACCESS.md, docs/TELEGRAM.md, docs/OPERATIONS.md; app/services/handoff_service.py, ticket_service.py, sla_service.py; app/api/inbox.py và các kiểm thử tương ứng. Đối chiếu ngày 15/10/2026.

[S6] Bằng chứng đo kỹ thuật: evals/load/README.md và các raw results; evals/bt20, evals/rag-context, evals/rag-policy. Lượt đo tải ngày 21/09/2026 và regression RAG tháng 10 có workload/phạm vi riêng; không lấy throughput cũ làm kết quả đo của phiên bản hiện tại.

## Chương 4 Thiết kế hệ thống

### 4.1 BFD tổng quan và trách nhiệm

BFD được dùng theo nghĩa sơ đồ phân rã chức năng trong yêu cầu học phần: chức năng gốc chia thành sáu nhóm và các chức năng con. BFD thể hiện phạm vi chức năng; trình tự và ngoại lệ được mô hình hóa bằng BPMN ở mục 4.3. Nhãn vai trò trên chức năng con giúp nhận biết trách nhiệm mà không biến cây phân rã thành luồng thời gian.

| Nhóm BFD | Chức năng con | Vai trò chịu trách nhiệm |
|---|---|---|
| BFD01 Truy cập và danh tính | Tài khoản/phiên staff và khách; xác minh email; cấp quyền từng đơn | Khách, admin; FastAPI kiểm tra quyền; SMTP truyền thư |
| BFD02 Kho tri thức | Upload, lập chỉ mục, xem nguồn, lập chỉ mục lại và xóa | Admin quản lý; staff xem; FastAPI, Ollama/Qdrant xử lý |
| BFD03 Hội thoại đa kênh | Nhận/lưu tin, hỏi đáp có nguồn, tra đơn, lịch sử và giao tin | Khách, staff; FastAPI điều phối; Telegram Bot API truyền tin |
| BFD04 Ticket và chuyển giao | Handoff, nhận việc độc quyền, trả lời, giải quyết/đóng, mở lượt mới | Khách yêu cầu; staff phụ trách; FastAPI quản lý trạng thái |
| BFD05 Quản lý và báo cáo | Hồ sơ/đơn giả lập, tìm kiếm, phân trang, SLA và thống kê | Admin sửa; staff xem; FastAPI tổng hợp |
| BFD06 Đánh giá và vận hành | Phiếu người duyệt, đo tải, probe, backup/restore | Người duyệt và người vận hành máy chủ |

### 4.2 Quy ước BFD và BPMN 2.0

Bốn sơ đồ dùng BPMN 2.0 với file XML có BPMN Diagram Interchange để chỉnh sửa trong công cụ mô hình hóa, cùng ảnh SVG/PNG để đọc trong báo cáo. Process đặt isExecutable=false: mô hình phục vụ phân tích nghiệp vụ, chưa phải quy trình được engine BPMN thực thi. XML hợp lệ theo schema không thay nghiệm thu nghiệp vụ hoặc bảo đảm runtime hoạt động đúng.

Pool phân biệt bên tham gia độc lập; lane phân trách nhiệm trong cùng tổ chức. Khách hàng và Telegram Bot API là pool bên ngoài khi tham gia luồng trao đổi. Lane FastAPI, nhân viên/admin và dịch vụ RAG local thuộc tổ chức cửa hàng; Ollama/Qdrant là dịch vụ nội bộ, không trình bày thành nhà cung cấp bên ngoài. Message flow dùng nét đứt giữa pool; sequence flow dùng nét liền trong cùng process và được phép đi qua lane.

Sự kiện đầu/cuối thể hiện điểm bắt đầu/kết thúc một lượt xử lý. User task là việc con người thực hiện; service task là xử lý tự động. Exclusive gateway chọn một nhánh theo điều kiện; nhánh mặc định được đánh dấu. Boundary error event gắn với tác vụ dịch vụ để chuyển lỗi sang xử lý ngoại lệ. Các nhánh kết thúc một lượt không đồng nghĩa hội thoại bị đóng; đặc biệt AI bị bỏ hoặc từ chối không tự kết thúc phiên khách.

Hình 4.1 tổng hợp BFD ở mục 4.1. Bộ hình BFD và BPMN được đặt cùng nhau sau mục 4.5 để thuận tiện đối chiếu.

### 4.3 Bộ quy trình BPMN

#### 4.3.1 BPMN01 Tiếp nhận hỏi chính sách và chuyển giao

Phạm vi FR03, FR04, FR06, FR07, BR03, BR04 và BR11. Pool khách gửi yêu cầu; FastAPI kiểm tra phiên/dữ liệu, chống trùng và lưu tin. Hội thoại open hỏi chính sách đi dịch vụ RAG, còn tra đơn được điều phối theo BPMN02; yêu cầu người thật đi hàng chờ; đang chờ/assigned chỉ lưu tin; closed bị từ chối gửi trong phiên cũ. RAG có boundary error dẫn tới báo lỗi giữ tin. Sau RAG, gateway kiểm tra trạng thái, tin cuối và nguồn: kết quả cũ bị bỏ, kết quả hợp lệ trả bằng chứng hoặc thông báo thiếu căn cứ. Hàng chờ được nhân viên xử lý trong BPMN03.

#### 4.3.2 BPMN02 Xác minh và tra cứu đơn hàng

Phạm vi FR06, BR01, BR02 và BR09. Một lượt bắt đầu từ yêu cầu tra đơn widget. Admin kiểm tra người yêu cầu qua kênh tin cậy; thất bại chuyển nhân viên, không tiết lộ dữ liệu đơn. Xác minh đạt thì cấp mã, khách nhận qua kênh tin cậy và nhập ở biểu mẫu riêng. FastAPI kiểm tra mã/phạm vi/phiên/hạn rồi tra cứu; kiểm tra quyền lại trước trả kết quả để chặn thu hồi/hết hạn xảy ra đồng thời. Hủy/đổi trả và Telegram đi handoff ngay. Mô hình mô tả cả bước ngoài ứng dụng; hệ thống không tự làm thao tác xác minh thủ công hoặc giao mã.

#### 4.3.3 BPMN03 Nhân viên xử lý ticket và giao phản hồi

Phạm vi FR08–FR11, BR05–BR08 và BR10. Nhân viên đọc hàng chờ và gửi yêu cầu nhận; ứng dụng gán có điều kiện, nhánh tranh chấp báo tải lại. Người phụ trách soạn trả lời; Website lưu và cho khách đọc, Telegram lưu hàng gửi rồi gọi Bot API. Boundary error tạo nhánh failed/uncertain, giữ lịch sử và chặn tin sau cùng người nhận. Nhân viên quyết định bỏ qua hoặc gửi lại; uncertain yêu cầu xác nhận nguy cơ trùng. Sau phản hồi, nhân viên có thể tiếp tục hỗ trợ hoặc hoàn tất. Khi kết thúc ticket, backend kiểm tra ghi chú, người phụ trách, ticket và tin cuối; xung đột trở về đọc lại. Việc nhắn tiếp sau resolved/closed tuân BR07 ở lượt nhận tiếp theo, không nằm trong token kết thúc của lượt hiện tại.

#### 4.3.4 BPMN04 Quản lý và lập chỉ mục tri thức

Phạm vi FR05 và BR11. Admin tải tài liệu; ứng dụng kiểm tra loại, kích thước và hash, lưu nguồn rồi đọc/chia đoạn. File không hợp lệ bị từ chối; nội dung scan chưa OCR không được báo là đã có tri thức đọc được. Dịch vụ local tạo embedding và ghi vector; boundary error đánh dấu tài liệu lỗi để lập chỉ mục lại. Thành công mới chuyển trạng thái sẵn sàng. Chọn lập chỉ mục lại tạo phiên bản chỉ mục mới; chọn xóa ngừng truy hồi trước khi dọn file/vector. RAG còn phải kiểm tra phiên bản trước khi lưu đáp án như BPMN01.

### 4.4 Kiến trúc và dữ liệu

Backend FastAPI dùng SQLAlchemy/SQLite; frontend React/Vite chạy cùng origin qua proxy hoặc bản build do backend phục vụ. Qdrant embedded lưu vector, Ollama local chạy qwen3:4b và embeddinggemma:300m. Một API worker điều phối polling Telegram; cấu hình mặc định tắt. SMTP dùng TLS cho thư xác minh/khôi phục. Không tích hợp thanh toán, vận chuyển hoặc hệ thống đơn hàng sản xuất; Order là dữ liệu nội bộ giả lập.

Nhóm thực thể truy cập gồm User, AuthSession, WidgetSession, CustomerAccount, CustomerSession và CustomerEmailToken. Nhóm nghiệp vụ gồm Customer, Conversation, Message, Ticket, Order và OrderAccess. Nhóm tích hợp gồm TelegramCursor, TelegramPeer, TelegramUpdate, TelegramDelivery; nhóm tri thức gồm KnowledgeDocument và DocumentChunk. Conversation lưu người phụ trách và tin khách cuối; Message giữ citation và tool_trace nội bộ; Ticket lưu kết quả, ghi chú và snapshot SLA. Schema đã có migration v1–v10; phần v10 lưu trạng thái đọc Inbox riêng nhân viên.

Token phiên và mã quyền lưu hash, cookie tách khách/nhân viên, thao tác ghi kiểm tra CSRF. Transaction lưu tin kết thúc trước lời gọi model/Telegram; sau model phải khóa và kiểm tra lại điều kiện. SQLite hiện chưa bật cưỡng chế khóa ngoại; tính toàn vẹn còn phụ thuộc kiểm tra của ứng dụng và kiểm thử. Mở rộng nhiều worker cần kiểm chứng lại khóa, giới hạn tốc độ, Qdrant và quyền sở hữu worker Telegram. ERD và Sequence chi tiết giữ tại docs/DESIGN.md, hợp đồng endpoint tại docs/API.md.

### 4.5 Kiểm tra mô hình và giới hạn

Các file BPMN có ID duy nhất, tham chiếu hợp lệ, lane gán đúng node, gateway có nhánh điều kiện/mặc định, sự kiện lỗi gắn đúng service task và DI đủ hình/cạnh. Chạy kiểm tra XML theo schema OMG cùng kiểm tra đồ thị và bố cục; sau đó xem ảnh từng sơ đồ và bản Word. Cây BFD đối chiếu sáu nhóm ở mục 4.1 và ma trận truy vết ở mục 3.8.

Bộ sơ đồ phân biệt thành công, thiếu dữ liệu, thiếu quyền, thiếu bằng chứng, nguồn thay đổi, tranh chấp và lỗi dịch vụ. Những nhánh dựa trên xác minh thủ công vẫn cần con người thực hiện; mô hình không biến checkbox thành bằng chứng danh tính. Kiểm chứng mô hình không gọi Ollama, Telegram hoặc SMTP thật và không thay nghiệm thu tải/độ đúng của câu trả lời.

Các hình sau lần lượt minh họa BFD và BPMN01–BPMN04. Bản Word dùng trang A4 ngang để giữ rõ phân làn và nhánh xử lý; file SVG có thể phóng to, file BPMN có thể chỉnh sửa.

![BFD tổng quan của nền tảng hỗ trợ khách hàng](diagrams/BFD.png)

![BPMN01 Tiếp nhận hỏi chính sách và chuyển giao](diagrams/BPMN01.png)

![BPMN02 Xác minh và tra cứu đơn hàng](diagrams/BPMN02.png)

![BPMN03 Nhân viên xử lý ticket và giao phản hồi](diagrams/BPMN03.png)

![BPMN04 Quản lý và lập chỉ mục tri thức](diagrams/BPMN04.png)

## Sử dụng bộ hồ sơ

- Báo cáo tích hợp: [bản Markdown](../report/BaoCao.md) và [bản Word](../report/BaoCao.docx).
- [BFD dạng SVG](diagrams/BFD.svg).
- [BPMN01](diagrams/BPMN01.bpmn), [BPMN02](diagrams/BPMN02.bpmn), [BPMN03](diagrams/BPMN03.bpmn), [BPMN04](diagrams/BPMN04.bpmn). Mỗi mô hình có SVG/PNG cùng tên.
- Nạp file `.bpmn` vào công cụ hỗ trợ BPMN 2.0 có DI để chỉnh sửa. Giữ nguyên pool/lane và dùng message flow khi trao đổi giữa các pool.
- Chạy `python docs/week04/build.py --check` để kiểm tra cấu trúc và ảnh đã tạo. Chạy không tham số để tái tạo sơ đồ và đồng bộ Chương 3–4 sang Markdown/Word; cần python-docx và Pillow trong runtime tài liệu. Schema XSD chỉ dùng cho kiểm chứng thêm nếu có thư mục cache được chỉ định bằng `--schema-dir`.

Ngày 15/10/2026, nội dung tuần 04 được bổ sung vào [đề cương](../decuong/262701-DACN-07-Nhom2B_DeCuong_ChinhSua.docx), Chương 3 tại mục 3.1–3.5. BFD và bốn BPMN nằm ở mục 3.3; nguồn tham khảo bổ sung tại mục 10. Trong đề cương, NFR10 giữ ngưỡng đáp án đúng tối thiểu 80% để thống nhất với mục 6.4; ngưỡng 85% trong hồ sơ này vẫn là đề xuất cần GVHD thống nhất. Use Case và Sequence chi tiết thuộc nội dung tuần 05.
