# Lộ trình đồ án CSKH đa kênh với Agentic RAG

Ngày lập: 11/09/2026. Cập nhật: 13/09/2026. Đã kiểm chứng mốc con xác thực và handoff trong MVP local; các mốc M0-M8 chưa nghiệm thu toàn bộ.

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

M2 mới hoàn thành phần nền tảng auth và migration cộng thêm cột; thiết kế đầy đủ, PostgreSQL và thử kênh thứ hai còn thiếu. M3 vẫn là prototype hash embedding/in-memory/extractive answer. M4 thiếu widget/realtime/SLA; M5 thiếu tool calling bằng LLM và đánh giá sentiment/tóm tắt. Không dùng mốc con này để tuyên bố hoàn thành M2-M5.

Stack đang chạy: FastAPI + SQLAlchemy/SQLite + React/Vite; Next.js/PostgreSQL/Qdrant trong bảng là phương án ban đầu, chưa phải cấu hình đã triển khai.
