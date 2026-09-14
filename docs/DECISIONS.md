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

## Ràng buộc ID câu trong schema sinh

Lỗi ID vượt phạm vi được xử lý bằng JSON Schema có sẵn của Ollama. Mỗi nhánh oneOf gắn một source_id với enum sentence_id thực có của nguồn đó; không đặt một giới hạn chung khiến câu của nguồn dài được gán nhầm sang nguồn ngắn. Giữ schema bên ngoài, prompt chọn/kiểm định, model, retrieval và giới hạn số câu. Không thêm retry, lượt model, thư viện hoặc luật theo tên sản phẩm.

Backend tiếp tục xác thực kiểu dữ liệu, phạm vi và ID trùng sau phản hồi, kể cả khi provider bỏ qua schema; mọi nguồn vẫn được kiểm định và kiểm tra phiên bản. Ràng buộc chỉ bảo đảm miền ID khi provider tuân thủ grammar, không chứng minh câu được chọn phù hợp. Kiểm thử nguồn một câu và nguồn ba câu xác nhận các cặp hợp lệ và chặn cặp chéo nguồn. Đánh giá dev trước, rồi giữ nguyên bản đã chọn khi chạy regression; nhãn mơ hồ và kiểm định phủ định không đổi trong đợt này.

Dev bounded-ids-dev giữ 22/24 quyết định đúng/proxy, từ chối đúng 9/9, từ chối sai 2/15, không lỗi provider. p50/p95 13,287/14,022 giây; số đo từng lượt có thể khác do điều kiện máy, không khẳng định tăng tốc từ schema. Chọn bản ràng buộc miền ID vì sửa lỗi cấu trúc và không làm giảm kết quả dev; giữ nguyên trước hai lượt regression TXT và PDF/DOCX.

PDF/DOCX regression giữ nguyên điểm từng ca: 21/24 khớp nhãn/proxy, từ chối đúng 9/10, từ chối sai 2/14; không lỗi provider hoặc cặp ID vượt phạm vi. doc-005 chọn được câu chứa mốc 18 giờ nhưng kèm mảnh câu từ ranh giới chunk và câu về hóa đơn, rồi bị kiểm định từ chối. Ràng buộc ID đã làm đúng vai trò cấu trúc; không coi ca này đã trả lời đúng. Giữ nguyên nhãn doc-019, không chỉnh selector/kiểm định tiếp theo kết quả regression trong đợt này.

TXT regression giữ 40/48 khớp nhãn/proxy, từ chối đúng 14/16 và từ chối sai 6/32; p50/p95 13,484/15,081 giây. Điểm từng ca của cả ba lượt không đổi; 96 ca không lỗi provider hoặc ID vượt phạm vi. Giữ bản sửa vì miền ID được ràng buộc đúng, không tuyên bố tăng độ đúng hoặc tốc độ. Cần người duyệt và dev riêng cho lỗi chọn nội dung/kiểm định, không bỏ bộ lọc để tăng điểm.

## Phân biệt câu trả lời đúng với chấp thuận dịch vụ

Dev cho thấy kiểm định bỏ sót nội dung đã có: dev-004 trích cả phí và ngưỡng miễn phí, dev-013 trích điều kiện nguyên tem/hóa đơn sau dấu chấm phẩy nhưng vẫn bị coi là thiếu ý. Thử bổ sung hướng dẫn đọc toàn bộ các vế và phân biệt chất lượng đáp án với việc khách được chấp thuận dịch vụ. Câu trả lời phủ định có nguồn vẫn có thể giải quyết câu hỏi. Giữ ba cờ kiểm định bắt buộc, quy tắc thiếu ngữ cảnh/mâu thuẫn/injection, selector, model và retrieval; không dùng tên chính sách hay đáp án benchmark trong prompt.

Chỉ chọn bản mới nếu dev tăng quyết định khớp nhãn/proxy, không giảm từ chối đúng và không phát sinh lỗi provider. Chốt theo dev trước khi chạy lại TXT/PDF/DOCX; không chỉnh tiếp theo lỗi test trong đợt này. Mọi nhãn vẫn chờ người duyệt; sửa prompt không thay đánh giá độc lập hoặc bằng chứng ngữ nghĩa.

Bản đầu review-semantics-v2-dev đạt 23/24, giải quyết dev-004/013 và không còn từ chối sai, nhưng từ chối đúng giảm 9/9 xuống 8/9. dev-017 hỏi phương thức thanh toán không được nguồn đề cập; đáp án chỉ liệt kê phương thức khác vẫn được chấp nhận. Loại bản này theo tiêu chí đã đặt, giữ kết quả/snapshot. Bản tiếp theo bổ sung phân biệt không được nhắc đến với phủ định được nguồn xác nhận, không cho danh sách lựa chọn khác thay câu trả lời về lựa chọn khách hỏi.

Bản review-semantics-v3-dev vẫn lọt dev-017 và từ chối sai dev-013: 22/24 khớp nhãn/proxy, từ chối đúng 8/9, từ chối sai 1/15; p50/p95 15,323/16,340 giây, không lỗi provider. Loại bản này. Thử nghiệm kế tiếp dùng lại tiêu chí prompt gốc, chỉ đổi thứ tự trường trong schema để ba cờ được sinh trước reason, đồng bộ câu hướng dẫn thứ tự. Đây là thử ảnh hưởng thứ tự đầu ra, chưa khẳng định sửa được ngữ nghĩa; giữ nguyên phép AND ba cờ, xác thực chặt và giới hạn giải thích.

Bản review-flags-first-dev chỉ đạt 14/24, từ chối đúng 9/9 nhưng từ chối sai 10/15; p50/p95 15,276/15,963 giây. Loại cả ba thử nghiệm trước test, đưa answer_service.py về đúng bản 0180479. Giữ 72 ca dev và snapshot; không chạy lại test khi RAG ứng dụng không đổi. Không dùng điểm tổng của bản 23/24 để che hồi quy ở câu ngoài nguồn.

Ưu tiên hoàn thiện vòng người duyệt thay vì tiếp tục thử prompt trên tập cũ. CLI app.review_rag dùng stdlib, đọc phiếu riêng và kết quả bất biến, xác thực ID/kiểu/người chấm/phạm vi áp dụng rồi xuất tỷ lệ theo mẫu số thực được chấm. Nhãn bị bác bỏ và phần chưa chấm không thành điểm âm/dương; lỗi provider tách riêng. Không tự sửa nhãn, gọi model chấm thay người hoặc thêm UI/dependency khi quy trình JSONL đã có. Hash đầu vào và mã giúp đối chiếu báo cáo; danh tính người chấm vẫn tự khai.

## Phiên khách và widget cùng origin 14/09/2026

Triển khai phần widget của M4 trong lúc M3 chờ người duyệt, giữ nguyên model/prompt/retrieval và nhãn. Website dùng cookie HttpOnly riêng, thời hạn cố định 24 giờ, SameSite Strict, Secure ngoài development và đường dẫn chỉ trong API widget. Server tự tạo Customer/Conversation; token chỉ lưu hash. Không nhận danh tính khách/hội thoại từ payload và không đồng nhất tên tự nhập với khách mua hàng đã có.

Tái sử dụng process_message, kiểm tra quyền ở route và ràng buộc trạng thái tại DB. UUID cho phép thử lại cùng tin mà không sinh trùng; cùng ID khác nội dung trả 409. Snapshot công khai chỉ chứa lịch sử của phiên cùng quote/vị trí đã lưu, không chứa retrieval thô hoặc ticket nội bộ. Kết thúc đóng hội thoại/ticket và thu hồi token; phản hồi sau model kiểm tra lại phiên. Handoff không chờ AI và kết quả AI muộn không được lưu khi trạng thái đã đổi.

Chọn iframe cùng origin và polling 3 giây để có luồng website hoàn chỉnh với phần nền tảng hiện tại; chưa thêm CORS, cookie bên thứ ba, WebSocket/SSE hoặc dependency. Giới hạn 200 tin, rate limit theo IP trong bộ nhớ một worker và một lượt AI widget giúp giới hạn tài nguyên local; cần phân trang, bộ giới hạn dùng chung và điều phối toàn bộ lời gọi model trước mở rộng. Không coi đây là SLA, chống lạm dụng đầy đủ hay nghiệm thu M4. Inbox realtime và SLA là task chức năng tiếp theo; đánh giá bằng người và dữ liệu độc lập vẫn cần cho M3.

## Polling Inbox và SLA phản hồi đầu tiên 14/09/2026

Tận dụng GET có xác thực và timestamp ticket/tin nhân viên hiện có. Inbox lấy danh sách và chi tiết mỗi 3 giây, chỉ khi đang hiển thị trang; hủy vòng cũ khi đổi bộ lọc/hội thoại hoặc thao tác ghi, không giữ transaction hay thêm kết nối push. Cập nhật nền không tháo giao diện, giữ bản nháp và lựa chọn khi có hội thoại mới. Lỗi mạng hiển thị dữ liệu cũ kèm cảnh báo và tự thử lại; phản hồi bị hủy không ghi đè lựa chọn mới.

SLA demo đo phản hồi đầu tiên của người thật, tính 24/7 từ lúc tạo ticket: urgent 5, high 15, normal 60, low 240 phút. Dùng tin agent có agent_id và created_at từ thời điểm ticket; nhận việc, AI, khách và tin trước ticket không đáp ứng SLA. Phản hồi tại hạn tính đạt, sau hạn tính trễ; đóng chưa phản hồi là cancelled, không phải đạt. Tóm tắt hội thoại chọn hạn sớm nhất trong các ticket đang chờ, sau đó mới dùng ticket mới nhất; bộ lọc và chỉ số dùng cùng tóm tắt này.

Ở đợt polling ban đầu, không thêm cột hoặc migration cho chính sách cố định, không ghi DB theo đồng hồ mỗi lần poll. Các ticket cũ được tính lại theo chính sách này; cần lưu deadline/phiên bản chính sách trước khi cho phép đổi ưu tiên hoặc quy tắc để bảo toàn lịch sử. Chưa có giờ làm việc, SLA giải quyết, escalation, chỉ số tổng hợp đã kiểm toán hoặc push realtime; không coi kiểm thử local là chứng minh chịu tải. Model/prompt/retrieval và nhãn M3 giữ nguyên.

## Hoàn tất ticket và tiếp tục hỗ trợ 14/09/2026

Giải quyết và đóng là hai kết quả khác nhau. Giải quyết cho khách nhắn tiếp trên cùng phiên và lịch sử, tạo ticket mới ở hàng chờ, bỏ người phụ trách cũ và giữ AI dừng. Đóng chặn tin mới; khách phải kết thúc phiên rồi bắt đầu phiên khác. Chỉ người đang phụ trách được hoàn tất, kể cả admin. Ghi chú 1-2000 ký tự không trắng là nội bộ; thông báo công khai không sao chép ghi chú.

POST /api/v1/inbox/conversations/{id}/finish nhận status, ticket_id, last_customer_message_id và note. Khóa ghi hội thoại dùng chung với inbound và trả lời nhân viên; kiểm tra tin khách mới nhất trước khi kết thúc các ticket đang hoạt động trong cùng transaction. Tin khách thắng tranh chấp khiến thao tác trả 409; giải quyết thắng khiến tin tiếp theo tạo lượt mới. Retry cùng ticket/trạng thái/người/ghi chú trả duplicate trước kiểm tra người phụ trách hiện tại, không ghi thêm hoặc tác động lượt mới; tổ hợp khác trả 409. UUID tin khách được kiểm tra trước nhánh mở lại sau resolved.

Migration v4 thêm completed_at, completed_by_id, completion_note và first_response_at. Khi kết thúc từ Inbox hoặc thu hồi phiên widget, chốt mốc phản hồi của từng ticket cùng transaction; null có nghĩa chưa phản hồi, không được lấy tin của lượt sau. Migration chốt phản hồi đã quan sát của ticket cũ đã kết thúc đúng một lần; không đoán thời điểm hoặc người hoàn tất thiếu dữ liệu. SLA vẫn dùng chính sách ưu tiên cố định, chưa lưu deadline/phiên bản. Chưa thêm mở lại thủ công, SLA giải quyết, escalation hoặc dependency; phải thiết kế quyền và chính sách trước khi mở rộng các thao tác này.

## Hồ sơ thiết kế và smoke M4 15/09/2026

Ghi nhận người dùng cho phép tiếp tục các việc độc lập trong lúc chưa có thời gian duyệt. Nhãn/đáp án M3 và nghiệm thu người dùng giữ chờ duyệt; không tự ghi tên người chấm hoặc công bố đạt chất lượng. Hồ sơ Mermaid và API diễn tả mã thực có, tách rõ BFD/luồng phân làn với file BPMN 2.0 chưa làm và quyền staff với phiên khách công khai.

Dùng TestClient đã cài để chạy smoke toàn luồng HTTP với Ollama thật trong tiến trình riêng. Đặt DB/vector/knowledge tạm trước import, chạy lifespan/migration thật, tạo mật khẩu ngẫu nhiên và login qua API; không dùng token QA cố định, server cổng mới hoặc dependency mới. Smoke chỉ một câu và một vòng nghiệp vụ, không thay kiểm thử trình duyệt, tải hoặc đánh giá chất lượng. Khi đổi UI/proxy cần chạy lại QA trình duyệt; khi đổi model/prompt/retrieval cần quy trình dev và regression riêng.
