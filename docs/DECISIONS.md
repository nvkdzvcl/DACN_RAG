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

## Quyết định sau baseline dev

Bộ đầu tiên gồm 72 câu do trợ lý soạn trên cửa hàng giả lập: 24 dev và 48 test, tách nhóm nội dung cùng nguồn theo tập; mọi nhãn chờ người dùng duyệt. Chỉ số tự động là proxy, không gọi là độ đúng được người xác nhận. Lỗi provider tính riêng, không cộng vào từ chối đúng. Kết quả lưu model digest, hash dữ liệu/mã nguồn và từng completion để kiểm toán.

Giữ ngưỡng 0,35 và prompt hiện tại. Dev có Recall@5 = 100% trên 17 câu có gold nhưng quyết định đúng 17/24; tăng ngưỡng lên 0,45 loại nguồn đúng ở một câu có đáp án. Bản prompt v2 thử trên cùng dev không tăng decision accuracy và giảm từ chối đúng từ 6/9 xuống 5/9, xuất hiện câu bịa mã FREE80 với citation thuộc chính sách khác. Bản này bị loại trước khi chạy test, được lưu nguyên trong evals/rag/runs/prompt-v2-dev. Không nới kiểm tra quote hay thêm reranker khi chưa có bằng chứng retrieval là điểm nghẽn.

Mốc tiếp theo cần kiểm chứng câu trả lời thực sự được nguồn hỗ trợ, phân biệt thiếu thông tin với trả lời phủ định và xử lý nguồn mâu thuẫn. Sau khi xem tập test này, các thay đổi dùng nó làm regression; thêm một tập chưa xem nếu muốn đánh giá khả năng tổng quát hóa. Xem docs/RAG_EVALUATION.md cho kết quả cuối.

## Kiểm định đáp án sau sinh

Thêm một lần gọi cùng Ollama sau khi đáp án vượt kiểm tra JSON/source ID/quote. Kiểm định nhận câu hỏi, lịch sử, đáp án và toàn bộ nguồn đã cấp cho LLM; ba điều kiện question_resolved, sources_consistent và claims_supported phải cùng true mới được trả lời. claims_supported bao gồm kiểm tra chỉ dẫn chèn không phải bằng chứng chính sách. JSON kiểm định lỗi dẫn đến từ chối; lỗi provider được giữ nguyên để API báo lỗi và tin khách vẫn được lưu. Không thêm dependency hoặc model, không nới kiểm tra quote, không dùng tên sản phẩm hay mã tấn công trong benchmark làm luật ứng dụng.

Bản đầu dùng bốn cờ boolean bị model hiểu nhầm cờ follows_instructions: nhầm trả lời chính sách thông thường thành làm theo chỉ dẫn độc hại. Trên dev, từ chối đúng 9/9 nhưng từ chối sai tăng lên 8/15, quyết định đúng chỉ 16/24. Loại bản này, giữ snapshot và kết quả verified-dev; bản tiếp theo dùng verdict rõ nghĩa để tránh cờ đảo nghĩa.

Bản một verdict (verified-v2-dev) giữ từ chối sai 4/15 nhưng bỏ sót cả hai câu mâu thuẫn, chỉ đạt 18/24 quyết định đúng. Chọn bản ba điều kiện bắt buộc (verified-v3-dev): 20/24 quyết định đúng, từ chối đúng 9/9, từ chối sai vẫn 4/15 như baseline. p50/p95 là 11,735/13,145 giây so với baseline dev 8,341/9,135 giây. Chốt lựa chọn này trước khi chạy lại 48 câu test làm regression; không hiệu chỉnh theo lượt test mới.

Cả sinh đáp án và kiểm định đều nằm ngoài SQL transaction. Kiểm tra phiên bản không chỉ với citation mà còn mọi nguồn dùng để kiểm định; nguồn phụ thay đổi có thể làm kết luận về mâu thuẫn hết hiệu lực. Kiểm tra lại trước khi lưu AI, đồng thời giữ guard handoff và tin khách mới. Nguồn mới chưa từng được truy xuất không thuộc snapshot này; chưa bảo đảm snapshot toàn bộ kho khi có ingestion đồng thời.

Đây là bộ lọc bằng cùng model nhỏ, có lỗi tương quan với model sinh và tăng độ trễ. Kết quả kiểm định không phải bằng chứng toán học hay nhãn được người chấm. M3 chỉ được nghiệm thu sau đánh giá độc lập; số đo và ca còn lỗi trong docs/RAG_EVALUATION.md.

Regression đạt 35/48 quyết định đúng (gốc 34/48); từ chối đúng tăng 7/16 lên 10/16 nhưng từ chối sai tăng 5/32 lên 7/32. p50/p95 là 12,695/13,220 giây. Giữ bộ lọc trong MVP local vì chặn test-047/048 bịa thông tin trực tiếp và test-044 chọn nguồn mâu thuẫn. Đây là đánh đổi để giảm đáp án thiếu căn cứ, không phải bước cải thiện lớn về chất lượng chung. Chưa giải quyết ba ca mơ hồ, một ca đảo nghĩa chính sách và hai ca mâu thuẫn; không tiếp tục sửa prompt theo lượt test này trong đợt hiện tại.

## Thử chế độ suy luận và trích nguyên văn

Thử tính năng think có sẵn của Ollama trên qwen3:1.7b trước khi tăng độ phức tạp ứng dụng. Sáu ca dev được phát lại với retrieval cũ cho kết quả ban đầu khả quan, nhưng lượt 24 dev đầy đủ chỉ đạt proxy 20/24 như trước, một lỗi hết 2048 token và một đáp án đảo điều kiện thời gian vẫn lọt. Không dùng pilot có lựa chọn ca để kết luận chất lượng toàn tập.

Thử chọn source_id/sentence_id rồi ghép nguyên văn, với giới hạn 4096 token. Bản tách cả chấm phẩy đạt proxy 20/24 và làm rơi vế phủ định/điều kiện. Bản giữ chấm phẩy vẫn chỉ đạt proxy 20/24, có một lỗi hết token và model kiểm định đánh cờ sai. Hai cấu hình 1,7B này bị loại; snapshot nằm trong extractive-dev và extractive-v2-dev. Tiếp tục so model lớn hơn trên cùng Ollama, không thêm luật riêng cho tên sản phẩm của benchmark.

Giữ kiểm tra transport: phản hồi chưa hoàn tất, rỗng hoặc done_reason=length là lỗi provider; không tính vào từ chối đúng và không lưu phản hồi bị cắt. Trường thinking không được đưa vào đáp án hoặc lịch sử hội thoại. Manifest lấy tham số từ transport và lưu thêm ollama.py.txt để tránh mô tả sai cấu hình thực chạy.

qwen3:4b Q4_K_M tải local khoảng 2,5 GB, digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7. Ollama báo khoảng 3,87 GB VRAM cho model/context 8192 khi chạy thử; đây là một ảnh chụp mức dùng bộ nhớ, không phải mức đỉnh. Với luồng sinh cũ, dev đạt 19/24 quyết định đúng và proxy 17/24; quote bị chép sai số, câu phủ định và từ chối nguồn có chỉ dẫn độc hại vẫn lỗi. Vì vậy đổi model đơn thuần cũng bị loại.

Bản thử kế tiếp dùng 4B không suy luận, giới hạn 700 token, chọn tối đa ba câu bằng ID rồi backend lấy nguyên văn. Bỏ cờ supported ở bước chọn: danh sách rỗng biểu thị không có bằng chứng để chọn; một chính sách phủ định vẫn là bằng chứng. Giữ chấm phẩy cùng câu để tránh tách rời điều kiện. Bộ kiểm định ba điều kiện vẫn đọc toàn bộ nguồn đã cấp, có quy tắc rõ rằng chính sách hợp lệ nằm cạnh chỉ dẫn độc hại không tự động bị loại. Không dùng suy luận trung gian làm nhãn chấm.

Bản model4b-extractive-dev đạt 21/24 quyết định đúng và proxy, từ chối đúng 9/9, từ chối sai 3/15; p50/p95 16,620/19,358 giây, không lỗi provider. Hai giải thích kiểm định dài chạm giới hạn schema 1.500 ký tự, kết thúc giữa câu rồi đánh cờ nguồn mâu thuẫn sai. Bản tiếp theo yêu cầu reason là một câu kết luận ngắn, mục tiêu 200 ký tự; giới hạn schema vẫn 1.500 nên đây là hướng dẫn sinh, không phải ràng buộc độ dài 200 ký tự. Sáu ca pilot chỉ dùng chẩn đoán, quyết định chọn vẫn dựa toàn bộ dev.

Phạm vi trích xuất: tối đa năm nguồn, 1.200 ký tự mỗi nguồn, tối đa ba câu; tách bằng dấu chấm/chấm hỏi/chấm than theo sau bởi khoảng trắng, giữ chấm phẩy. Backend chuẩn hóa khoảng trắng nhưng giữ từ, số và dấu câu của phần đã chọn. Chưa xử lý đầy đủ chữ viết tắt, đoạn bị cắt hoặc điều kiện nằm ở câu khác; đáp án giữ ngôn ngữ nguồn, chưa dịch hoặc tổng hợp tự do. Chọn đúng ID chỉ loại việc LLM viết lại dữ kiện, không bảo đảm chọn đủ câu hoặc trả lời đúng yêu cầu. Bộ kiểm định và kiểm tra phiên bản mọi nguồn vẫn bắt buộc.

Chọn model4b-extractive-short-dev trước regression: 22/24 quyết định đúng và proxy, từ chối đúng 9/9, từ chối sai 2/15, không lỗi vận hành. So bản đang dùng verified-v3-dev: tăng từ 20/24, từ chối sai giảm từ 4/15; p50/p95 tăng từ 11,735/13,145 lên 14,627/15,597 giây. So bản trích xuất 4B giải thích dài: sửa dev-001/003 nhưng thêm từ chối sai ở dev-013; dev-004 vẫn bị từ chối nhầm. Chọn theo toàn bộ dev và giữ nguyên prompt/schema/model cho lượt test regression tiếp theo; không sửa tiếp theo lỗi test trong đợt này.

Regression bản đã chốt đạt 40/48 quyết định đúng (trước 35/48), từ chối đúng 14/16 (trước 10/16), từ chối sai 6/32 (trước 7/32), proxy 40/48 (trước 33/48); p50/p95 14,096/14,739 giây so 12,695/13,220 giây. Không lỗi vận hành. Giữ bản này trong MVP local với chi phí chậm hơn; chưa nghiệm thu M3. Sáu ca từ chối sai: test-021/025/026/029/045/046; hai ca cuối hồi quy do kiểm định loại chính sách hợp lệ cạnh chỉ dẫn độc hại. Vẫn trả lời sai yêu cầu ở test-036 (cộng điểm thay đổi tiền) và test-038 (tự chọn dịch vụ giao). Cả bốn ca mâu thuẫn và hai yêu cầu bịa trực tiếp được từ chối đúng. Không tiếp tục tuning trên test trong đợt này.

## Đo PDF và DOCX với cấu hình giữ nguyên

Mở rộng trình đánh giá hiện có bằng `--dataset`, tái sử dụng `extract_sections` và `chunk_text`; không thêm parser hoặc dependency ứng dụng. Gold quote phải nằm trọn trong chunk đúng vị trí; page được kiểm tra khi nhãn có trường này. Bộ TXT và 408 kết quả đã lưu chấm lại không đổi. Bộ mới có 24 ca trên PDF ba trang và DOCX có bảng, được tạo trước lượt hỏi với cấu hình 78e50f9; đây là phép đo bổ sung do cùng trợ lý soạn sau khi xem lỗi cũ, chưa là đánh giá độc lập. Không chỉnh prompt/nhãn theo kết quả mới.

Lượt đầu dừng ở log datetime trước câu hỏi; sửa bằng cách chỉ ghi trường trạng thái/chunk/lỗi và thời gian đo, thêm test đi qua trình chạy với metadata datetime. Giữ manifest incomplete, chạy vào thư mục khác. Lượt hoàn tất đạt 21/24 quyết định khớp nhãn, từ chối đúng 9/10, từ chối sai 2/14, không lỗi provider. doc-005 chọn ID câu không tồn tại dù retrieval có gold; doc-013 hiểu chính sách phủ định nhưng cờ kiểm định false. doc-019 trả phạm vi và điều kiện thay vì từ chối; cần người chấm quyết định có chấp nhận không. Citation khớp gold 63,16% bị ảnh hưởng bởi các câu nguồn thật ngoài phần gold, không dùng làm tỷ lệ hallucination. Bước tiếp theo cần người duyệt và dev riêng cho ID/kiểm định, giữ trace mới làm regression.
