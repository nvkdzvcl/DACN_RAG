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
