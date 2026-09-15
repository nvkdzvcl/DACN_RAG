# Đặc tả API local

Đối chiếu mã và OpenAPI ngày 15/09/2026: 31 cặp method/path dưới /api/v1. Swagger tại /docs, schema tại /openapi.json trên backend đang chạy là nguồn tham chiếu kiểu dữ liệu. Các route trả dict hiện chưa khai báo đầy đủ response_model hoặc lỗi runtime trong OpenAPI; bảng dưới bổ sung hợp đồng nghiệp vụ thực có, không tuyên bố OpenAPI đã mô tả hết bảo mật/lỗi.

## Phiên và quyền truy cập

Mọi thao tác ghi yêu cầu header `X-CSRF-Protection: 1`. Trình duyệt gửi cookie cùng origin. Staff là tài khoản admin hoặc agent đang hoạt động với cookie `rag_session` (path /api, tối đa 8 giờ); khách dùng `rag_widget_session` (path /api/v1/widget, tối đa 24 giờ). Token chỉ lưu hash SHA-256 trong DB, HttpOnly/SameSite Strict và Secure khi APP_ENV khác development. Không nhận token qua payload.

Admin quản lý tài khoản/tài liệu. Staff đọc toàn bộ Inbox nội bộ; trả lời và hoàn tất vẫn phải là người phụ trách, kể cả admin. Khách chỉ truy cập hội thoại gắn với cookie, không tự chọn customer_id/conversation_id. Tên tự khai không cấp quyền đơn hàng.

## Danh mục endpoint

Mọi đường dẫn trong bảng đã có tiền tố /api/v1. Body JSON trừ upload multipart; kết quả thành công mặc định 200, ngoại lệ ghi ở cột cuối.

| Method | Path | Quyền | Đầu vào và kết quả chính |
|---|---|---|---|
| POST | /auth/login | CSRF | username, password; cấp cookie, trả người dùng công khai |
| GET | /auth/me | Staff | Trả id, username, display_name, role |
| POST | /auth/logout | CSRF | Thu hồi token nhân viên hiện tại, xóa cookie |
| POST | /auth/users | Admin | username, password, display_name, role; 201 |
| POST | /widget/session | CSRF | display_name 1-80 không trắng; tạo/khôi phục snapshot, 201 |
| GET | /widget/session | Phiên khách | Snapshot riêng của phiên |
| DELETE | /widget/session | Phiên khách | Đóng hội thoại/ticket hoạt động, thu hồi phiên; status ended |
| POST | /widget/messages | Phiên khách | content 1-4000 không trắng, client_message_id UUID; snapshot và kết quả lưu |
| POST | /widget/handoff | Phiên khách | client_message_id UUID; lưu yêu cầu gặp người thật và trả snapshot |
| POST | /conversations | Staff | customer_id, channel; tạo hội thoại nội bộ |
| POST | /conversations/{conversation_id}/messages | Staff | content, external_message_id tùy chọn; xử lý tin khách, không phải gửi tin nhân viên |
| POST | /conversations/{conversation_id}/tickets | Staff | Tạo/tái sử dụng ticket hoạt động, không giả lập tin khách |
| POST | /conversations/{conversation_id}/process | Staff | content; cùng process_message, không có UUID trong schema này |
| GET | /inbox/conversations | Staff | Query status, priority, sla; count và conversations |
| GET | /inbox/conversations/{conversation_id} | Staff | Khách, messages, tickets, phân công, tin khách cuối và SLA |
| POST | /inbox/conversations/{conversation_id}/accept | Staff | Không body; chỉ nhận khi handoff_requested và chưa phân công |
| POST | /inbox/conversations/{conversation_id}/messages | Người phụ trách | content 1-4000 không trắng; lưu tin agent với agent_id từ phiên |
| POST | /inbox/conversations/{conversation_id}/finish | Người phụ trách | status, ticket_id, last_customer_message_id, note; status và duplicate |
| GET | /documents | Staff | Danh sách tài liệu và trạng thái lập chỉ mục |
| GET | /documents/runtime | Staff | ready, model cấu hình và model đã tải; lỗi Ollama trả ready false |
| POST | /documents/upload | Admin | Multipart file tối đa 10 MiB; PDF/DOCX/TXT/MD/Markdown; 201, phải kiểm tra status |
| POST | /documents/{document_id}/reindex | Admin | Lập chỉ mục lại tài liệu đã có |
| DELETE | /documents/{document_id} | Admin | Ngừng truy xuất rồi xóa dữ liệu tài liệu; trả deleted |
| GET | /documents/{document_id}/chunks | Staff | Các đoạn của tài liệu |
| GET | /documents/{document_id}/chunks/{chunk_id} | Staff | Query index_version tùy chọn để phát hiện nguồn đã đổi |
| POST | /rag/search | Staff | query 1-2000, top_k 1-20 mặc định 5; retrieval thử |
| POST | /rag/answer | Staff | query và top_k; trả đáp án, grounded, citations và dữ liệu chẩn đoán nội bộ |
| POST | /orders/lookup | Staff | order_id, customer_id; tra cứu theo chủ đơn |
| GET | /orders/{order_id} | Staff | Query customer_id; không thuộc khách trả 404 |
| POST | /demo/seed | Admin | Tạo dữ liệu demo lặp lại an toàn, không phải reset |
| GET | /health | Công khai | status ok, service; không chứng minh Ollama/DB/vector sẵn sàng |

API staff cho phép chỉ định khách để vận hành nội bộ, không dùng thay xác minh khách công khai. Bộ lọc sla nhận on_track, overdue, met, breached, cancelled hoặc none; giá trị khác trả 422. status/priority hiện là chuỗi lọc so khớp, giá trị không có có thể trả danh sách rỗng. Chưa phân trang Inbox.

## Snapshot widget

GET /widget/session trả conversation_id, display_name, status, expires_at, history_truncated và messages. Mỗi tin chứa id, sender_type, content, created_at, client_message_id của tin khách hoặc null, cùng citations chỉ gồm source/page/location/quote. Không trả ticket, ghi chú nội bộ, agent_id, ID tài liệu/chunk hoặc retrieval thô.

Chỉ trả 200 tin gần nhất theo thứ tự thời gian; history_truncated báo còn tin cũ. POST /widget/messages thêm message_id, duplicate và ai_error. Lỗi provider sau khi lưu tin có thể trả 200 kèm ai_error và không có tin AI mới; 200 không tự chứng minh đã có đáp án. Nếu phiên bị thu hồi/hết hạn trong lúc model chạy, kiểm tra lại phiên trước trả snapshot và trả 401.

UUID phải giữ khi thử lại cùng tin. Cùng UUID khác nội dung trả 409; retry tin cũ sau resolved không tạo ticket mới. Hội thoại closed từ chối gửi kể cả retry. UUID chưa được xác nhận chỉ giữ trong trang hiện tại, tải lại trang có thể mất draft/UUID. Tin agent chưa có khóa idempotency; khi lỗi mạng cần đọc lại lịch sử trước gửi lại để tránh trùng.

## Hoàn tất ticket

Payload ví dụ, các ID phải lấy từ GET chi tiết hiện tại:

```json
{
  "status": "resolved",
  "ticket_id": "ticket-id-from-detail",
  "last_customer_message_id": "message-id-from-detail",
  "note": "Đã hướng dẫn điều kiện đổi trả."
}
```

status chỉ resolved/closed. ticket_id dài 1-64; last_customer_message_id bắt buộc có trường nhưng được null nếu chưa có tin khách, chuỗi tối đa 64. note dài 1-2000, trim và không được rỗng. Schema không nhận trường thừa. Ticket phải thuộc hội thoại. Hoàn tất áp dụng cho tất cả ticket open/assigned trong hội thoại, lưu cùng transaction với thông báo trạng thái chung.

Thành công trả `{"status":"resolved","duplicate":false}`. Retry cùng ticket/trạng thái/người/ghi chú đã chốt trả duplicate true và trạng thái hội thoại hiện tại; không sửa lượt đang hoạt động mới. Sai người hoặc tin khách cuối đã đổi trả 409. Client đọc lại chi tiết, giữ ghi chú để người phụ trách quyết định tiếp. Khách nhắn sau resolved mở ticket mới và xóa phân công; closed yêu cầu kết thúc phiên và tạo phiên mới.

## Chọn công cụ và nhật ký

Từ migration v5, mỗi message trong GET chi tiết Inbox có thêm tool_trace (dict hoặc null), chỉ cho staff. Trường này ghi pending, clarification, executed, rag, provider_error hoặc skipped, kèm mã đơn/tool/kết quả kiểm tra khi có. Không chứa mã vận đơn hay phản hồi thô của model. Pending chỉ có nghĩa đã bắt đầu lựa chọn, không chứng minh tool đã chạy; tiến trình dừng hoặc lỗi DB có thể giữ pending. Widget vẫn dùng snapshot lọc riêng và không nhận trace.

Tin có đúng một mã đơn rõ ràng thêm bước chọn tool ngoài SQL transaction. Backend kiểm tra schema, khóa lại hội thoại và chỉ thực thi khi còn open/đúng tin khách cuối; chủ đơn lấy theo khách trong DB. Model chọn rag thì dùng RAG chính sách hiện có. Tool trả trạng thái qua mẫu cố định, không đưa dữ liệu đơn cho model sinh lại. Lỗi chọn tool dùng ai_error như lỗi provider; lỗi SQL khi tra đơn trả 503, giữ inbound đã commit. Không thêm endpoint tool công khai hoặc quyền cho model.

## SLA và lỗi

SLA gồm ticket_id, conversation_id, target_minutes, due_at, responded_at và status. due_at/response là ISO 8601 UTC; datetime khác trong JSON có thể không chứa offset do SQLite, frontend hiện diễn giải timestamp lưu DB là UTC. Hạn từ tạo ticket theo ưu tiên, không reset khi tiếp nhận; đúng thời điểm hạn vẫn đạt. cancelled là kết thúc trước phản hồi, không phải đạt. Ticket terminal lấy first_response_at đã chốt. Tóm tắt chọn ticket đang chờ có hạn sớm nhất, nếu không có chọn ticket mới nhất.

| HTTP | Ý nghĩa cần xử lý |
|---|---|
| 400 | File không hợp lệ hoặc vượt giới hạn ở upload |
| 401 | Chưa đăng nhập, phiên hết hạn/thu hồi hoặc tài khoản vô hiệu |
| 403 | Thiếu CSRF, sai vai trò hoặc thiếu quyền admin |
| 404 | Hội thoại/ticket/tài liệu/nguồn không tồn tại hoặc đơn không thuộc khách |
| 409 | Tranh chấp trạng thái, tin mới, UUID khác nội dung, tài liệu đang đổi hoặc nguồn cũ |
| 422 | Payload/schema không hợp lệ; detail có thể là danh sách lỗi Pydantic |
| 429 | Giới hạn IP hoặc AI widget bận; đọc Retry-After |
| 503 | ProviderError tới handler chung; không tự coi là RAG từ chối |

Lỗi nghiệp vụ thường có `detail` dạng chuỗi. Giới hạn widget mỗi IP/phút: 6 tạo phiên, 10 gửi tin, 6 handoff; đăng nhập 10 lần/phút. Một lượt AI widget chạy cùng lúc; slot bận trả 429 trước lưu tin. Chưa điều phối cùng các API RAG nội bộ. Từ chối RAG có nguồn thiếu/kiểm định không đạt là kết quả nghiệp vụ, khác lỗi provider và khác giới hạn gửi.
