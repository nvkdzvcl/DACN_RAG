# Đo tải HTTP local cho Inbox và widget

Ngày đo: 21/09/2026. CLI chạy Uvicorn thật trên loopback với một worker và SQLite tạm. Kết quả kiểm chứng tải API cùng chống trùng/tranh chấp; không đo tốc độ hoặc chất lượng RAG.

## Chạy lại

Từ 22/09/2026, CLI kiểm tra total và trang Inbox mặc định 25 dòng, ghi inbox_page_size=25 trong kết quả. Các lượt ngày 21/09 giữ nguyên và trả toàn danh sách; workload đã khác, không so throughput trực tiếp để kết luận cải thiện do phân trang. Smoke mới hai client/31 hội thoại chỉ xác nhận hợp đồng API và invariants.

Tại root repo, dùng Python đã cài requirements-dev.txt:

```powershell
python -m app.measure_load --clients 10 --rounds 20 --conversations 500 --output evals/load/runs/my-indexed-500
python -m unittest app.tests.test_load app.tests.test_auth_handoff -v
```

Đầu ra phải là thư mục mới. CLI không nhận URL đích, chỉ khởi động tiến trình riêng ở cổng loopback trống; không thay `.env`, DB hoặc API đang chạy. DB/vector/tài liệu nằm trong thư mục tạm, Telegram và frontend tắt, Ollama trỏ tới cổng không dùng. Sau chạy, CLI dừng tiến trình của mình và dọn store tạm. Không có lượt generation hoặc truy hồi vector trong kịch bản này.

Giới hạn đầu vào: 1-20 clients, 1-100 rounds, clients <= conversations <= 5000. Đây là giới hạn của công cụ, không phải sức chứa đã được kiểm chứng. Không chạy Python với `-O` vì kịch bản dùng assert để kiểm tra tính đúng.

## Kịch bản và mẫu số

- Seed N hội thoại đã giao nhân viên, mỗi hội thoại có 10 tin khách và một ticket; thêm một hội thoại mở để thử handoff. Vì vậy tham số 500 tạo tổng 501 hội thoại, 5.000 tin lịch sử và 500 ticket ban đầu.
- Seed cookie phiên nhân viên/khách ngẫu nhiên trực tiếp trong DB, mật khẩu không dùng để đăng nhập. Mỗi client có nhân viên, khách và hội thoại riêng. Phép đo không bao gồm login, tạo phiên hoặc chi phí băm mật khẩu.
- Các client cùng bắt đầu; mỗi round lần lượt đọc danh sách Inbox, đọc hội thoại riêng, poll widget, gửi tin nhân viên với UUID mới, gửi lại cùng UUID và kiểm tra cùng message_id. Không có thời gian nghỉ giữa request; không mô phỏng đúng chu kỳ polling UI 3 giây.
- Sau tải chính, khách probe yêu cầu handoff; tất cả nhân viên cùng tiếp nhận. Phải có đúng một HTTP 200 và clients - 1 HTTP 409. Năm lần gửi lại handoff thành công, lần tiếp theo trả 429 với Retry-After 60 theo giới hạn hiện có. Các bước này không nằm trong throughput tải chính.
- Đối chiếu cuối: đúng clients * rounds tin nhân viên, không có tin AI, probe chỉ có một tin khách/một ticket. Kiểm tra ID khách/hội thoại ở từng vòng và ID tin khi retry. Kết quả không thay kiểm thử quyền truy cập âm tính trong unittest.

`results.json` giữ complete=false khi thất bại, raw samples theo operation, mã HTTP, thời gian, cờ expected; complete=true chỉ sau toàn bộ assert. Mã 0 là lỗi transport, không phải HTTP. Tổng unexpected phải bằng 0; HTTP 409/429 đúng pha vẫn được ghi và không bị tính thành lỗi ngoài dự kiến. `server.log` ghi startup/lỗi, không bật access log. Không có cookie/token trong kết quả.

p50/p95 dùng nearest rank trên thời gian request của từng operation: phần tử thứ ceil(n * p), bắt đầu từ 1, đổi sang ms. Thời gian bao gồm chờ HTTP, không gồm startup/seed; p95 của pha ít mẫu chỉ là thống kê mô tả. Throughput = clients * rounds * 5 / số giây từ trước khi tạo pool tải chính đến khi mọi client hoàn tất; có cả điều phối client và parse/kiểm tra JSON giữa request. Không tính request health lúc chờ startup hoặc pha tranh chấp sau tải chính.

Manifest lưu Python/OS/số CPU logic, phiên bản dependency và SHA-256 từng file app/**/*.py. Các hash xác định mã của lượt chạy, không thay snapshot mã nguồn/Git; cần giữ phiên bản mã tương ứng để tái tạo baseline.

## Kết quả lưu lại

Môi trường: Windows, Python 3.13.0, 16 CPU logic; FastAPI 0.141.1, Uvicorn 0.52.4, SQLAlchemy 2.0.52, httpx 0.28.1. Không kiểm soát toàn bộ tải nền, nhiệt độ CPU hoặc cache OS. Hai lượt sau index cùng cấu hình; lượt 100 hội thoại chỉ là thăm dò, không dùng để so hiệu quả index.

| Thư mục trong runs/ | Clients / rounds / N | Request tải chính | Giây | Request/giây | Unexpected |
|---|---|---|---|---|---|
| baseline-100 | 5 / 10 / 100 | 250 | 4,239 | 58,976 | 0 |
| baseline-500 | 10 / 20 / 500 | 1000 | 72,698 | 13,755 | 0 |
| indexed-500 | 10 / 20 / 500 | 1000 | 26,712 | 37,437 | 0 |
| indexed-500-repeat | 10 / 20 / 500 | 1000 | 26,310 | 38,008 | 0 |

| Operation | Baseline p50 / p95 ms | Index p50 / p95 ms | Lặp index p50 / p95 ms |
|---|---|---|---|
| inbox_list | 783,327 / 1371,878 | 260,224 / 640,324 | 266,351 / 513,581 |
| inbox_detail | 556,661 / 1131,879 | 251,734 / 442,568 | 267,476 / 459,316 |
| widget_poll | 503,525 / 1019,952 | 215,976 / 385,522 | 189,029 / 366,256 |
| staff_send | 802,870 / 2496,090 | 258,352 / 554,166 | 266,215 / 501,180 |
| staff_retry | 502,347 / 1992,962 | 208,325 / 422,272 | 212,441 / 514,563 |

Cả bốn lượt complete=true, mọi invariant đạt. Mỗi lượt 500 có thêm 17 request ở pha handoff/tranh chấp, gồm chín 409 và một 429 dự kiến. Dữ liệu gốc: [baseline](runs/baseline-500/results.json), [sau index](runs/indexed-500/results.json), [lặp sau index](runs/indexed-500-repeat/results.json).

## Thay đổi và giới hạn

Thêm hai index không unique: messages(conversation_id, created_at, id) và tickets(conversation_id, created_at). Metadata tạo trên DB mới; migration cài idempotent khi khởi động DB v7 đã có, không đổi dữ liệu hoặc schema version v7. Kiểm thử migration giữ dữ liệu/SLA và xác nhận EXPLAIN QUERY PLAN dùng index. Bản sao v7 cũ vẫn tương thích; index được thêm khi chạy migration. Tạo index có thể kéo dài startup ở DB lớn, chưa đo trong throughput.

Hash nguồn giữa baseline-500 và indexed-500 chỉ khác models/support.py, db/migrations.py và test_auth_handoff.py; runner và API không đổi. Lượt lặp xác nhận cùng xu hướng: throughput quan sát khoảng 2,7 lần baseline. Đây là phép so local với một baseline và hai lượt sau sửa, chưa có khoảng tin cậy hoặc bằng chứng về năng lực production.

Inbox còn trả toàn bộ danh sách và tính SLA; lịch sử tăng làm payload/chi phí xử lý tăng. Chưa thử phân trang Inbox, tải bền nhiều giờ, nhiều worker, mạng WAN, HTTPS/proxy, Telegram thật, trình duyệt, ingestion đồng thời hoặc RAG đồng thời. Chưa xác định số người dùng tối đa/SLO, chưa nghiệm thu M7. Chỉ mở rộng phân trang/kiến trúc sau khi có yêu cầu tải và phép đo tương ứng.
