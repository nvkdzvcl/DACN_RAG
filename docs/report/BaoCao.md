# Nền tảng trợ lý AI hỗ trợ khách hàng đa kênh dựa trên kiến trúc RAG

Báo cáo tiến độ ngày 13 tháng 9 năm 2026

Nhóm 5B phát triển hệ thống CSKH cho cửa hàng bán lẻ trực tuyến giả lập, dưới sự hướng dẫn của giảng viên Trần Đình Nghĩa. Phần xác thực nhân viên, tiếp nhận và trả lời trong Unified Inbox đã được kiểm chứng trên Windows với SQLite. RAG đã chạy mô hình Ollama local và Qdrant lưu bền, có giao diện quản lý tài liệu và câu trả lời kèm nguồn. Hệ thống chưa hoàn thành MVP đa kênh hoặc đánh giá chất lượng RAG toàn diện.

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

Backend là ứng dụng FastAPI chia module, dùng SQLAlchemy và SQLite; frontend là React/Vite. Các thực thể chính gồm User, AuthSession, Customer, Conversation, Message, Ticket, Order, KnowledgeDocument và DocumentChunk. Conversation lưu assigned_agent_id; Message lưu agent_id và citations. Các bảng hội thoại và tài liệu tách khỏi Qdrant embedded trên đĩa. Tài liệu có hash chống trùng, phiên bản chỉ mục và model embedding; đoạn nguồn có trang hoặc vị trí dòng/đoạn/bảng.

Mật khẩu được băm PBKDF2-HMAC-SHA256 với salt ngẫu nhiên và 600.000 vòng. Token phiên ngẫu nhiên có thời hạn 8 giờ; DB lưu giá trị SHA-256 của token. Trình duyệt giữ cookie HttpOnly, SameSite=Strict; thao tác ghi yêu cầu header chống CSRF. Cookie Secure bật khi APP_ENV khác development. Admin có quyền cấp tài khoản và tải tài liệu; quyền trả lời vẫn yêu cầu đúng người phụ trách, kể cả với admin.

Tiếp nhận dùng câu lệnh cập nhật có điều kiện theo trạng thái và người phụ trách chưa được gán. Luồng tin nhắn lưu tin khách và kết thúc transaction trước khi gọi Ollama. Sau khi model trả lời, backend kiểm tra lại trạng thái, ID tin khách mới nhất và phiên bản nguồn trước khi lưu/gửi AI. Lỗi model giữ nguyên tin khách; phản hồi cũ bị bỏ nếu đã handoff hoặc có tin khách mới.

Migration phiên bản 1 và 2 bổ sung bảng/cột, metadata nguồn và ID tin khách mới nhất, giữ nội dung cũ và có thể chạy lại. Các hội thoại đã được gán bằng bản demo nhưng chưa có nhân viên xác thực được đưa về hàng chờ. Chỉ SQLite đã được kiểm chứng; PostgreSQL và migration thay đổi cấu trúc phức tạp chưa nằm trong kết quả của mốc này.

## Chương 5 Triển khai và thực hiện

Đã triển khai API đăng nhập, xem phiên, đăng xuất và cấp tài khoản; bổ sung CLI nhập mật khẩu ẩn để tạo nhân viên/admin. Không có mật khẩu mặc định. Giới hạn thử đăng nhập hiện chạy trong bộ nhớ một API worker, 10 lần mỗi phút theo địa chỉ kết nối. Triển khai nhiều worker hoặc reverse proxy cần cơ chế giới hạn dùng chung.

Hai endpoint nhận tin messages và process dùng chung dịch vụ. Khi hội thoại mở, hệ thống phân loại bằng từ khóa, tra cứu đơn hoặc trả lời từ tài liệu, đồng thời lưu phản hồi AI và citation. Khi cần chuyển giao, hệ thống tạo ticket với trích đoạn tối đa tám tin gần nhất. Khi chờ hoặc đã được tiếp nhận, tin khách tiếp tục được lưu nhưng không gọi RAG/order tool, không hạ trạng thái assigned và không tạo ticket mới cho mỗi lần khiếu nại.

Frontend có màn hình đăng nhập, khôi phục phiên sau tải lại, đăng xuất, thông báo AI đã dừng và quyền phụ trách. Bản nháp được giữ riêng theo ID hội thoại trong bộ nhớ trang. Sau tiếp nhận hoặc gửi, Inbox tải lại dữ liệu; cập nhật từ các phiên khác vẫn cần nút Làm mới do chưa có realtime.

Ollama portable Windows hiện chạy qwen3:4b và embeddinggemma:300m, tạo vector 768 chiều; model qwen3:1.7b cũ được giữ để đối chiếu. Qdrant embedded dùng một API worker. Ingestion PDF/DOCX/TXT/Markdown có giới hạn 10 MB; PDF scan chưa có OCR. Tài liệu lỗi hoặc bị gián đoạn có thể lập chỉ mục lại; xóa ngừng truy xuất trước khi dọn file/vector. Giao diện Kho tri thức cho admin tải, xem, xóa, lập chỉ mục lại; nhân viên xem nguồn và hỏi thử.

LLM nhận tối đa bốn tin lịch sử ngắn để hiểu câu nối tiếp; tài liệu là bằng chứng cho nội dung chính sách. Model chọn tối đa ba cặp ID nguồn và ID câu. Backend xác thực ID, loại trùng rồi ghép nguyên văn các câu, chỉ chuẩn hóa khoảng trắng; model không viết lại số hoặc điều kiện trong câu đã chọn. Giữ ngưỡng retrieval 0,35, tối đa năm nguồn và 1.200 ký tự mỗi nguồn. Tách câu theo dấu chấm, chấm hỏi hoặc chấm than theo sau bởi khoảng trắng, giữ chấm phẩy cùng câu. Chưa xử lý đầy đủ chữ viết tắt, phần nguồn bị cắt hoặc điều kiện nằm ở câu khác. Đáp án giữ ngôn ngữ nguồn, chưa dịch hoặc tổng hợp tự do; chọn đúng ID chưa bảo đảm trả lời đúng câu hỏi.

Sau trích xuất, hệ thống gọi cùng qwen3:4b một lần nữa để kiểm định đáp án với giải thích ngắn. Ba điều kiện phải cùng đúng: câu hỏi đủ ngữ cảnh, các nguồn liên quan nhất quán và mọi dữ kiện được quote hỗ trợ. Kiểm định nhận cả nguồn không được đáp án trích dẫn trong tập nguồn đã cấp. Chính sách hợp lệ nằm cạnh chỉ dẫn độc hại vẫn có thể dùng nếu đáp án bỏ qua chỉ dẫn đó. JSON kiểm định sai dẫn đến từ chối; provider chưa hoàn tất, hết giới hạn sinh hoặc không có nội dung cuối được báo lỗi riêng và giữ tin khách. Không đưa trường thinking vào đáp án hoặc lịch sử. Cấu hình chat tắt suy luận, context 8192, tối đa 700 token. Cả hai lần gọi model nằm ngoài SQL transaction; phiên bản mọi nguồn được kiểm tra lại trước khi lưu AI, cùng guard handoff và tin khách mới.

## Chương 6 Kết quả thực hiện

Lệnh python -m unittest discover -s app/tests -v chạy đạt 33 kiểm thử trên DB thử tách biệt. Các nhóm kiểm tra bao gồm mật khẩu/cookie, phiên hết hạn và tài khoản vô hiệu, quyền admin/agent và CSRF, giới hạn đăng nhập, dữ liệu gửi giả mạo, luồng tin nhắn/handoff, nhận tranh chấp bằng hai luồng, migration giữ dữ liệu, Inbox, nhận diện mã đơn, vector lưu bền, metadata, chống trùng, retry/xóa tài liệu, citation sai, lỗi provider, AI muộn sau tin khách mới và công thức chấm benchmark. Bổ sung kiểm tra citation đúng không vượt được kết quả kiểm định từ chối, schema kiểm định sai, đáp án phủ định có nguồn, lỗi model trong bước kiểm định giữ tin khách và nguồn không được trích dẫn bị đổi trước khi lưu AI. Đợt trích xuất bổ sung kiểm tra giữ nguyên số/chấm phẩy, từ chối ID sai hoặc trùng và phản hồi Ollama bị cắt/rỗng.

Kiểm tra trình duyệt trên dữ liệu tạm đã xác nhận đăng nhập, tiếp nhận, gửi trả lời, giữ bản nháp theo hội thoại, giữ phiên sau tải lại và đăng xuất. Bố cục desktop và mobile rộng 390 pixel được kiểm tra trực quan. Frontend build bằng Vite thành công. Kho tri thức cũng đã được kiểm tra tải và lập chỉ mục thật, xem nội dung, hỏi Ollama và mở đoạn nguồn trên desktop/mobile. Các kết quả này chứng minh chức năng local, chưa phải nghiệm thu trọn M2, M3, M4 hay M5.

Bộ benchmark RAG gồm 72 câu tiếng Việt trên chính sách cửa hàng giả lập: 24 dev và 48 test, với sáu nhóm có đáp án, hỏi nối tiếp, ngoài tài liệu, mơ hồ, nguồn mâu thuẫn và prompt injection. Nhóm chính sách có đáp án cùng corpus tách theo tập; một số mẫu ý định vẫn giống nhau. Nhãn và đáp án tham chiếu hiện chưa được người dùng duyệt. Trình chạy dùng SQL/vector tạm, lưu hash dữ liệu/mã, digest model, kết quả truy xuất và completion thô. Đã thực hiện 96 lượt gồm dev gốc, dev thử prompt và test gốc; không có lỗi vận hành.

Trên 48 câu test cấu hình gốc, Recall@5 đạt 100% ở 36 câu có gold. Quyết định trả lời/từ chối khớp nhãn ở 34/48 câu (70,83%); từ chối đúng 7/16 câu phải từ chối (43,75%), từ chối sai 5/32 câu phải trả lời. Citation khớp nguồn gold đạt 83,33%; proxy dữ kiện đạt 31/48 (64,58%), chưa phải tỷ lệ đúng do người chấm. Độ trễ p50/p95 là 7,669/8,292 giây, đo tuần tự trên 48 câu thành công, gồm tải/gỡ model và embedding truy vấn, không gồm ingestion. Máy đo có 16 GB RAM và RTX 3060 Laptop GPU 6 GB VRAM; chưa đánh giá tải đồng thời hoặc khoảng tin cậy.

Lỗi baseline gồm quote đổi dấu câu gây từ chối, hiểu câu trả lời phủ định thành thiếu bằng chứng, tự chọn sản phẩm khi câu hỏi mơ hồ và chọn một nguồn mâu thuẫn. Test gốc còn lấy tỷ lệ cộng điểm làm tỷ lệ đổi tiền mặt và chấp nhận hai yêu cầu phải từ chối do injection. Một thử nghiệm chỉ sửa prompt sinh trên dev không tăng decision accuracy và gây thêm đáp án bịa nên đã bị loại trước khi chạy test gốc. Công thức, kết quả và danh sách ca cần duyệt nằm trong docs/RAG_EVALUATION.md và evals/rag/.

Đợt tiếp theo thử ba cách biểu diễn kết quả kiểm định trên cùng 24 câu dev. Bản bốn cờ bị hiểu nhầm chỉ dẫn độc hại nên từ chối sai 8/15; bản một nhãn chung bỏ sót cả hai câu mâu thuẫn. Bản ba điều kiện đạt 20/24 quyết định đúng (83,33%), tăng từ baseline 17/24; từ chối đúng 9/9 và từ chối sai giữ 4/15. Độ trễ p50/p95 tăng từ 8,341/9,135 lên 11,735/13,145 giây. Chọn bản ba điều kiện theo dev, giữ nguyên trước lượt regression test. Không sửa model, retrieval, dữ liệu, nhãn hoặc kết quả cũ để tăng điểm.

Trên 48 câu regression, quyết định đúng tăng từ 34/48 lên 35/48 (72,92%); từ chối đúng tăng 7/16 lên 10/16 (62,50%), nhưng từ chối sai tăng 5/32 lên 7/32 (21,88%). Hai yêu cầu bịa mã giảm giá và số điện thoại bị chặn, cùng một ca chọn nguồn mâu thuẫn. Model kiểm định từ chối sai đáp án bảo hành đúng ở test-013; test-029 bị chặn vì đáp án sinh thiếu chính xác nhưng nguồn vẫn đủ để trả lời, nên cũng tính từ chối sai. Proxy dữ kiện tăng từ 31/48 lên 33/48 (68,75%). p50/p95 tăng từ 7,669/8,292 lên 12,695/13,220 giây. Đợt này chạy thêm 120 lượt hỏi, gồm ba tập dev và một tập regression; không lỗi vận hành.

Ở đợt trước, nhóm giữ bước kiểm định cho MVP local vì đã chặn hai yêu cầu bịa trực tiếp và một ca mâu thuẫn trong regression, với chi phí từ chối sai và độ trễ nêu trên. Cải thiện còn nhỏ: ba ca mơ hồ, một ca đảo tỷ lệ cộng điểm thành đổi tiền và hai ca mâu thuẫn vẫn lọt; test-021 còn thiếu ý chính. Kết quả kiểm định bằng cùng model có thể trái với chính lời giải thích của nó. Chưa thể nghiệm thu chất lượng M3, công bố tỷ lệ đúng do người chấm hoặc suy rộng sang tập chưa xem. Snapshot, completion, kết quả và phiếu người duyệt được giữ trong evals/rag/runs/.

Đợt cải tiến tiếp theo so sáu cấu hình dev, mỗi cấu hình 24 câu. Bật suy luận trên model 1,7B phát sinh lỗi hết token và vẫn có đáp án đảo điều kiện; hai bản trích xuất 1,7B chưa tăng proxy. Chỉ đổi sang 4B với luồng sinh tự do cũng giảm chất lượng do chép sai số và kiểm định sai. Bản 4B chọn câu nguyên văn đạt 21/24 nhưng giải thích kiểm định dài chạm giới hạn schema. Bản yêu cầu giải thích ngắn đạt 22/24 quyết định đúng và proxy, từ chối đúng 9/9, từ chối sai 2/15, không lỗi provider. So bản kiểm định trước, từ chối sai giảm từ 4/15; p50/p95 tăng từ 11,735/13,145 lên 14,627/15,597 giây. Chọn bản này theo dev rồi giữ nguyên trước regression. Model 4B Q4_K_M tải khoảng 2,5 GB; một lần quan sát Ollama ghi khoảng 3,87 GB VRAM với context 8192, chưa phải bộ nhớ đỉnh.

Trên 48 câu regression của bản trích xuất 4B, quyết định đúng đạt 40/48 so 35/48 bản kiểm định trước; từ chối đúng 14/16 so 10/16, từ chối sai 6/32 so 7/32. Proxy dữ kiện đạt 40/48 so 33/48; citation khớp nguồn gold 87.10%, Recall@5 100.00% trên 36 câu có gold. p50/p95 là 14.096/14.739 giây so 12,695/13,220 giây; 0 lỗi vận hành. Đợt này có 192 lượt đánh giá đầy đủ, gồm 144 dev và 48 regression; hai lỗi hết token thuộc các cấu hình 1,7B bị loại. Pilot chỉ phục vụ chẩn đoán, không đưa vào các tỷ lệ này. Corpus, nhãn, retrieval và kết quả cũ được giữ, kèm hash mã thực chạy và digest model.

Bản trích xuất từ chối đúng cả bốn ca mâu thuẫn và hai yêu cầu bịa trực tiếp, nhưng còn test-036 lấy chính sách cộng điểm để trả lời đổi tiền mặt và test-038 tự chọn dịch vụ giao hàng. Sáu ca từ chối sai là test-021, 025, 026, 029, 045 và 046. Hai ca cuối hồi quy so bản trước: đáp án trích chính sách hợp lệ nhưng bị kiểm định loại vì nguồn chứa chỉ dẫn độc hại ở phần khác. Trích nguyên văn giảm lỗi viết lại số và điều kiện, chưa giải quyết sai đối tượng hoặc đủ ngữ cảnh; kết quả ba cờ kiểm định vẫn có thể trái với giải thích. Không sửa tiếp theo lượt test này. Tập test là regression đã xem lỗi; chưa có câu nào được người duyệt và không suy điểm tự động thành độ đúng ngữ nghĩa.

Bộ dữ liệu nhỏ, giả lập, dạng TXT chưa thay kiểm thử tài liệu dài/PDF/OCR hoặc dữ liệu khách thật. Chưa có factual correctness hay citation entailment được người duyệt, số liệu sentiment hoặc SLA. Tóm tắt handoff vẫn là trích đoạn, chọn order tool bằng dò mã, chưa phải LLM tool calling.

## Chương 7 Kết luận và đề xuất

Mốc hiện tại tạo nền tảng xác thực và chuyển giao có người phụ trách, giúp giữ nhất quán quyền trả lời và trạng thái AI. RAG local đã có mô hình thật, lưu bền, bộ 72 câu, trích câu nguồn bằng ID và kiểm định đáp án. M3 chưa nghiệm thu: cần người duyệt nhãn và mức đúng/có căn cứ, bổ sung tài liệu PDF/DOCX và câu hỏi chưa xem, xử lý từ chối sai và điều kiện còn thiếu. Sau đó hoàn thiện widget/phiên khách/realtime/SLA, Agentic RAG, kênh thứ hai, đánh giá và triển khai.

Hồ sơ cần tiếp tục bổ sung thông tin thành viên, sơ đồ nghiệp vụ/ERD/sequence, nguồn tham khảo học thuật và kết quả đo thực tế. DeCuong.md giữ kế hoạch nghiên cứu; docs/TASKS.md và ROADMAP.md theo dõi phạm vi và bằng chứng hoàn thành.
