# Công việc

## 09/10/2026 - Giữ UUID chờ và báo tin mới cho khách

Sau push `8613c2f`, chặn nháp mới ghi đè tin chưa xác nhận trong Inbox/widget; cho xem và gửi lại đúng nội dung/UUID cũ, xác nhận xong vẫn giữ nháp mới. Widget báo tin mới khi cuộn lên, giữ vị trí đọc, thêm về tin mới nhất và trả focus vào log. Footer co/cuộn, cảnh báo nháp lỗi luôn hiện cùng ô soạn trong viewport thấp đã thử. Bốn kiểm thử trình duyệt, hai test backend liên quan, build và diff check đạt. Chỉ sửa frontend, không thêm dependency hoặc thay RAG; điện thoại/trình đọc màn hình thật vẫn chờ. Chi tiết: `docs/UI_UPGRADE_20261009.md`.

## 09/10/2026 - Khôi phục nháp, soạn khi AI xử lý và khả năng truy cập

Nháp/ghi chú và UUID gửi chưa xác nhận lưu bằng sessionStorage trong tab, hết hạn sau 24 giờ từ lần lưu cuối; tách nhân viên/hội thoại, khôi phục sau reload hoặc đăng nhập lại cùng tài khoản và xóa khi đăng xuất chủ động/kết thúc hội thoại khách. Có cảnh báo storage lỗi và gửi lại UUID cũ. Khách soạn tin tiếp khi AI xử lý; kết quả cũ không xóa nháp mới. Thêm đánh dấu chưa đọc riêng nhân viên, chờ request đọc cùng tab trước khi lùi cursor. Dashboard giữ dữ liệu khi làm mới/lỗi, hiển thị thời điểm và tự cập nhật khi quay lại tab. Hồ sơ mobile dùng dialog native, giữ focus và trả focus khi Escape; điều chỉnh tương phản mẫu chữ, log tin mới và giữ ô soạn khi cảnh báo dài. 225 kiểm thử backend đạt (146,750 giây); runner trình duyệt mới: `frontend/tests/productivity.cjs`. Không đổi schema/RAG hoặc thêm dependency; chưa thử điện thoại/trình đọc màn hình thật. Chi tiết: `docs/UI_UPGRADE_20261009.md`.

## 09/10/2026 - Lọc chưa đọc, Back/reload và giao diện mobile

Đã bổ sung lọc SQL chưa đọc riêng nhân viên trước phân trang; giữ chat sau khi đọc, giảm nhãn Inbox, URL/Back/reload giữ trang/bộ lọc/hội thoại và bản ghi khách/đơn. Bảng khách/đơn thành thẻ mobile; sáng/tối và thương hiệu RAG Support dùng chung đăng nhập/admin/khách. Cảnh báo tải lại khi Inbox còn bản nháp/ghi chú; sửa ResizeObserver khi đổi viewport. 223 kiểm thử backend đạt (141,515 giây), ba kiểm thử trình duyệt đạt, QA 320–1366 px đạt trong luồng đã thử. Không đổi schema v10/RAG/model hoặc thêm dependency; QA trình duyệt dùng API giả lập, chưa thử bàn phím điện thoại thật/tải lớn. Chi tiết: `docs/UI_UPGRADE_20261009.md`.

## 09/10/2026 - Inbox chưa đọc, chat mobile và kho tri thức

Đã thêm preview/tin cuối, sắp xếp hoạt động gần nhất và cursor đọc riêng nhân viên ở backend (schema v10), không ghi đọc từ GET hoặc chỉ nhìn danh sách mobile. Thu gọn header/SLA mobile, giữ bản nháp và thêm về tin mới; kho tri thức có tab bàn phím/tìm tên/lọc trạng thái, phân biệt kết quả AI và lỗi, xem đoạn nguồn đánh dấu quote; dashboard đưa hàng chờ thật lên đầu và mở đúng bộ lọc. Cập nhật backup/readiness theo schema mới. 221 kiểm thử backend, build và QA API trên DB tạm đạt, viewport 320–1366 không tràn ngang; AI trong QA được giả lập, không thay model/prompt hoặc dùng điểm cũ làm nghiệm thu mới. Chi tiết, kiểm thử và giới hạn: `docs/UI_UPGRADE_20261009.md`. Sao lưu offline trước nâng môi trường thật.

## 09/10/2026 - Ràng buộc nguồn sửa trong kiểm định RAG

Bản `refund-schema-v1-20261009` giữ 180/180 hồi quy, 218 kiểm thử backend đạt. Bước kiểm định dùng chung grammar cặp ID với bước chọn nguồn, ngăn đề xuất câu giao hàng đã bị loại trong câu hỏi hoàn tiền; backend vẫn kiểm tra ID và mọi nguồn vẫn được dùng để kiểm định mâu thuẫn. Sáu ca trọng tâm lặp xen kẽ năm vòng đạt 30/30, riêng `bt20-032` 5/5 thay vì 0/3 của chẩn đoán trước; đây là phát lại truy hồi lưu sẵn, không phải 30 ca end-to-end độc lập. Không đổi prompt, model hoặc corpus/nhãn. Giới hạn còn lại: câu mở có thể dư đoạn, chưa bảo đảm ổn định với dữ liệu mới, chưa có người duyệt/tập kín độc lập; chưa nghiệm thu toàn bộ ưu tiên cao/M3. Báo cáo và bằng chứng: `evals/rag-policy/RANG_BUOC_KIEM_DINH_20261009.md`.

## 09/10/2026 - Diễn đạt có nguồn và giảm đoạn dư RAG

Kiểm tra lặp sáu ca với truy hồi lưu sẵn: 15/18 đạt; `bt20-032` bị từ chối sai ba lần vì kiểm định đề xuất mốc giao hàng không hợp lệ. Ca này đạt trong lượt đầy đủ nhưng chưa ổn định, vẫn thuộc ưu tiên cao. Không cộng lượt chẩn đoán vào điểm end-to-end.

Bản `precision-final-20261009` đạt 180/180 rubric tự động, từ 178/180; 216 kiểm thử backend đạt. Sửa hỏi lại dư ở mốc hoàn tiền `bt20-032`, diễn đạt phủ định theo lịch độc quyền ở `test-026`, bỏ đoạn đổi trả dư ở `policy-013`. Mọi diễn đạt và đáp án rút gọn đều qua kiểm định, giữ nguyên citation/điều kiện và tối đa ba lần chat. 153/153 quote khớp chunk; 0 lỗi provider; corpus/nhãn giữ nguyên. Lưu cả hai lượt thử có thoái lui để đối chiếu. Câu mở vẫn có thể dư đoạn; chưa có người duyệt hoặc tập kín độc lập, chưa nghiệm thu M3/toàn bộ ưu tiên cao. Chi tiết và bằng chứng tại `evals/rag-policy/DO_CHINH_XAC_20261009.md`.

## 09/10/2026 - Xử lý tồn đọng RAG ưu tiên cao

Bản `priority-followup-verified-v2-20261009`: 178/180 đạt rubric tự động (trước 173/180), 209 test backend đạt. Sửa 6/7 ca cũ; còn `test-026` lệch rubric và ca mới `bt20-032` hỏi lại dư dù có nguồn. Không gọi ưu tiên cao hoàn tất. Giữ tối đa ba lần chat và kiểm tra phiên bản nguồn, bổ sung trích câu cho chunk bị cắt, giữ bước xác minh, hỏi sản phẩm thiếu, chặn trả thông tin tài khoản khi thiếu số và chọn nhầm mốc giao cho hoàn tiền. 0 lỗi provider, 164/164 quote khớp chunk, mâu thuẫn 13/13 và injection 17/17 trên bộ này. Không sửa corpus/nhãn cũ; chưa có người thật duyệt hoặc tập kín độc lập. `policy-013` vẫn có đoạn dư dù đạt rubric. Chi tiết ca còn lại, các lượt không được chọn và hash tại `evals/rag-policy/XU_LY_TON_DONG_20261009.md`; quy trình bàn giao kiểm thử độc lập tại `evals/rag-policy/NGHIEM_THU_DOC_LAP.md`. Chưa nghiệm thu M3.

## 09/10/2026 - Truy hồi, ngữ cảnh và chính sách mẫu RAG

Ngày 09/10/2026 nâng cấp truy hồi và ngữ cảnh RAG: lấy tập ứng viên vector giới hạn, xếp lại bằng cụm hai từ hiếm trong tập ứng viên nhưng giữ nguyên cosine score và kiểm tra phiên bản nguồn. Lọc mẫu chỉ dẫn giả khỏi lịch sử và lựa chọn nguồn; giữ đoạn đầu an toàn nguyên văn, các câu sạch phía sau vẫn có mặt để kiểm định xung đột. Trùng ID được gộp, không bỏ kiểm định. Bổ sung hỏi lại đơn cụ thể thiếu dịch vụ giao/lý do đổi/phương thức thanh toán, giữ chủ đề câu nối tiếp và chặn trả số điện thoại khi quote không có số. Giữ model/embedding/ngưỡng 0,35 và tối đa ba lần chat. BT20 58/60 thành 58/60; TN8/LS2 22/24 thành 24/24; PDF/DOCX 20/24 thành 23/24; TXT 42/48 thành 45/48. Bộ chính sách mẫu Mộc Demo mới: 20/24 thành 23/24. 180 lượt bản được chọn không lỗi provider hoặc chuỗi cấm theo rubric; 159/159 quote khớp đoạn truy hồi. 198 kiểm thử backend đạt. Không thay nhãn/corpus cũ, không tải chính sách giả lập vào kho tri thức thật. Các tập đã xem kết quả chỉ dùng phát triển/hồi quy; người duyệt và đánh giá độc lập vẫn chưa hoàn tất. Chi tiết, ca thoái lui và bằng chứng tại evals/rag-policy/NANG_CAP_20261009.md.

## 08/10/2026 - Nâng cấp trích đoạn và đo hồi quy

Đợt trích đoạn tiếp theo ngày 08/10/2026: BT20 từ 52/60 lên 58/60; TN8/LS2 từ 19/24 lên 22/24. Hồi quy PDF/DOCX 20/24 (trước 21/24), TXT 42/48 (trước 40/48). Tổng 156 lượt Ollama thật, 0 lỗi dịch vụ; 114/114 quote khớp đoạn truy hồi. 188 kiểm thử backend đạt. ID câu 1 chọn cả đoạn giới hạn 1.200 ký tự; ID từ 2 chọn câu riêng, giữ các điều kiện phụ mà không bắt buộc đưa chỉ dẫn giả vào đáp án. Bổ sung nhận diện lý do gửi nhầm/nhận sai và chỉ hỏi lại bằng quy tắc chờ đợi khi toàn câu là mẫu mơ hồ, tránh chặn chủ đề ngoài bán hàng. Chặn quote chứa mẫu yêu cầu bỏ qua chỉ dẫn/quy tắc ở backend; không coi bộ lọc cụm từ này là chống injection toàn diện. Giữ model, embedding, ngưỡng truy hồi và tối đa ba lượt chat; sửa bằng chứng vẫn phải kiểm định lại. Không đổi nhãn/corpus, không sửa dữ liệu người dùng. Các tập đều đã dùng để phát triển/hồi quy, chưa có người duyệt độc lập; điểm này không phải độ chính xác thực tế hoặc nghiệm thu M3. Chi tiết ca sửa được, thoái lui và giới hạn tại evals/bt20/TRICH_DOAN_20261008.md.

## 08/10/2026 - Nâng cấp chọn nguồn và kiểm định RAG

Ngày 08/10/2026 nâng cấp chọn câu và kiểm định RAG: giữ điều kiện trong cùng đoạn, loại trích dẫn lặp, hỏi làm rõ hai dạng mơ hồ tiếng Việt trước khi chọn nguồn và cho phép sửa ID câu tối đa một lần nhưng phải kiểm định lại. Giữ qwen3:4b, embeddinggemma:300m, think=false và ngưỡng truy hồi 0,35; không bỏ kiểm định hoặc thay kho tri thức người dùng. Chạy lại BT20 đạt 52/60 (86.7%), so với 43/60 trước sửa; từ chối sai giảm từ 13/46 còn 4/46. Cả hai câu mơ hồ hỏi lại; 4/4 ca mâu thuẫn, 4/4 ca chỉ dẫn giả và 6/6 ca thiếu dữ kiện đạt rubric. Bộ mới TN8/LS2 gồm 24 câu soạn trước lượt chạy đầu tiên đạt 19/24; tổng 84 lượt không lỗi dịch vụ và 71/71 trích dẫn khớp văn bản corpus. 184 kiểm thử backend đạt. BT20 có p50 5.197 giây, p95 6.553 giây. BT20 đã dùng để chỉnh sửa nên chỉ là đo hồi quy; bộ mới do cùng trợ lý soạn, chưa có người duyệt độc lập. Còn lỗi thiếu điều kiện phụ, chọn câu và truy hồi; chưa nghiệm thu M3. Chi tiết và toàn bộ đáp án tại evals/bt20/NANG_CAP_20261008.md và evals/rag-context/KET_QUA.md.

## 08/10/2026 - Kiểm chứng 60 câu RAG BT20

Ngày 08/10/2026 bổ sung và chạy bộ kiểm chứng RAG BT20 gồm 60 câu đã chốt trước đo, dùng bản sao chính sách đầy đủ và hai tài liệu CX10 mâu thuẫn trong DB/Qdrant tạm. Ollama 0.40.0 chạy qwen3:4b và embeddinggemma:300m trên RTX 3060 Laptop; 60/60 ca hoàn tất không lỗi dịch vụ. Chấm tự động đạt 43/60 (71,7%); 13/46 câu có nguồn bị từ chối. Recall@5 trung bình trên 50 ca gán nguồn đạt 98%; cả 67 quote đều khớp văn bản nhưng chưa chứng minh đúng ngữ nghĩa. Trung vị 4,960 giây, p95 7,521 giây trong lượt tuần tự. Lỗi nổi bật gồm review từ chối sai, chọn câu mất điều kiện, câu mơ hồ bị tự suy chủ đề và lịch sử chứa chỉ dẫn giả ảnh hưởng bước kiểm định. Hai nhãn có hạn chế được ghi riêng; không sửa nhãn/prompt sau đo, chưa có người duyệt độc lập. Chín test evaluator đạt sau sửa metadata keep_alive lấy từ runtime. Chi tiết tại evals/bt20/KET_QUA.md và CHI_TIET_60_CAU.md; chưa nghiệm thu M3.

Khánh phụ trách sửa pipeline và tích hợp chính; nhóm kiểm thử duyệt nhãn, đối chiếu 17 ca chưa đạt và chuẩn bị bộ câu mới độc lập; nhóm báo cáo tổng hợp bảng và bằng chứng. Tiếp theo ưu tiên review, giữ điều kiện nguồn và hỏi làm rõ; không tắt kiểm định để tăng điểm.

## 08/10/2026 - Giao diện sáng và tối

08/10/2026: bổ sung giao diện sáng/tối cho toàn bộ khu vực admin/nhân viên. Nút đổi trên sidebar và mobile; lưu lựa chọn bằng localStorage, mặc định theo hệ thống khi chưa chọn. Đổi theme giữ bản nháp; khi storage bị chặn vẫn đổi được trong phiên. Build và kiểm thử trình duyệt desktop/mobile đạt; đã xem sáu trang nội bộ trên API với DB thử. Runner: frontend/tests/theme.cjs. Phạm vi chưa gồm trang đăng nhập và customer /chat.

## 08/10/2026 - Inbox theo bố cục Chatwoot

Ngày 08/10/2026 cập nhật Inbox theo bố cục tham khảo Chatwoot, dựng bằng React hiện có: thanh điều hướng sáng, danh sách hội thoại, vùng chat và hồ sơ khách có thể thu gọn. Bộ lọc Tất cả, Của tôi và Chưa nhận được áp dụng ở backend trước khi đếm và phân trang; người phụ trách lấy từ phiên đăng nhập. Ticket/SLA chuyển sang cột thông tin, hỗ trợ mở đơn hàng theo khách. Enter gửi tin, Shift+Enter xuống dòng; ô nhập tự tăng chiều cao tối đa 160 px. Kiểm chứng 30 test Inbox/xác thực, build frontend, kiểm thử ô nhập và trình duyệt với API thật trên DB tạm; sáu chiều rộng 320–1536 px không tràn ngang. Đã kiểm tra giữ bản nháp khi lỗi, phân quyền, tiếp nhận và hoàn tất ticket. Không gọi Ollama hoặc Telegram thật trong lượt QA giao diện này.

Khánh giữ phần thiết kế/tích hợp chính. Nhóm kiểm thử đối chiếu admin/agent, bộ lọc, bản nháp và mobile; nhóm báo cáo lưu ảnh. Bằng chứng cục bộ: output/inbox-redesign/result.json và desktop-final.png. Không sao chép frontend Chatwoot; không đổi schema hoặc mở thêm quyền xem hội thoại.

## 08/10/2026 - Ô soạn tin khách hàng và nhân viên

- [x] Enter gửi qua form hiện có; Shift+Enter xuống dòng. Không gửi khi IME đang chọn ký tự, phím lặp hoặc nút gửi bị khóa.
- [x] Ô nhập tự tăng/thu theo nội dung và độ rộng, tối đa 160 px rồi cuộn; giữ giới hạn 4.000 ký tự và xử lý gửi/lỗi hiện có.
- [x] Frontend build đạt; kiểm thử trình duyệt component chung đạt cho Enter, Shift+Enter, IME, phím lặp, nội dung trắng, nút khóa, tăng/thu/giới hạn chiều cao và tự ngắt dòng. Runner: frontend/tests/message-input.cjs, dùng Playwright có sẵn qua NODE_PATH; không thêm dependency. Chưa chạy lại toàn luồng API ở mốc UI này.

## 07/10/2026 - Chuẩn bị cấu hình triển khai HTTPS

Ngày 07/10/2026 bổ sung bộ cấu hình triển khai Windows một máy: Caddy HTTPS, frontend/API cùng origin, Uvicorn loopback một worker, Ollama nội bộ và dữ liệu production tách riêng. Script dùng file môi trường được chọn, chặn cấu hình development/HTTP và không chạy reload. Proxy chặn tài liệu API công khai, đặt header bảo vệ, giới hạn body 12 MB và không phục vụ thư mục mã nguồn. Một kiểm thử launcher đạt; Caddy v2.11.7 qua validate sau kiểm tra SHA-512. Smoke HTTPS local dùng DB/CA riêng đã kiểm chứng chứng chỉ, frontend, cookie Secure/HttpOnly, CSRF, logout, chặn file riêng tư, giả mạo IP và chuyển HTTP sang HTTPS. Chưa đổi DNS, mở firewall, triển khai cloud hoặc cài Windows Service; chưa đo GPU/model thật, tải bền hay diễn tập RPO/RTO. Cấu hình SMTP và Telegram giữ trống/tắt cho đến khi nghiệm thu riêng.

Tài liệu: docs/DEPLOYMENT.md. Mốc kế tiếp: chốt máy và tên miền, cấu hình DNS/firewall rồi nghiệm thu trên thiết bị thứ hai; chưa coi M7 hoàn tất. Khánh giữ cấu hình/tích hợp chính; nhóm kiểm thử đối chiếu kịch bản triển khai, nhóm báo cáo lưu bằng chứng.


## 07/10/2026 - Xác minh email và khôi phục mật khẩu khách hàng

Ngày 07/10/2026 triển khai xác minh email và khôi phục mật khẩu khách hàng qua SMTP dùng TLS. Schema v9 thêm cờ email_verified và bảng token email; tài khoản cũ mặc định chưa xác minh. Liên kết xác minh có hạn 60 phút, yêu cầu mật khẩu hiện tại; liên kết đặt lại mật khẩu có hạn 15 phút, chỉ cấp cho email đã xác minh. Token chỉ lưu hash, dùng một lần; đổi hoặc đặt lại mật khẩu thu hồi mọi phiên và token của tài khoản. Không tự ghép hồ sơ hoặc cấp quyền đơn hàng theo email.

Bộ backend đạt 172 kiểm thử, frontend build đạt. Kiểm tra trình duyệt bằng DB và hộp thư thử cục bộ xác nhận đăng ký, xác minh từ phiên khác, từ chối mật khẩu sai, quên mật khẩu, đặt lại mật khẩu, thu hồi phiên cũ và chặn dùng lại liên kết; giao diện 390 px không tràn ngang. Kiểm thử còn bao gồm reset đồng thời, token hết hạn/sai mục đích, giới hạn gửi theo IP và tài khoản, TLS, lỗi SMTP không lộ bí mật, migration giữ dữ liệu và backup thu hồi token. Chưa cấu hình hoặc gửi thử tới hộp thư thật. Gửi email hiện dùng tác vụ nền trong tiến trình, chưa có hàng gửi bền hoặc retry tự động; cần kiểm chứng giao thư sau khi cấu hình SMTP trước nghiệm thu vận hành.

Khánh tiếp tục phụ trách tích hợp chính và cấu hình hộp thư; nhóm kiểm thử chạy độc lập bằng email thật sau cấu hình, kiểm tra thư rác và thiết bị khác; nhóm báo cáo lưu bằng chứng giao thư. Mốc kế tiếp: cấu hình SMTP và nghiệm thu email thật; sau đó trở lại kiểm chứng RAG toàn luồng/Telegram.


## 03/10/2026 - Tài khoản khách hàng và giao diện đăng nhập

Ngày 03/10/2026 bổ sung tài khoản khách hàng bằng email và mật khẩu tự quản lý, tách khỏi tài khoản nhân viên. Schema v8 thêm CustomerAccount và CustomerSession; hỗ trợ đăng ký, đăng nhập nhiều thiết bị, lịch sử theo tài khoản và đổi mật khẩu thu hồi mọi phiên. Mật khẩu lưu PBKDF2-SHA256; cookie HttpOnly có hạn 24 giờ. Email chưa xác minh, chưa có khôi phục qua email; không tự ghép lịch sử khách vãng lai hoặc cấp quyền xem đơn theo email.

Giao diện đăng nhập khách hàng và nhân viên dùng bố cục hai cột, font Inter và form thích ứng màn hình nhỏ; có hiện/ẩn mật khẩu, đăng ký và khách vãng lai. Bộ backend đạt 165 kiểm thử; frontend build thành công. Kiểm tra trình duyệt với DB tạm xác nhận đăng ký, đăng nhập hai thiết bị, lịch sử, đổi mật khẩu thu hồi phiên, tải lại giữ phiên, kiểm tra mật khẩu nhập lại và widget nhúng. Kiểm tra chiều rộng 320–1536 px không tràn ngang. Chat thử dùng lời chào xử lý tại chỗ, không phải phép đo chất lượng hoặc độ trễ Ollama/RAG. Các kết quả này không thay nghiệm thu bot Telegram thật, nhãn RAG độc lập hoặc khả năng chịu tải triển khai.

Khánh giữ phát triển và tích hợp chính. Nhóm kiểm thử bổ sung ca độc lập cho tài khoản, lịch sử và quyền đơn; nhóm báo cáo đối chiếu bằng chứng và cập nhật hồ sơ. Mốc tiếp theo: kiểm thử độc lập, sau đó bổ sung xác minh email/khôi phục mật khẩu khi chốt dịch vụ gửi email.


## 01/10/2026 - Tự phục hồi kiểm tra kết nối Telegram

Worker thử lại getMe/getWebhookInfo sau 5 giây khi lỗi mạng hoặc HTTP 5xx, thay vì dừng hẳn đến khi khởi động lại API. Trạng thái error giữ trong lúc chờ; Event cho dừng khoảng chờ khi tắt API. Token sai, bot không hợp lệ và webhook đang hoạt động vẫn dừng để xử lý cấu hình. Chỉ phục hồi hàng gửi và bắt đầu polling sau khi xác minh xong; không tự thử lại sendMessage hoặc đổi cấu hình/token.

Hai test mới tái hiện trước sửa; 23 test Telegram đạt trong 6,217 giây sau sửa. Kiểm chứng chuỗi lỗi mạng/503/thành công, dừng trong lúc chờ, không truy cập DB trước xác minh và lỗi cấu hình không retry. DB tạm, transport/model giả lập; chưa gọi bot thật hoặc nghiệm thu M6. Khánh giữ sửa/tích hợp chính; nhóm kiểm thử chuẩn bị và chạy kịch bản bot thật khi có cấu hình. Không đổi schema/UI hoặc chạy lại toàn bộ suite cho thay đổi giới hạn trong khởi động Telegram.

Word đồng bộ 91 đoạn/bảy chương/14 trang; đề cương giữ 10 mục. Renderer thiếu LibreOffice nên xuất qua Word; trang 12 đã xem, 13 trang khác khớp từng pixel với bản trước. git diff --check đạt.

## 01/10/2026 - Phản hồi HTTP Telegram bị gián đoạn

Bắt lỗi giao thức HTTP bằng ngoại lệ chuẩn http.client.HTTPException, chuyển sendMessage thành uncertain thay vì để sending kẹt đến restart. Giữ che token/lỗi thô, chặn tự gửi lại và tiếp tục gửi cho peer khác. Lỗi getUpdates đi qua nhánh phục hồi polling đã có; không đổi schema/UI/cấu hình.

Test mới tái hiện IncompleteRead trước sửa; 21 test Telegram đạt trong 5,312 giây sau sửa, có BadStatusLine, không tự gửi lại, không xác nhận sent/SLA khi chưa rõ và không chặn peer khác. DB tạm, model/transport mock; không gọi bot thật. Không chạy lại toàn bộ suite vừa đạt 154 test ở mốc trước vì thay đổi giới hạn trong transport Telegram. Khánh giữ sửa/tích hợp chính; nhóm kiểm thử còn cần chạy kịch bản bot thật, M6 chưa nghiệm thu.

Word đồng bộ 91 đoạn/bảy chương/14 trang, đề cương giữ 10 mục. Renderer thiếu LibreOffice nên xuất bằng Word; đã xem trang 12 thay đổi, 13 trang khác khớp từng pixel với bản trước. git diff --check đạt.

## 01/10/2026 - Xử lý hàng chờ Telegram khi nhận tin lỗi

Lỗi getUpdates trước đây bỏ qua process_next, khiến cả update đã commit bị kẹt. Đã tách lỗi transport/response khỏi xử lý một update trong hàng chờ mỗi vòng; rollback phần nhận lỗi, giữ con trỏ, trạng thái error và khoảng chờ 5 giây. Quy tắc failed/uncertain vẫn chặn gửi lại tự động. Không đổi schema, API, UI hoặc cấu hình thật; lỗi DB/khởi động vẫn cần xử lý riêng.

Test mới tái hiện trước sửa, 20 test Telegram đạt trong 7,243 giây sau sửa; dùng DB tạm và transport/model giả lập. Kiểm tra pending/processing, lỗi mạng/response, con trỏ bền và không trùng tin/ticket. Khánh giữ phần sửa/tích hợp chính; nhóm kiểm thử thực hiện kịch bản bot thật khi có cấu hình, nhóm báo cáo đối chiếu bằng chứng. Chưa nghiệm thu M6, chưa tách worker hoặc đo tải Telegram.

Hồi quy bản cuối: 154 unittest đạt trong 99,759 giây; git diff --check đạt. Word đồng bộ 91 đoạn/bảy chương/14 trang, đề cương giữ 10 mục. Renderer thiếu LibreOffice, xuất bằng Word; đã xem trang 1/12 thay đổi, 12 trang còn lại khớp từng pixel với bản trước. 44 ca M5 vẫn chờ duyệt; không chạy bot/model thật hoặc build lại UI không đổi.

## 26/09/2026 - Gộp phiếu M5 theo phần được giao

CLI app.review_tools thêm --merge để gộp JSON cùng lượt đo, giữ bằng chứng gốc, tên/ghi chú và ca chưa quyết định. Bỏ qua phần hoàn toàn trống, gộp bản trùng đúng nội dung; ca có bất kỳ trường duyệt khác nhau đều báo ID xung đột và không tạo output. Không chọn theo thứ tự file hoặc lấy đa số. Có thể xuất HTML để tiếp tục; phiếu gộp phải chạy --reviews riêng để tính điểm.

Chín test liên quan đạt trong 0,368 giây, gồm hai test mới cho gộp phần riêng, ghi chú chờ, thứ tự đầu vào, xung đột, sai lượt/ID, giữ nguồn và không ghi đè/gọi model. Khánh giữ tích hợp chính, chia ID và đối chiếu xung đột với người duyệt; nhóm kiểm thử chỉ điền phần được giao, nhóm báo cáo dùng summary đã kiểm tra. Cả 44 ca thật còn trống; chưa nghiệm thu M5. Hướng dẫn: evals/tools/README.md. Không thay UI/runtime hoặc chạy lại Ollama.

Đối chiếu ba bộ thật: gộp bản trống không sinh quyết định, HTML khớp template, runtime khớp snapshot. Word khớp 91 đoạn Markdown, bảy chương/14 trang; đề cương giữ 10 mục. Renderer thiếu LibreOffice, xuất qua Word; trang 13 đã kiểm tra, 13 trang còn lại khớp từng pixel với bản trước. git diff --check đạt.

## 26/09/2026 - Giao diện duyệt nhãn M5 offline

Đã có ba file HTML cho 24 ca gốc, tám ca nối tiếp và 12 ca ngữ cảnh; tên, quyết định và ghi chú lưu nháp trong trình duyệt. Chặn quyết định thiếu tên/lý do bác, xuất JSON giữ nguyên bằng chứng số và hash; CLI có thể tạo HTML tiếp tục từ JSON hợp lệ. Nội dung ca hiển thị như văn bản, CSP chặn mạng; không thêm dependency hoặc server.

Bảy test CLI/HTML đạt trong 0,216 giây. QA desktop/mobile 390px trên ba ca giả lập kiểm tra điều hướng, khôi phục nháp, validation, HTML không thực thi và JSON được CLI chấp nhận. Tải Blob trong trình duyệt tích hợp chưa xác nhận; có ô sao chép JSON dự phòng đã kiểm chứng. Runtime không đổi, không chạy lại Ollama hoặc toàn bộ test runtime.

Khánh giữ phần chính: tích hợp, tổng hợp quyết định, xử lý nhãn bị bác và đo lại khi đã chốt. Nhóm kiểm thử dùng biểu mẫu, ghi lý do/bổ sung câu độc lập; nhóm báo cáo đối chiếu bằng chứng và mẫu số. Cả 44 ca thật vẫn chờ người duyệt; chưa nghiệm thu M5. Hướng dẫn: evals/tools/README.md.

Báo cáo Word khớp 91 đoạn Markdown, bảy chương/14 trang; đề cương giữ 10 mục. Renderer thiếu LibreOffice nên xuất qua Word; trang 13 đã xem, 13 trang khác giống từng pixel với bản trước. Ba snapshot runtime khớp mã hiện tại, các biểu mẫu HTML khớp template và 44 phiếu JSON vẫn chưa duyệt; git diff --check đạt. Đã dừng server và đóng tab QA riêng.

## 26/09/2026 - Phiếu duyệt nhãn M5

Thêm CLI app.review_tools tạo phiếu hoặc báo cáo từ lượt đo hoàn tất, ràng buộc hash và giữ nguyên bằng chứng. Kiểm tra manifest/kết quả/summary/điểm đã lưu; bác sửa case, sai lượt, ID trùng, kiểu dữ liệu sai, quyết định thiếu người chấm và ghi đè output. Nhãn được duyệt mới vào tỷ lệ; lỗi vẫn nằm trong mẫu số đó, nhãn bác/chờ duyệt ghi riêng; chưa duyệt thì tỷ lệ null. Tên người chấm tự khai, chưa có xác thực hoặc chấm mù.

Đã tạo 44 phiếu trống cho bộ gốc/nối tiếp/ngữ cảnh ở evals/tools/reviews; toàn bộ còn chờ duyệt. Năm test mới đạt trong 0,078 giây; kiểm chứng CLI với lượt đo thật đã lưu, không gọi model hoặc sửa benchmark. Runtime khớp snapshot trước, không chạy lại bộ 144 test runtime. Khánh giữ tích hợp/điều phối và xử lý kết quả; nhóm kiểm thử duyệt nhãn, ghi lý do bác và chuẩn bị bộ độc lập; nhóm báo cáo cập nhật số liệu có mẫu số rõ. Chưa nghiệm thu M5 hoặc thay các điểm nhãn nháp đã công bố.

Báo cáo Word đồng bộ 91 đoạn/bảy chương, giữ 14 trang; xuất qua Word do renderer thiếu LibreOffice. Đã xem trang 13 thay đổi, 13 trang còn lại giống từng pixel với bản trước; đề cương giữ 10 mục. git diff --check đạt.

## 26/09/2026 - Giảm chuyển giao nhầm và chuẩn hóa đầu vào model

Bỏ qua riêng cụm tiền tệ, mẫu phủ định gặp người rõ ở đầu mệnh đề và mẫu hỏi chính sách hoàn tiền; khiếu nại/yêu cầu khác trong cùng tin vẫn chuyển nhân viên. Quy tắc chạy đồng bộ chung cho widget/nghiệp vụ; tin trung tính không vượt giới hạn AI, handoff thật vẫn đi khi AI bận. Đầu vào bộ chọn được chuẩn hóa NFC sau khi bộ biên phát hiện model hiểu sai dấu tách; văn bản lưu/tóm tắt giữ nguyên. Không đổi schema/quyền hoặc thêm lời gọi model.

Ba test mới và mở rộng kiểm tra NFC/văn bản gốc; bản cuối đạt 144 unittest trong 49,188 giây, model/transport được mock. Đo cuối bằng Ollama thật đạt 24/24 bộ gốc, 8/8 bộ nối tiếp, 10/12 bộ ngữ cảnh mới; 25 lời gọi selector, không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. Lưu cả lượt trước NFC (9/12 bộ biên) và bản cuối ở evals/tools/runs/handoff-*. RAG giả lập, nhãn chưa người duyệt; hai ca policy-free-form và negation-prefixed vẫn nhận nhầm, chưa nghiệm thu M5. Khánh giữ phần tích hợp/sửa luồng chính; nhóm kiểm thử duyệt nhãn và bổ sung câu độc lập, nhóm báo cáo đối chiếu số liệu.

Báo cáo Word đồng bộ 91 đoạn/bảy chương, giữ 14 trang sau rút gọn đoạn kết quả. Renderer thiếu LibreOffice; xuất bằng Word, kiểm tra trang 13 thay đổi và xác nhận 13 trang khác giống từng pixel với bản trước. DeCuong.md giữ 10 mục; snapshot nguồn và số liệu bản cuối đã đối chiếu, git diff --check đạt.

## 26/09/2026 - Hỏi nối tiếp về đơn hàng M5

Tin không nêu mã nhưng nhắc rõ đơn đó/này/ấy/vừa nêu/ở trên được đối chiếu với mã khách đã gửi trong bốn tin khách/AI gần nhất của cùng hội thoại. Mã hiện tại ưu tiên; nhiều mã lịch sử yêu cầu làm rõ; mã AI nêu không được dùng. Tin mới có DH/ORD sai định dạng không âm thầm chọn mã cũ. Trace nội bộ đánh dấu nguồn history; schema vẫn khóa một mã, quyền hiện tại kiểm tra lại khi thực thi, tool muộn tiếp tục bị chặn. Chưa suy luận tham chiếu tự do hoặc lịch sử dài.

Bốn test mới và mở rộng kiểm thử tranh chấp trên cả mã hiện tại/lịch sử; 141 unittest đạt trong 49,555 giây. Ollama thật đạt 21/24 so với 18/24 trước đó, thêm ba ca nối tiếp đạt; tám ca biên bổ sung đạt. Tổng 22 lời gọi selector mới, không lỗi provider hoặc lộ marker bị cấm/sửa đơn quan sát được. RAG giả lập; nhãn chưa người duyệt, đây là tập phát triển/regression. Còn ba ca refund-policy, no-human-needed, currency-policy nhận nhầm do từ khóa. Bằng chứng tại evals/tools/runs/history-reference-20260926 và history-boundaries-20260926. Khánh phụ trách tích hợp/luồng chính; nhóm kiểm thử duyệt nhãn và bổ sung câu độc lập; chưa nghiệm thu M5.

Báo cáo Word đã đồng bộ 91 đoạn/bảy chương, giữ 14 trang; xuất qua Word do renderer thiếu LibreOffice. Đã kiểm tra trang 13 thay đổi, 13 trang khác giống từng pixel với bản trước. Đề cương giữ 10 mục; git diff --check đạt. Không đổi schema/UI hoặc nghiệm thu bot thật.

## 26/09/2026 - Đánh giá điều phối M5 bằng model thật

Thêm CLI app.evaluate_tools và 24 ca nhãn nháp trên SQLite trong bộ nhớ, chạy bộ chọn Ollama/quyền thật, chỉ giả lập nhánh RAG. Baseline 17/24; thêm một câu prompt ưu tiên handoff cho yêu cầu hỗn hợp tra cứu và hủy/đổi đơn đạt 18/24. Tổng 30 lời gọi bộ chọn thật, không lỗi provider, không quan sát lộ marker mã vận đơn bị cấm hoặc sửa đơn. Lưu riêng manifest nguồn/model/dataset và kết quả hai lượt tại evals/tools/runs; đây là tập phát triển đã dùng chỉnh prompt, chưa nghiệm thu độc lập.

Ba test runner mới; bộ đầy đủ 137 unittest đạt trước chỉnh prompt (83,449 giây), 10 test công cụ/runner chạy lại trên prompt cuối đạt (1,271 giây, transport mock). Kiểm tra CLI từ chối output đã tồn tại và giữ nguyên hash kết quả. Sáu ca chưa đạt thuộc quy tắc handoff ở phủ định/chính sách và hỏi nối tiếp không nêu mã; nhãn chưa được người duyệt, chưa đánh giá RAG/tóm tắt/bot thật. Khánh giữ phần sửa luồng chính, tích hợp và đo lại; nhóm kiểm thử duyệt nhãn, bổ sung ca độc lập; nhóm báo cáo đối chiếu số liệu. Chi tiết tại [evals/tools](../evals/tools/README.md).

Báo cáo Word đồng bộ 91 đoạn với Markdown, giữ bảy chương/14 trang. Renderer đóng gói thiếu LibreOffice; xuất bằng Word và kiểm tra trang 13 thay đổi, 13 trang còn lại giống từng pixel với bản đã duyệt bố cục trước đó. DeCuong.md giữ đủ 10 mục; git diff --check đạt.

## 26/09/2026 - Phân trang lịch sử widget

Widget đã đọc được lịch sử ngoài 200 tin: mặc định 50/tối đa 100 tin mỗi request, before phải thuộc hội thoại của cookie còn hiệu lực. Giữ bộ lọc dữ liệu công khai, không trả ticket/ghi chú/trace/ID nguồn nội bộ. Mọi snapshot trả message_page; history_truncated giữ tương thích với has_more. Giao diện giữ bản nháp khi đổi trang/lỗi, polling trang cũ theo mốc, quay về mới nhất sau gửi/handoff/cấp quyền tra đơn; hết phiên xóa lịch sử đang hiển thị.

Bốn test mới kiểm tra 223 tin trùng thời gian, tin mới giữa các trang, snapshot sau gửi, mốc khác phiên, hết hạn/thu hồi, hội thoại đóng, dữ liệu riêng tư và giới hạn. Tổng 134 unittest đạt trong 136,589 giây; Vite build đạt. QA trình duyệt trên DB tạm kiểm chứng năm trang, trích dẫn tin cũ, lỗi 503/thử lại giữ bản nháp, gửi từ trang cũ, hết phiên và desktop/mobile 390px không tràn ngang. Không gọi model/Telegram thật, không thay schema; chưa nghiệm thu tải bền hoặc M4/M7 toàn bộ. Hợp đồng mới tại [API.md](API.md#snapshot-widget).

## 25/09/2026 - Phân trang lịch sử tin nhắn Inbox

Chi tiết Inbox mặc định 50/tối đa 100 tin, phân trang bằng ID mốc trong cùng hội thoại và cặp created_at/id, không tải toàn bộ lịch sử vào bộ nhớ. Giao diện có Tin cũ hơn, Tin mới hơn cho trang lịch sử trước và Về tin mới nhất; giữ bản nháp/ghi chú, gửi xong về mới nhất, yêu cầu đọc trang mới nhất trước khi hoàn tất. Polling trang cũ giữ mốc và cập nhật trace/delivery; cửa sổ mới nhất vẫn thay đổi khi có tin mới.

Ba test mới kiểm tra 123 tin trùng thời gian, tin đến sau mốc, không mất/trùng trang, cách ly cursor, trace cập nhật, trang rỗng, giới hạn và quyền. Tổng 130 unittest đạt trong 95,222 giây, Vite build đạt. QA trình duyệt trên DB tạm kiểm chứng ba trang 50/50/23 tin, polling khi có tin mới, giữ bản nháp, gửi từ trang cũ, hội thoại rỗng, khóa hoàn tất ở trang cũ và mobile 390px không tràn ngang. Không gọi Ollama/Telegram thật; ticket/SLA chưa phân trang, widget vẫn 200 tin. Hợp đồng thay đổi tại [API.md](API.md#phân-trang-lịch-sử-inbox); chưa nghiệm thu tải bền M7.

## 25/09/2026 - Khôi phục mật khẩu local

Đã có `python -m app.reset_password USERNAME --env-file .env` cho tài khoản đã tồn tại: nhập mật khẩu ẩn, kiểm tra 12-128 ký tự và khác mật khẩu cũ; cập nhật hash và thu hồi mọi phiên của tài khoản trong cùng transaction. Giữ nguyên quyền/trạng thái hoạt động, chặn đăng nhập đang dùng hash cũ và rollback nếu thu hồi phiên lỗi. `--env-file` đọc trước khi tạo engine, biến môi trường có sẵn được ưu tiên. Không sửa tài khoản thật, không thêm endpoint công khai hoặc migration.

Sáu test mới dùng DB tạm kiểm tra vòng đăng nhập, tài khoản vô hiệu, đầu vào lỗi/hủy, rollback, đăng nhập đồng thời và cấu hình DB qua subprocess. Toàn bộ 127 unittest đạt trong 52,458 giây; CLI help và diff check đạt. Hướng dẫn tại [OPERATIONS.md](OPERATIONS.md#khôi-phục-mật-khẩu-nhân-viên). Chưa có reset qua email/OTP hoặc audit quản trị; M3/M5/M6/M7 vẫn chờ nghiệm thu riêng.

## 25/09/2026 - Giữ model trong GPU

25/09/2026 (mốc con M7 độ trễ Ollama): giữ hai model 5 phút thay vì dỡ sau mỗi lời gọi; Ollama đã dùng GPU trước sửa. RTX 3060 6 GiB xác nhận cả hai model 100% GPU, tổng 4,16 GiB. Ba lượt cũ 15,207-16,066 giây; lượt mới đầu 10,704 giây, hai lượt đã nạp 3,351-3,719 giây. Smoke HTTP thật đạt, câu hỏi 3,675 giây; 15 test RAG đạt. Giữ model/prompt/context/kiểm định; một câu hỏi lặp chưa chứng minh chất lượng M3 hoặc tải bền M7. Bằng chứng tại evals/ollama.

Script khởi động ưu tiên Ollama đã cài, không mở trùng dịch vụ, cho phép hai model cùng nạp khi khởi động mới. 15 test RAG đạt trong 6,471 giây; thêm kiểm tra payload giữ 5m và không đổi tham số generation. Runner từ chối ghi đè kết quả cũ. Không sửa .env hoặc dữ liệu người dùng; không đổi UI/schema.

Kiểm tra cuối: báo cáo Word khớp 87 đoạn Markdown, bảy chương/13 trang. Xuất bằng Word do thiếu LibreOffice đóng gói; trang 1/13 đã kiểm tra trực quan, 11 trang còn lại khớp từng pixel với bản trước. git diff --check đạt.

## 22/09/2026 - Phân trang Inbox và tìm kiếm toàn danh sách

- [x] API mặc định 25/tối đa 100 dòng, kiểm tra offset/limit/q, trả total và has_more; sắp ngày tạo giảm dần/ID tăng dần. Không tìm kiếm/lọc SLA thì SQL lấy đúng trang trước tính SLA.
- [x] Tìm kiếm tiếng Việt không phân biệt hoa/thường và lọc SLA trước chia trang, quét theo lô 200 hội thoại. Ký tự %/_ không thành wildcard; không lọc riêng trên trang hiện tại.
- [x] UI trước/sau, reset trang khi đổi bộ lọc, lùi về trang hợp lệ khi tổng giảm; giữ hội thoại và bản nháp, mở hội thoại ngoài trang từ hồ sơ khách. Thẻ số phân biệt tổng với số trên trang.
- [x] Ba test mới; 120 unittest đạt trong 64,141 giây. Test HTTP biên offset chạy lại đạt sau chặn số vượt 32 bit; Vite build đạt. Smoke hai client/31 hội thoại kiểm tra API và retry/tranh chấp, không dùng làm benchmark hiệu năng.
- [x] QA dữ liệu tạm: ba trang, tìm khách ngoài trang đầu, kết hợp SLA/rỗng, giữ bản nháp, mở từ hồ sơ khách, tiếp nhận và trả lời. Desktop 1440px/mobile 390px, phân trang bằng Enter, không tràn ngang hoặc lỗi console.

Giới hạn: tìm kiếm/SLA còn quét tập phù hợp status/priority để đếm tổng; dữ liệu sống có thể dịch trang offset. API chi tiết vẫn trả toàn lịch sử. Chưa chạy model/Telegram thật hoặc nghiệm thu tải bền/cloud; không thay schema.

Kiểm tra cuối: git diff --check đạt. Báo cáo Word khớp 86 đoạn Markdown, bảy chương/13 trang; xuất bằng Word do thiếu LibreOffice đóng gói. Trang 6/12/13 đã kiểm tra trực quan, mười trang còn lại khớp từng pixel với bản đã kiểm tra. Tab QA riêng đã đóng.

## 22/09/2026 - Lưu bền thông báo handoff Telegram

- [x] Tái hiện worker dừng sau commit handoff khiến trạng thái/ticket đã lưu nhưng thông báo cho khách bị mất.
- [x] Lưu thông báo Telegram cùng transaction với trạng thái/ticket; bỏ tạo thông báo riêng trong adapter. Áp dụng cả handoff do lỗi gửi/phục hồi, không đổi schema v7.
- [x] Hai test mới: gián đoạn và mở lại Session, nhận lại update, nhắn thêm khi chờ, rollback đồng thời, yêu cầu mới sau giải quyết. Kiểm tra phục hồi gửi lặp không tạo thông báo trùng.
- [x] Tổng 117 unittest đạt trong 91,870 giây, gồm 19 test Telegram; transport/model Telegram được mock trên dữ liệu tạm.

Lỗi gửi trước đó vẫn chặn thông báo trong hàng chờ; người phụ trách cần gửi lại/bỏ qua. Không tự bù thông báo thiếu trong dữ liệu cũ. Chưa kiểm chứng bot thật hoặc nghiệm thu M6.

Kiểm tra cuối: git diff --check đạt. Báo cáo Word khớp 85 đoạn Markdown, bảy chương/13 trang; xuất bằng Word do thiếu LibreOffice đóng gói. Trang 6/12 đã kiểm tra trực quan, 11 trang còn lại khớp từng pixel với bản đã kiểm tra.

## 22/09/2026 - Giữ đủ file khi sao lưu

- [x] Tái hiện backup bỏ mọi file tên .lock trong tài liệu/thư mục con nhưng vẫn báo thành công; verify không phát hiện thay đổi các file bị bỏ qua.
- [x] Giới hạn ngoại lệ đúng file thường .lock ở gốc Qdrant trong create/verify/restore; các file cùng tên khác vào manifest SHA-256 và được khôi phục nguyên vẹn.
- [x] Hai test mới thất bại trước sửa, đạt sau sửa; kiểm tra file nguyên vẹn, khóa runtime không sao chép, file bị sửa/thêm bị từ chối trước restore và nguồn giữ nguyên.
- [x] Chín test backup đạt, gồm CLI tạo/kiểm tra/khôi phục và mở lại Qdrant embedded thật. Không thay schema/format manifest, UI hoặc dữ liệu người dùng.

Bản sao cũ thiếu file không tự phục hồi được; đã ghi hướng dẫn tạo lại từ nguồn đầy đủ. Phạm vi vẫn là sao lưu offline, chưa nghiệm thu M7 hoặc phục hồi bot thật.

Kiểm tra cuối: chín test backup đạt trong 9,407 giây; git diff --check đạt. Báo cáo Word khớp 84 đoạn Markdown, bảy chương/13 trang; xuất bằng Word do thiếu LibreOffice đóng gói. Trang 12 thay đổi đã kiểm tra trực quan, 12 trang còn lại khớp từng pixel với bản đã kiểm tra.

## 22/09/2026 - Handoff đúng ranh giới từ và Unicode

- [x] Tái hiện tệp PDF bị nhầm thành khiếu nại tệ; gặp xuống dòng nhân viên/dấu NFD bị bỏ sót, widget trả 429 khi AI bận.
- [x] Chuẩn hóa NFC/casefold/khoảng trắng riêng cho so khớp, dùng ranh giới từ Unicode; giữ nguyên tin và trích đoạn ticket, bộ từ khóa/nhãn/ưu tiên không đổi.
- [x] Năm test mới: biến thể NFC/NFD, hoa/thường, năm loại khoảng trắng trên bảy từ khóa, từ chứa từ khóa, widget AI bận/retry/lưu nguyên văn, câu hỏi tệp không tạo ticket, Telegram receipt trùng không tạo thêm ticket.
- [x] Test tái hiện thất bại trước sửa; tổng 113 unittest đạt trong 78,586 giây sau sửa. Không thay UI hoặc chạy model/Telegram thật.

Giới hạn: chưa hiểu phủ định/trích dẫn/ngữ cảnh hoặc tiếng Việt không dấu; không dùng kết quả này làm độ chính xác sentiment/handoff M5. Trình phân loại vẫn trả negative cho các từ khóa đang có, kể cả yêu cầu gặp người thật trung tính.

Báo cáo Word đồng bộ 83 đoạn với Markdown, giữ bảy chương/13 trang. Xuất bằng Word do renderer đóng gói thiếu LibreOffice; đã kiểm tra trang 6/12/13 thay đổi, mười trang còn lại khớp từng pixel với bản đã kiểm tra. git diff --check đạt.

## 22/09/2026 - Chặn nhận nhầm mã đơn

- [x] Tái hiện lỗi DH12345-EXTRA/x-DH12345 bị nhận thành DH12345, Unicode IGNORECASE nhận chữ ngoài ASCII và mã quá 64 ký tự vẫn qua bộ nhận diện.
- [x] Sửa ORDER_PATTERN dùng ranh giới chữ/số/gạch nối/gạch dưới, tổng 6-64 ký tự và case-insensitive chỉ trong nhóm ASCII; không đổi kiểm tra quyền chủ đơn/widget.
- [x] Hai test nhận diện và một test orchestration mới: mã hợp lệ, dấu câu, hoa/thường, biên độ dài, Unicode và mã ghép; xác nhận mã sai không gọi selector/lookup hoặc lộ vận đơn. Test tái hiện thất bại trước sửa, đạt sau sửa.
- [x] Toàn bộ 108 unittest đạt trong 83,904 giây. UI không đổi; không build lại hoặc gọi model thật.

Không có mã hợp lệ vẫn đi RAG như trước, chưa có thông báo riêng cho mã sai. Không nhận đơn từ lịch sử hoặc tự sửa mã khách nhập. Đây là sửa nhận diện đầu vào, không phải kết quả đánh giá ngữ nghĩa M5/M3.

Báo cáo Word đồng bộ 82 đoạn với Markdown, giữ bảy chương/12 trang. Xuất bằng Word do renderer đóng gói thiếu LibreOffice; trang 6/12 đã kiểm tra trực quan, mười trang còn lại khớp từng pixel với bản đã duyệt bố cục trước đó. git diff --check đạt.

## 22/09/2026 - Nhật ký công cụ trong Inbox

- [x] Hiển thị trạng thái, mã đơn, hành động và kết quả dưới tin khách bằng details/summary; mặc định thu gọn, giữ mở qua polling, dùng được bàn phím.
- [x] Phân biệt pending/gián đoạn, lỗi provider, bỏ qua lượt cũ, nhiều mã đơn và nhánh RAG; trạng thái lạ có fallback, tin thiếu trace không hiện nhật ký. Không render JSON thô hoặc cho chạy lại công cụ.
- [x] Bổ sung assertion API chi tiết giữ trace, widget không nhận trace trong test sẵn có; sáu test công cụ đạt trong 3,033 giây, Vite build đạt.
- [x] QA trên bản build và DB tạm: chín trace gồm sáu trạng thái hiện có, hai kết quả lookup, handoff và trạng thái lạ; một tin không trace. Desktop 1440px/mobile 390px, mở/đóng Enter, giữ mở sau polling, không tràn ngang.

Không đổi API/schema/quyền hoặc pipeline RAG. Không chạy lại benchmark/model thật; kết quả này kiểm chứng hiển thị nhật ký, chưa nghiệm thu chất lượng M5. Khánh tiếp tục phụ trách tích hợp chính; nhóm kiểm thử có thể dùng docs/DEMO.md để đối chiếu nhật ký với kết quả hỗ trợ.

Báo cáo Word ngày 22/09 đồng bộ 81 đoạn với Markdown, đủ bảy chương/12 trang; xuất bằng Word và kiểm tra toàn bộ ảnh trang vì renderer đóng gói thiếu LibreOffice. git diff --check đạt; tab và server QA riêng đã đóng.

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

## Năm trang quản lý theo giao diện — 18/09/2026

- [x] Mở đủ Tổng quan, Khách hàng, Đơn hàng, Phân tích, Cài đặt; sidebar xanh đậm/teal theo mockup, điều hướng mobile đủ bảy mục.
- [x] Tổng hợp dữ liệu thật, kỳ 7/30/90 ngày UTC và SLA theo ticket tạo trong kỳ; tỷ lệ chỉ tính ticket đã phản hồi, không có mẫu trả null.
- [x] Tìm kiếm/phân trang khách và đơn, hồ sơ lịch sử/mở Inbox, admin tạo/sửa có đối chiếu giá trị cũ; không đổi chủ đơn hoặc xóa dữ liệu.
- [x] Cài đặt cho admin cấp tài khoản, mỗi người đổi mật khẩu cũ và thu hồi mọi phiên riêng. Kênh/SLA chưa tùy biến được ghi rõ.
- [x] 66 unittest đạt trong 23,627 giây; Vite build đạt. QA trình duyệt trên store riêng: CRUD trong phạm vi, phân trang, mở đúng hội thoại, báo cáo, tạo agent/đăng nhập/quyền, đổi mật khẩu. Desktop/mobile 390px không tràn ngang toàn trang.
- [x] Cập nhật README/demo, hợp đồng 42 method/path, thiết kế, quyết định, roadmap, đề cương và báo cáo bảy chương. Word mười trang khớp Markdown, kiểm tra đủ trang; xuất bằng Word/Poppler vì renderer thiếu LibreOffice trên Windows.

Giới hạn: đơn nội bộ mô phỏng, chưa tích hợp vận chuyển/thanh toán; không có xóa/gộp khách, reset mật khẩu người khác, khóa tài khoản UI hoặc audit quản trị. Tổng hợp chưa đo tải lớn, SLA/kênh chưa chỉnh được. M3 chờ duyệt; không đổi RAG, không chạy lại benchmark. Tiếp tục đánh giá M5/xác minh khách/kênh thứ hai theo roadmap.

## Quyền tra đơn cho phiên widget ngày 21/09/2026

- [x] Admin cấp/thu hồi quyền từng đơn, mã chỉ hiển thị lúc cấp, hash trong DB, hết hạn sau 15 phút.
- [x] Biểu mẫu widget riêng, chống CSRF và giới hạn thử, không chuyển mã vào Message/LLM hoặc gộp khách.
- [x] Quyền chỉ đúng đơn/phiên, kiểm tra lại khi thực thi tool; thu hồi, đổi chủ, hết hạn và kết thúc phiên chặn lượt tra mới; giữ handoff.
- [x] Migration v6 cộng bảng, bảy test mới; tổng 73 unittest/build đạt.
- [x] Cập nhật hợp đồng API, thiết kế, đề cương và báo cáo tiến độ.

Giới hạn: admin xác minh và giao mã qua kênh tin cậy ngoài hệ thống; chưa OTP email/SMS, đăng nhập khách hoặc audit đầy đủ. Kênh thứ hai chưa kết nối, M3 chưa có người chấm. Hướng dẫn và kiểm chứng: docs/ORDER_ACCESS.md.

## 21/09/2026 - Adapter Telegram, chờ bot thật

- [x] Polling opt-in, kiểm tra bot/webhook; không xóa webhook hoặc lộ token.
- [x] Migration v7, danh tính bot/người dùng, update/con trỏ bền, chống nhận trùng và phục hồi sau gián đoạn.
- [x] RAG/handoff dùng chung; chặn AI lỗi thời, chuyển nhân viên khi gửi lỗi, giữ thứ tự theo người nhận.
- [x] Nhật ký pending/sending/sent/failed/uncertain/skipped; quyền retry/skip trong Inbox, UUID tin nhân viên, SLA theo xác nhận Telegram.
- [x] 16 test Telegram; tổng 89 unittest đạt trong 32,999 giây, frontend build đạt. Model/transport được mock trong nhóm Telegram.
- [ ] Bot thật: hai người dùng, RAG, /human, phản hồi nhân viên, đóng/nhắn lại và phục hồi gián đoạn.
- [ ] Nghiệm thu M6, tải đồng thời, worker có lease/queue và triển khai thực tế.

Cấu hình, demo và giới hạn: docs/TELEGRAM.md. Người dùng vẫn phụ trách kiến trúc/tích hợp chính; bộ phận kiểm thử có thể chuẩn bị kịch bản và lưu bằng chứng bot thật. Không thay người duyệt nhãn/đáp án M3.

QA trình duyệt trên DB/vector riêng xác nhận cảnh báo nguy cơ trùng, gửi lại chuyển pending, bỏ qua giữ lịch sử, phản hồi nhân viên chờ gửi khi bot tắt và Cài đặt báo chưa kết nối. Desktop và khung mobile 390 pixel đã kiểm tra trực quan, không tràn ngang; không gửi tin ra Telegram thật.

## 21/09/2026 - Sao lưu và khôi phục local

- [x] CLI create/verify/restore, cấu hình env rõ ràng, chỉ SQLite schema v7.
- [x] Snapshot SQLite bằng API backup, sao chép Qdrant/tài liệu offline, manifest SHA-256; chặn nguồn/đích lồng nhau, symlink/junction và ghi đè.
- [x] Khôi phục vào thư mục mới, thu hồi phiên staff/widget và quyền truy cập đơn; giữ nguyên nguồn và bản sao.
- [x] Bảy kiểm thử, gồm Qdrant thật sau khôi phục, dữ liệu hỏng/thiếu/thừa, lỗi sao chép và CLI không sao chép token.
- [ ] Diễn tập trên môi trường triển khai, phục hồi Telegram thật, lịch sao lưu và retention, đo RPO/RTO.

Hướng dẫn vận hành: docs/OPERATIONS.md. Không thay dữ liệu/config người dùng; frontend và pipeline RAG không đổi.

Kiểm chứng mốc sao lưu: 96 unittest đạt trong 52,638 giây; git diff --check đạt. Không build lại frontend vì không thay UI.

## 21/09/2026 - Bản build cùng origin và kiểm tra sẵn sàng

- [x] SERVE_FRONTEND opt-in dùng StaticFiles/FileResponse sẵn có; một Uvicorn phục vụ build và API, không thêm dependency hoặc launcher.
- [x] Allowlist trang/widget/assets, no-cache HTML, không lộ file riêng tư hoặc dùng HTML cho API lạ; thiếu build dừng rõ ràng.
- [x] GET /api/v1/ready cho Staff: schema, nguồn, số vector theo phiên bản và model Ollama; timeout ngắn, không gọi generation, không giữ transaction khi gọi mạng.
- [x] Bảy test mới cùng smoke HTTP Uvicorn thật: build/assets, chặn đường dẫn, đăng nhập, ready 503 khi Ollama tắt/kho trống, widget handoff, Inbox và logout.
- [ ] HTTPS/cloud, kiểm tra model thật trong môi trường triển khai và đo tải; M7 chưa nghiệm thu.

Smoke dùng DB/vector/tài liệu tạm, tài khoản ngẫu nhiên, Telegram tắt; không sửa dữ liệu/config người dùng. Frontend không đổi, dùng bản build hiện có để kiểm tra HTTP.

Kiểm chứng mốc chạy bản build: 103 unittest đạt trong 56,660 giây; bảy test liên quan chạy lại đạt sau chỉnh trạng thái unchecked khi bận. OpenAPI có 47 method/path; git diff --check đạt.

## 21/09/2026 - Đo tải HTTP local và index Inbox

- [x] CLI app.measure_load dùng Uvicorn loopback/store tạm riêng; seed phiên, lưu raw samples/p50/p95/throughput, hash mã và complete=false khi lỗi; không ghi đè kết quả.
- [x] Bốn lượt hoàn tất: thăm dò 100 hội thoại, baseline 500 và hai lượt 500 sau index. Với 10 client/1.000 request tải chính, throughput từ 13,755 lên 37,437/38,008 request/giây; mọi invariant đạt, không lỗi ngoài dự kiến.
- [x] Retry UUID không trùng tin; tranh chấp chỉ một nhân viên nhận; handoff không trùng ticket và trả 429 đúng giới hạn. HTTP 409/429 dự kiến được ghi riêng.
- [x] Hai index theo hội thoại/thời gian cho messages/tickets; migration chạy lại trên v7, test EXPLAIN QUERY PLAN xác nhận index và giữ dữ liệu/SLA cũ.
- [x] Hai test công cụ đo mới; tổng 105 unittest đạt trong 57,055 giây. UI/RAG không đổi, không build hoặc chạy lại benchmark RAG.
- [ ] Tải bền, RAG/Telegram đồng thời, proxy/HTTPS/cloud và SLO theo yêu cầu thực tế; chưa nghiệm thu M7.

Kịch bản không có think time, không phải lịch polling UI 3 giây; không đo login/tạo phiên hoặc năng lực tối đa. Inbox còn trả toàn bộ danh sách. Hướng dẫn và bằng chứng tại evals/load/README.md; chưa cần đổi kiến trúc hoặc thêm dependency từ phép đo này.

Kiểm tra cuối: 12 test auth/migration/công cụ đo chạy lại đạt sau bổ sung trường hợp DB v7 thiếu index; git diff --check đạt. Báo cáo Word đồng bộ 80 đoạn với Markdown, giữ bảy chương và 12 trang; đã xuất bằng Word và kiểm tra đủ ảnh trang do renderer đóng gói thiếu LibreOffice. Các tiến trình đo tải riêng đã kết thúc.
