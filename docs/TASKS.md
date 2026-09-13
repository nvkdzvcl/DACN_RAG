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
- [ ] Xây order tool và handoff.
- [ ] Xây widget và inbox.

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
