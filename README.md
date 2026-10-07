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

Lịch sử Inbox đã phân trang 50 tin, có điều hướng tin cũ và về tin mới nhất; bản nháp/ghi chú được giữ khi đổi trang. Trang cũ polling theo mốc tin cố định và vẫn cập nhật trạng thái gửi/nhật ký công cụ. API giới hạn 100 tin mỗi request, trả message_page; client cần theo next_before để đọc đủ lịch sử. Widget cũng đã có phân trang 50 tin với mốc thuộc phiên khách; ticket chưa phân trang. Xem [API.md](docs/API.md#phân-trang-lịch-sử-inbox).

Inbox đã phân trang 25 hội thoại, tìm kiếm toàn bộ tên/mã khách/kênh và lọc SLA trước chia trang. Giữ hội thoại/bản nháp khi đổi trang; thẻ số ghi rõ tổng khớp bộ lọc và số trên trang. API trả thêm total/offset/limit/has_more; count chỉ còn số dòng trang. Tìm kiếm/SLA vẫn quét dữ liệu theo lô, chưa phải tối ưu cho tải lớn. Chi tiết tại [API.md](docs/API.md).

Hồ sơ kỹ thuật: [thiết kế và sơ đồ](docs/DESIGN.md), [đặc tả API](docs/API.md), [ma trận kiểm chứng M4](docs/M4_ACCEPTANCE.md). Chạy toàn luồng với Ollama thật bằng `python -m app.tests.smoke_m4`; lệnh tự dùng DB/vector/tài liệu tạm. Phần nghiệm thu người dùng và chấm chất lượng M3 vẫn chờ duyệt.

Đã có Unified Inbox với đăng nhập nhân viên, tiếp nhận và trả lời theo người phụ trách; AI dừng khi handoff. Backend chạy FastAPI/SQLite, frontend React/Vite. RAG chạy Ollama local (qwen3:4b + embeddinggemma:300m), Qdrant embedded lưu bền, có trích nguồn và giao diện Kho tri thức. LLM chọn câu nguồn bằng ID, backend ghép nguyên văn rồi gọi kiểm định. Tin khách được lưu trước khi gọi LLM; kiểm tra lại handoff/tin mới/phiên bản nguồn trước khi lưu AI.

Chạy lần đầu tại root repo:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.create_user admin --role admin
python -m uvicorn app.main:app --reload
```

CLI yêu cầu nhập mật khẩu riêng (12-128 ký tự), không có tài khoản mặc định. Terminal thứ hai: `cd frontend`, rồi `npm run dev`. Xem `docs/DEMO.md` để tạo nhân viên và thử luồng handoff. API nội bộ yêu cầu phiên nhân viên; khách dùng `/chat` hoặc `/widget-demo.html` với phiên riêng, không cần tài khoản nhân viên.

Quên mật khẩu tài khoản đã tồn tại: chạy `python -m app.reset_password admin-recovery --env-file .env`, thay username theo tài khoản cần khôi phục. Nhập mật khẩu mới ẩn; lệnh thu hồi tất cả phiên của tài khoản đó, giữ nguyên quyền và trạng thái hoạt động. Không dùng `create_user` để đặt lại mật khẩu. Xem [quy trình khôi phục](docs/OPERATIONS.md#khôi-phục-mật-khẩu-nhân-viên).

Kiểm tra: `python -m unittest discover -s app/tests -v`; frontend: `npm --prefix frontend run build`. Tiến độ thực tế trong `docs/TASKS.md`, kế hoạch trong `ROADMAP.md`.

## Website chat widget

Mở `http://localhost:5173/widget-demo.html`, chọn Hỗ trợ và nhập tên; `/chat` là trang khách hàng gồm Tin nhắn, Tra đơn và Hỏi đáp; widget nhúng dùng giao diện gọn của cùng luồng chat. Widget gọi RAG hiện có, hiển thị trích dẫn đã lưu, cho phép Gặp nhân viên và nhận phản hồi qua polling mỗi 3 giây khi tab hiển thị, không có thao tác đang chờ. Inbox nhân viên cũng tự cập nhật mỗi 3 giây; nút Làm mới tải lại cả danh sách và hội thoại.

Nhúng trên website cùng origin đã phục vụ frontend và proxy `/api` tới FastAPI:

```html
<script src="/widget.js" defer></script>
```

Giữ đường dẫn `/chat` trả về frontend SPA khi phục vụ bản build. Origin gồm scheme, hostname và port; không trộn `localhost` với `127.0.0.1`. Chưa hỗ trợ nhúng khác origin. Ngoài development cần HTTPS để cookie Secure hoạt động; chạy một API worker.

Cookie HttpOnly riêng có hạn cố định 24 giờ, DB chỉ lưu hash token; server tạo danh tính khách và gắn phiên với một hội thoại. Tên tự nhập không xác minh chủ đơn hàng: tra mã đơn không thuộc khách này chuyển nhân viên, không lộ thông tin đơn. Đóng khung chat giữ phiên; Kết thúc thu hồi phiên, đóng hội thoại/ticket và giữ lịch sử cho nhân viên. Widget hiển thị 50 tin mỗi trang, cho xem tin cũ ngoài 200 tin và giữ bản nháp/ID khi thử gửi lại trong cùng trang trình duyệt. Gửi hoặc handoff thành công trở về tin mới nhất; hết phiên không xem tiếp được lịch sử. Giới hạn mỗi IP/phút: 6 yêu cầu tạo phiên, 10 gửi tin, 6 chuyển nhân viên; chỉ một lượt AI từ widget được xử lý cùng lúc, lượt bận trả 429 trước khi lưu. Handoff vẫn hoạt động trong lúc AI chờ; giới hạn này chưa điều phối các lời gọi RAG nội bộ của nhân viên.

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

Chính sách cố định được tính từ timestamp hiện có, áp dụng cả ticket cũ; chưa có lịch làm việc/ngày nghỉ, hạn giải quyết, escalation hoặc thống kê SLA đã kiểm toán. Cần lưu phiên bản chính sách và deadline trước khi cho phép sửa quy tắc. Polling không phải WebSocket/SSE; đã đo tải HTTP local theo [kịch bản riêng](evals/load/README.md), chưa bảo đảm độ trễ realtime hoặc tải production.

## Giải quyết và đóng yêu cầu hỗ trợ

Người đang phụ trách nhập ghi chú nội bộ rồi chọn **Giải quyết** hoặc **Đóng hội thoại** trong Inbox. Cả hai thao tác kết thúc các ticket đang hoạt động và lưu thời điểm/người hoàn tất; admin cũng phải là người phụ trách. Ghi chú bắt buộc, tối đa 2000 ký tự, chỉ hiển thị cho nhân viên. Widget nhận thông báo trạng thái chung.

Sau **Giải quyết**, khách nhắn tiếp trên cùng phiên sẽ tạo ticket mới, chuyển về hàng chờ và bỏ phân công cũ; nhân viên cần tiếp nhận lại, AI vẫn dừng. Gửi lại UUID của tin cũ không mở lượt hỗ trợ mới. Sau **Đóng hội thoại**, khách chỉ xem lịch sử; chọn Kết thúc rồi bắt đầu phiên mới để gửi yêu cầu khác.

Nếu khách có tin mới trước khi thao tác hoàn tất được ghi, API trả 409 để nhân viên đọc lại; ghi chú đang soạn được giữ. Retry cùng ticket/trạng thái/người/ghi chú không kết thúc nhầm lượt hỗ trợ mới. SLA phản hồi đầu được chốt trên từng ticket khi kết thúc, nên phản hồi lượt sau không đổi kết quả lượt trước. Migration v4 bổ sung dữ liệu hoàn tất và chốt phản hồi đã quan sát của ticket cũ; không suy đoán thời điểm hoặc người hoàn tất còn thiếu.

## Chọn công cụ đơn hàng M5

Đã có [44 phiếu duyệt nhãn M5](evals/tools/README.md#duyệt-bằng-trình-duyệt-offline) dạng HTML offline và JSON, cùng CLI `python -m app.review_tools`. Trang lưu nháp, kiểm tra quyết định và xuất JSON gắn với bằng chứng lượt đo; CLI gộp phần duyệt bằng `--merge`, chặn xung đột và chỉ tính tỷ lệ trên nhãn được thành viên duyệt. Hiện cả 44 ca chưa duyệt; không coi phiếu trống hoặc điểm tự động là nghiệm thu chất lượng.

Đã đo điều phối bằng Ollama thật trên DB giả lập riêng: bộ gốc tăng từ 17/24 lên 24/24 sau sửa yêu cầu hỗn hợp, hỏi nối tiếp và ngữ cảnh handoff rõ; bộ nối tiếp đạt 8/8, bộ ngữ cảnh mới đạt 10/12. Hai cách nói tự do vẫn nhận nhầm. Nhãn chưa được người duyệt; tập dùng phát triển, nhánh RAG giả lập, chưa nghiệm thu M5. Chạy `python -m app.evaluate_tools --output evals/tools/runs/my-new-run` với thư mục mới; phương pháp và giới hạn tại [evals/tools](evals/tools/README.md).

Trong hội thoại đang mở, tin chứa đúng một mã đơn dạng DH/ORD được model phân loại bằng JSON Schema: tra trạng thái, chuyển nhân viên hoặc hỏi chính sách qua RAG. Nhiều mã đơn yêu cầu khách chọn một mã; yêu cầu gặp nhân viên theo quy tắc vẫn được xử lý ngay. Đây là lựa chọn công cụ có cấu trúc do backend điều phối, chưa phải agent tự lập kế hoạch nhiều bước.

Mã nhận diện chỉ dùng chữ/số ASCII, tổng tối đa 64 ký tự, không phân biệt hoa/thường. Không cắt DH12345 từ DH12345-EXTRA hoặc đổi chữ Unicode giống hình thành mã ASCII; quy tắc đầy đủ tại [M5_TOOLS.md](docs/M5_TOOLS.md).

Nhận diện handoff chuẩn hóa Unicode/khoảng trắng, so đủ từ và bỏ qua riêng cụm trung tính/phủ định rõ: “tiền tệ”, “không cần gặp nhân viên”, một số mẫu hỏi chính sách hoàn tiền. Khiếu nại/yêu cầu gặp người ở phần khác vẫn chuyển giao ngay cả khi AI bận; tin trung tính chịu giới hạn AI thông thường. Bộ chọn tool nhận NFC, văn bản lưu giữ nguyên. Quy tắc chưa hiểu ngữ cảnh hoặc phủ định tự do; giới hạn tại [M5_TOOLS.md](docs/M5_TOOLS.md).

Tool tra đơn chỉ đọc DB giả lập, lấy customer_id từ hội thoại và kiểm tra chủ đơn ngay trước thực thi; không nhận danh tính, URL hoặc công cụ khác từ model. Backend dựng câu trả lời từ dữ liệu đơn, không nhờ model viết lại. Không thấy đơn thuộc khách thì chuyển nhân viên; không tự hủy/sửa đơn. Khách widget ẩn danh chưa được xác minh chủ đơn, tên giống nhau không cấp quyền.

Migration v5 thêm Message.tool_trace cho nhật ký nội bộ; nhân viên mở **Nhật ký công cụ** dưới tin khách trong Inbox để xem trạng thái, mã đơn, hành động và kết quả. Widget không nhận trường này. Lỗi provider giữ tin khách; lỗi DB trả 503 và ghi log, trace có thể còn pending (Chưa có kết quả). Retry UUID cũ không gọi lại tool; cần đọc lịch sử trước khi gửi yêu cầu mới. Cách kiểm chứng và giới hạn tại [M5_TOOLS.md](docs/M5_TOOLS.md); chạy `python -m app.tests.smoke_tools` bằng Ollama thật trên DB/vector tạm.

## RAG local với Ollama

Máy hiện tại đã cài Ollama, có qwen3:4b và embeddinggemma:300m trong kho model của bản cài đặt; kho portable cũ vẫn giữ tại data/runtime. Nếu Ollama đang chạy thì không mở thêm serve. Script `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-ollama.ps1` tái sử dụng dịch vụ ở 127.0.0.1:11434; nếu chưa chạy thì ưu tiên bản cài đặt, dự phòng portable, cho phép hai model nạp và một request song song. ExecutionPolicy chỉ áp dụng cho tiến trình lệnh này. Giữ terminal mở khi script khởi động dịch vụ mới. Không cần API key.

Máy mới: cài Ollama từ https://ollama.com/download/windows rồi chạy `ollama pull embeddinggemma:300m` và `ollama pull qwen3:4b`. Sao chép `.env.example` thành `.env` nếu chưa có, rồi chạy `python -m uvicorn app.main:app --reload --env-file .env`. Nếu nâng cấp từ bản 1.7B, đổi riêng `LLM_MODEL=qwen3:4b` trong `.env` và khởi động lại backend để nạp cấu hình. Không ghi đè `.env` đang có. Cài dependencies bằng `python -m pip install -r requirements-dev.txt`.

Đăng nhập admin, chọn **Kho tri thức**, tải PDF/DOCX/TXT/Markdown tối đa 10 MB. File cũ từ prototype cần **Lập chỉ mục lại**. Nhân viên được xem tài liệu và hỏi thử; chỉ admin được tải/xóa/lập chỉ mục lại. PDF giữ số trang; DOCX giữ đoạn/bảng; TXT giữ dòng. PDF scan cần OCR bên ngoài.

Qdrant embedded chỉ dùng **một API worker**; không mở hai tiến trình cùng `QDRANT_PATH`. Chuyển sang Qdrant server trước khi chạy nhiều worker. Sao lưu cùng SQL DB, `data/knowledge_base` và `data/vectors` khi API đã dừng. Model và runtime tải lại được. Đổi embedding model phải lập chỉ mục lại.

Kiểm chứng mô hình thật, DB/vector tạm: `python -m app.tests.smoke_ollama`. Lượt đầu tải model có thể mất hơn một phút. Giữ ngưỡng score 0.35 sau chẩn đoán trên dev. Model chọn tối đa ba cặp source_id/sentence_id; backend xác thực ID rồi lấy nguyên văn, chỉ chuẩn hóa khoảng trắng. Đáp án giữ ngôn ngữ nguồn; chưa dịch hoặc tổng hợp tự do. Tách câu bằng dấu chấm/chấm hỏi/chấm than theo sau bởi khoảng trắng, giữ chấm phẩy cùng điều kiện; chưa xử lý đầy đủ chữ viết tắt hoặc nguồn dài bị cắt.

JSON Schema gửi Ollama chỉ cho chọn ID câu thực có của từng nguồn, dùng một nhánh `oneOf` cho mỗi nguồn. Backend vẫn kiểm tra ID/trùng sau phản hồi nếu provider bỏ qua schema; ràng buộc không bảo đảm chọn đúng nội dung và không thêm lượt gọi model.

Một lượt Ollama riêng kiểm định đáp án với câu hỏi/lịch sử và toàn bộ nguồn đã cấp cho LLM. Chỉ trả lời khi đủ ngữ cảnh, nguồn nhất quán và dữ kiện có căn cứ; JSON kiểm định lỗi dẫn đến từ chối. Provider chưa hoàn tất, hết giới hạn sinh hoặc không có nội dung cuối được báo lỗi dịch vụ và giữ tin khách. Cấu hình chat: think=false, context 8192, tối đa 700 token, giữ model 5 phút sau lần dùng cuối, Ollama tự chọn GPU và có thể dỡ model khi thiếu bộ nhớ. Kiểm định dùng cùng model nên vẫn có thể sai, tăng độ trễ và không thay người duyệt. Backend kiểm tra lại phiên bản mọi nguồn đã kiểm định trước khi lưu AI.

## Đánh giá RAG

Bộ 72 câu tiếng Việt và chính sách giả lập nằm trong `evals/rag/`; nhãn đang chờ người dùng duyệt. Chạy `python -m app.evaluate_rag --split dev --output evals/rag/runs/my-dev-run`, rồi dùng `--split test` và thư mục mới cho tập kiểm tra. Trình chạy dùng SQL/vector tạm, ghi từng đáp án/lỗi và tổng hợp Recall@k, citation, từ chối, p50/p95; không sửa dữ liệu ứng dụng. Xem `evals/rag/README.md` để hiểu mẫu số và giới hạn từng chỉ số, `docs/RAG_EVALUATION.md` để xem kết quả baseline và ca cần sửa.

Bộ bổ sung `evals/rag-documents/` có 24 câu trên PDF ba trang và DOCX có bảng. Chạy `python -m app.evaluate_rag --dataset evals/rag-documents --split test --output evals/rag-documents/runs/my-run`. Trình chạy kiểm tra gold theo trang/đoạn/bảng, lưu hash file nhị phân và log ingestion; không tự nạp `.env`. Bộ mới giữ cấu hình RAG đã chốt, nhãn vẫn chờ người duyệt; không gộp điểm với bộ TXT để tuyên bố cải thiện.

Chấm bản sao `human-review.jsonl`, rồi tổng hợp bằng `python -m app.review_rag --run evals/rag/runs/bounded-ids-test --reviews PHIEU_DA_CHAM.jsonl --output BAO_CAO_MOI.json`. CLI không gọi model; chỉ tính rating có tên người chấm và nhãn được duyệt, báo mẫu số riêng cùng ca chưa chấm, không ghi đè kết quả. Cách điền và trường áp dụng trong `evals/rag/README.md`.

## Tổng quan và quản lý nội bộ

Năm mục Tổng quan, Khách hàng, Đơn hàng, Phân tích, Cài đặt đã dùng được. Staff tìm/xem khách và đơn; admin tạo/sửa. Phân tích có kỳ 7/30/90 ngày và SLA từ dữ liệu thật. Trong Cài đặt, admin tạo tài khoản nhân viên; mỗi người tự đổi mật khẩu hiện tại, thu hồi mọi phiên của chính mình. Chi tiết quyền, công thức và giới hạn tại [WORKSPACE.md](docs/WORKSPACE.md).

## Quyền tra đơn cho khách widget

Admin có thể cấp mã truy cập một lần từ trang Đơn hàng sau khi xác minh người nhận qua kênh tin cậy. Khách nhập mã trong mục Quyền tra cứu đơn của widget; quyền chỉ áp dụng một đơn và một phiên, hết hạn sau 15 phút tính từ lúc cấp. Cấp lại/thu hồi chặn quyền cũ. Không đổi danh tính khách, không tự gửi mã qua email/SMS và không gửi mã trong biểu mẫu tới AI. Hướng dẫn, API và giới hạn tại [ORDER_ACCESS.md](docs/ORDER_ACCESS.md). Khởi động lại backend để chạy migration v6 trước khi dùng giao diện mới.

## Telegram

Kiểm tra bot lúc khởi động tự thử lại sau 5 giây nếu lỗi mạng/HTTP 5xx; token sai hoặc webhook đang hoạt động vẫn cần xử lý cấu hình và khởi động lại. Thử lại không áp dụng cho tin gửi có kết quả chưa rõ. 23 test Telegram đạt bằng transport giả lập.

Lỗi HTTP bị cắt/sai giao thức khi gửi được ghi `uncertain`, tránh kẹt `sending` đến restart; không tự gửi lại hoặc chặn gửi cho khách khác. 21 test Telegram đạt bằng transport giả lập.

Đã sửa kẹt hàng chờ khi `getUpdates` lỗi: update đã lưu vẫn được xử lý, trạng thái kết nối tiếp tục báo lỗi và con trỏ không tiến khi response sai. Không tự gửi lại tin có kết quả chưa rõ; cần kiểm chứng bot thật.

Đã có adapter polling cho chat riêng, dùng chung RAG/Inbox/handoff; mặc định tắt. Cấu hình TELEGRAM_ENABLED và TELEGRAM_BOT_TOKEN trong `.env` local, khởi động một API worker. Inbox hiển thị trạng thái gửi, cho người phụ trách gửi lại/bỏ qua tin lỗi; SLA Telegram tính khi Telegram xác nhận gửi. Chưa thử bot thật hoặc nghiệm thu M6. Hướng dẫn và giới hạn: [TELEGRAM.md](docs/TELEGRAM.md).

Thông báo chuyển nhân viên được lưu cùng transaction với trạng thái/ticket để không mất khi worker gián đoạn; retry không tạo thêm thông báo. Lỗi gửi trước đó vẫn chặn hàng chờ, cần người phụ trách xử lý. Không tự bù thông báo thiếu trong dữ liệu cũ.

## Sao lưu và khôi phục

CLI `python -m app.backup` sao lưu SQLite, Qdrant và tài liệu khi đã dừng API; kiểm tra SHA-256 và khôi phục vào thư mục mới, không ghi đè dữ liệu đang dùng. Bản khôi phục thu hồi phiên đăng nhập/widget và quyền tra đơn cũ. Lệnh, cấu hình và giới hạn tại [OPERATIONS.md](docs/OPERATIONS.md).

Chỉ bỏ file khóa `.lock` ở gốc Qdrant; file cùng tên trong tài liệu/thư mục con được giữ và kiểm tra toàn vẹn. Nếu bản sao cũ từng bỏ mất các file này, tạo lại từ nguồn đầy đủ.

## Chạy bản build cùng API

`npm --prefix frontend run build`, đặt `SERVE_FRONTEND=true`, rồi chạy `python -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000`. Mở `/` hoặc `/chat` trên cổng 8000, không cần Vite. Sau đăng nhập, `/api/v1/ready` kiểm tra schema, tài liệu/vector và model Ollama; `/api/v1/health` vẫn chỉ kiểm tra API. Cách đọc kết quả và giới hạn tại [OPERATIONS.md](docs/OPERATIONS.md).

## Đo tải Inbox và widget

`python -m app.measure_load --clients 10 --rounds 20 --conversations 500 --output evals/load/runs/my-run` chạy Uvicorn/store tạm riêng, không gọi LLM hoặc Telegram. Kịch bản 1.000 request tải chính với 10 client đạt 13,755 request/giây trước index và 37,437-38,008 sau hai index tin nhắn/ticket; không lỗi ngoài dự kiến, kiểm tra UUID và tranh chấp tiếp nhận đạt. Migration tự thêm index cho DB v7 khi khởi động, không đổi phiên bản dữ liệu. Cách đo, mẫu số và giới hạn tại [evals/load/README.md](evals/load/README.md); đây chưa phải sức chứa production hoặc tốc độ RAG.

Giữ model trên GPU: kiểm chứng RTX 3060 6 GiB cho cả hai model 100% GPU. Cùng câu hỏi thử giảm từ 15,2-16,1 giây xuống 3,35-3,72 giây khi đã nạp; lượt đầu cấu hình mới 10,7 giây. Không đại diện mọi tài liệu/tải. Số đo và cách chạy lại tại [evals/ollama/README.md](evals/ollama/README.md). Kiểm tra bằng `ollama ps`; khởi động lại backend nếu không dùng --reload.

## Tài khoản khách hàng bằng email và mật khẩu

Mở `/chat`, chọn **Đăng ký**, nhập tên hiển thị, email và mật khẩu 15–128 ký tự. Khách có thể đăng nhập trên nhiều thiết bị, xem **Lịch sử**, tạo **Chat mới** và đổi mật khẩu trong **Tài khoản**. Đổi mật khẩu đăng xuất mọi thiết bị; đăng xuất thông thường chỉ kết thúc phiên hiện tại. Vẫn hỗ trợ khách vãng lai.

Đăng ký và đăng nhập không cần dịch vụ xác thực ngoài. Đã có **xác minh email và quên mật khẩu qua SMTP**: cấu hình hộp thư trong `.env`, vào Tài khoản để gửi xác minh; chỉ email đã xác minh được khôi phục mật khẩu. Đặt lại mật khẩu thu hồi mọi phiên và liên kết cũ. Không tự ghép lịch sử khách vãng lai hoặc cấp quyền xem đơn theo email. Backend tự nâng schema lên v9; tra đơn vẫn cần mã truy cập riêng. Chi tiết: [Tài khoản khách hàng](docs/CUSTOMER_AUTH.md).
