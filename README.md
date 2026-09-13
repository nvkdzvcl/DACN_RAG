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

Đã có Unified Inbox với đăng nhập nhân viên, tiếp nhận và trả lời theo người phụ trách; AI dừng khi handoff. Backend chạy FastAPI/SQLite, frontend React/Vite. RAG chạy Ollama local (qwen3:1.7b + embeddinggemma:300m), Qdrant embedded lưu bền, có trích nguồn và giao diện Kho tri thức. Tin khách được lưu trước khi gọi LLM; kiểm tra lại handoff/tin mới/phiên bản nguồn trước khi lưu AI.

Chạy lần đầu tại root repo:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.create_user admin --role admin
python -m uvicorn app.main:app --reload
```

CLI yêu cầu nhập mật khẩu riêng (12-128 ký tự), không có tài khoản mặc định. Terminal thứ hai: `cd frontend`, rồi `npm run dev`. Xem `docs/DEMO.md` để tạo nhân viên và thử luồng handoff. API nội bộ hiện yêu cầu phiên nhân viên; phiên khách/widget triển khai ở mốc sau.

Kiểm tra: `python -m unittest discover -s app/tests -v`; frontend: `npm --prefix frontend run build`. Tiến độ thực tế trong `docs/TASKS.md`, kế hoạch trong `ROADMAP.md`.

## RAG local với Ollama

Máy hiện tại đã có Ollama portable và hai model tại `data/runtime/` (không đưa lên Git). Sau khi khởi động lại máy, chạy `powershell -File scripts/start-ollama.ps1` trong terminal riêng; giữ terminal mở. Dịch vụ chỉ nghe 127.0.0.1:11434. Không cần API key.

Máy mới: cài Ollama từ https://ollama.com/download/windows rồi chạy `ollama pull embeddinggemma:300m` và `ollama pull qwen3:1.7b`. Sao chép `.env.example` thành `.env` nếu chưa có, rồi chạy `python -m uvicorn app.main:app --reload --env-file .env`. Không ghi đè `.env` đang có. Cài dependencies bằng `python -m pip install -r requirements-dev.txt`.

Đăng nhập admin, chọn **Kho tri thức**, tải PDF/DOCX/TXT/Markdown tối đa 10 MB. File cũ từ prototype cần **Lập chỉ mục lại**. Nhân viên được xem tài liệu và hỏi thử; chỉ admin được tải/xóa/lập chỉ mục lại. PDF giữ số trang; DOCX giữ đoạn/bảng; TXT giữ dòng. PDF scan cần OCR bên ngoài.

Qdrant embedded chỉ dùng **một API worker**; không mở hai tiến trình cùng `QDRANT_PATH`. Chuyển sang Qdrant server trước khi chạy nhiều worker. Sao lưu cùng SQL DB, `data/knowledge_base` và `data/vectors` khi API đã dừng. Model và runtime tải lại được. Đổi embedding model phải lập chỉ mục lại.

Kiểm chứng mô hình thật, DB/vector tạm: `python -m app.tests.smoke_ollama`. Lượt đầu tải model có thể mất hơn một phút. Ngưỡng score 0.35 là cấu hình khởi đầu, chưa hiệu chỉnh bằng bộ đánh giá. Citation kiểm tra nguồn và câu trích nguyên văn, chưa chứng minh mọi mệnh đề trong câu trả lời đều được nguồn hỗ trợ.

## Đánh giá RAG

Bộ 72 câu tiếng Việt và chính sách giả lập nằm trong `evals/rag/`; nhãn đang chờ người dùng duyệt. Chạy `python -m app.evaluate_rag --split dev --output evals/rag/runs/my-dev-run`, rồi dùng `--split test` và thư mục mới cho tập kiểm tra. Trình chạy dùng SQL/vector tạm, ghi từng đáp án/lỗi và tổng hợp Recall@k, citation, từ chối, p50/p95; không sửa dữ liệu ứng dụng. Xem `evals/rag/README.md` để hiểu mẫu số và giới hạn từng chỉ số, `docs/RAG_EVALUATION.md` để xem kết quả baseline và ca cần sửa.
