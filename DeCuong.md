**ỦY BAN NHÂN DÂN THÀNH PHỐ HỒ CHÍ MINH**

**TRƯỜNG ĐẠI HỌC SÀI GÒN**

**KHOA CÔNG NGHỆ THÔNG TIN**

![](Aspose.Words.1b5decef-b9ed-49de-bd23-d8f2d08ce55b.001.png)![](Aspose.Words.1b5decef-b9ed-49de-bd23-d8f2d08ce55b.002.png)








**Đề cương tiểu luận học phần Đồ án chuyên ngành**

**NỀN TẢNG TRỢ LÝ AI HỖ TRỢ KHÁCH HÀNG ĐA KÊNH DỰA TRÊN KIẾN TRÚC RAG**

`	`**NHÓM 5B**

`                                                 `**Sinh viên: 	<<Danh sách thành viên>>**

`                                                     `**GVHD:     Trần Đình Nghĩa**









` `**Thành phố Hồ Chí Minh, năm 2026**

**ĐỀ CƯƠNG TIỂU LUẬN**

**1. Lý do chọn đề tài/tính cấp thiết của vấn đề nghiên cứu.**

Nhân viên chăm sóc khách hàng phải xử lý nhiều câu hỏi lặp lại về chính sách và trạng thái đơn hàng. Đề tài xây dựng hệ thống truy xuất tài liệu nội bộ để hỗ trợ trả lời có nguồn, đồng thời chuyển hội thoại cho nhân viên khi khách hàng yêu cầu hoặc xuất hiện khiếu nại. Việc quản lý tập trung giúp giữ lịch sử trao đổi và người chịu trách nhiệm xử lý.

**2. Lịch sử nghiên cứu vấn đề/ tổng quan**

Nội dung cần bổ sung: tổng quan RAG, truy hồi ngữ nghĩa, tool calling và human-in-the-loop; so sánh với chatbot hỏi đáp tài liệu thông thường. Chưa hoàn thành khảo cứu và danh mục tài liệu học thuật, không xem phần này là tổng quan đã nghiệm thu.

**3. Mục đích nghiên cứu**

Xây dựng nền tảng CSKH cho cửa hàng bán lẻ trực tuyến giả lập, có Website Chat và một kênh xã hội thật, trả lời từ PDF/DOCX có dẫn nguồn, tra cứu đơn hàng có kiểm soát quyền và chuyển nhân viên kèm ngữ cảnh. Đánh giá mức độ có căn cứ của câu trả lời và độ đúng của luồng chuyển giao; không đặt giả định tuyệt đối không có hallucination.

**4. Nhiệm vụ nghiên cứu**

Phân tích nghiệp vụ và vai trò admin/nhân viên/khách hàng; thiết kế dữ liệu, API và giao diện; xây ingestion và RAG; tích hợp công cụ đơn hàng; xây ticket/SLA và handoff; phát triển widget và kênh thứ hai; kiểm thử, triển khai và hoàn thiện báo cáo. Nhân viên phải được xác thực, chỉ người phụ trách được trả lời, AI phải dừng khi cuộc hội thoại chuyển sang người thật.

**5. Đối tượng nghiên cứu và phạm vi nghiên cứu**

Đối tượng là hội thoại CSKH tiếng Việt, tài liệu chính sách PDF/DOCX và dữ liệu đơn hàng giả lập. Phạm vi bắt buộc gồm Website và kênh thứ hai (đề xuất Telegram, cần thống nhất với GVHD). Phát triển trực tiếp trên Windows; Zalo, OCR nâng cao và Self-RAG là hướng mở rộng. Không dùng dữ liệu giả lập để khẳng định đã tích hợp kênh thật.

Khách hàng có thể dùng phiên vãng lai hoặc tài khoản email và mật khẩu tự quản lý để giữ lịch sử trên nhiều thiết bị. Tài khoản khách tách khỏi tài khoản nhân viên; email chưa xác minh không được dùng làm căn cứ cấp quyền xem đơn. Xác minh email và khôi phục mật khẩu qua email là phần mở rộng chưa triển khai.

**6. Phương pháp nghiên cứu**

Phát triển lặp theo các mốc có kiểm chứng. Dùng kiểm thử API, kiểm thử quyền và tranh chấp tiếp nhận, kiểm tra giao diện desktop/mobile; xây bộ câu hỏi có nguồn để đo Recall@k, độ đúng trích dẫn, khả năng từ chối và độ trễ p50/p95. So sánh sinh đáp án tự do với chọn câu nguồn bằng ID và trích nguyên văn, kết hợp kiểm định bằng LLM; đo lỗi còn lọt, từ chối sai và chi phí độ trễ khi đổi model/chế độ suy luận local. Trích đúng câu nguồn chưa bảo đảm trả lời đúng câu hỏi hoặc giữ đủ điều kiện. Bổ sung PDF nhiều trang và DOCX có bảng để kiểm tra ingestion, chunking và vị trí citation ngoài corpus TXT; giữ cấu hình trước lượt đo, lưu hash đầu vào và lỗi từng file. Tách tập phát triển với tập đánh giá; tập test đã xem lỗi chỉ dùng làm regression. Bộ giả lập do cùng người phát triển soạn và kiểm định bằng cùng model không thay nhãn hoặc đánh giá độc lập của người duyệt.

Phiếu người duyệt được đối chiếu với ID của lượt đánh giá và tổng hợp riêng: chỉ tính đánh giá có người chấm, nhãn được duyệt và chỉ số áp dụng; giữ phần chưa chấm ở trạng thái null, nêu mẫu số riêng cho mỗi tỷ lệ. Lưu hash đầu vào để truy vết, không dùng điểm tự động điền thay người hoặc suy kết quả chấm một phần thành chất lượng toàn bộ tập.

**7. Giả thuyết khoa học/Những đóng góp mới của đề tài**

Giả thuyết cần kiểm chứng: kết hợp truy hồi bằng chứng, công cụ nghiệp vụ và chuyển giao có trạng thái giúp hỗ trợ CSKH đáng tin cậy hơn luồng trả lời không kiểm soát. Ràng buộc ID câu theo từng nguồn trong JSON Schema và kiểm tra lại ở backend bảo vệ miền giá trị; hiệu quả trả lời đúng vẫn phải được đánh giá riêng bằng hồi quy và người duyệt. Đóng góp dự kiến là tích hợp các thành phần vào quy trình đa kênh và xây bộ đánh giá phù hợp; chưa tuyên bố có thuật toán mới hoặc kết quả cải thiện định lượng.

**8. Dự kiến kế hoạch nghiên cứu (tuần/thực hiện công việc gì ?)**

Ưu tiên theo công việc: nền tảng dữ liệu và xác thực; RAG dùng mô hình thật; widget/realtime/SLA; Agentic RAG và handoff; kênh thứ hai; kiểm thử, triển khai và hồ sơ. Chi tiết mốc ở ROADMAP.md, trạng thái kỹ thuật ở docs/TASKS.md. Phần đã kiểm chứng của xác thực, handoff, RAG local dùng Ollama/Qdrant và baseline trên bộ câu hỏi giả lập được trình bày trong Chương 5-6 báo cáo; không coi các mục còn dự kiến là kết quả hoàn thành.

Ngày 14/09/2026 bổ sung mốc con M4: widget cùng origin, phiên khách ẩn danh có thời hạn, lưu và khôi phục hội thoại, trích dẫn, chuyển nhân viên và nhận phản hồi bằng polling. Kiểm chứng cách ly danh tính, chống gửi trùng và chặn AI muộn; tên tự nhập không thay xác minh quyền sở hữu đơn hàng. Inbox đã tự cập nhật bằng polling và có SLA phản hồi đầu tiên theo ưu tiên, tính 24/7; realtime đẩy sự kiện, lịch làm việc và hạn giải quyết còn dự kiến. Vòng đời ticket đã có giải quyết/đóng bởi người phụ trách, ghi chú nội bộ và tiếp nhận lại khi khách nhắn sau giải quyết; SLA phản hồi từng lượt được giữ khi ticket kết thúc. Ngày 15/09/2026 đã bổ sung hồ sơ thiết kế bám mã nguồn, hợp đồng API và ma trận kiểm chứng cùng smoke toàn luồng dùng Ollama thật trên dữ liệu tạm. Hồ sơ và nghiệm thu người dùng chờ duyệt; các phần độc lập tiếp tục triển khai. Mốc con M5 đã có model chọn tool bằng JSON Schema cho tin có một mã đơn, server kiểm tra chủ đơn/trạng thái trước thực thi và lưu trace nội bộ. Tra đơn chỉ đọc dữ liệu giả lập; yêu cầu hủy chuyển nhân viên, không sửa đơn. Chưa nghiệm thu agent nhiều bước hoặc chất lượng nhận diện/tóm tắt. Ngày 18/09/2026 bổ sung Tổng quan, quản lý khách/đơn nội bộ, Phân tích SLA và Cài đặt tài khoản theo mockup; có phân quyền và kiểm thử chức năng. Ngày 21/09/2026 bổ sung quyền tra từng đơn cho widget bằng mã admin cấp sau xác minh thủ công qua kênh tin cậy; có thời hạn, thu hồi và kiểm thử cách ly phiên, chưa có OTP tự động hoặc đăng nhập khách. Adapter Telegram đã có polling chat riêng, tách danh tính theo bot/người dùng, lưu bền và kiểm soát gửi lại trong Inbox; kiểm thử local đạt, còn chờ bot thật để nghiệm thu đa kênh. Đã có chế độ chạy bản build cùng API và kiểm tra sẵn sàng dành cho nhân viên. Đã bổ sung công cụ sao lưu và khôi phục local trên thư mục mới, kiểm tra toàn vẹn và thu hồi phiên cũ; kiểm chứng giữ đủ file khi loại trừ đúng khóa runtime Qdrant; chưa nghiệm thu vận hành cloud hoặc phục hồi bot thật. M3 vẫn chờ người duyệt nhãn/đáp án và dữ liệu độc lập; tiến độ chức năng không thay nghiệm thu chất lượng RAG.

Phép đo vận hành local ngày 21/09/2026 dùng HTTP thật, một Uvicorn worker và dữ liệu tạm; 10 client thực hiện 1.000 request đọc Inbox/widget, gửi tin và retry trên 500 hội thoại seed cùng một probe. Sau bổ sung index tin nhắn/ticket, throughput quan sát tăng từ 13,755 lên 37,437-38,008 request/giây; kiểm tra chống trùng và tranh chấp đạt. Phép đo giữ mẫu số và log tại evals/load, không gọi LLM/Telegram hoặc suy thành chất lượng RAG, tải tối đa hay nghiệm thu cloud. Tiếp tục đo trên môi trường triển khai khi có cấu hình và mục tiêu tải cụ thể.

Ngày 22/09/2026 bổ sung nhật ký chọn công cụ trong Inbox cho nhân viên, đối chiếu trạng thái/mã đơn/hành động/kết quả ngay dưới tin khách. Kiểm chứng hiển thị và quyền riêng tư trên dữ liệu tạm; bổ sung kiểm tra mã đơn nguyên vẹn, giới hạn độ dài và chữ ASCII để tránh tra nhầm do cắt mã hoặc đổi chữ Unicode. Nhận diện chuyển nhân viên được kiểm tra thêm với Unicode tiếng Việt, khoảng trắng và ranh giới từ để tránh bỏ sót yêu cầu hoặc nhầm từ khóa trong từ khác. Không thay kết quả đánh giá chất lượng M5 hoặc M3.

Độ bền Telegram được bổ sung kiểm chứng gián đoạn: thông báo chuyển nhân viên lưu cùng trạng thái và ticket, rollback đồng thời và không tạo lại khi xử lý update trùng. Ngày 01/10/2026 sửa hàng chờ đã lưu bị kẹt khi nhận tin mới lỗi; giữ con trỏ và trạng thái lỗi kết nối. Response HTTP bị cắt/sai giao thức khi gửi được ghi uncertain, không tự gửi lại. Probe khởi động tự thử lại lỗi mạng/HTTP 5xx, lỗi cấu hình vẫn cần xử lý. Kiểm thử local đạt; lỗi gửi vẫn cần người phụ trách xử lý và chưa thay thế nghiệm thu bot thật.

Inbox được bổ sung phân trang, tìm kiếm tiếng Việt trên toàn danh sách và lọc SLA trước chia trang; kiểm chứng giữ đúng hội thoại/bản nháp và luồng nhân viên trên desktop/mobile. Tìm kiếm/SLA còn xử lý theo lô, chưa thay nghiệm thu khả năng chịu tải trong môi trường triển khai.

Đã đo giảm độ trễ local bằng giữ model trong GPU giữa các lượt, không giảm bước kiểm định hoặc đổi mô hình. Phép đo nhỏ có dữ liệu gốc riêng; chưa suy thành chất lượng trả lời hoặc khả năng chịu tải tổng quát.

Đã bổ sung khôi phục mật khẩu nhân viên qua CLI dành cho người vận hành máy chủ, thu hồi phiên trong cùng transaction và kiểm thử trên dữ liệu tạm. Chức năng này không thay xác minh danh tính khách hàng hoặc nghiệm thu vận hành khi triển khai.

Lịch sử tin nhắn Inbox đã có phân trang theo mốc tin, giữ quyền truy cập và trạng thái xử lý khi xem tin cũ; đã kiểm thử chức năng và giao diện mobile. Đánh giá tải bền và nghiệm thu đa kênh thực tế vẫn thực hiện riêng.

Widget khách hàng cũng đã có phân trang lịch sử trong phạm vi phiên còn hiệu lực, giữ trích dẫn công khai và chặn truy cập tin của phiên khác. Kiểm chứng chức năng này không thay đánh giá chất lượng RAG hoặc tải đồng thời.

Đã bổ sung phép đo điều phối công cụ với model thật trên dữ liệu tạm; sau sửa yêu cầu hỗn hợp, tham chiếu đơn gần và ngữ cảnh handoff rõ, bộ gốc đạt 24/24 so với 17/24 ban đầu, bộ nối tiếp đạt 8/8, bộ ngữ cảnh mới đạt 10/12. Nhãn chưa được người duyệt, tập dùng phát triển và nhánh RAG giả lập; hai cách nói tự do vẫn nhận nhầm, chưa suy luận tham chiếu/ngữ cảnh tổng quát. Cần đánh giá độc lập trước nghiệm thu M5.

Đã chuẩn bị 44 phiếu duyệt nhãn gắn với bằng chứng từng lượt đo, giao diện HTML offline lưu nháp/xuất JSON và công cụ gộp phần duyệt có kiểm tra xung đột, tổng hợp có mẫu số rõ; hiện chưa có quyết định của người chấm. Công cụ hỗ trợ kiểm tra nhãn đã dùng phát triển, không thay bộ đánh giá độc lập hoặc chấm chất lượng đáp án RAG.

**9. Dự kiến nội dung của tiểu luận**

**Chương 1**: Mở đầu

1\.  Lý do chọn đề tài

2\. Mục tiêu nghiên cứu

3\. Đối tượng và phạm vi nghiên cứu

4\. Giả thuyết khoa học / Những đóng góp mới của đề tài

**Chương 2**: Cơ sở lý thuyết và tổng quan tài liệu

1\. Khái niệm …

2\. Hệ thống …

…

**Chương 3**: Phân tích yêu cầu hệ thống

…

**Chương 4**: Thiết kế hệ thống

…

**Chương 5**: Triển khai và thực hiện

1\. Môi trường phát triển và công cụ sử dụng

2\. Xây dựng chức năng …

3\. Xây dựng chức năng …

…

**Chương 6:** Kết quả thực hiện

**Chương 7**: Kết luận và đề xuất

**10. Danh mục tài liệu tham khảo**

- *GitHub. (2026). GitHub Actions Documentation. [*GitHub Docs*](https://docs.github.com/en/actions/get-started/understand-github-actions).*
- *…*
