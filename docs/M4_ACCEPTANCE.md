# Kiểm chứng chức năng M4

Ngày 15/09/2026. Trạng thái: đã kiểm chứng local bằng kiểm thử tự động, smoke HTTP với Ollama thật và QA giao diện đợt trước; chờ người dùng/GVHD duyệt. Người dùng cho phép tiếp tục triển khai khi bận, không đồng nghĩa đã chấm nhãn/đáp án M3 hoặc nghiệm thu M4.

## Cách chạy lại

Chạy từ root repo, dùng Python và dependency dự án đã cài. Các unittest dùng DB riêng. Smoke tự đặt đường dẫn DB/vector/tài liệu tạm trước khi nạp ứng dụng, chạy migration/lifespan thật, tạo mật khẩu ngẫu nhiên và đăng nhập qua API; không sửa .env hoặc tài khoản hiện có. Cần Ollama local sẵn sàng với qwen3:4b và embeddinggemma:300m. Chạy smoke bằng tiến trình riêng như lệnh dưới, không import và gọi trong server đang dùng.

```powershell
python -m unittest discover -s app/tests -v
python -m app.tests.smoke_m4
npm --prefix frontend run build
```

smoke_m4 dùng TestClient để gọi HTTP qua ứng dụng ASGI; không mở cổng mạng, không chạy trình duyệt hoặc mô phỏng tải. Chỉ patch biến đường dẫn/env cho tiến trình thử; embedding, model, authentication, ingestion, RAG, migration và nghiệp vụ chạy thật. Assertion thất bại trả exit code khác 0, không chuyển lỗi thành thành công. Thư mục tạm dọn khi kết thúc; JSON cuối lưu kết quả/timing/digest, không in mật khẩu/cookie.

## Ma trận truy vết

Tên kiểm thử nằm trong app/tests; UC tham chiếu [DESIGN.md](DESIGN.md). Dùng cùng bộ kiểm thử hiện có thay vì sao chép ca sang framework mới.

| Tiêu chí | Use Case | Bằng chứng tự động | Trạng thái |
|---|---|---|---|
| Đăng nhập, cookie, thu hồi, tài khoản vô hiệu | UC01-02 | test_auth_handoff: test_password_and_cookie_session_lifecycle, test_expired_and_disabled_sessions | Đạt local |
| Vai trò, CSRF, giả mạo người gửi | UC01, UC08 | test_auth_handoff: test_auth_roles_csrf_and_forged_agent | Đạt local |
| Phiên khách cách ly, không truy cập API staff | UC03 | test_widget: test_session_isolation_csrf_and_forged_fields | Đạt local |
| Tải, lập chỉ mục, nguồn bền, retry và xóa | UC05 | test_rag: test_persistent_vectors_metadata_duplicate_reindex_delete, test_failed_embedding_can_retry_and_non_admin_cannot_mutate | Đạt local |
| Lưu khách trước model, lỗi provider giữ tin | UC04 | test_rag: test_review_provider_error_preserves_inbound_without_unverified_ai | Đạt local |
| UUID trùng, payload riêng tư và provider lỗi | UC03-04 | test_widget: test_message_retry_public_payload_and_provider_failure | Đạt local |
| Hai nhân viên tranh chấp tiếp nhận | UC07 | test_auth_handoff: test_two_agents_race_to_accept | Đạt local |
| Handoff không chờ model và không lưu AI muộn | UC06 | test_widget: test_rate_limit_capacity_and_handoff_during_generation | Đạt local |
| Đóng phiên/hoàn tất khi AI đang chờ | UC03, UC09 | test_widget: test_end_session_during_generation_prevents_late_disclosure, test_finish_during_inflight_ai_prevents_late_reply | Đạt local |
| Chỉ chủ hội thoại trả lời | UC08 | test_inbox: test_accept_and_agent_reply | Đạt local |
| SLA ranh giới, phản hồi thật, quá hạn, cancelled | UC11 | test_inbox: test_sla_deadline_acceptance_and_sender_isolation, test_sla_first_reply_boundary_late_and_cancelled, test_sla_filters_and_earliest_pending_ticket | Đạt local |
| Hoàn tất đúng người, ghi chú và tin khách cuối | UC09 | test_widget: test_finish_requires_owner_valid_payload_and_current_customer_message | Đạt local |
| Tranh chấp tin mới không làm mất inbound | UC09-10 | test_widget: test_finish_racing_customer_message_never_loses_inbound | Đạt local |
| Giải quyết, mở lượt mới, retry, SLA lịch sử, đóng | UC09-10 | test_widget: test_resolve_reopen_close_preserves_ticket_history_and_sla | Đạt local |
| Migration cũ chạy lại không mất dữ liệu | UC09, UC11 | test_auth_handoff: test_migration_preserves_legacy_records_and_is_repeatable | Đạt local |
| Tên khách không cấp quyền đơn có sẵn | UC03 | test_widget: test_unverified_name_cannot_claim_existing_order | Đạt local |
| Tải tài liệu qua API rồi chat thật tới kết thúc | UC02-10 | smoke_m4 với Ollama thật, đăng nhập thật và store tạm | Đạt ngày 15/09 |
| Polling, mất mạng, draft, đổi người phụ trách | UC03, UC11 | QA Edge 14/09, docs/DEMO.md; bản build desktop/mobile 390px | Đạt đợt trước, không đo lại trong đợt tài liệu |
| Chấm chất lượng ngữ nghĩa | UC12 | Phiếu M3 còn trống; CLI giữ tỷ lệ null khi chưa chấm | Chờ người duyệt |

## Kết quả đợt này

53 unittest đạt; Vite build đạt và assets giữ nguyên. Smoke mới hoàn tất toàn luồng với một câu hỏi có nguồn: 16,217 giây cho request hỏi đáp, 28,088 giây toàn lượt gồm kiểm tra model, migration, đăng nhập, upload/embedding và các bước hỗ trợ. Mở lại vector từ đĩa trước truy vấn. Kiểm tra quote nằm trong tài liệu, câu trả lời có mốc 7 ngày, UUID không tạo trùng, người lạ không đọc phiên, AI không phát sinh thêm sau handoff, ghi chú không lộ, SLA ticket cũ giữ nguyên và logout thu hồi quyền.

Đây là một lần smoke trên câu hỏi chính sách giả lập; không tính percentile, độ đúng RAG, tải đồng thời hoặc so tốc độ với benchmark. TestClient không chứng minh proxy/HTTPS/browser hoạt động; phần giao diện dựa trên QA đã ghi ngày 14/09. Không thay model/prompt/retrieval hoặc chạy lại các tập benchmark.

| Model | Digest quan sát trong smoke |
|---|---|
| qwen3:4b | 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7 |
| embeddinggemma:300m | 85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1 |

## Điều kiện còn mở

Hồ sơ Mermaid đã có BFD, luồng phân làn, ERD, trạng thái và Sequence, kèm Use Case và hợp đồng API. Chưa có file BPMN 2.0, mockup được duyệt, nguồn tham khảo học thuật hoàn chỉnh hoặc xác nhận GVHD. Cần người dùng duyệt nghiệp vụ khi có thời gian; phần này không chặn tiếp tục M5.

M4 chưa nghiệm thu toàn bộ: polling cùng origin chưa phải push realtime; chưa kiểm thử tải, lịch làm việc, SLA giải quyết, phân trang hoặc triển khai cloud. M3 vẫn chờ chấm nhãn/đáp án và nguồn/câu hỏi độc lập. M5 tiếp theo cần tool calling với schema và quyền xác định bởi server; không để LLM tự khai customer_id hoặc tự thực hiện hành động ghi. Kênh thứ hai chỉ tính hoàn tất khi có tài khoản/tích hợp thật và kiểm chứng gửi nhận.

## Hồi quy khi thêm M5

Ngày 15/09/2026, migration v5 và bộ chọn tool đơn hàng được kiểm chứng bằng tổng 59 unittest, gồm các ca M4 hiện có. Smoke HTTP toàn luồng M4 với Ollama thật chạy lại đạt: câu hỏi 15,175 giây, toàn luồng 22,249 giây. UI và assets không đổi. Nhật ký tool chỉ thêm vào API chi tiết staff; snapshot widget không lộ trace. Kết quả tool/model và giới hạn riêng tại docs/M5_TOOLS.md, không thay nghiệm thu người dùng M4 hoặc chấm ngữ nghĩa M3.
