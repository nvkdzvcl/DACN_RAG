# Lộ trình đồ án CSKH đa kênh với Agentic RAG

## 09/10/2026 - Hoàn thiện thao tác Inbox và tri thức

Inbox có hoạt động/tin cuối và trạng thái đọc theo nhân viên; mobile dành thêm chỗ cho tin nhắn, dashboard mở hàng chờ đã lọc. Kho tri thức có tab/lọc, kết quả AI phân loại rõ và đối chiếu đoạn nguồn. Schema v10 thêm cursor đọc, giữ dữ liệu cũ; backup/readiness được cập nhật. QA dùng DB tạm và model giả lập, chưa thay nghiệm thu RAG hoặc đa kênh thật. Chi tiết: `docs/UI_UPGRADE_20261009.md`.

## 09/10/2026 - Ổn định ID sửa bằng chứng RAG

Lượt `refund-schema-v1-20261009` đạt 180/180 hồi quy, 218 kiểm thử backend. Kiểm định dùng grammar cặp ID hợp lệ của bước chọn nguồn; giữ kiểm tra backend, toàn bộ nguồn kiểm định và giới hạn ba lần chat. Chẩn đoán sáu ca xen kẽ đạt 30/30, gồm năm lần mốc hoàn tiền, nhưng không thay thế tập kín/người duyệt độc lập. Không đổi nhãn hoặc chính sách thật; chưa nghiệm thu M3/toàn bộ ưu tiên cao. Báo cáo: `evals/rag-policy/RANG_BUOC_KIEM_DINH_20261009.md`.

## 09/10/2026 - Nâng cấp diễn đạt và độ liên quan RAG

Kiểm tra lặp trên truy hồi lưu sẵn đạt 15/18; `bt20-032` chưa ổn định dù đạt trong lượt đầy đủ. Giữ từ chối an toàn khi kiểm định đề xuất ID ngoài tập hợp lệ; không đánh dấu ca này hoàn tất.

Lượt `precision-final-20261009` đạt 180/180 rubric hồi quy (trước 178/180), 216 kiểm thử backend đạt. Mốc hoàn tiền và loại trừ ngày ngoài lịch độc quyền được diễn đạt trước kiểm định; câu có/không bỏ nguồn dư nhưng giữ điều kiện và kiểm định lại. Không đổi corpus/nhãn, model hoặc giới hạn ba lần chat. Câu mở còn có thể dư đoạn; điểm hồi quy không thay thế người duyệt/tập kín độc lập. M3 và toàn bộ ưu tiên cao chưa nghiệm thu. Báo cáo: `evals/rag-policy/DO_CHINH_XAC_20261009.md`.

## 09/10/2026 - Đóng băng bản xử lý tồn đọng RAG

Lượt `priority-followup-verified-v2-20261009` đạt 178/180 rubric tự động, 209 kiểm thử backend; sửa 6/7 ca tồn đọng ban đầu. Giữ nhãn/corpus và chính sách thử tách khỏi dữ liệu thật. Còn ca hỏi lại dư `bt20-032`, bất đồng rubric `test-026`, đoạn dư ở `policy-013` và kiểm chứng độ ổn định. Chưa có người duyệt toàn tập hoặc tập kín do người khác soạn; không đánh dấu M3/ưu tiên cao hoàn tất. Báo cáo tại `evals/rag-policy/XU_LY_TON_DONG_20261009.md`, hướng dẫn nghiệm thu độc lập tại `evals/rag-policy/NGHIEM_THU_DOC_LAP.md`.

## 09/10/2026 - Truy hồi, ngữ cảnh và chính sách mẫu RAG

Ngày 09/10/2026 nâng cấp truy hồi và ngữ cảnh RAG: lấy tập ứng viên vector giới hạn, xếp lại bằng cụm hai từ hiếm trong tập ứng viên nhưng giữ nguyên cosine score và kiểm tra phiên bản nguồn. Lọc mẫu chỉ dẫn giả khỏi lịch sử và lựa chọn nguồn; giữ đoạn đầu an toàn nguyên văn, các câu sạch phía sau vẫn có mặt để kiểm định xung đột. Trùng ID được gộp, không bỏ kiểm định. Bổ sung hỏi lại đơn cụ thể thiếu dịch vụ giao/lý do đổi/phương thức thanh toán, giữ chủ đề câu nối tiếp và chặn trả số điện thoại khi quote không có số. Giữ model/embedding/ngưỡng 0,35 và tối đa ba lần chat. BT20 58/60 thành 58/60; TN8/LS2 22/24 thành 24/24; PDF/DOCX 20/24 thành 23/24; TXT 42/48 thành 45/48. Bộ chính sách mẫu Mộc Demo mới: 20/24 thành 23/24. 180 lượt bản được chọn không lỗi provider hoặc chuỗi cấm theo rubric; 159/159 quote khớp đoạn truy hồi. 198 kiểm thử backend đạt. Không thay nhãn/corpus cũ, không tải chính sách giả lập vào kho tri thức thật. Các tập đã xem kết quả chỉ dùng phát triển/hồi quy; người duyệt và đánh giá độc lập vẫn chưa hoàn tất. Chi tiết, ca thoái lui và bằng chứng tại evals/rag-policy/NANG_CAP_20261009.md.

## 08/10/2026 - Nâng cấp trích đoạn và đo hồi quy

Đợt trích đoạn tiếp theo ngày 08/10/2026: BT20 từ 52/60 lên 58/60; TN8/LS2 từ 19/24 lên 22/24. Hồi quy PDF/DOCX 20/24 (trước 21/24), TXT 42/48 (trước 40/48). Tổng 156 lượt Ollama thật, 0 lỗi dịch vụ; 114/114 quote khớp đoạn truy hồi. 188 kiểm thử backend đạt. ID câu 1 chọn cả đoạn giới hạn 1.200 ký tự; ID từ 2 chọn câu riêng, giữ các điều kiện phụ mà không bắt buộc đưa chỉ dẫn giả vào đáp án. Bổ sung nhận diện lý do gửi nhầm/nhận sai và chỉ hỏi lại bằng quy tắc chờ đợi khi toàn câu là mẫu mơ hồ, tránh chặn chủ đề ngoài bán hàng. Chặn quote chứa mẫu yêu cầu bỏ qua chỉ dẫn/quy tắc ở backend; không coi bộ lọc cụm từ này là chống injection toàn diện. Giữ model, embedding, ngưỡng truy hồi và tối đa ba lượt chat; sửa bằng chứng vẫn phải kiểm định lại. Không đổi nhãn/corpus, không sửa dữ liệu người dùng. Các tập đều đã dùng để phát triển/hồi quy, chưa có người duyệt độc lập; điểm này không phải độ chính xác thực tế hoặc nghiệm thu M3. Chi tiết ca sửa được, thoái lui và giới hạn tại evals/bt20/TRICH_DOAN_20261008.md.

## 08/10/2026 - Nâng cấp chọn nguồn và kiểm định RAG

Ngày 08/10/2026 nâng cấp chọn câu và kiểm định RAG: giữ điều kiện trong cùng đoạn, loại trích dẫn lặp, hỏi làm rõ hai dạng mơ hồ tiếng Việt trước khi chọn nguồn và cho phép sửa ID câu tối đa một lần nhưng phải kiểm định lại. Giữ qwen3:4b, embeddinggemma:300m, think=false và ngưỡng truy hồi 0,35; không bỏ kiểm định hoặc thay kho tri thức người dùng. Chạy lại BT20 đạt 52/60 (86.7%), so với 43/60 trước sửa; từ chối sai giảm từ 13/46 còn 4/46. Cả hai câu mơ hồ hỏi lại; 4/4 ca mâu thuẫn, 4/4 ca chỉ dẫn giả và 6/6 ca thiếu dữ kiện đạt rubric. Bộ mới TN8/LS2 gồm 24 câu soạn trước lượt chạy đầu tiên đạt 19/24; tổng 84 lượt không lỗi dịch vụ và 71/71 trích dẫn khớp văn bản corpus. 184 kiểm thử backend đạt. BT20 có p50 5.197 giây, p95 6.553 giây. BT20 đã dùng để chỉnh sửa nên chỉ là đo hồi quy; bộ mới do cùng trợ lý soạn, chưa có người duyệt độc lập. Còn lỗi thiếu điều kiện phụ, chọn câu và truy hồi; chưa nghiệm thu M3. Chi tiết và toàn bộ đáp án tại evals/bt20/NANG_CAP_20261008.md và evals/rag-context/KET_QUA.md.

08/10/2026 (M3 kiểm chứng BT20): 60 câu Ollama thật hoàn tất; 43/60 đạt rubric, 13/46 từ chối sai theo nhãn; p50/p95 4,960/7,521 giây. Trích nguồn khớp nhưng còn lỗi review/ngữ cảnh; chưa nghiệm thu chất lượng, chưa người duyệt độc lập. Bằng chứng: evals/bt20/KET_QUA.md.

08/10/2026: bổ sung giao diện sáng/tối cho toàn bộ khu vực admin/nhân viên. Nút đổi trên sidebar và mobile; lưu lựa chọn bằng localStorage, mặc định theo hệ thống khi chưa chọn. Đổi theme giữ bản nháp; khi storage bị chặn vẫn đổi được trong phiên. Build và kiểm thử trình duyệt desktop/mobile đạt; đã xem sáu trang nội bộ trên API với DB thử. Runner: frontend/tests/theme.cjs. Phạm vi chưa gồm trang đăng nhập và customer /chat.

08/10/2026 (giao diện Inbox): bố cục tham khảo Chatwoot, bộ lọc theo người phụ trách trên backend, hồ sơ/ticket thu gọn và mobile hai màn. 30 test Inbox/xác thực, build và QA trình duyệt API thật đạt; giữ quyền hiện có và chưa coi là nghiệm thu đa kênh/RAG.

08/10/2026 (ô soạn tin): khách hàng và nhân viên dùng Enter để gửi, Shift+Enter xuống dòng; tự tăng chiều cao đến 160 px rồi cuộn. Frontend build và kiểm thử trình duyệt component chung đạt; không thay API hoặc pipeline RAG.

07/10/2026 (chuẩn bị M7): thêm production.env mẫu, Caddy HTTPS, launcher Windows một worker và hướng dẫn backup/restore. Kiểm thử launcher và smoke HTTPS local đạt; chưa triển khai Internet, chưa có tên miền/máy chủ được chọn, M7 còn chờ nghiệm thu.

07/10/2026: đã triển khai xác minh email và khôi phục mật khẩu qua SMTP, schema v9; 172 kiểm thử và build đạt, UI kiểm chứng với hộp thư thử. SMTP thật chưa cấu hình, chưa nghiệm thu giao thư. Tài khoản cũ phải xác minh trước khi được khôi phục email; đơn hàng vẫn theo mã truy cập.

03/10/2026: tài khoản khách hàng email + mật khẩu và giao diện đăng nhập đã kiểm chứng; schema v8, lịch sử nhiều thiết bị, đổi mật khẩu thu hồi phiên. 165 kiểm thử backend đạt, frontend build và QA trình duyệt đạt. Email chưa xác minh/chưa khôi phục qua email; quyền đơn vẫn theo mã truy cập. Chi tiết tại docs/CUSTOMER_AUTH.md và docs/TASKS.md.

22/09/2026 (mốc con M5 nhật ký trong Inbox): nhân viên xem trace ngay dưới tin khách, gồm trạng thái/mã đơn/hành động/kết quả; pending không bị coi là đang chạy, rag không bị coi là đáp án thành công. Dùng details/summary, không thêm API, dependency hoặc quyền khách. Sáu test công cụ và Vite build đạt; QA trình duyệt desktop/390px xác nhận nhãn, bàn phím, giữ mở qua polling và không tràn ngang. Không thay model/quyền/tool execution; M3/M5/M6/M7 vẫn chờ các phần nghiệm thu riêng.

Ngày lập: 11/09/2026. Cập nhật: 07/10/2026. Đã kiểm chứng mốc con xác thực, handoff, RAG local, widget có phiên khách, Inbox polling và vòng đời ticket/SLA phản hồi; các mốc M0-M8 chưa nghiệm thu toàn bộ.

01/10/2026 (độ bền hàng chờ Telegram): lỗi nhận tin tiếp theo không còn chặn update đã commit; giữ trạng thái lỗi, con trỏ và quy tắc gửi lại. Test tái hiện trước sửa, 20 test Telegram đạt sau sửa bằng transport/model giả lập. Chưa tách worker, chưa kiểm chứng bot thật hoặc nghiệm thu M6.

26/09/2026 (gộp phiếu M5): CLI --merge ghép phần duyệt cùng lượt đo, giữ ghi chú chờ và tên người chấm; xung đột cùng ca chặn output để Khánh đối chiếu. Chín test liên quan đạt, không gọi model hoặc đổi runtime; 44 ca thật vẫn chưa duyệt. Không có biểu quyết tự động hoặc nghiệm thu độc lập từ phiếu gộp. Hướng dẫn tại evals/tools/README.md.

01/10/2026 (lỗi HTTP Telegram): response bị cắt/sai giao thức được ghi uncertain khi gửi, giữ che token và chặn gửi lại tự động; peer khác tiếp tục xử lý. 21 test Telegram đạt với transport/model giả lập, chưa kiểm chứng bot thật hoặc nghiệm thu M6.

01/10/2026 (phục hồi khởi động Telegram): probe bot/webhook tự thử lại lỗi mạng/HTTP 5xx sau 5 giây; lỗi cấu hình vẫn dừng, chưa chạm DB trước xác minh. Hai test tái hiện trước sửa, 23 test Telegram đạt sau sửa; không gọi bot thật hoặc thay quy tắc gửi lại uncertain. M6 chưa nghiệm thu.

## Mục tiêu và phạm vi

Xây dựng mới từ đầu trên Windows native. Repo RAG cũ chỉ là tài liệu tham khảo.
Mục tiêu nội bộ: sản phẩm, triển khai và hồ sơ sẵn sàng ngày 13/11/2026; hạn nộp chính thức 11:30 ngày 23/11/2026; bảo vệ ngày 27/11/2026.

Bắt buộc: Website widget và một kênh thứ hai thực tế (đề xuất Telegram, cần xác nhận phù hợp với GVHD); unified inbox, ticket/SLA; PDF/DOCX RAG có nguồn; công cụ tra cứu đơn hàng qua API giả lập; nhận diện khiếu nại, yêu cầu gặp người thật; handoff có tóm tắt; phân quyền; lưu hội thoại; triển khai và đánh giá.

Zalo, OCR nâng cao, phân tích dashboard nâng cao và các workflow Self-RAG phức tạp là mở rộng sau khi luồng bắt buộc ổn định. Không gọi việc nhận webhook giả lập là tích hợp đa kênh thực tế.

## Kiến trúc đề xuất

- Modular monolith: FastAPI cho API và nghiệp vụ, worker xử lý tài liệu, PostgreSQL cho dữ liệu giao dịch, Qdrant Cloud cho vector trong giai đoạn Windows native.
- Next.js/React cho trang quản trị và widget; kênh realtime cho tin nhắn/trạng thái; adapter chuẩn hóa tin nhắn Website và Telegram.
- LLM/embedding qua adapter; chọn provider/model còn hỗ trợ tại thời điểm thử nghiệm. Không tự chuyển sang stub trong môi trường demo.
- Luồng điều phối có trạng thái: nhận tin -> kiểm tra quyền và trạng thái handoff -> phân loại -> RAG / order tool / chuyển nhân viên -> lưu và gửi phản hồi.
- AI không trả lời tiếp khi nhân viên đã nhận hội thoại. Công cụ đơn hàng phải kiểm tra quyền truy cập; mã đơn hàng đơn lẻ không đủ để xác minh khách hàng.
- Tách ingestion khỏi request chat; tài liệu có trạng thái xử lý, phiên bản, nguồn và trang/đoạn; upload trùng, lỗi và xóa tài liệu cần được xử lý.
- Native Windows không bắt buộc Docker/WSL. Nếu muốn dùng Docker Desktop cho Linux container, phải tính riêng yêu cầu backend WSL2/Hyper-V. pgvector là phương án thay thế khi môi trường đã được kiểm chứng.

## Các mốc nội bộ

| Mốc | Thời gian | Điều kiện hoàn thành | Báo cáo cần cập nhật |
|---|---|---|---|
| M0 - Chốt bài toán | 11-17/09 | Chốt lĩnh vực CSKH mẫu, phạm vi, vai trò, tiêu chí nghiệm thu; WBS, rủi ro; thử kết nối LLM, embedding và vector DB trên Windows | Bản nháp 10 mục DeCuong.md; Chương 1 và khung báo cáo |
| M1 - Đề cương | 18-22/09 | Hoàn chỉnh 10 mục; tài liệu tham khảo có nguồn thật; lịch và phân công rõ; đủ để nộp ngày 25/09 | DeCuong.md và bản đề cương Word, ghi rõ trạng thái dự kiến |
| M2 - Thiết kế và nền tảng | 23/09-01/10 | BFD/BPMN, Use Case, Sequence, ERD, API spec và UI mockup; scaffold, migrations, auth/roles; thử quyền tích hợp kênh thứ hai | Chương 2-4 bản nháp; cập nhật theo góp ý GVHD |
| M3 - RAG xuyên suốt | 02-08/10 | Upload PDF/DOCX -> xử lý -> vector -> hỏi đáp có nguồn; từ chối thiếu bằng chứng; bộ câu hỏi đánh giá đầu tiên | Chương 4-5 phần KB/RAG; lưu kết quả thử nghiệm thật |
| M4 - Hội thoại và widget | 09-15/10 | Widget nhúng, lưu tin nhắn, unified inbox, realtime, ticket và SLA cơ bản; chốt hồ sơ thiết kế nội bộ ngày 12/10 trước mốc 16/10 | Chương 3-5 phần hội thoại; hồ sơ thiết kế mức 0 |
| M5 - Agent và handoff | 16-22/10 | Tra cứu đơn hàng có kiểm soát quyền; khiếu nại/yêu cầu gặp nhân viên -> tóm tắt -> nhận xử lý -> AI dừng; kiểm thử tranh chấp AI/nhân viên | Chương 4-5 phần tool calling và chuyển giao; test nghiệp vụ |
| M6 - Đa kênh và MVP | 23-29/10 | Kênh thứ hai thật về inbox; chống xử lý sự kiện kênh trùng; phân biệt danh tính theo kênh; demo toàn bộ luồng; đóng băng tính năng | Chương 5; Chương 6 sơ bộ; kịch bản demo và danh sách giới hạn |
| M7 - Kiểm thử và triển khai | 30/10-05/11 | Kiểm thử tích hợp, quyền truy cập, RAG, handoff; cloud chạy; đo chất lượng/độ trễ; sẵn sàng demo 06/11 | Chương 6 bằng số liệu thật; hướng dẫn cài đặt và vận hành |
| M8 - Hoàn thiện | 06-13/11 | Sửa lỗi, regression; báo cáo Word/PDF, nguồn GitHub, link cloud, đề cương đã duyệt, slide nháp; diễn tập demo | Hoàn chỉnh Chương 1-7, trích dẫn, hình/bảng; kiểm tra bố cục Word/PDF |
| Dự phòng và nộp | 14-22/11 | Sửa theo góp ý, kiểm tra in ấn và gói nộp; không mở rộng tính năng | Soát hồ sơ trước hạn 11:30 ngày 23/11 |
| Bảo vệ | 23-27/11 | Diễn tập thuyết trình, vấn đáp và phương án demo dự phòng | Slide, kịch bản và câu hỏi phản biện |

## Tiêu chí nghiệm thu

- Mỗi mốc phải có sản phẩm kiểm chứng được: file thiết kế, chức năng chạy, test, số liệu hoặc kịch bản demo. Không dùng số file hay lượng code làm bằng chứng hoàn thành.
- RAG: bộ 60-100 câu hỏi tiếng Việt có đáp án và nguồn do người kiểm tra, gồm câu có đáp án, thiếu dữ kiện, không có nguồn, tài liệu mâu thuẫn và prompt injection. Tách tập phát triển và tập đánh giá cố định.
- Đo retrieval Recall@k, tính có căn cứ và đúng trích dẫn, từ chối đúng, độ trễ p50/p95; chốt ngưỡng sau baseline đầu tiên. Không tuyên bố tuyệt đối không hallucination.
- Order tool: đúng đơn, từ chối truy cập không hợp lệ, xử lý không tìm thấy và API lỗi.
- Handoff: yêu cầu gặp nhân viên được xử lý rõ ràng; kiểm thử độ chính xác nhận diện khiếu nại, tóm tắt, phân công và AI ngừng phản hồi.
- Hai kênh thật: nhận/gửi, giữ đúng hội thoại, tránh trùng tin khi nhận lại sự kiện; không tự gộp khách hàng hai kênh chỉ vì cùng tên.

## Quy tắc đồng hành báo cáo

Sau mỗi mốc hoàn thành và được kiểm chứng:

1. Thông báo mốc vừa hoàn thành, bằng chứng, tồn đọng và mốc kế tiếp.
2. Cập nhật trạng thái/bằng chứng trong file này và nội dung tương ứng của DeCuong.md. Đề cương giữ cấu trúc 10 mục; không dùng làm nhật ký lập trình.
3. Khi đề cương được duyệt, lưu bản duyệt riêng; mọi thay đổi phạm vi sau đó ghi nhận rõ, không âm thầm thay bản đã duyệt.
4. Cập nhật báo cáo dài theo 7 chương trong docs/report/BaoCao.md và xuất docs/report/BaoCao.docx. Bản đề cương nộp riêng tại docs/report/DeCuong.docx. Áp dụng skill documents và kiểm tra bản render khi tạo/sửa Word; xuất PDF khi đóng gói nộp.
5. Chỉ viết đã thực hiện khi có bằng chứng; phần chưa làm ghi dự kiến. Không bịa kết quả đo, nguồn tham khảo, tên thành viên hay xác nhận của GVHD.
6. Khi thiếu thông tin cá nhân/biểu mẫu, ghi rõ chỗ cần bổ sung. DeCuong.md hiện còn tên đề tài, danh sách thành viên và hai ảnh liên kết chưa có file trong thư mục.

Theo dõi định kỳ chỉ cập nhật khi có mốc mới hoặc thay đổi đáng kể; nhắc mốc chưa hoàn thành trước hạn nội bộ 3 ngày, 1 ngày hoặc khi quá hạn, tránh nhắc lặp. Không suy ra hoàn thành chỉ từ ngày đến hạn. Sau bảo vệ 27/11/2026 dừng theo dõi.

## Nhật ký nghiệm thu

26/09/2026 (mốc con M5 duyệt nhãn): CLI đọc lượt đo hoàn tất, tạo phiếu gắn hash và tổng hợp chỉ nhãn được thành viên chấp thuận; lỗi xử lý vẫn ở mẫu số, ca bác/chờ tách riêng, chưa duyệt cho tỷ lệ null. Đã tạo 44 phiếu trống, năm test mới đạt trong 0,078 giây; không gọi model/sửa benchmark hoặc thay runtime. Người chấm tự khai, đây là duyệt sau xem kết quả, chưa phải đánh giá độc lập hoặc nghiệm thu M5. Phân công và hướng dẫn tại evals/tools/README.md.

26/09/2026 (giao diện duyệt M5): ba biểu mẫu HTML offline lưu nháp, kiểm tra tên/lý do bác và xuất JSON nguyên bằng chứng; hỗ trợ tiếp tục từ JSON bằng CLI. Bảy test đạt, QA desktop/mobile và JSON xuất từ giao diện được CLI chấp nhận trên ca giả lập. Có sao chép JSON dự phòng vì tải Blob trong trình duyệt tích hợp chưa xác nhận. Cả 44 ca thật còn chờ duyệt; không thay runtime/model, chưa nghiệm thu độc lập M5.

26/09/2026 (mốc con M5 ngữ cảnh handoff): bỏ qua riêng tiền tệ/phủ định rõ/câu hỏi chính sách hoàn tiền, giữ chuyển người khi còn yêu cầu khác; chuẩn hóa NFC ở đầu vào selector, giữ tin gốc. 144 unittest đạt trong 49,188 giây. Ba phép đo bản cuối bằng Ollama thật đạt 24/24 gốc, 8/8 nối tiếp, 10/12 ngữ cảnh mới, tổng 25 lời gọi selector không lỗi provider. Hai cách nói tự do vẫn nhận nhầm; RAG giả lập, nhãn chưa người duyệt, chưa nghiệm thu M5. Không đổi schema/quyền; lưu bằng chứng trước/sau tại evals/tools.

26/09/2026 (mốc con M5 hỏi nối tiếp): giải quyết tham chiếu rõ “đơn đó/này” từ mã khách gửi trong bốn tin gần nhất cùng hội thoại; nhiều mã hỏi lại, không dùng mã AI nêu hoặc thay mã mới sai bằng mã cũ. Quyền hiện tại và chặn tool muộn giữ nguyên. 141 unittest đạt trong 49,555 giây; Ollama thật đạt 21/24 so 18/24, tám ca biên mới đạt, tổng 22 lời gọi selector mới không lỗi provider. Còn ba ca nhận nhầm do từ khóa; RAG giả lập, nhãn chưa người duyệt, chưa nghiệm thu độc lập M5. Bằng chứng tại evals/tools.

26/09/2026 (mốc con M5 đánh giá điều phối): thêm 24 ca nhãn nháp, CLI đo Ollama thật và quyền trên SQLite tạm; riêng RAG giả lập. Một câu prompt ưu tiên handoff khi vừa tra cứu vừa hủy/đổi đơn nâng kết quả từ 17/24 lên 18/24; tổng 30 lời gọi selector, không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. Bộ 137 unittest đạt trước sửa prompt, 10 test liên quan chạy lại đạt trên bản cuối. Sáu ca còn lỗi phủ định/chính sách/nối tiếp; tập này đã dùng chỉnh prompt, chưa người duyệt hoặc đánh giá độc lập. Chưa nghiệm thu M5/M3; bằng chứng và phân công tại evals/tools/README.md.

26/09/2026 (mốc con M4 lịch sử widget): phân trang 50/tối đa 100 tin bằng cursor thuộc phiên khách, đọc vượt 200 tin mà vẫn lọc dữ liệu nội bộ. Giữ bản nháp, xử lý lỗi và hết phiên; bốn test mới, tổng 134 unittest đạt trong 136,589 giây. Build và QA desktop/mobile trên DB tạm đạt. Không đổi schema hoặc kiểm chứng model/kênh thật; ticket/SLA chưa phân trang, M4/M7 chưa nghiệm thu toàn bộ.

25/09/2026 (mốc con M4 lịch sử Inbox): phân trang tin bằng cursor, mặc định 50/tối đa 100; giao diện giữ bản nháp và polling trang đang đọc. Ba test mới, tổng 130 unittest đạt trong 95,222 giây; build và QA desktop/mobile trên DB tạm đạt. Mốc đúng hội thoại, thứ tự ổn định khi trùng thời gian, không thay schema; API messages chỉ còn một trang. Ticket và lịch sử widget chưa phân trang, chưa nghiệm thu tải bền hoặc toàn bộ M4/M7.

25/09/2026 (mốc con M7 khôi phục tài khoản): CLI local đặt lại mật khẩu tài khoản đã có và thu hồi mọi phiên trong cùng transaction, giữ nguyên role/active; chặn đăng nhập dùng hash cũ sau reset. Sáu test mới bằng DB tạm gồm rollback và cấu hình DB qua subprocess; tổng 127 unittest đạt trong 52,458 giây. Không thay tài khoản thật, schema hoặc API; chưa có email/OTP reset và audit quản trị. Hướng dẫn tại docs/OPERATIONS.md; chưa nghiệm thu toàn bộ M7.

25/09/2026 (mốc con M7 độ trễ Ollama): giữ hai model 5 phút thay vì dỡ sau mỗi lời gọi; Ollama đã dùng GPU trước sửa. RTX 3060 6 GiB xác nhận cả hai model 100% GPU, tổng 4,16 GiB. Ba lượt cũ 15,207-16,066 giây; lượt mới đầu 10,704 giây, hai lượt đã nạp 3,351-3,719 giây. Smoke HTTP thật đạt, câu hỏi 3,675 giây; 15 test RAG đạt. Giữ model/prompt/context/kiểm định; một câu hỏi lặp chưa chứng minh chất lượng M3 hoặc tải bền M7. Bằng chứng tại evals/ollama.

22/09/2026 (mốc con M4 phân trang Inbox): API mặc định 25/tối đa 100 hội thoại, tìm kiếm Unicode và lọc SLA trước chia trang; giao diện giữ hội thoại/bản nháp, mở đúng hội thoại ngoài trang từ hồ sơ khách. Ba test mới, tổng 120 unittest đạt trong 64,141 giây; test biên offset chạy lại đạt, Vite build và QA desktop/mobile 390px đạt. Smoke HTTP riêng với 31 hội thoại kiểm chứng hợp đồng phân trang, không dùng so throughput với baseline trả toàn danh sách. Tìm kiếm/SLA còn quét theo lô, offset không phải snapshot; chưa nghiệm thu tải bền/cloud hoặc M4/M7.

22/09/2026 (mốc con M6 phục hồi handoff): sửa mất thông báo chuyển nhân viên khi worker dừng sau commit nghiệp vụ. Thông báo Telegram được lưu cùng trạng thái/ticket, rollback đồng thời; nhận lại update hoặc nhắn thêm khi đang chờ không tạo thông báo trùng, yêu cầu sau giải quyết tạo thông báo lượt mới. Hai test mới tái hiện lỗi trước sửa; tổng 117 unittest đạt trong 91,870 giây. Transport/model Telegram được mock; lỗi gửi vẫn chặn hàng chờ, không tự bù thông báo thiếu cũ. Schema v7 giữ nguyên; chưa nghiệm thu bot thật hoặc M6.

22/09/2026 (mốc con M7 toàn vẹn sao lưu): sửa ngoại lệ .lock quá rộng gây bỏ file trong tài liệu/thư mục con mà vẫn báo thành công. Chỉ bỏ file khóa ở gốc Qdrant; các file khác được hash, sao chép và kiểm tra khi restore. Hai test tái hiện trước/sau và tổng chín test backup đạt, có Qdrant embedded thật. Giữ format 1/schema v7; bản cũ thiếu file cần tạo lại từ nguồn đầy đủ. Không sửa dữ liệu người dùng, chưa nghiệm thu vận hành cloud hoặc M7.

22/09/2026 (mốc con M5 handoff văn bản): sửa nhận nhầm tệ trong tệp và bỏ sót yêu cầu gặp nhân viên do xuống dòng/dấu Unicode tách rời. So khớp NFC, gộp khoảng trắng và ranh giới từ; tin lưu/trích đoạn ticket giữ nguyên. Widget vẫn chuyển giao khi AI bận, Telegram dùng chung và chống update trùng. Năm test mới, tổng 113 unittest đạt trong 78,586 giây; model/transport được mock trong kiểm thử tích hợp. Chưa đánh giá ngữ nghĩa độc lập, phủ định/ngữ cảnh hay bot thật; M3/M5/M6 chưa nghiệm thu.

22/09/2026 (mốc con M5 nhận diện mã đơn): sửa lỗi cắt mã trong chuỗi có dấu gạch nối và nhận chữ Unicode ngoài ASCII qua IGNORECASE; giới hạn tổng 64 ký tự như API tạo đơn. Ba test mới có bằng chứng thất bại trước sửa/đạt sau sửa; tổng 108 unittest đạt trong 83,904 giây. Quyền tra đơn, schema, UI và model giữ nguyên; không có mã hợp lệ vẫn đi nhánh RAG. Chưa nghiệm thu chất lượng chọn tool hoặc M3; hướng dẫn tại docs/M5_TOOLS.md.

13/09/2026: kiểm chứng mốc con xác thực nhân viên, tiếp nhận và trả lời trong Inbox; bảo vệ API, lưu người phụ trách, chặn nhận tranh chấp, dừng AI khi handoff, lưu lịch sử và citation. Có kiểm thử tự động trong app/tests và kiểm tra trình duyệt desktop/mobile trên DB thử riêng.

M2 mới hoàn thành phần nền tảng auth và migration cộng thêm cột; thiết kế đầy đủ, PostgreSQL và thử kênh thứ hai còn thiếu. M3 đã có Ollama thật và Qdrant embedded lưu bền, quản lý tài liệu/citation; đã có baseline 72 câu, chưa nghiệm thu chất lượng vì nhãn chờ người duyệt và còn lỗi mơ hồ/mâu thuẫn/injection. M4 thiếu widget/realtime/SLA; M5 thiếu tool calling bằng LLM và đánh giá sentiment/tóm tắt. Không dùng mốc con này để tuyên bố hoàn thành M2-M5.

Stack đang chạy: FastAPI + SQLAlchemy/SQLite + React/Vite; Qdrant embedded đã triển khai; Next.js/PostgreSQL trong bảng vẫn là phương án ban đầu.

13/09/2026 (mốc con M3): Ollama local theo lựa chọn người dùng, embeddinggemma:300m + qwen3:1.7b, Qdrant lưu đĩa, metadata trang/đoạn, CRUD tri thức và câu trả lời có quote kiểm tra được. 22 unittest, build frontend và QA desktop/mobile đạt; 4 ca smoke với model thật đạt. LLM chạy ngoài SQL transaction; kiểm thử handoff/tiếp nhận hoàn tất khi LLM đang chờ và chặn AI muộn. M3 tiếp theo cần bộ 60-100 câu tiếng Việt và baseline; chưa có Recall@k, p50/p95 hay tỷ lệ hallucination được đo trên tập cố định.

13/09/2026 (baseline M3): hoàn thành bộ 72 câu giả lập (24 dev/48 test) và CLI đánh giá lưu raw output/hash/model digest. Đã chạy 96 lượt gồm một thử nghiệm prompt bị loại; không lỗi provider. Test cấu hình gốc có Recall@5 100% trên 36 câu có gold, decision accuracy 70,83%, từ chối đúng 43,75%, p50/p95 7,669/8,292 giây. 27 unittest và Vite build đạt. Nhãn chưa được người duyệt; điểm trên không phải factual correctness/entailment được xác nhận. M3 chưa nghiệm thu; ưu tiên chặn đáp án thiếu căn cứ, mơ hồ/mâu thuẫn/injection trước widget/realtime. Chi tiết: docs/RAG_EVALUATION.md.

13/09/2026 (kiểm định M3): thêm bước kiểm định đáp án bằng cùng Ollama sau kiểm tra quote; ba điều kiện về ngữ cảnh, tính nhất quán nguồn và căn cứ dữ kiện phải cùng đúng. Kiểm tra lại phiên bản cả nguồn không được trích dẫn; lỗi model không làm mất tin khách, giữ chặn AI muộn. 31 unittest và Vite build đạt. Ba thử nghiệm dev mới được giữ nguyên; chọn bản ba điều kiện với 20/24 quyết định đúng, từ chối đúng 9/9, từ chối sai 4/15; p50/p95 11,735/13,145 giây. M3 chưa nghiệm thu: kiểm định cùng model vẫn sai, cần giảm từ chối sai, duyệt bằng người và thử tài liệu/câu hỏi chưa xem.

Regression sau kiểm định: 35/48 quyết định đúng so 34/48 gốc; từ chối đúng tăng 7/16 lên 10/16, từ chối sai tăng 5/32 lên 7/32; p50/p95 tăng từ 7,669/8,292 lên 12,695/13,220 giây. Đã chặn hai yêu cầu bịa trực tiếp và thêm một ca mâu thuẫn; chưa giải quyết ba ca mơ hồ, một ca đảo nghĩa chính sách và hai ca mâu thuẫn còn lại. Tổng 120 lượt hỏi mới không lỗi vận hành. Tiếp tục M3 trước widget/realtime; không suy điểm dev cao thành chất lượng tổng quát.

13/09/2026 (trích câu nguồn M3): sau các thử nghiệm suy luận và model, chọn qwen3:4b không suy luận; model chọn ID câu, backend trích nguyên văn rồi kiểm định ba điều kiện với giải thích ngắn. Dev đạt 22/24 quyết định đúng so 20/24 bản trước; từ chối đúng giữ 9/9, từ chối sai giảm 4/15 xuống 2/15; p50/p95 14,627/15,597 giây. 33 unittest và Vite build đạt. Giữ embedding/ngưỡng/corpus/nhãn, lưu toàn bộ các lượt thử và snapshot, đóng băng cấu hình trước regression. M3 vẫn chờ người duyệt và đánh giá PDF/DOCX/câu chưa xem; kế tiếp mới triển khai widget/phiên khách và realtime.

Regression trích xuất 4B: 40/48 quyết định đúng, 14/16 từ chối đúng, 6/32 từ chối sai; proxy 40/48, p50/p95 14,096/14,739 giây, không lỗi provider. So bản trước tăng năm quyết định đúng, nhưng hai câu có chính sách hợp lệ cạnh injection bị từ chối nhầm. Còn hai ca trả lời sai yêu cầu (test-036/038). Đợt này lưu 192 lượt dev/regression, hai lỗi hết token thuộc cấu hình bị loại; M3 chưa nghiệm thu. Hạn chế tiếp tục chỉnh theo tập cũ; ưu tiên người duyệt và bộ PDF/DOCX/câu chưa xem.

13/09/2026 (đánh giá PDF/DOCX M3): CLI mở rộng dataset và vị trí gold, log ingestion từng file. Thêm 24 câu trên PDF ba trang/DOCX có bảng, giữ cấu hình RAG đã chốt; kết quả 21/24 khớp nhãn/proxy, từ chối đúng 9/10, từ chối sai 2/14, Recall@5 100% trên 16 câu có gold, p50/p95 14,031/15,727 giây. 37 unittest đạt, chấm lại 408 kết quả TXT không đổi. Lượt đầu lỗi log trước câu hỏi được giữ riêng; lượt hoàn tất không lỗi provider. M3 chưa nghiệm thu: bộ vẫn do trợ lý soạn, nhãn chưa người duyệt; doc-019 nêu phạm vi dịch vụ cần thống nhất có chấp nhận hay phải hỏi làm rõ. Ưu tiên duyệt người và sửa ID câu/kiểm định phủ định qua dev riêng trước widget/realtime.

13/09/2026 (ràng buộc ID câu M3): schema oneOf giới hạn ID câu theo nguồn thực có, backend vẫn chặn ID sai/trùng; 38 unittest và Vite build đạt. Chốt theo dev 22/24 rồi giữ nguyên trước hồi quy: PDF/DOCX 21/24, TXT 40/48 quyết định khớp nhãn/proxy, điểm từng ca không đổi. 96 lượt mới không lỗi provider hoặc cặp ID vượt phạm vi. doc-005 hết ID sai nhưng vẫn bị kiểm định từ chối; chưa cải thiện ngữ nghĩa. M3 còn chờ người duyệt, tiêu chí trả lời nêu điều kiện và xử lý chọn câu/kiểm định sai qua dev riêng; không chỉnh tiếp trên regression trong đợt này.

14/09/2026 (vòng người duyệt M3): loại ba thử nghiệm kiểm định sau 72 ca dev vì giảm từ chối đúng hoặc tăng từ chối sai; giữ nguyên RAG bản 0180479, không chạy test cho bản bị loại. Bổ sung CLI app.review_rag tổng hợp phiếu người duyệt với ID/kiểu hợp lệ, tên người chấm, nhãn được duyệt và mẫu số riêng; không tính null/lỗi provider thành đánh giá, không ghi đè dữ liệu. 40 unittest và Vite build đạt. 48 phiếu trống vẫn cho 0 câu chấm; M3 chờ người duyệt thực tế và dữ liệu độc lập, chưa giải quyết hết phủ định/nối tiếp.

14/09/2026 (mốc con M4): triển khai widget nhúng cùng origin, phiên khách 24 giờ, lịch sử/trích dẫn, chống gửi trùng, handoff và nhận phản hồi nhân viên bằng polling 3 giây. Migration v3 cộng bảng phiên; 46 unittest, Vite build và QA Edge desktop/mobile 390px trên DB/vector tạm đạt. Một câu hỏi qua Ollama thật có đáp án/quote, khôi phục phiên và xử lý mất mạng/kết thúc đã kiểm tra. M4 chưa nghiệm thu vì thiếu Inbox realtime và SLA; chưa có nhúng khác origin hay xác minh chủ đơn cho khách ẩn danh. M3 giữ nguyên cấu hình, tiếp tục chờ người duyệt và dữ liệu độc lập.

14/09/2026 (tự cập nhật Inbox và SLA M4): danh sách/nội dung/người phụ trách tự cập nhật mỗi 3 giây khi tab hiển thị; giữ lựa chọn và bản nháp, xử lý lỗi mạng và phản hồi cũ. SLA phản hồi đầu tiên tính từ tạo ticket theo ưu tiên 5/15/60/240 phút, tách đang chờ quá hạn, đã trả lời đúng/trễ và đóng trước phản hồi; bộ lọc cùng chỉ số trên tập đang xem. 49 unittest, Vite build và QA hai phiên Edge desktop/mobile đạt. Chưa có SSE/WebSocket, lịch làm việc, hạn giải quyết hoặc escalation; chưa nghiệm thu toàn bộ M4/hồ sơ thiết kế. Kế tiếp hoàn thiện vòng đời ticket ở Inbox; M3 vẫn chờ người duyệt và dữ liệu độc lập.

14/09/2026 (vòng đời ticket M4): Inbox cho người phụ trách giải quyết/đóng với ghi chú nội bộ, lưu thời điểm/người hoàn tất. Khách nhắn sau giải quyết tạo ticket mới và về hàng chờ, AI vẫn dừng; đóng yêu cầu kết thúc phiên rồi bắt đầu phiên mới. Kiểm tra tin khách mới nhất và retry theo ticket ngăn hoàn tất nhầm lượt; migration v4 chốt phản hồi từng ticket, giữ SLA lịch sử. 53 unittest, Vite build và QA Edge hai nhân viên/phiên khách desktop/mobile đạt. Chưa có mở lại thủ công, SLA giải quyết hoặc kiểm thử tải. Tiếp theo hồ sơ thiết kế và nghiệm thu toàn luồng M4, sau đó Agentic RAG/kênh thứ hai; M3 vẫn chờ người duyệt và dữ liệu độc lập.

15/09/2026 (hồ sơ và kiểm chứng M4): bổ sung docs/DESIGN.md với BFD, luồng phân làn, Use Case, ERD, trạng thái và Sequence; docs/API.md đối chiếu 31 endpoint; docs/M4_ACCEPTANCE.md ánh xạ UC với kiểm thử. smoke_m4 chạy login/upload/RAG/handoff/giải quyết/nhắn tiếp/đóng bằng Ollama thật trên store tạm đạt; câu hỏi 16,217 giây, toàn luồng 28,088 giây. 53 unittest và Vite build đạt. Luồng phân làn chưa phải BPMN 2.0; hồ sơ chưa người dùng/GVHD duyệt, chưa kiểm thử tải/cloud hoặc nghiệm thu trọn M4. Người dùng cho phép tiếp tục khi bận; M3 vẫn giữ pending human review. Kế tiếp M5 tool calling với quyền do server xác định, rồi kênh thứ hai.

15/09/2026 (mốc con M5 chọn tool): model chọn lookup_order/handoff/rag bằng JSON Schema cho một mã đơn rõ ràng; backend xác thực tham số, lấy danh tính từ hội thoại, khóa lại và kiểm tra tin cuối/chủ đơn trước thực thi. Tool tra DB giả lập chỉ đọc, yêu cầu hủy chuyển nhân viên, không sửa đơn. Migration v5 lưu trace nội bộ; 59 unittest và Vite build đạt, 7/7 ca smoke model thật đạt. Pilot native tools bị loại vì sinh quá giới hạn ở ba ca; không dùng điểm smoke làm nghiệm thu agent hoặc chất lượng M3. Tiếp theo kiểm chứng M5 với dữ liệu độc lập, xác minh khách và tích hợp kênh thứ hai; người dùng vẫn có thể duyệt sau.

Ngày 18/09/2026 hoàn thiện năm trang quản lý theo mockup: Tổng quan, Khách hàng, Đơn hàng, Phân tích, Cài đặt. Có API, phân quyền, phân trang, bảo vệ ghi đè và đổi mật khẩu; 66 unittest/build và QA trình duyệt desktop/mobile đạt. Chi tiết docs/WORKSPACE.md. Không thay nghiệm thu chất lượng M3/M5 hoặc xác minh khách widget; kênh thứ hai vẫn chưa kết nối.

21/09/2026 (mốc con M5 quyền tra đơn): admin cấp/thu hồi mã 256 bit, hết hạn sau 15 phút, chỉ lưu hash; khách nhập biểu mẫu riêng để ràng buộc một đơn vào một phiên widget. Không gộp danh tính hoặc gửi mã biểu mẫu tới LLM. Kiểm tra quyền sau khi model chạy, giữ handoff và chặn dùng lại ở phiên khác. Migration v6 giữ dữ liệu cũ; 73 unittest và Vite build đạt. Chi tiết docs/ORDER_ACCESS.md. Xác minh/giao mã qua kênh tin cậy vẫn thủ công, chưa có OTP tự động. M3 chờ người chấm; kênh thứ hai/cloud chưa hoàn tất. Kế tiếp tích hợp kênh thứ hai thật và kiểm chứng M5 độc lập.

21/09/2026 (mốc con M6 adapter Telegram): đã có polling chat riêng, danh tính theo bot/người dùng, lưu update/con trỏ bền và nhật ký gửi; xử lý lỗi không rõ kết quả bằng xác nhận gửi lại hoặc bỏ qua. Inbox dùng UUID cho tin nhân viên; SLA Telegram tính lúc API xác nhận gửi. Migration v7, 16 test Telegram mới và tổng 89 unittest đạt; frontend build đạt. Adapter chưa có token để kiểm chứng bot thật, mặc định tắt; không ghi M6 đã nghiệm thu. Một worker xử lý tuần tự, chưa đo tải hoặc triển khai cloud. Bước tiếp theo là smoke trên bot thử nghiệm thật theo docs/TELEGRAM.md; M3 vẫn chờ người duyệt.

21/09/2026 (mốc con M7 vận hành local): bổ sung CLI sao lưu offline SQLite/Qdrant/tài liệu, manifest SHA-256 và kiểm tra schema v7. Khôi phục chỉ vào thư mục mới, giữ nguồn và thu hồi phiên/quyền tra đơn cũ; có kiểm thử vòng khôi phục bằng Qdrant embedded thật. Hướng dẫn docs/OPERATIONS.md yêu cầu dừng API, giữ Telegram tắt khi kiểm tra bản khôi phục và đối chiếu lịch sử trước bật lại bot. Chưa sao lưu nóng, mã hóa trong CLI, lịch/retention, RPO/RTO, cloud hoặc nghiệm thu M7.

Kiểm chứng mốc sao lưu: 96 unittest đạt trong 52,638 giây; git diff --check đạt. Không build lại frontend vì không thay UI.

21/09/2026 (mốc con M7 chạy bản build): SERVE_FRONTEND cho phép FastAPI phục vụ UI và API cùng origin, không cần Vite khi demo. Thêm /api/v1/ready dành Staff kiểm tra schema v7, nguồn/vector và model Ollama; 47 cặp method/path API. Bảy test mới và smoke Uvicorn thật trên dữ liệu tạm đã kiểm tra giao diện tĩnh, auth, lỗi readiness, handoff/Inbox/logout. Chưa đo tải, HTTPS/cloud hoặc sinh đáp án từ probe; /health giữ kiểm tra nhẹ. Cách chạy tại docs/OPERATIONS.md.

Kiểm chứng mốc chạy bản build: 103 unittest đạt trong 56,660 giây; bảy test liên quan chạy lại đạt sau chỉnh trạng thái unchecked khi bận. OpenAPI có 47 method/path; git diff --check đạt.

21/09/2026 (mốc con M7 đo tải local): app.measure_load chạy Uvicorn một worker và store tạm, seed phiên riêng; đo Inbox/widget/gửi tin/retry, kiểm tra tranh chấp tiếp nhận và giới hạn handoff. Với 10 client, 500 hội thoại seed cùng một probe, 1.000 request tải chính đạt 13,755 request/giây trước index; thêm index tin nhắn/ticket đạt 37,437 và lượt lặp 38,008. p95 danh sách Inbox giảm từ 1371,878 xuống 640,324/513,581 ms; không lỗi ngoài dự kiến, UUID/ticket/người phụ trách đúng. Migration cài index idempotent trên DB v7, không đổi dữ liệu nghiệp vụ. 105 unittest đạt trong 57,055 giây. Bằng chứng và giới hạn tại evals/load/README.md; không đo LLM, Telegram thật, mạng ngoài, tải bền hoặc số người dùng tối đa. Tiếp theo kiểm chứng tải trong môi trường triển khai và bot thật; M3/M6/M7 vẫn chưa nghiệm thu.
