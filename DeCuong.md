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

**6. Phương pháp nghiên cứu**

Phát triển lặp theo các mốc có kiểm chứng. Dùng kiểm thử API, kiểm thử quyền và tranh chấp tiếp nhận, kiểm tra giao diện desktop/mobile; xây bộ câu hỏi có nguồn để đo Recall@k, độ đúng trích dẫn, khả năng từ chối và độ trễ p50/p95. So sánh sinh đáp án tự do với chọn câu nguồn bằng ID và trích nguyên văn, kết hợp kiểm định bằng LLM; đo lỗi còn lọt, từ chối sai và chi phí độ trễ khi đổi model/chế độ suy luận local. Trích đúng câu nguồn chưa bảo đảm trả lời đúng câu hỏi hoặc giữ đủ điều kiện. Bổ sung PDF nhiều trang và DOCX có bảng để kiểm tra ingestion, chunking và vị trí citation ngoài corpus TXT; giữ cấu hình trước lượt đo, lưu hash đầu vào và lỗi từng file. Tách tập phát triển với tập đánh giá; tập test đã xem lỗi chỉ dùng làm regression. Bộ giả lập do cùng người phát triển soạn và kiểm định bằng cùng model không thay nhãn hoặc đánh giá độc lập của người duyệt.

Phiếu người duyệt được đối chiếu với ID của lượt đánh giá và tổng hợp riêng: chỉ tính đánh giá có người chấm, nhãn được duyệt và chỉ số áp dụng; giữ phần chưa chấm ở trạng thái null, nêu mẫu số riêng cho mỗi tỷ lệ. Lưu hash đầu vào để truy vết, không dùng điểm tự động điền thay người hoặc suy kết quả chấm một phần thành chất lượng toàn bộ tập.

**7. Giả thuyết khoa học/Những đóng góp mới của đề tài**

Giả thuyết cần kiểm chứng: kết hợp truy hồi bằng chứng, công cụ nghiệp vụ và chuyển giao có trạng thái giúp hỗ trợ CSKH đáng tin cậy hơn luồng trả lời không kiểm soát. Ràng buộc ID câu theo từng nguồn trong JSON Schema và kiểm tra lại ở backend bảo vệ miền giá trị; hiệu quả trả lời đúng vẫn phải được đánh giá riêng bằng hồi quy và người duyệt. Đóng góp dự kiến là tích hợp các thành phần vào quy trình đa kênh và xây bộ đánh giá phù hợp; chưa tuyên bố có thuật toán mới hoặc kết quả cải thiện định lượng.

**8. Dự kiến kế hoạch nghiên cứu (tuần/thực hiện công việc gì ?)**

Ưu tiên theo công việc: nền tảng dữ liệu và xác thực; RAG dùng mô hình thật; widget/realtime/SLA; Agentic RAG và handoff; kênh thứ hai; kiểm thử, triển khai và hồ sơ. Chi tiết mốc ở ROADMAP.md, trạng thái kỹ thuật ở docs/TASKS.md. Phần đã kiểm chứng của xác thực, handoff, RAG local dùng Ollama/Qdrant và baseline trên bộ câu hỏi giả lập được trình bày trong Chương 5-6 báo cáo; không coi các mục còn dự kiến là kết quả hoàn thành.

Ngày 14/09/2026 bổ sung mốc con M4: widget cùng origin, phiên khách ẩn danh có thời hạn, lưu và khôi phục hội thoại, trích dẫn, chuyển nhân viên và nhận phản hồi bằng polling. Kiểm chứng cách ly danh tính, chống gửi trùng và chặn AI muộn; tên tự nhập không thay xác minh quyền sở hữu đơn hàng. Inbox realtime và SLA còn dự kiến. M3 vẫn chờ người duyệt nhãn/đáp án và dữ liệu độc lập; tiến độ chức năng widget không thay nghiệm thu chất lượng RAG.

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
