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
