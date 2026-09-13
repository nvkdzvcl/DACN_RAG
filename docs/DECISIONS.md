# Quyết định ban đầu

## Bối cảnh nghiệp vụ

Chọn cửa hàng bán lẻ trực tuyến giả lập để có đủ tình huống hỏi đáp chính sách và tra cứu đơn hàng mà không phụ thuộc dữ liệu doanh nghiệp thật.

## Kiến trúc triển khai

Bắt đầu bằng modular monolith: FastAPI, PostgreSQL, Qdrant hoặc pgvector qua adapter, Next.js/React. Có thể tách worker và dịch vụ riêng sau khi luồng MVP ổn định.

## Cấu hình thực tế ngày 13/09/2026

MVP local đang dùng FastAPI + SQLAlchemy/SQLite và React/Vite. Chưa chuyển Next.js/PostgreSQL/Qdrant. Auth dùng stdlib PBKDF2 và token phiên ngẫu nhiên lưu hash trong DB, không thêm thư viện JWT. Frontend/API cùng origin; cookie HttpOnly/SameSite=Strict, header chống CSRF cho thao tác ghi. Chạy một API worker; rate limit chia sẻ và xử lý LLM ngoài transaction là yêu cầu trước khi hosting.

Admin cấp tài khoản qua CLI hoặc API, agent chỉ trả lời hội thoại mình phụ trách. Các API nhận tin và tra cứu đơn hiện là nội bộ được bảo vệ; phiên khách riêng sẽ thêm cùng widget. Migration cộng thêm cột có phiên bản và giữ dữ liệu; chuyển assignment demo thiếu nhân viên về hàng chờ để nhận lại.

## Chính sách an toàn câu trả lời

Không suy đoán trạng thái đơn hàng, chính sách hoặc thông tin khách hàng. Nếu không có bằng chứng hoặc tool trả lỗi, trả lời có kiểm soát và tạo đề xuất chuyển nhân viên khi phù hợp.

## RAG local theo lựa chọn người dùng ngày 13/09/2026

Chọn Ollama local thay Gemini: qwen3:1.7b cho chat, embeddinggemma:300m cho embedding 768 chiều; model giải phóng sau mỗi gọi để giảm dùng RAM. Máy kiểm thử có 16 GB RAM và RTX 3060 Laptop GPU 6 GB VRAM. Gọi HTTP bằng httpx đã có; thêm qdrant-client vì cần vector DB lưu bền, không tự viết bộ lưu vector.

Qdrant embedded tại data/vectors, một worker; SQLite tiếp tục giữ metadata/lịch sử. Mỗi lượt lập chỉ mục có UUID phiên bản, tìm kiếm chỉ dùng tài liệu indexed đúng embedding model. Xóa/chỉ mục lỗi không còn được truy xuất. Migration v2 cộng metadata và last_customer_message_id; v1 vẫn giữ dữ liệu cũ.

Ingestion chạy đồng bộ trong threadpool, khóa một tác vụ sửa kho tri thức mỗi lúc và có retry thủ công. Khởi động lại đánh dấu processing bị gián đoạn thành failed. Chưa có durable job queue/OCR; thêm worker nền khi dung lượng hoặc nhu cầu hosting tăng. Network call nằm ngoài SQL transaction; final check ngăn AI muộn sau handoff/tin khách mới/nguồn thay đổi.

LLM trả JSON có supported, answer và nguồn kèm quote. Backend kiểm tra schema, source ID, quote nguyên văn và phiên bản tài liệu. Ngưỡng retrieval ban đầu 0.35; chưa có reranker hay bộ kiểm chứng entailment. Cần bộ 60-100 câu đánh giá trước nghiệm thu chất lượng M3.
