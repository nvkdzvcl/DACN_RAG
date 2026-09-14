# Lộ trình đồ án CSKH đa kênh với Agentic RAG

Ngày lập: 11/09/2026. Cập nhật: 14/09/2026. Đã kiểm chứng mốc con xác thực, handoff, RAG local, widget có phiên khách, Inbox polling và vòng đời ticket/SLA phản hồi; các mốc M0-M8 chưa nghiệm thu toàn bộ.

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
| M6 - Đa kênh và MVP | 23-29/10 | Kênh thứ hai thật về inbox; chống xử lý webhook trùng; phân biệt danh tính theo kênh; demo toàn bộ luồng; đóng băng tính năng | Chương 5; Chương 6 sơ bộ; kịch bản demo và danh sách giới hạn |
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
- Hai kênh thật: nhận/gửi, giữ đúng hội thoại, tránh trùng tin khi webhook retry; không tự gộp khách hàng hai kênh chỉ vì cùng tên.

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
