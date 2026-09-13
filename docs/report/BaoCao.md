# Nền tảng trợ lý AI hỗ trợ khách hàng đa kênh dựa trên kiến trúc RAG

Báo cáo tiến độ ngày 13 tháng 9 năm 2026

Nhóm 5B phát triển hệ thống CSKH cho cửa hàng bán lẻ trực tuyến giả lập, dưới sự hướng dẫn của giảng viên Trần Đình Nghĩa. Phần xác thực nhân viên, tiếp nhận và trả lời trong Unified Inbox đã được kiểm chứng trên Windows với SQLite. Hệ thống chưa hoàn thành MVP đa kênh; RAG hiện vẫn dùng hash embedding và trả lời bằng trích đoạn.

## Chương 1 Mở đầu

Khách hàng cần được hỗ trợ về chính sách và trạng thái đơn hàng, trong khi nhân viên phải xử lý nhiều câu hỏi lặp lại. Hệ thống dự kiến dùng RAG để truy xuất tài liệu nội bộ, công cụ nghiệp vụ để tra cứu đơn và chuyển người thật khi phát hiện yêu cầu hỗ trợ trực tiếp.

Phạm vi gồm Website Chat Widget và một kênh xã hội thật, Knowledge Base PDF/DOCX, hội thoại và ticket/SLA, trả lời có nguồn, tra cứu đơn hàng giả lập và handoff. Telegram là kênh thứ hai được đề xuất, chưa tích hợp. Mục tiêu chất lượng là giảm trả lời thiếu căn cứ và từ chối khi thiếu bằng chứng; chưa khẳng định không có hallucination.

## Chương 2 Cơ sở lý thuyết và tổng quan

RAG kết hợp truy hồi thông tin với quá trình tạo câu trả lời. Embedding ngữ nghĩa và cơ sở dữ liệu vector cần được đánh giá bằng tập câu hỏi có nguồn. Agentic RAG bổ sung quyết định dùng công cụ hoặc chuyển nhân viên dựa trên trạng thái và yêu cầu nghiệp vụ.

Human-in-the-loop trong hệ thống này yêu cầu phân biệt AI đang xử lý, chờ nhân viên và nhân viên đã nhận. Việc chuyển giao phải đồng bộ ở backend, tránh để giao diện chỉ hiển thị AI dừng trong khi API vẫn sinh câu trả lời. Phần khảo cứu tài liệu học thuật và so sánh hệ thống liên quan cần được bổ sung ở mốc hoàn thiện cơ sở lý thuyết.

## Chương 3 Phân tích yêu cầu hệ thống

Quản trị viên cấp tài khoản nhân viên và quản lý tài liệu. Nhân viên đọc Inbox, tiếp nhận hội thoại đang chờ và chỉ trả lời khi là người phụ trách. Khách hàng gửi câu hỏi, nhận câu trả lời có nguồn hoặc được chuyển người thật. Phiên khách riêng cho widget chưa được xây; API nhận tin hiện là API nội bộ có xác thực nhân viên phục vụ phát triển và demo.

Các điều kiện kiểm chứng của mốc này gồm chặn truy cập chưa đăng nhập, chặn giả mạo người gửi, bảo đảm chỉ một nhân viên nhận thành công khi có tranh chấp, giữ lịch sử tin nhắn và ngừng RAG khi đã handoff. Giao diện phải có trạng thái tải/lỗi/rỗng, giữ đúng khách đang chọn và không đưa bản nháp sang hội thoại khác.

## Chương 4 Thiết kế hệ thống

Backend là ứng dụng FastAPI chia module, dùng SQLAlchemy và SQLite; frontend là React/Vite. Các thực thể chính gồm User, AuthSession, Customer, Conversation, Message, Ticket, Order, KnowledgeDocument và DocumentChunk. Conversation lưu assigned_agent_id; Message lưu agent_id và citations. Các bảng hội thoại và tài liệu tách khỏi chỉ mục vector trong bộ nhớ.

Mật khẩu được băm PBKDF2-HMAC-SHA256 với salt ngẫu nhiên và 600.000 vòng. Token phiên ngẫu nhiên có thời hạn 8 giờ; DB lưu giá trị SHA-256 của token. Trình duyệt giữ cookie HttpOnly, SameSite=Strict; thao tác ghi yêu cầu header chống CSRF. Cookie Secure bật khi APP_ENV khác development. Admin có quyền cấp tài khoản và tải tài liệu; quyền trả lời vẫn yêu cầu đúng người phụ trách, kể cả với admin.

Tiếp nhận dùng câu lệnh cập nhật có điều kiện theo trạng thái và người phụ trách chưa được gán. Luồng tin nhắn giữ khóa ghi trong transaction để đồng bộ với tiếp nhận và lưu phản hồi. Cách này phù hợp retrieval local hiện tại; trước khi gọi LLM chậm qua mạng cần chuyển sang xử lý nền và kiểm tra lại trạng thái trước khi lưu hoặc gửi phản hồi.

Migration phiên bản 1 bổ sung bảng và cột, giữ nội dung cũ, có thể chạy lại. Các hội thoại đã được gán bằng bản demo nhưng chưa có nhân viên xác thực được đưa về hàng chờ. Chỉ SQLite đã được kiểm chứng; PostgreSQL và migration thay đổi cấu trúc phức tạp chưa nằm trong kết quả của mốc này.

## Chương 5 Triển khai và thực hiện

Đã triển khai API đăng nhập, xem phiên, đăng xuất và cấp tài khoản; bổ sung CLI nhập mật khẩu ẩn để tạo nhân viên/admin. Không có mật khẩu mặc định. Giới hạn thử đăng nhập hiện chạy trong bộ nhớ một API worker, 10 lần mỗi phút theo địa chỉ kết nối. Triển khai nhiều worker hoặc reverse proxy cần cơ chế giới hạn dùng chung.

Hai endpoint nhận tin messages và process dùng chung dịch vụ. Khi hội thoại mở, hệ thống phân loại bằng từ khóa, tra cứu đơn hoặc trả lời từ tài liệu, đồng thời lưu phản hồi AI và citation. Khi cần chuyển giao, hệ thống tạo ticket với trích đoạn tối đa tám tin gần nhất. Khi chờ hoặc đã được tiếp nhận, tin khách tiếp tục được lưu nhưng không gọi RAG/order tool, không hạ trạng thái assigned và không tạo ticket mới cho mỗi lần khiếu nại.

Frontend có màn hình đăng nhập, khôi phục phiên sau tải lại, đăng xuất, thông báo AI đã dừng và quyền phụ trách. Bản nháp được giữ riêng theo ID hội thoại trong bộ nhớ trang. Sau tiếp nhận hoặc gửi, Inbox tải lại dữ liệu; cập nhật từ các phiên khác vẫn cần nút Làm mới do chưa có realtime.

## Chương 6 Kết quả thực hiện

Lệnh python -m unittest discover -s app/tests -v chạy đạt 15 kiểm thử trên DB thử tách biệt. Các nhóm kiểm tra bao gồm mật khẩu/cookie, phiên hết hạn và tài khoản vô hiệu, quyền admin/agent và CSRF, giới hạn đăng nhập, dữ liệu gửi giả mạo, luồng tin nhắn/handoff, nhận tranh chấp bằng hai luồng, migration giữ dữ liệu, Inbox và nhận diện mã đơn.

Kiểm tra trình duyệt trên dữ liệu tạm đã xác nhận đăng nhập, tiếp nhận, gửi trả lời, giữ bản nháp theo hội thoại, giữ phiên sau tải lại và đăng xuất. Bố cục desktop và mobile rộng 390 pixel được kiểm tra trực quan. Frontend build bằng Vite thành công. Các kết quả này chứng minh mốc con xác thực và handoff local, chưa phải nghiệm thu trọn M2, M3, M4 hay M5.

Chưa có số liệu chất lượng RAG, độ đúng sentiment, SLA hoặc độ trễ p50/p95. Hash embedding 256 chiều và chỉ mục trong RAM chưa thay thế embedding ngữ nghĩa/vector DB bền. Tóm tắt là trích đoạn, công cụ đơn hàng được chọn bằng dò mã, chưa phải LLM tool calling. Không dùng các kiểm thử nghiệp vụ để suy ra chất lượng mô hình AI.

## Chương 7 Kết luận và đề xuất

Mốc hiện tại tạo nền tảng xác thực và chuyển giao có người phụ trách, giúp giữ nhất quán quyền trả lời và trạng thái AI. Công việc tiếp theo là thay RAG local bằng embedding ngữ nghĩa, vector DB lưu bền và LLM có nguồn; sau đó hoàn thiện widget/realtime/SLA, Agentic RAG, kênh thứ hai, đánh giá và triển khai.

Hồ sơ cần tiếp tục bổ sung thông tin thành viên, sơ đồ nghiệp vụ/ERD/sequence, nguồn tham khảo học thuật và kết quả đo thực tế. DeCuong.md giữ kế hoạch nghiên cứu; docs/TASKS.md và ROADMAP.md theo dõi phạm vi và bằng chứng hoàn thành.
