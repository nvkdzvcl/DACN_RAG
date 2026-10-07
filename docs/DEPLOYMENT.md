# Chuẩn bị triển khai trên Windows

Cập nhật ngày 07/10/2026. Bộ cấu hình dành cho một máy Windows có GPU: Caddy nhận HTTPS, FastAPI phục vụ frontend và API cùng origin, Ollama chạy trên máy đó. Dữ liệu production tách khỏi dữ liệu development. Đây là cấu hình chuẩn bị và smoke local, chưa phải nghiệm thu triển khai Internet.

## Kiến trúc và điều kiện

- Người dùng mở `https://TEN-MIEN/` cho nhân viên, `/chat` cho khách. Không chạy Vite trong production.
- Caddy nhận TCP 80/443; backend chỉ nghe `127.0.0.1:8000`, Ollama `127.0.0.1:11434`, Caddy admin `127.0.0.1:2019`. Không chuyển tiếp các cổng nội bộ ra Internet.
- Dùng đúng **một worker**, không reload: SQLite, Qdrant embedded, rate limit trong bộ nhớ và Telegram polling chưa hỗ trợ chia nhiều worker. Máy cần chạy liên tục, tránh sleep.
- Dùng tài khoản Windows riêng để vận hành khi đưa ra ngoài; hạn chế quyền đọc cấu hình SMTP/token, DB, tài liệu và bản sao lưu.
- Tên miền phải trỏ tới máy triển khai; chứng chỉ công khai cần điều kiện DNS/mạng phù hợp. Nếu máy sau CGNAT hoặc không mở được cổng thì cần chốt phương án máy chủ/tunnel khác trước, không suy rằng chỉ có file cấu hình là đã public được.
- Không có tên miền hoặc máy chủ được chọn trong lượt này. Không tự mở firewall/router, tạo tài khoản cloud hay mua dịch vụ.

## Chuẩn bị cấu hình và dữ liệu

Chạy tại thư mục dự án trên máy triển khai. Ví dụ hiện tại là `E:\DACN_RAG`; thay đường dẫn nếu checkout khác.

```powershell
Set-Location E:\DACN_RAG
python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
if (-not (Test-Path deploy/production.env)) { Copy-Item deploy/production.env.example deploy/production.env }
New-Item -ItemType Directory -Force data/production, data/production/vectors, data/production/knowledge_base
```

Chỉ sao chép file mẫu khi chưa có `deploy/production.env`; không ghi đè cấu hình đang dùng. File thực và toàn bộ `data/production/` được bỏ qua trong Git.

Sửa `deploy/production.env`:

- Giữ `APP_ENV=production`, `SERVE_FRONTEND=true`.
- Thay `CUSTOMER_PUBLIC_URL=https://support.example.com` bằng HTTPS origin thật, không có đường dẫn/query/fragment. Caddy và email khôi phục dùng cùng biến này.
- Giữ hoặc chọn lại bộ ba DATABASE_URL, QDRANT_PATH, KNOWLEDGE_PATH. Nếu đổi thư mục, tạo thư mục cha trước; mọi đường dẫn tương đối tính từ gốc repo. Không trỏ API development và production vào cùng DB/vector store đang mở.
- Model giữ `qwen3:4b` và `embeddinggemma:300m`; cần tải sẵn trên Ollama của máy chạy.
- Telegram mặc định tắt. Chỉ bật sau khi chốt bot riêng và thử gửi/nhận thật; không để bot development chạy cùng token.
- SMTP có thể để trống trong lúc chuẩn bị; chức năng gửi thư báo chưa sẵn sàng. Điền theo [CUSTOMER_AUTH.md](CUSTOMER_AUTH.md) khi có hộp thư.

Provision quản trị viên đúng DB production bằng dotenv CLI có sẵn trong môi trường hiện tại:

```powershell
python -m dotenv -f deploy/production.env run --override -- python -m app.create_user admin --role admin
```

Lệnh hỏi mật khẩu ẩn. Nếu username đã tồn tại, dùng `python -m app.reset_password admin --env-file deploy/production.env` trong terminal sạch, không tạo lại tài khoản. Không có tài khoản/mật khẩu mặc định hoặc tự seed dữ liệu demo vào production.

## Chạy dịch vụ

Cài Caddy bản chuẩn Windows từ nhà phát hành, kiểm tra checksum rồi đặt `caddy.exe` trên PATH hoặc dùng đường dẫn tuyệt đối. Lượt QA dùng Caddy v2.11.7 portable dưới output, không cài thành dịch vụ hoặc đưa binary vào Git.

Terminal 1 — Ollama:

```powershell
.\scripts\start-ollama.ps1
```

Terminal 2 — backend và frontend cùng origin:

```powershell
.\scripts\start-production.ps1
```

Script chạy từ gốc repo, đọc `deploy/production.env` (hoặc `-EnvFile PATH`), từ chối APP_ENV/SERVE_FRONTEND/origin sai; dotenv file được ưu tiên trước biến môi trường shell. Uvicorn chỉ tin proxy trên loopback, không log URL từng request, chờ shutdown tối đa 240 giây. Đóng bằng Ctrl+C; không dùng `--reload` hoặc tăng workers.

Terminal 3 — HTTPS:

```powershell
python -m dotenv -f deploy/production.env run --override -- caddy validate --config deploy/Caddyfile --adapter caddyfile
python -m dotenv -f deploy/production.env run --override -- caddy run --config deploy/Caddyfile --adapter caddyfile
```

Nếu Caddy không nằm trên PATH, thay `caddy` bằng đường dẫn exe. Trước khi đưa ra Internet mới cấu hình DNS và firewall/router cho 80/443. Caddy tự xử lý chứng chỉ và chuyển HTTP sang HTTPS khi đủ điều kiện. Giữ thư mục dữ liệu chứng chỉ của Caddy thuộc tài khoản Windows vận hành, không xóa mỗi lần restart. Không dùng `caddy trust` hoặc bỏ kiểm tra chứng chỉ trên máy người dùng cho bản công khai.

Proxy chỉ chuyển tiếp vào backend, không phục vụ thư mục repo. Chặn /docs, /redoc, /openapi.json công khai; route lạ và file riêng tư vẫn do backend trả 404. Header chống đoán MIME, chỉ nhúng cùng origin và không gửi referrer. Giới hạn body 12 MB để chứa file 10 MiB cộng overhead; yêu cầu quá lớn có thể nhận 413 hoặc bị ngắt kết nối khi proxy dừng đọc body. Không đặt timeout phản hồi ngắn làm cắt chuỗi gọi model; ứng dụng vẫn có giới hạn riêng cho Ollama.

Mẫu này chưa cấu hình CDN hoặc proxy thứ hai phía trước Caddy. Nếu thêm, cần kiểm tra lại danh sách proxy đáng tin và rate limit theo IP. Widget nhúng hiện cùng origin; cấu hình SAMEORIGIN không hỗ trợ iframe khác tên miền.

## Khởi động lại, kiểm tra và sao lưu

Cấu hình hiện chạy foreground để dễ kiểm tra. Chưa đăng ký Windows Service/Task Scheduler, chưa tự khởi động sau reboot. Khi đã chốt máy, có thể cấu hình tác vụ lúc khởi động bằng tài khoản vận hành, đặt working directory là repo, không chạy trùng tiến trình, bật restart khi thất bại và kiểm chứng sau reboot. Cần xác nhận cách chạy Ollama/GPU dưới tài khoản đó trước.

Kiểm tra sau khi mở dịch vụ:

1. Mở HTTPS trên thiết bị thứ hai; không có cảnh báo chứng chỉ, HTTP chuyển sang HTTPS.
2. /api/v1/health trả 200 chỉ chứng minh API sống. Đăng nhập nhân viên rồi kiểm tra /api/v1/ready: cần DB, nguồn tài liệu, vector và model đủ mới coi sẵn sàng.
3. Đăng ký khách, gửi tin, xác minh email và đặt lại mật khẩu khi SMTP đã cấu hình. Thử tra đơn với mã truy cập và handoff cho nhân viên.
4. Thử model thật và đo độ trễ/tải trên máy triển khai. Không dùng lời chào local hoặc test giả lập để kết luận Ollama đủ nhanh.

Sao lưu offline trước nâng code/schema, bằng terminal sạch không có biến DB/vector development ghi đè. Dừng API và mọi lệnh ingestion; Ollama có thể giữ chạy. Caddy có thể trả 502 trong khoảng dừng API, nên chọn thời gian bảo trì. Đổi tên đích thành thư mục mới cho mỗi lần sao lưu:

```powershell
python -m app.backup --env-file deploy/production.env create data/backups/prod-YYYYMMDD-HHMM --offline
python -m app.backup verify data/backups/prod-YYYYMMDD-HHMM
```

Chỉ dùng `--offline` sau khi đã dừng các tiến trình ghi; cờ này là xác nhận, không tự dừng API. Sao chép bản sao đã kiểm tra ra nơi riêng có kiểm soát quyền; bản sao trên cùng đĩa chưa bảo vệ khỏi hỏng đĩa. Khôi phục theo [OPERATIONS.md](OPERATIONS.md), dùng DB/vector/tài liệu cùng bộ và sửa ba đường dẫn cấu hình; giữ Telegram tắt khi diễn tập. Không chạy lệnh xóa tự động hoặc rollback schema bằng cách hạ code. Lịch sao lưu, retention và RPO/RTO thực tế còn chờ chốt.

## Bằng chứng local

- Một kiểm thử launcher bằng PowerShell thật: chọn file có khoảng trắng, ghi đè biến development, loopback/one-worker/proxy-trust và từ chối cấu hình không an toàn. Chạy lại: `python -m unittest app.tests.test_deployment -v`.
- Caddy v2.11.7: archive đối chiếu SHA-512 của nhà phát hành; cấu hình production qua `caddy validate`.
- Smoke HTTPS local dùng DB riêng, internal CA riêng, không cài CA vào hệ thống: health, frontend/fonts, cookie Secure/HttpOnly/SameSite, CSRF, logout, private-file/docs block, forwarded-IP spoof/rate limit và HTTP redirect.
- Body vượt 12 MB bị từ chối/ngắt kết nối, health vẫn hoạt động sau đó. Dùng cổng cao và bind loopback cho proxy thử; chưa thử ACME công khai, DNS, firewall, GPU/model thật, SMTP hoặc Telegram trong lượt này.

Nguồn chính thức: Caddy Command Line, Automatic HTTPS và reverse_proxy tại caddyserver.com/docs; CLI Uvicorn và python-dotenv đã đối chiếu trực tiếp trong môi trường dự án.
