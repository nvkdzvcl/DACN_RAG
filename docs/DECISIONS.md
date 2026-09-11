# Quyết định ban đầu

## Bối cảnh nghiệp vụ

Chọn cửa hàng bán lẻ trực tuyến giả lập để có đủ tình huống hỏi đáp chính sách và tra cứu đơn hàng mà không phụ thuộc dữ liệu doanh nghiệp thật.

## Kiến trúc triển khai

Bắt đầu bằng modular monolith: FastAPI, PostgreSQL, Qdrant hoặc pgvector qua adapter, Next.js/React. Có thể tách worker và dịch vụ riêng sau khi luồng MVP ổn định.

## Chính sách an toàn câu trả lời

Không suy đoán trạng thái đơn hàng, chính sách hoặc thông tin khách hàng. Nếu không có bằng chứng hoặc tool trả lỗi, trả lời có kiểm soát và tạo đề xuất chuyển nhân viên khi phù hợp.
