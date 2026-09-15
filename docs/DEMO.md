# Demo nhanh

## Tài khoản và xác thực

Tại root repo, cài công cụ và tạo tài khoản đầu tiên bằng CLI:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.create_user admin --role admin
python -m app.create_user agent1 --name 'Nhân viên 1'
```

CLI hỏi mật khẩu 12-128 ký tự và xác nhận; không ghi mật khẩu vào lệnh hoặc Git. Không có mật khẩu mặc định. Admin cũng có thể tạo nhân viên qua `POST /api/v1/auth/users`. Tài khoản tồn tại không bị ghi đè.

Backend tự chạy migration cộng thêm cột khi khởi động. Dữ liệu hội thoại/tin nhắn cũ được giữ. Các hội thoại `assigned` từ bản demo chưa có người phụ trách được đưa về `handoff_requested` để nhân viên thật nhận lại. Dừng backend cũ trước lần nâng cấp; sao lưu SQLite bằng `sqlite3.Connection.backup` nếu DB có dữ liệu quan trọng. Migration chưa được kiểm chứng trên PostgreSQL.

## Unified Inbox

Mở hai terminal tại thư mục dự án. Terminal backend:

```powershell
python -m uvicorn app.main:app --reload
```

Terminal frontend:

```powershell
cd frontend
npm run dev
```

Đăng nhập bằng tài khoản vừa tạo. Frontend và `/api` phải cùng origin; Vite chuyển tiếp tới `http://127.0.0.1:8000`. Nếu đổi cổng backend, đặt `$env:API_PROXY_TARGET = 'http://127.0.0.1:8001'` trước khi chạy Vite. Không cấu hình `VITE_API_BASE` sang origin khác cho cơ chế cookie hiện tại.

Để nạp file `.env`, chạy Uvicorn với `--env-file .env`. Khi triển khai HTTPS, đặt `APP_ENV=production` để bật cookie Secure. Không triển khai chế độ development qua HTTP công khai. Phiên dùng cookie HttpOnly/SameSite=Strict, hết hạn sau 8 giờ; đăng xuất thu hồi phiên trong DB. Giới hạn đăng nhập hiện hỗ trợ một API worker, 10 lần/phút theo địa chỉ kết nối; reverse proxy hoặc nhiều worker cần bộ giới hạn dùng chung trước khi hosting.

Danh sách rỗng là trạng thái hợp lệ. Chọn hội thoại để xem tin nhắn/ticket; lọc theo trạng thái/ưu tiên hoặc tìm tên/ID/kênh. Nhấn Tiếp nhận với hội thoại đang chờ; chỉ người nhận được gửi trả lời. Nhân viên khác nhận cùng lúc sẽ bị chặn. AI dừng cả khi chờ và sau khi được nhận. Bản nháp giữ riêng từng hội thoại trong phiên trang, không lưu sau tải lại. Các số liệu đầu trang chỉ tính tập hội thoại đang lọc; chưa có realtime, cần Làm mới để thấy tin từ nơi khác.

Kiểm tra backend bằng DB thử riêng, không sửa DB hiện có:

```powershell
python -m unittest discover -s app/tests -v
```

## API và dữ liệu mẫu

Khởi động API:

```powershell
uvicorn app.main:app --reload
```

Các endpoint nghiệp vụ hiện là API nội bộ, yêu cầu đăng nhập. Widget sẽ có phiên khách riêng ở mốc sau; không coi customer_id do client gửi là xác thực khách hàng. Đăng nhập bằng PowerShell (mật khẩu nhập ẩn):

```powershell
$api = 'http://127.0.0.1:8000/api/v1'
$csrfHeaders = @{ 'X-CSRF-Protection' = '1' }
$staffCredential = Get-Credential -Message 'Tài khoản admin vừa tạo'
$loginBody = @{ username = $staffCredential.UserName; password = $staffCredential.GetNetworkCredential().Password } | ConvertTo-Json
Invoke-RestMethod -Method Post "$api/auth/login" -ContentType 'application/json' -Headers $csrfHeaders -Body $loginBody -SessionVariable staffSession
$loginBody = $null
Invoke-RestMethod -Method Post "$api/demo/seed" -Headers $csrfHeaders -WebSession $staffSession
```

Tra cứu đơn hàng:

```powershell
Invoke-RestMethod -Method Post "$api/orders/lookup" -ContentType 'application/json' -Headers $csrfHeaders -WebSession $staffSession -Body '{"order_id":"ORD-DEMO01","customer_id":"cus_demo_001"}'
```

Tạo hội thoại và yêu cầu nhân viên:

```powershell
$chat = Invoke-RestMethod -Method Post "$api/conversations" -ContentType 'application/json' -Headers $csrfHeaders -WebSession $staffSession -Body '{"customer_id":"cus_demo_001","channel":"website"}'
$messageBody = @{ content = 'Tôi muốn gặp nhân viên' } | ConvertTo-Json
Invoke-RestMethod -Method Post "$api/conversations/$($chat.conversation_id)/process" -ContentType 'application/json; charset=utf-8' -Headers $csrfHeaders -WebSession $staffSession -Body ([Text.Encoding]::UTF8.GetBytes($messageBody))
```

Mở Inbox, Làm mới, Tiếp nhận rồi Gửi. Gửi thêm một tin qua `/process` hoặc `/messages`: tin khách được lưu nhưng không sinh trả lời AI, trạng thái vẫn `assigned`. Dùng tài khoản thứ hai thử trả lời để kiểm tra chặn quyền. Endpoint seed chỉ thêm đơn còn thiếu, không có reset.

## Demo RAG Ollama và Kho tri thức

1. Chạy `powershell -File scripts/start-ollama.ps1` nếu Ollama chưa chạy. Backend một worker: `python -m uvicorn app.main:app --reload --env-file .env`; frontend `npm --prefix frontend run dev`.
2. Đăng nhập admin, vào Kho tri thức. Kiểm tra thông báo kết nối Ollama và đã tải đủ model.
3. Tải tài liệu chính sách. Chờ trạng thái Đã lập chỉ mục; mở Xem nội dung để đối chiếu trang/dòng. File trùng bị từ chối; file failed có thể Lập chỉ mục lại.
4. Hỏi câu có đáp án, mở citation rồi Xem đoạn nguồn. Hỏi câu ngoài tài liệu: mong đợi Chưa đủ bằng chứng. Không coi thông báo Có trích nguồn là đảm bảo tuyệt đối câu trả lời đúng.
5. Đăng nhập agent: xem/hỏi được, không có nút sửa tài liệu. Mobile có thanh chuyển Hội thoại/Kho tri thức.
6. Trên tài liệu thử, lập chỉ mục lại rồi xóa có xác nhận. Sau xóa không còn retrieval; citation cũ trong lịch sử vẫn lưu quote nhưng không mở được nguồn đã xóa.

Kiểm thử model thật: `python -m app.tests.smoke_ollama` tự dùng thư mục tạm, kiểm tra vector sau đóng/mở, hai câu có nguồn, thiếu dữ kiện và yêu cầu bịa dữ liệu. Kiểm thử tranh chấp: `python -m unittest discover -s app/tests -v` xác nhận handoff và tiếp nhận hoàn tất khi LLM còn chờ, không lưu/gửi AI muộn.

## Demo widget và phiên khách

1. Chạy Ollama, backend và frontend như phần RAG. Mở `/widget-demo.html` trên origin frontend; `/chat` mở chat trực tiếp. Không dùng port QA 5184/8014 cho dữ liệu thật.
2. Chọn Hỗ trợ, nhập tên và bắt đầu. Hỏi chính sách đã lập chỉ mục; mở Nguồn để xem quote và vị trí. Tải lại trang, mở widget: phiên và lịch sử vẫn còn trong 24 giờ nếu cookie chưa bị xóa.
3. Chọn Gặp nhân viên; tại trang nhân viên `/`, chọn Làm mới, mở hội thoại và Tiếp nhận. Gửi trả lời: widget nhận trong chu kỳ polling 3 giây khi tab hiển thị và không đang chờ thao tác. AI không trả lời tiếp khi đã chuyển nhân viên.
4. Mở trình duyệt riêng hoặc cửa sổ ẩn danh: phiên mới không thấy hội thoại cũ. Tên giống khách có đơn không cấp quyền tra đơn; mã đơn không thuộc khách hiện tại chuyển nhân viên.
5. Mất mạng khi gửi: bản nháp vẫn còn; thử gửi lại cùng nội dung trên cùng trang dùng lại ID. HTTP 429 do AI bận chưa lưu tin; có thể thử lại hoặc Gặp nhân viên. Không tải lại trang nếu cần giữ bản nháp/ID chưa xác nhận.
6. Đóng khung chat rồi mở lại giữ phiên. Kết thúc có xác nhận, thu hồi phiên và đóng hội thoại/ticket; nhân viên vẫn xem lịch sử. Phiên hết hạn cần bắt đầu mới.

Nhúng bằng `<script src="/widget.js" defer></script>` trên cùng origin đã phục vụ frontend, `/chat` và proxy `/api` tới backend. Bản build cần SPA fallback cho `/chat`, HTTPS ngoài development và một API worker. Cookie khách riêng với phiên nhân viên, không cấu hình CORS/cookie bên thứ ba. Chỉ hiển thị 200 tin gần nhất; giới hạn mỗi IP/phút là 6 tạo phiên, 10 gửi tin, 6 handoff. Giới hạn AI một lượt chỉ áp dụng cho widget, chưa bao gồm hỏi thử của nhân viên. Inbox đã có polling và SLA phản hồi đầu tiên; push realtime, SLA giải quyết và nhúng khác origin chưa triển khai.

Kiểm chứng ngày 14/09/2026: 46 unittest đạt; trình duyệt Edge trên DB/vector QA riêng đã chạy một câu qua Ollama thật với quote, khôi phục phiên, handoff, phản hồi nhân viên bằng API và polling, giữ draft/UUID khi mất mạng, phục hồi polling, Escape trả focus và kết thúc thu hồi phiên. Kiểm tra trực quan desktop/mobile 390px, trang chat trực tiếp và khung nhúng; không tràn ngang. Đây là smoke chức năng, không phải benchmark chất lượng hoặc tải đồng thời.

## Demo Inbox tự cập nhật và SLA

1. Mở Inbox bằng tài khoản nhân viên và widget bằng phiên khách riêng. Khách chọn Gặp nhân viên: hội thoại xuất hiện tự động trong chu kỳ polling, không cần Làm mới. Khi đang xem một hội thoại, hội thoại mới không giành lựa chọn.
2. Quan sát SLA phản hồi đầu tiên và Hạn phản hồi. Handoff hiện tạo ticket ưu tiên cao nên hạn là 15 phút tính từ tạo ticket, 24/7. Chọn Tiếp nhận: SLA vẫn chờ; chỉ tin trả lời đầu tiên của nhân viên mới chuyển sang đã phản hồi đúng hạn hoặc trễ.
3. Khách gửi thêm tin khi đã assigned; nội dung tự xuất hiện trong Inbox, bản nháp của nhân viên vẫn giữ. Mở tài khoản nhân viên khác: trạng thái phụ trách tự cập nhật và ô gửi bị khóa nếu không phải người nhận.
4. Dùng bộ lọc SLA để xem Trong hạn, Quá hạn chờ phản hồi, Đã phản hồi đúng hạn/trễ, Kết thúc trước phản hồi hoặc Chưa có SLA. Thẻ số Quá hạn chỉ tính hội thoại đang chờ trong bộ lọc và tìm kiếm hiện tại. Kết thúc trước trả lời không được tính đạt; SLA từng ticket vẫn hiện trong chi tiết.
5. Tắt mạng trong trình duyệt thử: danh sách/nội dung và bản nháp còn giữ, có cảnh báo dữ liệu cũ; bật lại tự phục hồi. Chuyển tab ẩn hoặc mở Kho tri thức tạm ngừng polling. Nút Làm mới tải lại cả danh sách và chi tiết.

Không sửa timestamp DB thật để tạo ca trễ. Kiểm thử `python -m unittest app.tests.test_inbox -v` có ca giả lập quá hạn, đúng ranh giới, phản hồi trễ, đóng chưa phản hồi và nhiều ticket. QA ngày 14/09/2026 dùng DB/vector riêng, hai tài khoản nhân viên và phiên widget: tự cập nhật người phụ trách/tin mới, giữ draft/lựa chọn, lỗi mạng/phục hồi, bộ lọc, hủy phản hồi cũ, mô phỏng tab ẩn và kiểm tra giao diện 390px đạt. Tổng 49 unittest và Vite build đạt; chưa đo tải hoặc thay kết quả chất lượng RAG.

## Demo giải quyết và tiếp nhận lại

Kiểm tra tự động toàn luồng bằng `python -m app.tests.smoke_m4` từ root repo khi Ollama sẵn sàng. Lệnh đăng nhập/tải tài liệu/hỏi đáp thật qua API, rồi handoff/giải quyết/nhắn tiếp/đóng; dùng dữ liệu tạm, không mở cổng. Kết quả và phạm vi tại [M4_ACCEPTANCE.md](M4_ACCEPTANCE.md). Các bước trình duyệt bên dưới vẫn cần khi thay UI/proxy.

1. Khách chọn Gặp nhân viên; nhân viên thứ nhất Tiếp nhận. Nhập Ghi chú hoàn tất (nội bộ), chọn Giải quyết và xác nhận. Kiểm tra ticket lưu người/thời điểm/ghi chú, widget chỉ hiện thông báo chung.
2. Tải lại widget rồi nhắn thêm yêu cầu. Hội thoại cũ giữ lịch sử nhưng chuyển về hàng chờ, chưa có người phụ trách và có ticket mới. Nhân viên thứ hai tiếp nhận và trả lời; AI vẫn dừng.
3. So SLA hai ticket. Nếu lượt đầu kết thúc chưa được trả lời, trạng thái Kết thúc trước phản hồi vẫn giữ dù lượt sau đã phản hồi đúng hạn. Ghi chú mỗi lượt hiển thị riêng trong Inbox.
4. Ở lượt đang phụ trách, nhập ghi chú rồi chọn Đóng hội thoại. Hủy xác nhận để kiểm tra trạng thái không đổi; thực hiện lại và xác nhận để đóng. Widget khóa gửi, giữ lịch sử; chọn Kết thúc, nhập tên và bắt đầu phiên mới.
5. Kiểm tra xung đột trên dữ liệu thử: khi hộp xác nhận đang mở, khách gửi tin mới rồi nhân viên xác nhận. API trả 409, tải lại nội dung và giữ ghi chú để đọc lại trước khi hoàn tất. Không dùng dữ liệu khách thật cho QA.

Kiểm chứng ngày 14/09/2026: 53 unittest và Vite build đạt; QA Edge bản build với hai phiên nhân viên, phiên widget và DB/vector riêng kiểm tra đủ luồng trên, ghi chú không lộ, retry thao tác cũ không ảnh hưởng ticket mới. Desktop/mobile 390px đã kiểm tra trực quan, không tràn ngang. Chưa có mở lại hội thoại đã đóng bằng thao tác nhân viên, SLA giải quyết hoặc kiểm thử tải; không đo lại chất lượng RAG.

## Demo bộ chọn tool M5

Chạy `python -m app.tests.smoke_tools` khi Ollama local đã sẵn sàng. Lệnh tạo dữ liệu giả lập riêng và chạy bảy ca tra đơn/chuyển nhân viên/chính sách/nhiều mã; dùng dịch vụ nghiệp vụ thật, không mở server. Không sửa chủ đơn hoặc ID khách trong DB thật để tạo ca demo. Xem docs/M5_TOOLS.md cho trace và số liệu.

Trong widget, câu “Đơn DH99999 đang ở đâu?” được bộ chọn phân loại nhưng quyền vẫn theo khách của phiên, nên không lộ đơn có sẵn thuộc người khác. Câu “Hủy đơn DH12345 giúp tôi” chuyển nhân viên nếu bộ chọn trả handoff, không hủy đơn. Câu “Tra đơn DH12345 và DH99999” yêu cầu chọn một mã. Trace chỉ trong GET chi tiết Inbox dành staff, không có bảng nhật ký riêng trên UI. Lỗi provider giữ tin; đọc lịch sử trước khi gửi một yêu cầu mới để thử lại.
