# Multi-Channel AI Customer Support Platform

Đồ án xây dựng nền tảng trợ lý AI hỗ trợ khách hàng đa kênh dựa trên Agentic RAG.

## Phạm vi nghiệp vụ mặc định

- Doanh nghiệp mẫu: cửa hàng bán lẻ trực tuyến.
- Khách hàng gửi tin nhắn qua Website Chat Widget và một kênh mở rộng.
- AI trả lời chính sách giao hàng, đổi trả, thanh toán và bảo hành từ Knowledge Base.
- AI tra cứu trạng thái đơn hàng qua tool nội bộ giả lập.
- Hội thoại được phân loại theo mức độ ưu tiên và SLA.
- Khi phát hiện khiếu nại hoặc khách yêu cầu gặp người thật, hệ thống tạo handoff kèm tóm tắt.

## Nguyên tắc triển khai

- Phát triển Windows native, không phụ thuộc WSL.
- Backend và nghiệp vụ tách module; dữ liệu hội thoại không trộn với dữ liệu vector.
- AI chỉ trả lời dựa trên bằng chứng; thiếu bằng chứng thì nói rõ không đủ thông tin.
- Mọi hành động tool và handoff đều có log.

## Trạng thái

Đã có Unified Inbox với đăng nhập nhân viên, tiếp nhận và trả lời theo người phụ trách; AI dừng khi handoff. Backend chạy FastAPI/SQLite, frontend React/Vite. RAG hiện là bản local với hash embedding và câu trả lời trích đoạn, chưa dùng LLM thật hoặc vector DB lưu bền.

Chạy lần đầu tại root repo:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.create_user admin --role admin
python -m uvicorn app.main:app --reload
```

CLI yêu cầu nhập mật khẩu riêng (12-128 ký tự), không có tài khoản mặc định. Terminal thứ hai: `cd frontend`, rồi `npm run dev`. Xem `docs/DEMO.md` để tạo nhân viên và thử luồng handoff. API nội bộ hiện yêu cầu phiên nhân viên; phiên khách/widget triển khai ở mốc sau.

Kiểm tra: `python -m unittest discover -s app/tests -v`; frontend: `npm --prefix frontend run build`. Tiến độ thực tế trong `docs/TASKS.md`, kế hoạch trong `ROADMAP.md`.
