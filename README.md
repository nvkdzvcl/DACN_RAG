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

Đã có Unified Inbox với đăng nhập nhân viên, tiếp nhận và trả lời theo người phụ trách; AI dừng khi handoff. Backend chạy FastAPI/SQLite, frontend React/Vite. RAG chạy Ollama local (qwen3:4b + embeddinggemma:300m), Qdrant embedded lưu bền, có trích nguồn và giao diện Kho tri thức. LLM chọn câu nguồn bằng ID, backend ghép nguyên văn rồi gọi kiểm định. Tin khách được lưu trước khi gọi LLM; kiểm tra lại handoff/tin mới/phiên bản nguồn trước khi lưu AI.

Chạy lần đầu tại root repo:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.create_user admin --role admin
python -m uvicorn app.main:app --reload
```

CLI yêu cầu nhập mật khẩu riêng (12-128 ký tự), không có tài khoản mặc định. Terminal thứ hai: `cd frontend`, rồi `npm run dev`. Xem `docs/DEMO.md` để tạo nhân viên và thử luồng handoff. API nội bộ yêu cầu phiên nhân viên; khách dùng `/chat` hoặc `/widget-demo.html` với phiên riêng, không cần tài khoản nhân viên.

Kiểm tra: `python -m unittest discover -s app/tests -v`; frontend: `npm --prefix frontend run build`. Tiến độ thực tế trong `docs/TASKS.md`, kế hoạch trong `ROADMAP.md`.

## Website chat widget

Mở `http://localhost:5173/widget-demo.html`, chọn Hỗ trợ và nhập tên; `/chat` là trang chat trực tiếp. Widget gọi RAG hiện có, hiển thị trích dẫn đã lưu, cho phép Gặp nhân viên và nhận phản hồi qua polling mỗi 3 giây khi tab hiển thị, không có thao tác đang chờ. Inbox nhân viên cũng tự cập nhật mỗi 3 giây; nút Làm mới tải lại cả danh sách và hội thoại.

Nhúng trên website cùng origin đã phục vụ frontend và proxy `/api` tới FastAPI:

```html
<script src="/widget.js" defer></script>
```

Giữ đường dẫn `/chat` trả về frontend SPA khi phục vụ bản build. Origin gồm scheme, hostname và port; không trộn `localhost` với `127.0.0.1`. Chưa hỗ trợ nhúng khác origin. Ngoài development cần HTTPS để cookie Secure hoạt động; chạy một API worker.

Cookie HttpOnly riêng có hạn cố định 24 giờ, DB chỉ lưu hash token; server tạo danh tính khách và gắn phiên với một hội thoại. Tên tự nhập không xác minh chủ đơn hàng: tra mã đơn không thuộc khách này chuyển nhân viên, không lộ thông tin đơn. Đóng khung chat giữ phiên; Kết thúc thu hồi phiên, đóng hội thoại/ticket và giữ lịch sử cho nhân viên. Widget hiển thị tối đa 200 tin gần nhất, giữ ID khi thử gửi lại trong cùng trang. Giới hạn mỗi IP/phút: 6 yêu cầu tạo phiên, 10 gửi tin, 6 chuyển nhân viên; chỉ một lượt AI từ widget được xử lý cùng lúc, lượt bận trả 429 trước khi lưu. Handoff vẫn hoạt động trong lúc AI chờ; giới hạn này chưa điều phối các lời gọi RAG nội bộ của nhân viên.

## Inbox tự cập nhật và SLA phản hồi đầu tiên

Danh sách, nội dung, trạng thái phụ trách và SLA tự cập nhật mỗi 3 giây khi đang xem Inbox. Polling tạm dừng khi tab ẩn, mở Kho tri thức hoặc đang gửi/tiếp nhận; không gọi chồng trong cùng vòng cập nhật. Giữ hội thoại đang chọn, bản nháp và nội dung cũ khi mất mạng; báo dữ liệu có thể đã cũ và tự thử lại. API vẫn kiểm tra quyền nhân viên ở từng thao tác.

SLA demo tính liên tục 24/7 từ thời điểm tạo ticket đến tin đầu tiên có người gửi là nhân viên xác thực. Tiếp nhận, tin khách và AI không tính là phản hồi, không đặt lại hạn.

| Ưu tiên ticket | Hạn phản hồi đầu tiên |
|---|---|
| Khẩn cấp | 5 phút |
| Cao | 15 phút |
| Bình thường | 60 phút |
| Thấp | 240 phút |

Inbox hiển thị hạn, trạng thái và bộ lọc SLA; số Quá hạn chỉ đếm hội thoại đang chờ phản hồi trong bộ lọc hiện tại. Phản hồi đúng thời điểm hạn vẫn đạt; sau hạn là trễ. Đóng trước phản hồi mang trạng thái riêng, không tính đạt SLA. Với nhiều ticket, lấy ticket đang chờ có hạn sớm nhất; nếu không còn chờ, lấy ticket mới nhất. Chi tiết giữ SLA từng ticket.

Chính sách cố định được tính từ timestamp hiện có, áp dụng cả ticket cũ; chưa có lịch làm việc/ngày nghỉ, hạn giải quyết, escalation hoặc thống kê SLA đã kiểm toán. Cần lưu phiên bản chính sách và deadline trước khi cho phép sửa quy tắc. Polling không phải WebSocket/SSE; chưa đo tải lớn hoặc bảo đảm độ trễ realtime.

## RAG local với Ollama

Máy hiện tại đã có Ollama portable, model chat qwen3:4b và embeddinggemma:300m tại `data/runtime/` (không đưa lên Git); qwen3:1.7b cũ được giữ để đối chiếu. Sau khi khởi động lại máy, chạy `powershell -File scripts/start-ollama.ps1` trong terminal riêng; giữ terminal mở. Dịch vụ chỉ nghe 127.0.0.1:11434. Không cần API key.

Máy mới: cài Ollama từ https://ollama.com/download/windows rồi chạy `ollama pull embeddinggemma:300m` và `ollama pull qwen3:4b`. Sao chép `.env.example` thành `.env` nếu chưa có, rồi chạy `python -m uvicorn app.main:app --reload --env-file .env`. Nếu nâng cấp từ bản 1.7B, đổi riêng `LLM_MODEL=qwen3:4b` trong `.env` và khởi động lại backend để nạp cấu hình. Không ghi đè `.env` đang có. Cài dependencies bằng `python -m pip install -r requirements-dev.txt`.

Đăng nhập admin, chọn **Kho tri thức**, tải PDF/DOCX/TXT/Markdown tối đa 10 MB. File cũ từ prototype cần **Lập chỉ mục lại**. Nhân viên được xem tài liệu và hỏi thử; chỉ admin được tải/xóa/lập chỉ mục lại. PDF giữ số trang; DOCX giữ đoạn/bảng; TXT giữ dòng. PDF scan cần OCR bên ngoài.

Qdrant embedded chỉ dùng **một API worker**; không mở hai tiến trình cùng `QDRANT_PATH`. Chuyển sang Qdrant server trước khi chạy nhiều worker. Sao lưu cùng SQL DB, `data/knowledge_base` và `data/vectors` khi API đã dừng. Model và runtime tải lại được. Đổi embedding model phải lập chỉ mục lại.

Kiểm chứng mô hình thật, DB/vector tạm: `python -m app.tests.smoke_ollama`. Lượt đầu tải model có thể mất hơn một phút. Giữ ngưỡng score 0.35 sau chẩn đoán trên dev. Model chọn tối đa ba cặp source_id/sentence_id; backend xác thực ID rồi lấy nguyên văn, chỉ chuẩn hóa khoảng trắng. Đáp án giữ ngôn ngữ nguồn; chưa dịch hoặc tổng hợp tự do. Tách câu bằng dấu chấm/chấm hỏi/chấm than theo sau bởi khoảng trắng, giữ chấm phẩy cùng điều kiện; chưa xử lý đầy đủ chữ viết tắt hoặc nguồn dài bị cắt.

JSON Schema gửi Ollama chỉ cho chọn ID câu thực có của từng nguồn, dùng một nhánh `oneOf` cho mỗi nguồn. Backend vẫn kiểm tra ID/trùng sau phản hồi nếu provider bỏ qua schema; ràng buộc không bảo đảm chọn đúng nội dung và không thêm lượt gọi model.

Một lượt Ollama riêng kiểm định đáp án với câu hỏi/lịch sử và toàn bộ nguồn đã cấp cho LLM. Chỉ trả lời khi đủ ngữ cảnh, nguồn nhất quán và dữ kiện có căn cứ; JSON kiểm định lỗi dẫn đến từ chối. Provider chưa hoàn tất, hết giới hạn sinh hoặc không có nội dung cuối được báo lỗi dịch vụ và giữ tin khách. Cấu hình chat: think=false, context 8192, tối đa 700 token, giải phóng model sau mỗi gọi. Kiểm định dùng cùng model nên vẫn có thể sai, tăng độ trễ và không thay người duyệt. Backend kiểm tra lại phiên bản mọi nguồn đã kiểm định trước khi lưu AI.

## Đánh giá RAG

Bộ 72 câu tiếng Việt và chính sách giả lập nằm trong `evals/rag/`; nhãn đang chờ người dùng duyệt. Chạy `python -m app.evaluate_rag --split dev --output evals/rag/runs/my-dev-run`, rồi dùng `--split test` và thư mục mới cho tập kiểm tra. Trình chạy dùng SQL/vector tạm, ghi từng đáp án/lỗi và tổng hợp Recall@k, citation, từ chối, p50/p95; không sửa dữ liệu ứng dụng. Xem `evals/rag/README.md` để hiểu mẫu số và giới hạn từng chỉ số, `docs/RAG_EVALUATION.md` để xem kết quả baseline và ca cần sửa.

Bộ bổ sung `evals/rag-documents/` có 24 câu trên PDF ba trang và DOCX có bảng. Chạy `python -m app.evaluate_rag --dataset evals/rag-documents --split test --output evals/rag-documents/runs/my-run`. Trình chạy kiểm tra gold theo trang/đoạn/bảng, lưu hash file nhị phân và log ingestion; không tự nạp `.env`. Bộ mới giữ cấu hình RAG đã chốt, nhãn vẫn chờ người duyệt; không gộp điểm với bộ TXT để tuyên bố cải thiện.

Chấm bản sao `human-review.jsonl`, rồi tổng hợp bằng `python -m app.review_rag --run evals/rag/runs/bounded-ids-test --reviews PHIEU_DA_CHAM.jsonl --output BAO_CAO_MOI.json`. CLI không gọi model; chỉ tính rating có tên người chấm và nhãn được duyệt, báo mẫu số riêng cùng ca chưa chấm, không ghi đè kết quả. Cách điền và trường áp dụng trong `evals/rag/README.md`.
