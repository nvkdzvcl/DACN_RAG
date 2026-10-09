# Vận hành local và triển khai bản build

CLI `python -m app.backup` hỗ trợ SQLite schema v7/v8/v9/v10, Qdrant embedded và tài liệu nguồn. Dùng Python 3.12 trở lên với dependency hiện có; bản kiểm chứng chạy Python 3.13 trên Windows. Không hỗ trợ PostgreSQL, sao lưu nóng hoặc triển khai nhiều worker.

## Chạy giao diện và API cùng origin

Sau khi đã có dependency, tài khoản nhân viên và cấu hình `.env`, chạy từ root repo:

```powershell
npm --prefix frontend run build
$env:SERVE_FRONTEND='true'
python -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/` cho nhân viên; `/chat` cho khách; `/widget-demo.html` thử widget nhúng. Không cần Vite hoặc proxy riêng trong chế độ này. Chỉ một API worker; không dùng `--reload` khi chạy bản build để demo. Ollama khởi động riêng theo README. Giữ APP_ENV=development cho HTTP loopback; ngoài máy local phải có HTTPS và APP_ENV=production. Không đặt VITE_API_BASE khác origin khi build.

SERVE_FRONTEND mặc định false; có thể đặt trong `.env` thay biến PowerShell. Biến môi trường đã có được ưu tiên hơn `.env`. Thay đổi cần khởi động lại API; chỉ rebuild frontend khi nguồn frontend đổi. Backend kiểm tra có index.html, widget-demo.html, widget.js và thư mục assets; thiếu thì dừng với hướng dẫn build.

Chỉ phục vụ `/`, `/index.html`, `/chat`, `/widget-demo.html`, `/widget.js` và `/assets/*`. HTML/widget loader dùng Cache-Control: no-cache để trình duyệt kiểm tra phiên bản mới. File riêng tư và đường dẫn lạ trả 404; `/api/v1/typo` không trả HTML. Không có SPA fallback cho mọi URL. Các route giao diện không đưa vào OpenAPI; quyền API giữ nguyên.

## Khôi phục mật khẩu nhân viên

Nếu còn đăng nhập và nhớ mật khẩu cũ, dùng Cài đặt để đổi mật khẩu. Nếu quên mật khẩu, người vận hành có quyền truy cập máy chủ và DB chạy từ root repo:

```powershell
python -m app.reset_password admin-recovery --env-file .env
```

Thay `admin-recovery` bằng username đã có. Nhập mật khẩu mới 12-128 ký tự và xác nhận; mật khẩu phải khác mật khẩu cũ. Lệnh không nhận mật khẩu qua tham số hoặc in mật khẩu ra màn hình; thiếu terminal hỗ trợ nhập ẩn thì dừng. Username không phân biệt hoa/thường như đăng nhập. `create_user` vẫn chỉ tạo tài khoản mới.

`--env-file` nạp cấu hình trước khi mở DB; biến môi trường có sẵn được ưu tiên, giống Uvicorn. Bỏ tham số này thì không đọc `.env`, dùng DATABASE_URL từ môi trường hoặc DB mặc định. Dùng cùng cấu hình với backend để tránh đổi nhầm DB. Lệnh yêu cầu schema hiện có, không chạy migration hoặc tạo tài khoản.

Hash mật khẩu và việc xóa mọi AuthSession của đúng tài khoản được commit cùng transaction; lỗi trước commit rollback cả hai. Đăng nhập đang kiểm tra mật khẩu cũ không được cấp phiên sau khi reset đã commit. Giữ nguyên ID, tên, role, trạng thái active và lịch sử; tài khoản bị vô hiệu vẫn bị vô hiệu. Các request đã qua bước xác thực trước reset có thể tiếp tục hoàn tất; request kế tiếp cần đăng nhập lại.

Đây là quyền khôi phục trực tiếp trên máy chủ, không yêu cầu mật khẩu cũ hoặc cookie admin. Chỉ cấp quyền truy cập máy và DB cho người vận hành tin cậy; không mở lệnh này thành API công khai. Chưa có reset qua email/OTP hoặc nhật ký quản trị bền vững. Kiểm thử dùng DB tạm, không đổi mật khẩu tài khoản thật.

## Kiểm tra sẵn sàng trước demo

`GET /api/v1/health` công khai vẫn chỉ kiểm tra API trả lời. `GET /api/v1/ready` yêu cầu cookie nhân viên đang hoạt động; chưa đăng nhập trả 401. Có thể mở URL ready trong cùng trình duyệt sau khi đăng nhập. Response không cache, không chứa đường dẫn local, token hoặc lỗi provider thô.

```json
{"ready":true,"checks":{"database":"ok","knowledge":"ok","vectors":"ok","ollama":"ok"}}
```

HTTP 200 chỉ khi schema DB đúng v7, có tài liệu indexed dùng embedding model hiện tại, file nguồn tồn tại trong kho, số vector theo các index_version hiện tại bằng số chunk SQL và Ollama liệt kê đủ hai model cấu hình. HTTP 503 khi một kiểm tra chưa đạt. Kho mới chưa có tài liệu trả empty; đây không phải lỗi khởi động. Ingestion đang giữ khóa trả knowledge=busy và các mục còn lại unchecked; thử lại sau khi ingestion xong.

Các mã thường gặp: schema_mismatch (khác phiên bản DB), missing_source (thiếu file nguồn), missing_store/count_mismatch (kho vector thiếu hoặc lệch số chunk), missing_model (thiếu model), unavailable (không đọc được dịch vụ/kho) và error (truy vấn DB thất bại). Khi DB hỏng đến mức không xác thực được cookie, yêu cầu có thể thất bại trước probe; không coi mọi lỗi DB đều có response checks.

Probe không gọi embedding/generation, không đo chất lượng đáp án, không gửi Telegram, không kiểm tra hash/nội dung từng vector hoặc khả năng ghi đĩa. Ollama chỉ được gọi /api/tags với timeout 5 giây cho các pha I/O; model có tên không chứng minh đủ RAM để sinh câu trả lời. Không giữ transaction SQL trong lúc gọi Ollama. Kết quả phản ánh lần kiểm tra, không bảo đảm dữ liệu còn nguyên sau đó. Chỉ kiểm tra theo yêu cầu trước demo; không polling liên tục vào endpoint này. Dùng smoke_m4/smoke_ollama để kiểm chứng model thật riêng.

## Tạo và kiểm tra bản sao

1. Dừng toàn bộ API, polling Telegram và tiến trình ingestion; đợi thoát hoàn toàn. Không dùng bản sao tạo khi ứng dụng vẫn ghi dữ liệu.
2. Từ root repo, chạy các lệnh sau. Thay tên thư mục cho mỗi lần sao lưu; thư mục đích phải chưa tồn tại.

```powershell
python -m app.backup --env-file .env create data/backups/before-deploy-20260921 --offline
python -m app.backup verify data/backups/before-deploy-20260921
```

3. Chỉ dùng bản sao khi cả hai lệnh trả `OK`. Có thể khởi động lại API sau khi tạo xong. Lưu thêm một bản trên ổ lưu trữ được bảo vệ, tách khỏi ổ dữ liệu chính.

`--offline` là xác nhận của người vận hành đã dừng ứng dụng, không tự dừng hoặc khóa các tiến trình khác. CLI phát hiện thay đổi file vector/tài liệu trong lúc sao chép nhưng không bảo đảm snapshot liên kho khi có người tiếp tục ghi. SQLite dùng API backup nên giữ cả dữ liệu đã commit còn trong WAL. Qdrant được sao chép sau khi đã đóng client; bỏ file khóa `.lock`.

`--env-file` đọc cấu hình rõ ràng; biến môi trường đã có được ưu tiên như Uvicorn. Đường dẫn tương đối tính từ thư mục chạy lệnh. CLI không tự đọc `.env` khi thiếu tham số. Ba nguồn lấy từ DATABASE_URL, QDRANT_PATH và KNOWLEDGE_PATH; mặc định giống ứng dụng. Yêu cầu cả ba tồn tại, kể cả thư mục rỗng ở cài đặt mới; không tự tạo nguồn thiếu vì có thể cấu hình sai đường dẫn.

Bản sao chứa `database.sqlite`, `vectors/`, `knowledge/` và `manifest.json` với SHA-256 từng file, schema và thời gian UTC. Không sao chép `.env`, bot token, mã nguồn hoặc model Ollama. SHA-256 phát hiện hỏng/thay đổi so manifest; đây không phải chữ ký xác thực nguồn. Chỉ khôi phục bản sao từ nguồn tin cậy.

Từ 22/09/2026, chỉ file khóa `.lock` ngay tại gốc QDRANT_PATH được bỏ qua khi sao lưu, kiểm tra và khôi phục. File cùng tên trong tài liệu hoặc thư mục con vẫn được sao chép và kiểm tra SHA-256; file bị sửa/thêm ngoài manifest bị từ chối. Ngoại lệ chỉ áp dụng file thường, không cho phép symlink/junction. Bản cũ đã bỏ qua mọi file tên `.lock`: nếu nguồn có dữ liệu như vậy, cần tạo bản sao mới từ nguồn còn đủ; CLI không thể tái tạo file đã bị bỏ mất. Format manifest 1/schema v7 giữ nguyên.

Bản sao vẫn chứa hội thoại, tài liệu, hash mật khẩu và token phiên. Không đưa lên Git hoặc chia sẻ công khai; bảo vệ bằng quyền truy cập và mã hóa ổ đĩa. `data/backups/` và `data/restored/` đã được ignore, nhưng thư mục tùy chọn khác cần tự loại khỏi Git. CLI không mã hóa hoặc chuyển dữ liệu lên cloud.

## Khôi phục vào thư mục mới

1. Dùng phiên bản mã nguồn/dependency hỗ trợ schema của bản sao (v7, v8, v9 hoặc v10). Kiểm tra bản sao và chạy khôi phục vào thư mục chưa tồn tại:

```powershell
python -m app.backup restore data/backups/before-deploy-20260921 data/restored/check-20260921
```

2. Chỉ tiếp tục khi lệnh trả `restore: OK` và có `RESTORED.txt`. Bản sao gốc và dữ liệu đang dùng không bị ghi đè. Bản khôi phục tự xóa phiên staff/widget và quyền truy cập đơn; tài khoản, lịch sử và dữ liệu nghiệp vụ được giữ. Manifest sao lưu được bỏ khỏi bản khôi phục vì DB đã đổi; không chạy `verify` trên thư mục đã khôi phục.
3. Tạo cấu hình local riêng cho lần kiểm tra. Giữ cấu hình model phù hợp, chỉ đổi ba đường dẫn dưới đây. Không bật Telegram trong lúc kiểm tra bản khôi phục.

```dotenv
DATABASE_URL=sqlite:///./data/restored/check-20260921/database.sqlite
QDRANT_PATH=data/restored/check-20260921/vectors
KNOWLEDGE_PATH=data/restored/check-20260921/knowledge
TELEGRAM_ENABLED=false
```

4. Dừng API cũ trước khi khởi động bản khôi phục. Kiểm tra đăng nhập mới, khách/đơn/lịch sử, nguồn tài liệu, truy xuất vector và hỏi đáp bằng model hiện có. Model Ollama không nằm trong bản sao; phải cài đúng model/embedding đã dùng. Chưa đạt thì dừng API mới và quay lại cấu hình dữ liệu cũ.
5. Chỉ chuyển cấu hình sử dụng chính sau khi kiểm tra đạt; giữ dữ liệu cũ để quay lại. Những thao tác xảy ra sau thời điểm sao lưu không có trong bản khôi phục.

Khôi phục tài khoản đưa hash mật khẩu và trạng thái tài khoản về thời điểm sao lưu. Nếu có thay đổi bảo mật sau mốc đó, cần xử lý lại trước khi cho người dùng truy cập. Phiên cũ không được khôi phục.

Telegram giữ con trỏ và nhật ký tại thời điểm sao lưu. Bật bot trên DB cũ có thể gửi lại tin từng gửi sau thời điểm đó hoặc xử lý update cũ. Không chạy hai bản API cùng bot. Giữ `TELEGRAM_ENABLED=false` đến khi người vận hành đối chiếu lịch sử gửi/nhận; CLI chưa tự đồng bộ với Telegram. Quy trình này chưa được nghiệm thu phục hồi bot thật.

## Khi thất bại

CLI trả exit code 1, không ghi đè nguồn hoặc đích đã tồn tại. Thư mục mới có thể còn dữ liệu dở; không sử dụng và không thử ghi tiếp vào đó. Tạo đích mới sau khi sửa nguyên nhân. Không có manifest hợp lệ thì không coi là bản sao hoàn tất; không có `RESTORED.txt` thì không coi là khôi phục hoàn tất. Symlink/junction, nguồn/đích lồng nhau, schema sai và file thiếu/thừa/sai hash bị từ chối.

## Kiểm chứng và bước triển khai còn lại

`python -m unittest app.tests.test_backup -v` kiểm tra vòng sao lưu/khôi phục với Qdrant embedded thật, truy vấn lại vector, giữ DB nguồn, thu hồi quyền trên bản khôi phục, chống ghi đè, file hỏng/thiếu/thừa, manifest chứa đường dẫn lạ, lỗi sao chép, nguồn thay đổi và CLI đọc env mà không sao chép bí mật. Dữ liệu tạm được tách khỏi DB người dùng; không gọi Ollama/Telegram.

Trước triển khai bên ngoài vẫn cần HTTPS/proxy cùng origin, APP_ENV=production, một API worker, quyền thư mục/ổ mã hóa, bộ model thực tế, diễn tập phục hồi và đo tải trong môi trường triển khai. Chưa công bố RPO/RTO, lịch sao lưu tự động, retention, cloud hoặc nghiệm thu M7. Không thay cấu hình chạy của người dùng trong đợt triển khai CLI này.

## Đo tải HTTP trên dữ liệu tạm

Chạy `python -m app.measure_load --clients 10 --rounds 20 --conversations 500 --output evals/load/runs/my-run` từ root, dùng thư mục đầu ra chưa tồn tại. CLI tự tạo store và Uvicorn loopback riêng; không hướng tới API đang dùng, không sửa `.env`, không gọi Ollama/Telegram. Giữ máy ổn định trong lúc đo; chỉ coi lượt có complete=true và mọi kiểm tra đạt là hoàn tất. Kịch bản, raw samples, mẫu số p50/p95/throughput và kết quả ngày 21/09 nằm tại [evals/load/README.md](../evals/load/README.md).

Đã thêm index messages(conversation_id, created_at, id) và tickets(conversation_id, created_at), áp dụng cả DB mới/cũ khi migration chạy. Khởi động lại API trong cửa sổ bảo trì để cài index; thao tác có thể mất thời gian trên DB lớn. Schema vẫn v7, bản sao v7 cũ tương thích; không cần sửa cấu hình hoặc lập chỉ mục lại tài liệu. Phép đo 10 client/500 hội thoại cải thiện từ 13,755 lên 37,437-38,008 request/giây; không đo chi phí startup tạo index. Các lượt đo này trả toàn danh sách. Từ 22/09/2026 Inbox mặc định trả 25 dòng và CLI ghi inbox_page_size; không so throughput trực tiếp giữa hai workload. Tìm kiếm/SLA vẫn quét theo lô. Kết quả không xác định sức chứa tối đa, tải RAG/Telegram hoặc SLO production.

Từ schema v8, khôi phục thu hồi thêm `customer_sessions`. Tài khoản khách và lịch sử vẫn giữ; khách cần đăng nhập lại. Xem [CUSTOMER_AUTH.md](CUSTOMER_AUTH.md).

Schema v9 bổ sung xác minh và khôi phục email. Restore thu hồi cả `customer_email_tokens` để liên kết trước sao lưu không còn dùng được. Cấu hình SMTP và giới hạn giao thư: [CUSTOMER_AUTH.md](CUSTOMER_AUTH.md).
