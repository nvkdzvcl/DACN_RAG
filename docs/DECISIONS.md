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
