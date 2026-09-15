# Công việc

## Đang làm

- [x] Mô hình dữ liệu cơ bản: User, AuthSession, Customer, Conversation, Message, Ticket, Order, KnowledgeDocument.
- [x] Khởi tạo FastAPI và cấu hình môi trường Windows.

## Tiếp theo

- [x] Migration cộng thêm cột, có phiên bản và chạy lại được trên SQLite; PostgreSQL chưa kiểm chứng.
- [x] API health và API hội thoại tối thiểu; sửa schema response tạo hội thoại.
- [x] Xây ingestion PDF/DOCX.
- [x] Xây chunking, metadata và vector search local.
- [x] Xây RAG query có citation và từ chối khi thiếu bằng chứng.
- [x] Phân tích cảm xúc tối thiểu và tự động tạo handoff ticket.
- [x] Order Tool có kiểm tra quyền truy cập theo khách hàng.
- [x] Dữ liệu demo đơn hàng và endpoint seed lặp lại an toàn; chưa có reset.
- [x] Orchestration endpoint xử lý tin nhắn: RAG, Order Tool và handoff.
- [x] API Unified Inbox: danh sách, lọc và chi tiết hội thoại/ticket.
- [ ] Hoàn thiện LLM tool calling và đánh giá handoff; đã có order lookup kiểm tra quyền và handoff theo quy tắc.
- [x] Widget cùng origin và Inbox polling, SLA phản hồi đầu, giải quyết/đóng và tiếp nhận lại; nghiệm thu toàn bộ M4 còn riêng.

## Unified Inbox - 12/09/2026

- [x] Nối danh sách và chi tiết hội thoại với API thật; chọn đúng conversation ID.
- [x] Hiển thị tên/email khách hàng, tin nhắn theo thời gian, người gửi, trạng thái và ticket.
- [x] Lọc trạng thái/ưu tiên, tìm khách hàng/kênh và làm mới danh sách.
- [x] Trạng thái tải/lỗi/rỗng và thử lại; hủy request cũ khi chuyển hội thoại; bỏ dữ liệu mẫu tự động.
- [x] Proxy Vite cho backend local; sửa HTTP 404; kiểm tra backend và giao diện desktop/mobile.
- [x] API tiếp nhận conversation: đổi trạng thái handoff sang `assigned`, cập nhật ticket mở sang `assigned`.
- [x] API trả lời nhân viên: chỉ cho gửi khi conversation đã `assigned`; lưu `sender_type=agent`.
- [x] Test luồng tiếp nhận, trả lời và chặn trả lời trước khi tiếp nhận.
- [x] Nối nút `Tiếp nhận`, ô trả lời và nút `Gửi` vào API; khóa ô trả lời trước khi conversation được nhận.
- [x] Sau thao tác thành công, tải lại danh sách/chi tiết để phản ánh trạng thái và tin nhắn mới.
- [x] Hiển thị lỗi thao tác và giới hạn nội dung gửi 4.000 ký tự.
- [x] Xác thực/phân quyền nhân viên; thay `agent-demo` bằng ID từ phiên đăng nhập.
- [ ] Bổ sung realtime/widget.
- [x] Cập nhật DeCuong.md và phần báo cáo cho xác thực/tiếp nhận/trả lời; chưa nghiệm thu toàn bộ M4/M5.

## Xác thực và handoff có người phụ trách - 13/09/2026

- [x] Đăng nhập/đăng xuất, phiên 8 giờ trong DB; cookie HttpOnly/SameSite, header chống CSRF, giới hạn thử đăng nhập.
- [x] Vai trò admin/agent; CLI tạo tài khoản và API tạo nhân viên dành cho admin; bảo vệ API nội bộ.
- [x] Ghi người phụ trách và tác giả tin nhân viên; cập nhật có điều kiện để chỉ một nhân viên nhận được hội thoại.
- [x] Chỉ người phụ trách được trả lời; chặn nội dung trắng và giả mạo agent_id trong body.
- [x] Luồng /messages và /process dùng chung; lưu phản hồi AI/citation, dừng RAG/order tool khi chờ hoặc đã nhận handoff.
- [x] Giữ trạng thái assigned khi khách khiếu nại tiếp; không tạo ticket trùng; trích các tin gần nhất làm ngữ cảnh chuyển giao.
- [x] Bản nháp riêng từng hội thoại; đăng nhập lại khi phiên hết hạn; thông báo AI dừng và quyền phụ trách.
- [x] Kiểm tra trình duyệt: đăng nhập, tiếp nhận/gửi, giữ bản nháp, tải lại phiên, đăng xuất; desktop và mobile 390px.
- [x] 15 kiểm thử unittest đạt; frontend build đạt. Báo cáo Word ba trang đã xuất PDF bằng Word và kiểm tra ảnh bằng Poppler (renderer đóng gói thiếu LibreOffice trên Windows).

## RAG Ollama và quản lý tri thức - 13/09/2026

- [x] Ollama portable Windows, qwen3:1.7b và embeddinggemma:300m; kết nối local, timeout, lỗi rõ ràng, không fallback sang hash/stub.
- [x] Qdrant embedded lưu bền; lọc đúng tài liệu indexed/model/phiên bản; kiểm tra đóng/mở lại vector store.
- [x] Migration v2 cộng metadata/hash/phiên bản nguồn và last_customer_message_id, không mất dữ liệu cũ.
- [x] Ingestion giới hạn file/ký tự/số đoạn; PDF giữ trang, DOCX giữ đoạn và bảng, TXT/Markdown giữ dòng; chống trùng nội dung.
- [x] API danh sách, trạng thái, đọc đoạn nguồn, lập chỉ mục lại và xóa; phân quyền admin/agent; retry sau lỗi và xử lý bị gián đoạn.
- [x] LLM có lịch sử ngắn cho câu nối tiếp; JSON schema, source ID/quote nguyên văn, kiểm tra nguồn còn hiệu lực; từ chối khi thiếu bằng chứng.
- [x] Lưu tin khách trước LLM; không giữ SQL transaction trong lời gọi model; bỏ AI muộn khi handoff, tin mới hoặc nguồn thay đổi; lỗi model không làm mất tin khách.
- [x] Kho tri thức desktop/mobile: tải/xem/lập chỉ mục lại/xóa có xác nhận/hỏi thử/citation xem nguồn; điều hướng mobile.
- [x] 22 unittest đạt; Vite build đạt. Kiểm tra trình duyệt DB tạm: đăng nhập, tải/lập chỉ mục, nội dung, hỏi thật, mở nguồn, lập chỉ mục lại và hủy xác nhận xóa; bố cục mobile 390px. Báo cáo Word ba trang đã xuất PDF bằng Word và kiểm tra đủ ba ảnh trang bằng Poppler (renderer đóng gói thiếu LibreOffice).
- [x] Smoke test Ollama thật đạt 4 ca: câu có nguồn, hỏi nối tiếp, không có dữ kiện, yêu cầu bịa; vector được đóng/mở trước khi hỏi. Lần chạy cuối: 9,64 / 9,69 / 4,67 / 8,77 giây; đây là số đo từng ca, không phải p50/p95 hay đánh giá tổng thể.

Phạm vi hiện tại: một API worker, SQLite + Qdrant embedded; ingestion đồng bộ trong threadpool, chưa có job queue/OCR. M3 đã có chức năng RAG thật và baseline 72 câu, nhưng chưa nghiệm thu chất lượng: nhãn chưa được người dùng duyệt, còn lỗi thiếu bằng chứng/mâu thuẫn/injection. Citation hợp lệ không chứng minh entailment của toàn bộ câu trả lời. Chưa có widget/phiên khách, realtime, SLA hoặc kênh xã hội thật. Tóm tắt handoff vẫn trích đoạn, chưa dùng LLM tool calling.

## Bộ đánh giá và baseline M3 - 13/09/2026

- [x] Bộ 72 câu tiếng Việt trên corpus giả lập, 24 dev + 48 test; câu có đáp án, nối tiếp, thiếu dữ kiện, mơ hồ, mâu thuẫn, injection. Nguồn/vị trí/quote và đáp án tham chiếu được lưu; mọi nhãn pending_human_review.
- [x] CLI python -m app.evaluate_rag: DB/vector tạm, hash dữ liệu/mã, digest model, raw completion, lỗi và thời gian từng câu; không ghi đè baseline cũ, không tính lỗi provider là từ chối đúng.
- [x] Đo Recall@1/3/5, source citation precision/coverage, quyết định trả lời/từ chối, proxy dữ kiện và p50/p95; có mẫu số/công thức và phiếu người duyệt.
- [x] Chạy 24 dev gốc + 24 dev thử prompt + 48 test gốc trên Ollama thật; 96 lượt, 0 lỗi vận hành. Bản prompt thử bị loại trước test vì không tăng quyết định đúng và hồi quy injection; giữ model/ngưỡng/prompt ứng dụng.
- [x] Test gốc: Recall@5 100% trên 36 câu có gold; quyết định đúng 34/48 (70,83%); từ chối đúng 7/16 (43,75%); từ chối sai 5/32; proxy dữ kiện 31/48 (64,58%); p50 7,669s, p95 8,292s. Không gọi proxy là độ đúng do người xác nhận.
- [x] 27 unittest đạt; Vite build đạt. Báo cáo chi tiết tại docs/RAG_EVALUATION.md, dữ liệu từng lượt trong evals/rag/runs/. Báo cáo Word bốn trang đã xuất PDF bằng Word và kiểm tra đủ bốn ảnh trang (renderer đóng gói thiếu LibreOffice).
- [ ] Người dùng duyệt nhãn và chấm mức đúng/có căn cứ; hiện 0 câu được người duyệt.
- [x] Bổ sung bước kiểm định đáp án với nguồn và ngữ cảnh sau sinh; số liệu từng phiên bản ở mục tiếp theo. Đây là cải tiến bộ lọc, chưa nghiệm thu chất lượng M3.

## Kiểm định đáp án và regression M3 - 13/09/2026

- [x] Một lần gọi Ollama kiểm định sau kiểm tra quote; đủ ngữ cảnh, nguồn nhất quán, dữ kiện có căn cứ phải cùng đúng. Từ chối khi JSON kiểm định sai; provider lỗi giữ tin khách và không phát đáp án chưa kiểm định.
- [x] Kiểm định thấy cả nguồn không được trích dẫn trong tập nguồn đã cấp cho LLM. Kiểm tra lại phiên bản mọi nguồn đã xét; giữ guard handoff/tin khách mới và không giữ SQL transaction khi gọi model.
- [x] 31 unittest và Vite build đạt; thêm kiểm tra đáp án sai có quote đúng, JSON kiểm định sai, câu phủ định có nguồn, nguồn bị đổi trong/sau kiểm định và lỗi provider giữ tin khách.
- [x] Ba lượt dev mới, mỗi lượt 24 câu, không lỗi vận hành. Loại bản bốn cờ (16/24 quyết định đúng, từ chối sai 8/15) và một nhãn (18/24, bỏ sót hai ca mâu thuẫn).
- [x] Chọn bản ba điều kiện theo dev: 20/24 quyết định đúng, từ chối đúng 9/9, từ chối sai 4/15 không tăng so baseline; p50/p95 11,735/13,145 giây. Giữ model/ngưỡng/prompt sinh và dữ liệu cũ.
- [x] Regression 48 câu: quyết định đúng 35/48 (gốc 34/48), từ chối đúng 10/16 (gốc 7/16), từ chối sai 7/32 (gốc 5/32); proxy dữ kiện 33/48, p50/p95 12,695/13,220 giây. 120 lượt hỏi mới, 0 lỗi vận hành.
- [x] Chặn test-044, test-047 và test-048; thêm từ chối sai ở test-013 và test-029. Hai yêu cầu bịa trực tiếp bị chặn, nhưng ba ca mơ hồ, một ca đảo nghĩa chính sách và hai ca mâu thuẫn vẫn lọt. Giữ bước kiểm định trong local MVP; không coi là giải quyết hết grounding/injection.
- [x] Cập nhật đề cương, roadmap, quyết định, báo cáo Markdown/Word và bảng so sánh mọi lượt thử. Báo cáo Word bốn trang đã xuất PDF bằng Word và kiểm tra đủ bốn ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows.

Task tiếp theo: xử lý câu mơ hồ, suy diễn hoặc mâu thuẫn còn lọt và giảm từ chối sai ở câu phủ định/hỏi nối tiếp/quote đổi dấu. Cần người duyệt nhãn/đáp án, thêm bộ câu chưa xem và tài liệu PDF/DOCX trước nghiệm thu M3. Sau đó widget có phiên khách riêng và Inbox realtime.

## Trích câu nguồn và so model local M3 - 13/09/2026

- [x] So qwen3:1.7b bật suy luận, chọn câu nguyên văn và qwen3:4b; giữ các lượt thử bị loại, không ghi đè corpus/nhãn/kết quả cũ.
- [x] Model chỉ chọn source_id/sentence_id; backend xác thực ID, loại trùng và ghép tối đa ba câu nguyên văn. Giữ chấm phẩy, số và vị trí nguồn; tiếp tục kiểm định toàn bộ nguồn đã cấp.
- [x] Transport phân biệt hết giới hạn sinh, chưa hoàn tất và nội dung rỗng; không đưa trường thinking vào câu trả lời hoặc lịch sử. Lỗi provider giữ tin khách.
- [x] Chọn bản 4B không suy luận, kiểm định giải thích ngắn theo dev: 22/24 quyết định đúng và proxy, từ chối đúng 9/9, từ chối sai 2/15; p50/p95 14,627/15,597 giây. Giữ nguyên cấu hình trước regression.
- [x] 33 unittest và Vite build đạt. Kiểm tra giữ số/điều kiện/citation, từ chối ID không hợp lệ, nguồn đổi sau kiểm định và AI muộn sau handoff/tin mới.
- [x] Regression 48 ca: quyết định đúng 40/48 (trước 35/48), từ chối đúng 14/16 (trước 10/16), từ chối sai 6/32 (trước 7/32); proxy 40/48, p50/p95 14,096/14,739 giây, không lỗi provider. Cả bốn ca mâu thuẫn và hai yêu cầu bịa trực tiếp bị chặn.
- [x] Lưu sáu lượt dev và một lượt regression mới: 192 lượt đầy đủ, hai lỗi hết token ở cấu hình 1,7B bị loại. Hai ca policy hợp lệ cạnh injection test-045/046 hồi quy; test-036/038 còn trả lời sai yêu cầu.
- [x] Smoke Ollama thật 4/4 ca đạt trên DB/vector tạm (13,61 / 13,58 / 3,74 / 14,66 giây). Cập nhật model mặc định và `.env` sang qwen3:4b; backend đang chạy cần khởi động lại để nạp biến môi trường mới.
- [x] Đề cương giữ 10 mục; báo cáo Markdown/Word giữ bảy chương, cập nhật kết quả và giới hạn. Word năm trang đã xuất PDF bằng Word và kiểm tra đủ năm ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows. Hash snapshot/corpus/retrieval đã kiểm chứng, mã dev/test cuối khớp nhau.

Giới hạn: đáp án trích nguyên văn theo ngôn ngữ nguồn, tối đa ba câu từ năm nguồn bị giới hạn độ dài; chưa xử lý đầy đủ viết tắt/điều kiện ngoài đoạn hoặc tổng hợp tự do. Kiểm định cùng model vẫn có thể từ chối nhầm hoặc chấp nhận sai. Cần duyệt nhãn/đáp án và thêm tài liệu PDF/DOCX, câu hỏi chưa xem trước nghiệm thu M3.

## Đánh giá PDF và DOCX M3 - 13/09/2026

- [x] CLI nhận `--dataset` trong repo; nạp định dạng ingestion hiện có, kiểm tra gold bằng parser/chunker theo trang/đoạn/hàng bảng và chặn nguồn vượt thư mục. Ghi hash nhị phân, phiên bản parser, log trạng thái/thời gian/số chunk từng file.
- [x] Bộ 24 câu mới, 14 có đáp án/10 cần từ chối, trên PDF ba trang và DOCX một trang có bảng; kiểm tra trực quan đủ bốn trang. PDF lập 6 chunk, DOCX 10 chunk. Giữ nhãn pending_human_review và cấu hình RAG commit 78e50f9 trước lượt đo.
- [x] Lượt `frozen4b-test` dừng trước câu hỏi do serialize datetime trong log; sửa và thêm test, giữ manifest incomplete với 0 ca. Lượt `frozen4b-v2-test` hoàn tất 24 ca, không lỗi provider.
- [x] Quyết định khớp nhãn/proxy 21/24; từ chối đúng 9/10, từ chối sai 2/14; Recall@5 100% trên 16 câu có gold, citation khớp gold 63,16%; p50/p95 14,031/15,727 giây. Citation ngoài gold không tự đồng nghĩa bịa dữ kiện.
- [x] 37 unittest đạt; phát lại chấm 408 ca TXT đã lưu cho điểm từng ca và tổng hợp không đổi. Hash xác nhận model/prompt/retrieval không đổi, corpus và nhãn mới giữ nguyên giữa đầu/cuối lượt đo.
- [x] Vite build đạt. Báo cáo Word năm trang khớp Markdown, giữ bảy chương; đã xuất bằng Word và kiểm tra đủ năm ảnh trang. Corpus PDF/DOCX cũng được render và kiểm tra đủ trang; renderer đóng gói thiếu LibreOffice nên dùng Word/Poppler trên Windows.
- [ ] Người duyệt chấm cả tập; ưu tiên doc-005 chọn ID sai, doc-013 phủ định nối tiếp, doc-019 nêu phạm vi dịch vụ khi thiếu địa chỉ. Không tự sửa nhãn doc-019 để tăng điểm.

Task tiếp theo: xác nhận quy tắc trả lời nêu điều kiện so với hỏi làm rõ, có người duyệt nhãn/đáp án; sau đó xử lý ID câu không hợp lệ và kiểm định phủ định bằng dev riêng. PDF/DOCX mới vẫn giả lập, chưa gồm OCR/bảng PDF/nhiều cột/ô gộp; cần nguồn và câu hỏi do người khác cung cấp trước nghiệm thu M3. Widget/phiên khách và realtime vẫn là mốc sau.

## Ràng buộc ID câu theo nguồn M3 - 13/09/2026

- [x] Schema oneOf gắn từng nguồn với các ID câu thực có; giữ xác thực kiểu, phạm vi và trùng ở backend khi provider bỏ qua grammar. Không thêm dependency, retry hoặc lượt model.
- [x] 38 unittest và Vite build đạt; kiểm thử hai nguồn có số câu khác nhau, lựa chọn hợp lệ và cặp ID chéo nguồn không hợp lệ.
- [x] Chọn bản schema theo dev: giữ 22/24 quyết định khớp nhãn/proxy, từ chối đúng 9/9, từ chối sai 2/15; không lỗi provider. Đóng băng bản này trước hồi quy, giữ model, prompt, retrieval và nhãn.
- [x] PDF/DOCX regression giữ 21/24 quyết định khớp nhãn/proxy, từ chối đúng 9/10, từ chối sai 2/14; p50/p95 14,154/14,939 giây, không lỗi provider. doc-005 hết ID sai nhưng vẫn bị kiểm định từ chối; doc-013 và doc-019 chưa được giải quyết.
- [x] TXT regression giữ 40/48 quyết định khớp nhãn/proxy, từ chối đúng 14/16, từ chối sai 6/32; p50/p95 13,484/15,081 giây. Điểm từng ca của cả ba lượt giữ nguyên so baseline tương ứng; 96 lượt mới không lỗi provider và không cặp ID vượt phạm vi. Hash xác nhận mã/corpus thực chạy, cấu hình model/retrieval không đổi.
- [x] Cập nhật đề cương 10 mục, roadmap, quyết định và báo cáo Markdown/Word bảy chương. Word sáu trang khớp Markdown, đã xuất bằng Word và kiểm tra đủ sáu ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows.

Task tiếp theo: người duyệt xác nhận nhãn và cách trả lời nêu điều kiện ở doc-019; giảm chọn câu thừa/thiếu ngữ cảnh và kiểm định sai phủ định qua dev riêng. Không coi sửa ID là cải thiện điểm ngữ nghĩa hay hoàn thành M3. Widget/phiên khách và realtime vẫn chưa triển khai.

## Thử giảm từ chối sai và chấm bằng người M3 - 14/09/2026

- [x] Ba thử nghiệm dev, tổng 72 ca không lỗi provider: thêm hướng dẫn ngữ nghĩa đạt 23/24 nhưng giảm từ chối đúng 9/9 xuống 8/9; bổ sung phân biệt ngoài nguồn đạt 22/24, vẫn chỉ 8/9; sinh cờ trước reason đạt 14/24, từ chối sai 10/15. Loại cả ba, giữ snapshot và kết quả.
- [x] RAG ứng dụng giữ nguyên bản 0180479. Không hiệu chỉnh theo test hoặc đo lại hồi quy khi luồng ứng dụng không đổi. Lần khởi động lỗi Ollama trước câu hỏi được lưu riêng, không tính là ca từ chối.
- [x] CLI app.review_rag tổng hợp bản sao phiếu người duyệt: xác thực ID/kiểu/tên người chấm/trường áp dụng, chỉ tính nhãn được duyệt, mẫu số riêng cho từng chỉ số; giữ null khi chưa chấm và tách nhãn bị bác bỏ/lỗi provider.
- [x] Đầu ra mới có hash đầu vào/mã, không gọi model hoặc ghi đè kết quả. 40 unittest đạt, Vite build đạt; CLI trên 48 phiếu trống trả 0 câu chấm và tỷ lệ null. Chưa có người chấm thực tế.
- [x] Cập nhật đề cương 10 mục, roadmap, quyết định và hướng dẫn chấm. Báo cáo Word sáu trang khớp Markdown, giữ bảy chương; xuất bằng Word và kiểm tra đủ sáu ảnh trang bằng Poppler vì renderer đóng gói thiếu LibreOffice trên Windows.

Task tiếp theo: người duyệt chấm bản sao phiếu trên lượt bounded-ids-test, đối chiếu nguồn và thống nhất câu nêu điều kiện; tổng hợp bằng CLI mới. M3 chưa nghiệm thu, lỗi phủ định/nối tiếp chưa được giải quyết; cần dữ liệu độc lập trước đợt cải thiện tiếp. Widget/phiên khách/realtime vẫn là phần chức năng kế tiếp.

## Widget và phiên khách M4 - 14/09/2026

- [x] Migration v3 tạo phiên khách gắn một hội thoại; cookie HttpOnly/SameSite Strict, hạn 24 giờ, DB chỉ lưu hash và tự cấp Customer ID. Không nhận ID khách/hội thoại/người gửi từ payload.
- [x] API công khai tạo/khôi phục/gửi/handoff/kết thúc; chỉ trả lịch sử phiên và trích dẫn đã lưu. Tên trùng không cấp quyền đơn hàng; API nhân viên vẫn được bảo vệ.
- [x] UUID chống gửi trùng và chặn cùng ID khác nội dung; giữ tin khi provider lỗi; kiểm tra lại phiên sau model, chặn AI muộn khi handoff/kết thúc. Giới hạn IP và một lượt AI widget, handoff không chờ model.
- [x] Trang /chat, script /widget.js và demo nhúng cùng origin; giữ bản nháp/ID khi thử lại, polling 3 giây, thông báo trạng thái, nguồn và kết thúc có xác nhận. Viewport mobile, nhãn nhập liệu, Escape trả focus và chống phản hồi cũ ghi đè phiên.
- [x] 46 unittest và Vite build đạt. QA Edge trên DB/vector riêng: một câu qua Ollama thật có quote, tải lại giữ phiên, handoff, staff reply qua API và polling, mất mạng giữ draft/UUID, phục hồi polling, kết thúc thu hồi phiên; desktop/mobile 390px không tràn ngang.
- [x] Cập nhật README, demo, quyết định, roadmap, đề cương 10 mục và báo cáo Markdown/Word bảy chương. Word bảy trang khớp Markdown, đã xuất bằng Word và kiểm tra đủ bảy ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows.

Giới hạn: cùng origin, một API worker, bộ đếm IP trong bộ nhớ, 200 tin gần nhất, UUID retry giữ trong trang hiện tại; chưa xác minh chủ đơn và chưa điều phối chung AI với API nhân viên. Đóng khung giữ phiên; Kết thúc đóng hội thoại/ticket nhưng không xóa lịch sử DB. Polling widget không phải realtime Inbox hay SLA. M3 vẫn chờ người duyệt, không chạy lại benchmark vì không đổi RAG.

Task tiếp theo: tự cập nhật Inbox và trạng thái hội thoại, sau đó SLA cơ bản với hạn phản hồi và quá hạn. Song song cần người duyệt chấm phiếu M3 và cung cấp tài liệu/câu hỏi độc lập; các kết quả widget không thay nghiệm thu chất lượng.

## Inbox tự cập nhật và SLA M4 - 14/09/2026

- [x] Polling danh sách/chi tiết mỗi 3 giây khi đang xem Inbox; tạm dừng lúc tab ẩn, vào Kho tri thức hoặc thao tác ghi. Giữ lựa chọn, bản nháp và nội dung cũ, báo lỗi mạng và tự phục hồi; hủy phản hồi cũ khi đổi hội thoại/bộ lọc.
- [x] SLA phản hồi đầu tiên từ tạo ticket, ưu tiên 5/15/60/240 phút, 24/7. Chỉ tin nhân viên có agent_id tính phản hồi; tiếp nhận/AI/khách không đặt lại hạn. Đúng ranh giới đạt, trả lời sau hạn trễ, đóng trước trả lời tách riêng.
- [x] API danh sách/chi tiết trả SLA, lọc trạng thái hợp lệ; tóm tắt chọn ticket đang chờ có hạn sớm nhất hoặc ticket mới nhất. Inbox hiển thị hạn, thời điểm phản hồi đầu, trạng thái từng ticket và đếm quá hạn trong bộ lọc hiện tại.
- [x] 49 unittest và Vite build đạt. QA Edge trên bản build, DB/vector riêng, hai phiên nhân viên + phiên khách: cập nhật trạng thái/tin mới, giữ draft/lựa chọn, mất mạng/phục hồi, lọc SLA, phản hồi cũ, tab ẩn mô phỏng, đóng hội thoại và đăng xuất; desktop/mobile 390px không tràn ngang.
- [x] Cập nhật README, demo, quyết định, roadmap, đề cương 10 mục và báo cáo Markdown/Word bảy chương. Word tám trang khớp Markdown, đã xuất bằng Word và kiểm tra đủ tám ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows.

Giới hạn: polling chưa phải SSE/WebSocket; chính sách SLA demo cố định và tính lại từ timestamp, chưa có lịch làm việc, hạn giải quyết, escalation hoặc thống kê kiểm toán. Phải lưu deadline/phiên bản trước khi cho chỉnh chính sách/ưu tiên. Các API list chưa phân trang, chưa đo tải lớn. M3 giữ nguyên cấu hình, vẫn cần người chấm và dữ liệu độc lập.

Task tiếp theo của đợt Inbox/SLA: hoàn thiện giải quyết/đóng ticket từ Inbox và quy tắc tiếp tục hỗ trợ; kết quả ghi ở đợt tiếp theo.

## Vòng đời ticket M4 - 14/09/2026

- [x] Người phụ trách giải quyết/đóng hội thoại và các ticket hoạt động, ghi chú nội bộ bắt buộc, lưu người/thời điểm hoàn tất; admin không bỏ qua quyền phụ trách.
- [x] Khách nhắn sau giải quyết tạo ticket mới, về hàng chờ và bỏ phân công cũ; giữ lịch sử, AI dừng. Đóng chặn tin mới, cho kết thúc phiên rồi bắt đầu phiên khác.
- [x] Khóa ghi dùng chung với inbound; đối chiếu tin khách cuối, trả 409 khi nội dung đã đổi. Retry hoàn tất ticket cũ không ảnh hưởng lượt mới; UUID tin cũ không mở lại sau giải quyết.
- [x] Migration v4 cộng bốn cột hoàn tất/SLA, chốt phản hồi từng ticket khi kết thúc; chạy lại không lấy phản hồi của lượt sau hoặc bịa người/thời điểm hoàn tất cũ.
- [x] 53 unittest và Vite build đạt. QA Edge bản build, DB/vector riêng, hai nhân viên và phiên khách: quyền, hủy xác nhận, tin mới xung đột giữ ghi chú, giải quyết/tải lại/tiếp nhận lại, riêng tư ghi chú, SLA lịch sử, retry cũ, đóng/phiên mới. Desktop/mobile 390px không tràn ngang.
- [x] Cập nhật README, demo, quyết định, roadmap, đề cương 10 mục và báo cáo Markdown/Word bảy chương. Word tám trang khớp Markdown, đã xuất bằng Word và kiểm tra đủ tám ảnh trang bằng Poppler; renderer đóng gói thiếu LibreOffice trên Windows.

Giới hạn: chưa mở lại hội thoại đã đóng bằng thao tác nhân viên, chưa SLA giải quyết/escalation hoặc kiểm thử tải. Chính sách phản hồi vẫn cố định, cần deadline/phiên bản trước khi cho sửa ưu tiên/quy tắc. Không đổi model/prompt/retrieval, không chạy lại benchmark; M3 còn chờ người duyệt và dữ liệu độc lập.

Task tiếp theo: bổ sung BFD/BPMN, Use Case, ERD, Sequence, API spec và ma trận nghiệm thu toàn luồng M4 dựa trên chức năng thực có; sau đó Agentic RAG và kênh thứ hai theo roadmap. Không coi mốc con vòng đời ticket là nghiệm thu trọn M4.

## Hồ sơ thiết kế và kiểm chứng M4 - 15/09/2026

- [x] Bổ sung BFD, luồng phân làn, Use Case/quyền, ERD, trạng thái, kiến trúc và hai Sequence tại docs/DESIGN.md, đối chiếu với mã hiện có.
- [x] docs/API.md bao phủ 31 cặp method/path, cookie/quyền/CSRF, snapshot riêng tư, payload finish, retry/SLA và lỗi runtime ngoài OpenAPI.
- [x] docs/M4_ACCEPTANCE.md nối UC với kiểm thử và giới hạn; giữ người dùng/GVHD duyệt sau, không coi quyền tiếp tục làm là nghiệm thu M3/M4.
- [x] Lệnh python -m app.tests.smoke_m4 chạy login/upload/chat/handoff/giải quyết/tiếp nhận lại/đóng qua HTTP ASGI với Ollama thật, store tạm và mật khẩu ngẫu nhiên. Đạt: câu hỏi 16,217 giây, toàn luồng 28,088 giây; không sửa .env hoặc DB người dùng.
- [x] 53 unittest đạt trong 25,597 giây; Vite build đạt, assets không đổi. Không chạy lại QA giao diện hoặc benchmark khi UI/RAG không đổi.
- [x] Cập nhật đề cương 10 mục và báo cáo Markdown/Word bảy chương cùng README, demo, roadmap và quyết định. Word chín trang khớp Markdown, đã xuất bằng Word/Poppler và kiểm tra đủ trang; chương kết luận bắt đầu trang riêng. Renderer đóng gói thiếu LibreOffice trên Windows.

Giới hạn: sơ đồ phân làn chưa phải file BPMN 2.0; mockup và hồ sơ chờ duyệt, chưa đo tải/cloud hoặc nghiệm thu đầy đủ M4. Chưa chấm chất lượng M3; phần này giữ chờ người duyệt theo yêu cầu người dùng.

Task tiếp theo: M5 tool calling với schema, danh tính/quyền do server xác định, tool tra đơn chỉ đọc và handoff vẫn chặn AI muộn; kiểm thử lỗi model/tool, giả mạo và tranh chấp trước tích hợp kênh thứ hai. Không chờ người duyệt M3 để làm phần kỹ thuật độc lập.

## Chọn công cụ đơn hàng M5 - 15/09/2026

- [x] Bộ chọn JSON Schema giới hạn tên tool/tham số cho một mã đơn trong tin hiện tại. Không có mã giữ RAG; nhiều mã hỏi làm rõ; handoff theo quy tắc vẫn ưu tiên.
- [x] Tool tra cứu chỉ đọc, server lấy customer_id và kiểm tra chủ đơn/tin khách cuối dưới khóa ghi sau model. Kết quả được ghép từ DB; hủy/sửa đơn chỉ chuyển nhân viên.
- [x] Migration v5 cộng Message.tool_trace, API staff nhận nhưng widget không nhận. Lỗi provider giữ inbound, lỗi DB trả 503/log và có thể giữ pending; UUID cũ không gọi lại model/tool.
- [x] Sáu kiểm thử mới, tổng 59 unittest đạt trong 25,225 giây; schema giả mạo, quyền, retry, lỗi và tranh chấp được kiểm chứng. Vite build đạt, assets không đổi.
- [x] Smoke Ollama thật 7/7 ca đạt, không lỗi provider trong lượt hoàn tất. Ca chính sách có mã đi RAG có nguồn, dữ liệu đơn khác không lộ. Pilot native tools có ba ca hết token đã bị loại; một lượt khi Ollama chưa chạy dừng trước câu hỏi.
- [x] Cập nhật hồ sơ thiết kế/API, README/demo/quyết định/roadmap, đề cương 10 mục và báo cáo Markdown/Word bảy chương. Word mười trang khớp Markdown, đã kiểm tra đủ ảnh trang; xuất bằng Word/Poppler vì renderer đóng gói thiếu LibreOffice trên Windows.
- [x] Hồi quy HTTP M4 với Ollama thật đạt sau migration v5: câu hỏi 15,175 giây, toàn luồng 22,249 giây trên store tạm.

Giới hạn: structured tool selection do backend điều phối, chưa native tool_calls hoặc agent nhiều bước; nhận diện/tóm tắt chưa chấm chất lượng, chưa suy đơn từ lịch sử hoặc xác minh khách widget. Pipeline RAG cũ giữ nguyên; không chạy lại benchmark M3, không dùng smoke để tự nghiệm thu.

Task tiếp theo: bổ sung đánh giá nghiệp vụ M5 độc lập và cơ chế xác minh khách trước tra đơn trên widget; chuẩn bị kênh thứ hai với danh tính theo kênh và chống tin/webhook trùng. Chỉ ghi tích hợp thật khi đã kiểm chứng gửi/nhận trên tài khoản kênh thực tế; M3 tiếp tục chờ người duyệt.
