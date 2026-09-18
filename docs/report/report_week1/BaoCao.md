# SẢN PHẨM TUẦN 1 — DRAFT 1

**Trường:** Đại học Sài Gòn  
**Khoa:** Công nghệ Thông tin  
**Học phần:** Đồ án chuyên ngành  
**Đề tài:** Nền tảng Trợ lý AI Hỗ trợ Khách hàng Đa kênh dựa trên Kiến trúc RAG  
**Nhóm:** 5B  
**Giảng viên hướng dẫn:** Trần Đình Nghĩa  
**Thời gian tuần 1:** 11–17/09/2026  
**Sản phẩm:** Bản phác thảo đề tài Mục 1–5 và biên bản phân công nhóm.

| STT | Họ và tên | MSSV | Lớp | Vai trò |
|---|---|---|---|---|
| 1 | Nguyễn Văn Khanh | [Bổ sung] | [Bổ sung] | Nhóm trưởng, phát triển chính |
| 2 | Hoàng Vũ | [Bổ sung] | [Bổ sung] | Hỗ trợ AI/RAG và dữ liệu |
| 3 | Nguyễn Đức Vinh | [Bổ sung] | [Bổ sung] | Frontend và giao diện |
| 4 | Nguyễn Văn A | [Bổ sung] | [Bổ sung] | Kiểm thử và tổng hợp tài liệu |

Đây là bản nháp định hướng nghiên cứu và phân công dự kiến. Nội dung phân công cần được các thành viên thống nhất trước khi ký xác nhận; chưa dùng làm biên bản nghiệm thu hoặc xác nhận đóng góp thực tế.

## A. Bản phác thảo đề tài — Mục 1 đến Mục 5

### 1. Lý do chọn đề tài và tính cấp thiết của vấn đề nghiên cứu

Trong hoạt động bán lẻ trực tuyến, bộ phận chăm sóc khách hàng thường xuyên tiếp nhận những câu hỏi lặp lại về chính sách giao hàng, đổi trả, bảo hành, thanh toán và trạng thái đơn hàng. Khi khách hàng liên hệ qua nhiều kênh, lịch sử trao đổi dễ bị phân tán, gây khó khăn trong việc theo dõi yêu cầu và phối hợp giữa các nhân viên.

Chatbot theo kịch bản có thể xử lý những tình huống đã được thiết lập nhưng gặp hạn chế trước cách diễn đạt đa dạng hoặc câu hỏi cần kết hợp nhiều thông tin. Mô hình ngôn ngữ lớn có khả năng giao tiếp linh hoạt hơn, nhưng có thể tạo câu trả lời thiếu căn cứ nếu không được cung cấp dữ liệu phù hợp. Đối với chăm sóc khách hàng, thông tin sai về chính sách hoặc đơn hàng có thể ảnh hưởng đến trải nghiệm và quyền lợi của người sử dụng.

Kiến trúc Retrieval-Augmented Generation (RAG) kết hợp truy xuất tài liệu với mô hình ngôn ngữ, cho phép hệ thống sử dụng thông tin từ kho tri thức của doanh nghiệp để hỗ trợ trả lời. Việc gắn câu trả lời với nguồn tham chiếu giúp khách hàng và nhân viên kiểm tra căn cứ. Bên cạnh đó, công cụ tra cứu đơn hàng và cơ chế chuyển giao cho người thật giúp xử lý những yêu cầu vượt ngoài phạm vi hỏi đáp tài liệu.

Từ nhu cầu trên, nhóm chọn đề tài nhằm xây dựng một nền tảng hỗ trợ khách hàng tập trung, kết hợp RAG, tra cứu dữ liệu nghiệp vụ và phối hợp giữa AI với nhân viên. Đề tài có ý nghĩa thực tiễn trong việc hỗ trợ xử lý câu hỏi thường gặp, đồng thời tạo điều kiện nghiên cứu các vấn đề về độ tin cậy của câu trả lời, bảo vệ dữ liệu và kiểm soát quá trình chuyển giao.

### 2. Lịch sử nghiên cứu vấn đề và tổng quan

Các hệ thống chatbot hỗ trợ khách hàng có thể được tiếp cận theo ba hướng chính: chatbot dựa trên quy tắc, chatbot truy xuất câu trả lời và chatbot sử dụng mô hình ngôn ngữ lớn. Chatbot dựa trên quy tắc dễ kiểm soát trong phạm vi hẹp nhưng cần cập nhật kịch bản khi nghiệp vụ thay đổi. Chatbot truy xuất phụ thuộc vào mức độ bao phủ của tập câu hỏi và câu trả lời. Mô hình ngôn ngữ lớn hỗ trợ diễn đạt linh hoạt, tuy nhiên cần cơ chế bổ sung thông tin và kiểm tra đầu ra.

Nghiên cứu của Lewis và cộng sự (2020) giới thiệu phương pháp RAG, kết hợp mô hình sinh với khả năng truy xuất từ nguồn dữ liệu bên ngoài. Hướng tiếp cận này cung cấp cơ sở để xây dựng hệ thống hỏi đáp dựa trên tài liệu. Nghiên cứu Dense Passage Retrieval của Karpukhin và cộng sự (2020) trình bày phương pháp truy hồi đoạn văn bằng biểu diễn vector, có liên quan đến bước tìm kiếm ngữ nghĩa trong hệ thống RAG.

Trong bài toán chăm sóc khách hàng, hỏi đáp tài liệu cần được kết hợp với các chức năng nghiệp vụ. Câu hỏi về chính sách có thể sử dụng kho tri thức, trong khi trạng thái đơn hàng cần được lấy từ cơ sở dữ liệu hoặc API. Cơ chế gọi công cụ cho phép hệ thống lựa chọn thao tác phù hợp, nhưng quyền truy cập và tham số thực thi phải được kiểm tra tại máy chủ.

Ngoài ra, cơ chế human-in-the-loop cho phép nhân viên tiếp nhận hội thoại khi khách hàng yêu cầu hỗ trợ trực tiếp, có dấu hiệu không hài lòng hoặc khi AI không đủ thông tin. Hệ thống cần giữ lịch sử, cung cấp ngữ cảnh chuyển giao và ngừng phản hồi tự động khi nhân viên phụ trách.

Trên cơ sở các hướng tiếp cận trên, đề tài tập trung tích hợp RAG, công cụ tra cứu đơn hàng và chuyển giao nhân viên vào một nền tảng đa kênh. Đóng góp dự kiến nằm ở thiết kế và đánh giá quy trình tích hợp; nhóm chưa đặt mục tiêu đề xuất thuật toán RAG mới.

**Tài liệu nền tảng cho phần tổng quan:**

- Lewis, P. và cộng sự (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. [Bài báo](https://arxiv.org/abs/2005.11401).
- Karpukhin, V. và cộng sự (2020). *Dense Passage Retrieval for Open-Domain Question Answering*. [Bài báo](https://arxiv.org/abs/2004.04906).

### 3. Mục đích nghiên cứu

**Mục đích tổng quát**

Xây dựng và đánh giá nền tảng trợ lý AI hỗ trợ khách hàng đa kênh cho mô hình cửa hàng bán lẻ trực tuyến giả lập, có khả năng trả lời dựa trên tài liệu nội bộ, tra cứu đơn hàng có kiểm soát quyền và chuyển giao hội thoại cho nhân viên.

**Mục tiêu cụ thể**

- Xây dựng kho tri thức từ tài liệu chính sách, hỗ trợ xử lý PDF/DOCX, chia đoạn, tạo vector nhúng và truy xuất thông tin.
- Phát triển chức năng trả lời tiếng Việt kèm nguồn tham chiếu; yêu cầu làm rõ hoặc từ chối trả lời cụ thể khi chưa đủ bằng chứng.
- Tích hợp công cụ tra cứu trạng thái đơn hàng, bảo đảm kiểm tra quyền truy cập trước khi cung cấp dữ liệu.
- Xây dựng hộp thư tập trung tiếp nhận hội thoại từ Website Chat Widget và một kênh giao tiếp thứ hai.
- Hỗ trợ nhận diện yêu cầu chuyển nhân viên, cung cấp tóm tắt ngữ cảnh, phân công xử lý và theo dõi thời hạn phản hồi.
- Đánh giá khả năng truy hồi, mức độ có căn cứ của câu trả lời, độ đúng của trích dẫn, độ trễ và tính đúng đắn của luồng chuyển giao.

Đề tài hướng đến giảm câu trả lời thiếu căn cứ trong phạm vi dữ liệu được kiểm thử; không giả định hệ thống loại bỏ hoàn toàn hiện tượng bịa đặt thông tin.

### 4. Nhiệm vụ nghiên cứu

1. **Khảo sát và xác định yêu cầu:** phân tích quy trình chăm sóc khách hàng, các nhóm câu hỏi thường gặp và vai trò của quản trị viên, nhân viên, khách hàng; xây dựng tình huống sử dụng và tiêu chí kiểm chứng.
2. **Nghiên cứu cơ sở lý thuyết:** tìm hiểu RAG, biểu diễn vector, truy hồi ngữ nghĩa, gọi công cụ, nhận diện yêu cầu chuyển giao và cơ chế human-in-the-loop.
3. **Chuẩn bị dữ liệu:** xây dựng bộ tài liệu chính sách, dữ liệu đơn hàng giả lập và bộ câu hỏi đánh giá có nguồn tham chiếu; tách dữ liệu phát triển với dữ liệu đánh giá.
4. **Thiết kế hệ thống:** xây dựng kiến trúc, mô hình dữ liệu, API, phân quyền và giao diện; mô tả trạng thái hội thoại, ticket và quy trình chuyển giao.
5. **Phát triển các chức năng:** xây dựng kho tri thức, pipeline RAG, công cụ tra cứu đơn hàng, hộp thư tập trung, widget, kênh thứ hai và các trang quản lý hỗ trợ.
6. **Kiểm thử và đánh giá:** kiểm tra chức năng, quyền truy cập, bảo vệ dữ liệu, lỗi kết nối, gửi tin trùng và tranh chấp giữa AI với nhân viên; đánh giá câu trả lời bằng bộ câu hỏi và đối chiếu nguồn.
7. **Hoàn thiện sản phẩm:** chuẩn bị môi trường chạy thử, kịch bản demo, hướng dẫn sử dụng, báo cáo kết quả và phân tích những hạn chế còn tồn tại.

### 5. Đối tượng nghiên cứu và phạm vi nghiên cứu

#### 5.1. Đối tượng nghiên cứu

- Hội thoại chăm sóc khách hàng bằng tiếng Việt trong lĩnh vực bán lẻ trực tuyến.
- Tài liệu chính sách giao hàng, đổi trả, bảo hành, thanh toán và hướng dẫn dịch vụ.
- Dữ liệu khách hàng, đơn hàng và yêu cầu hỗ trợ trong môi trường giả lập.
- Quy trình truy xuất bằng chứng, lựa chọn công cụ và chuyển giao giữa AI với nhân viên.
- Các chỉ số phản ánh chất lượng trả lời và hiệu quả vận hành hệ thống.

#### 5.2. Phạm vi nghiệp vụ

Hệ thống phục vụ một cửa hàng bán lẻ trực tuyến giả lập. Chức năng trọng tâm gồm hỏi đáp chính sách, tra cứu trạng thái đơn hàng, tiếp nhận yêu cầu hỗ trợ, chuyển nhân viên và theo dõi thời hạn phản hồi đầu tiên.

Công cụ AI chỉ tra cứu đơn hàng. Các yêu cầu hủy đơn, thay đổi thông tin hoặc xử lý khiếu nại được chuyển nhân viên, không tự động thực hiện giao dịch. Mã đơn hàng, tên hoặc email tự nhập không đủ để xác minh quyền sở hữu đơn; máy chủ phải kiểm tra quyền trước khi cung cấp thông tin.

#### 5.3. Phạm vi dữ liệu và kênh giao tiếp

Kho tri thức ưu tiên PDF có lớp văn bản và DOCX; có thể sử dụng TXT/Markdown để chuẩn bị dữ liệu và kiểm thử. Xử lý tài liệu scan bằng OCR nâng cao nằm ngoài phạm vi chính.

Hệ thống dự kiến tích hợp Website Chat Widget và một kênh giao tiếp thật thứ hai. Telegram được đề xuất để triển khai, cần thống nhất với giảng viên hướng dẫn. Tích hợp thêm Zalo hoặc các nền tảng khác thuộc hướng mở rộng.

#### 5.4. Phạm vi công nghệ và triển khai

Dự kiến sử dụng Python/FastAPI cho backend, React cho frontend, Qdrant cho dữ liệu vector và Ollama để chạy mô hình ngôn ngữ tại máy. Dữ liệu nghiệp vụ sử dụng SQLite trong bản thử nghiệm. Môi trường phát triển là Windows.

#### 5.5. Phạm vi đánh giá

Đánh giá trên bộ tài liệu và tình huống đã xác định, gồm câu hỏi có đáp án, thiếu thông tin, ngoài phạm vi, yêu cầu tra đơn và chuyển nhân viên. Kết quả chỉ được diễn giải trong điều kiện thử nghiệm; chưa đại diện cho mọi doanh nghiệp hoặc khả năng vận hành ở quy mô lớn.

## B. Biên bản phân công nhóm — Bản nháp

**Nhóm:** 5B  
**Đề tài:** Nền tảng Trợ lý AI Hỗ trợ Khách hàng Đa kênh dựa trên Kiến trúc RAG  
**Thời gian họp:** [Giờ, ngày/tháng/năm thực tế]  
**Địa điểm/hình thức:** [Bổ sung]  
**Chủ trì dự kiến:** Nguyễn Văn Khanh — Nhóm trưởng  
**Thư ký:** [Bổ sung theo cuộc họp thực tế]  
**Thành viên dự kiến tham dự:** Nguyễn Văn Khanh, Hoàng Vũ, Nguyễn Đức Vinh, Nguyễn Văn A.  
**Thành viên tham dự thực tế/vắng mặt:** [Bổ sung]

### 1. Mục đích cuộc họp

Thảo luận yêu cầu đề tài, xác định phạm vi ban đầu và phân công chuẩn bị sản phẩm tuần 1 gồm bản phác thảo đề tài từ Mục 1 đến Mục 5 và biên bản phân công nhóm. Xác định trách nhiệm của từng thành viên trong lịch toàn đồ án, giữ các mốc bàn giao đã đề ra.

### 2. Phân công trách nhiệm chính

| Thành viên | Vai trò | Công việc phụ trách |
|---|---|---|
| **Nguyễn Văn Khanh** | **Nhóm trưởng, phát triển chính** | Quản lý tiến độ; thiết kế kiến trúc, CSDL/API; phát triển backend và phần lõi RAG; xác thực, phân quyền, tool đơn hàng, handoff; tích hợp, rà soát mã và triển khai |
| **Hoàng Vũ** | Hỗ trợ AI/RAG và dữ liệu | Khảo sát tài liệu; chuẩn bị kho tri thức PDF/DOCX; xây bộ câu hỏi, đáp án và nguồn tham chiếu; hỗ trợ thử nghiệm, đánh giá RAG |
| **Nguyễn Đức Vinh** | Frontend và giao diện | Thiết kế mockup; phát triển giao diện Inbox, widget và các trang quản lý; kết nối API dưới sự phối hợp của nhóm trưởng; kiểm tra desktop/mobile |
| **Nguyễn Văn A** | Kiểm thử và tổng hợp tài liệu | Viết test case; kiểm thử chức năng và phân quyền; hỗ trợ kiểm thử kênh thứ hai; tổng hợp báo cáo, hướng dẫn sử dụng, slide và kịch bản demo |

Mỗi thành viên viết tài liệu cho phần mình phụ trách. Nguyễn Văn A tổng hợp; Nguyễn Văn Khanh rà soát nội dung kỹ thuật trước bàn giao.

### 3. Phân công sản phẩm tuần 1

**Thời gian: 11–17/09/2026. Sản phẩm: Biên bản phân công nhóm và bản phác thảo đề tài Draft 1, Mục 1–5.**

| Thành viên | Công việc | Thời gian dự kiến | Sản phẩm bàn giao |
|---|---|---|---|
| **Nguyễn Văn Khanh** | Chốt bài toán, phạm vi và định hướng kỹ thuật; viết **Mục 1**; lập phân công, rà soát và tổng hợp Draft 1 | 11–16/09 | Mục 1, bảng phân công và bản nháp tổng hợp |
| **Hoàng Vũ** | Tìm hiểu RAG, truy hồi ngữ nghĩa, gọi công cụ và chuyển giao người thật; viết **Mục 2** | 11–15/09 | Tổng quan nghiên cứu và tài liệu tham khảo ban đầu |
| **Nguyễn Đức Vinh** | Xác định người dùng, luồng sử dụng và chức năng chính; viết **Mục 3** | 12–15/09 | Mục đích nghiên cứu và danh sách chức năng |
| **Nguyễn Văn A** | Viết **Mục 4–5** từ phạm vi nhóm thống nhất; soạn biên bản, kiểm tra định dạng | 12–16/09 | Nhiệm vụ, đối tượng, phạm vi và biên bản dự thảo |
| **Cả nhóm** | Đọc chéo, chỉnh sửa và xác nhận phân công | 16–17/09 | Draft 1 hoàn chỉnh và biên bản xác nhận |

### 4. Phân công theo tiến độ toàn đồ án

Các ngày thuộc năm **2026**, giữ lịch nội bộ trong [ROADMAP.md](../../../ROADMAP.md). Thời gian trong bảng là kế hoạch, không phải xác nhận công việc đã hoàn thành.

| Thời gian / mốc | Nguyễn Văn Khanh — phụ trách chính | Hoàng Vũ | Nguyễn Đức Vinh | Nguyễn Văn A | Mốc bàn giao |
|---|---|---|---|---|---|
| **11–17/09 — M0** | Chốt bài toán, phân công, tổng hợp Draft 1 | Tổng quan RAG, khảo sát dữ liệu | Mục tiêu và luồng người dùng | Nhiệm vụ, phạm vi, biên bản | Draft 1 Mục 1–5 |
| **18–22/09 — M1** | Chốt kế hoạch, phương pháp và tiêu chí kiểm chứng | Bổ sung nguồn tham khảo | Rà soát chức năng, giao diện dự kiến | Tổng hợp đủ 10 mục, kiểm tra hình thức | Đề cương sẵn sàng nộp **25/09** |
| **23/09–01/10 — M2** | Kiến trúc, CSDL/API, xác thực; thiết kế lõi RAG | Chuẩn bị tài liệu, thử xử lý PDF/DOCX | Mockup, khung giao diện, đăng nhập | Use Case, test plan, rà soát hồ sơ | Thiết kế nháp và nền tảng ứng dụng |
| **02–08/10 — M3** | Phát triển ingestion, retrieval và trả lời có nguồn | Bộ câu hỏi, đáp án, kiểm tra trích dẫn | Kho tri thức, tải tài liệu, hỏi thử | Kiểm thử API và lỗi tài liệu | RAG chạy xuyên suốt |
| **09–15/10 — M4** | Hội thoại, phiên khách, ticket, SLA; kết nối RAG | Kiểm tra câu trả lời trong hội thoại | Widget, Inbox, cập nhật tin/trạng thái | Kiểm thử phiên, lịch sử, SLA; tổng hợp thiết kế | Chốt nội bộ **12/10**, chuẩn bị nộp **16/10** |
| **16–22/10 — M5** | Tool đơn hàng, kiểm tra quyền, điều phối handoff và AI | Chuẩn bị tình huống khiếu nại, đánh giá tóm tắt | Hiển thị chuyển giao và người phụ trách | Kiểm thử sai chủ đơn, lỗi tool, tranh chấp | Tra đơn và handoff được kiểm chứng |
| **23–29/10 — M6** | Tích hợp kênh thứ hai, danh tính theo kênh, chống tin trùng | Kiểm tra RAG/tool trên hai kênh | Hoàn thiện giao diện đa kênh | Kiểm thử gửi/nhận, demo toàn luồng | MVP và đóng băng tính năng |
| **30/10–05/11 — M7** | Triển khai, sửa lỗi tích hợp, rà soát bảo mật | Đo chất lượng RAG và độ trễ | Sửa lỗi UI, kiểm tra responsive | Kiểm thử tổng thể, tổng hợp số liệu | Sẵn sàng demo **06/11** |
| **06–13/11 — M8** | Chốt mã nguồn, triển khai và rà soát báo cáo | Hoàn thiện phần AI, kết quả và giới hạn | Chốt UI, ảnh minh họa, demo | Tổng hợp Word/PDF, slide và hướng dẫn | Sản phẩm, hồ sơ sẵn sàng **13/11** |
| **14–22/11 — Dự phòng** | Sửa lỗi còn lại, kiểm tra gói mã nguồn | Rà soát số liệu và tài liệu tham khảo | Kiểm tra demo và slide | Soát biểu mẫu, định dạng và gói nộp | Hồ sơ hoàn chỉnh trước hạn |
| **23–27/11 — Nộp và bảo vệ** | Phối hợp nộp; trình bày kiến trúc, lõi kỹ thuật và tích hợp | Trình bày dữ liệu, đánh giá RAG | Trình diễn giao diện và luồng sử dụng | Trình bày kiểm thử, hỗ trợ demo dự phòng | Nộp trước **11:30 ngày 23/11**; bảo vệ **27/11** |

### 5. Nguyên tắc phối hợp và theo dõi tiến độ

| Nội dung | Cách thực hiện |
|---|---|
| Cập nhật công việc | Mỗi thành viên cập nhật công việc đã làm, sản phẩm và khó khăn ít nhất một lần mỗi tuần |
| Kiểm tra trước hạn | Nguyễn Văn Khanh rà soát trước mỗi mốc nội bộ 3 ngày; điều chỉnh phân công khi có nguy cơ trễ |
| Bàn giao | Kèm mã nguồn, tài liệu hoặc kết quả kiểm thử; người nhận kiểm tra trước khi xác nhận hoàn thành |
| Đọc chéo | Nguyễn Văn Khanh kiểm tra phần Nguyễn Văn A; Nguyễn Văn A kiểm tra phần Nguyễn Văn Khanh; Hoàng Vũ và Nguyễn Đức Vinh kiểm tra luồng kết nối AI với giao diện |
| Tài liệu và nguồn | Mỗi người lưu nguồn tham khảo, ghi nhận phần việc của mình; Nguyễn Văn A tổng hợp, Nguyễn Văn Khanh rà soát kỹ thuật |
| Thay đổi phạm vi | Các thay đổi lớn cần nhóm thống nhất và trao đổi với giảng viên hướng dẫn |
| Sau đóng băng tính năng | Ưu tiên sửa lỗi, kiểm thử và hoàn thiện hồ sơ; không tự mở rộng tính năng ngoài phạm vi đã thống nhất |
| Xác nhận đóng góp | Biên bản nghiệm thu và báo cáo đóng góp cuối kỳ ghi theo công việc thực tế, có sản phẩm và xác nhận của thành viên |

### 6. Sản phẩm bàn giao tuần 1

1. Bản phác thảo đề tài **Draft 1**, gồm Mục 1 đến Mục 5.
2. Biên bản phân công có tên thành viên, đầu việc và thời hạn.
3. Danh sách tài liệu tham khảo ban đầu.
4. Các vấn đề cần xin ý kiến GVHD: kênh thứ hai, phạm vi SLA và tiêu chí đánh giá RAG.

### 7. Kết luận và xác nhận cuộc họp

**Kết luận thực tế của cuộc họp:** [Bổ sung nội dung đã được nhóm thống nhất]  
**Điều chỉnh so với phân công dự kiến:** [Bổ sung nếu có]  
**Thời gian kết thúc:** [Giờ, ngày/tháng/năm thực tế]

| Thành viên | Xác nhận phân công / ý kiến | Chữ ký |
|---|---|---|
| Nguyễn Văn Khanh — Nhóm trưởng | [Bổ sung] | [Ký xác nhận] |
| Hoàng Vũ | [Bổ sung] | [Ký xác nhận] |
| Nguyễn Đức Vinh | [Bổ sung] | [Ký xác nhận] |
| Nguyễn Văn A | [Bổ sung] | [Ký xác nhận] |

**Thư ký cuộc họp:** [Họ tên, chữ ký]  
**Góp ý của giảng viên hướng dẫn:** [Bổ sung sau khi nhận góp ý]
