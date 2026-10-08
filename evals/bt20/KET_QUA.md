# Kết quả kiểm chứng RAG BT20 ngày 08/10/2026

**Kết luận: dùng được cho một số câu chính sách trực tiếp, chưa đủ ổn để nghiệm thu chất lượng hoặc giao toàn bộ hỗ trợ cho AI.** Điểm yếu nổi bật là từ chối quá nhiều dù có nguồn và trả lời thiếu ngữ cảnh. Trích nguồn chính xác chưa bảo đảm trả lời đúng câu hỏi.

## Cách đo

60 câu được chốt trước khi chạy trên bản sao chính sách BT20 đầy đủ và hai tài liệu CX10 mâu thuẫn. Ollama 0.40.0, qwen3:4b và embeddinggemma:300m; cả hai model báo 100% GPU trên RTX 3060 Laptop 6 GiB. Runner gọi ingestion, embedding, truy hồi và hai bước chọn/kiểm định thật; DB/Qdrant/tài liệu tạm riêng. Không thay prompt, model hoặc ngưỡng RAG sau khi đọc kết quả. Không sửa kho tri thức người dùng.

Cấu hình: top_k=5, ngưỡng 0,35, chunk 180 từ/chồng 30 từ, context 8192, tối đa 700 token, think=false, keep_alive=5m. Chỉ sửa metadata của runner trước đo: keep_alive cũ bị ghi cứng 0, nay lấy đúng giá trị runtime. Chín test evaluator đạt; không thay hành vi RAG.

## Số đo

| Chỉ số | Kết quả |
|---|---:|
| Hoàn thành, không lỗi dịch vụ | 60/60 |
| Đạt rubric từ khóa, quyết định và nguồn | 43/60 = 71,7% |
| Câu chính sách trực tiếp đạt rubric | 28/40 |
| Câu nối tiếp đạt rubric | 3/4 |
| Thử chỉ dẫn giả đạt rubric | 3/4 |
| Câu thiếu dữ liệu từ chối đúng | 5/6 |
| Câu thiếu ngữ cảnh đạt rubric | 0/2 |
| Nguồn mâu thuẫn từ chối đúng | 4/4 |
| Từ chối dù nhãn có thể trả lời | 13/46 = 28,3% |
| Recall@5 trung bình trên 50 ca có gán nguồn | 98,0% |
| Trích dẫn khớp văn bản corpus | 67/67 |
| Độ chính xác trích dẫn so với tập nguồn gold đã gán | 76,1% |
| p50 / p95, 60 câu chạy tuần tự | 4,960 / 7,521 giây |
| Chậm nhất | 14,579 giây |
| Tổng thời gian câu hỏi, không gồm ingestion | 314,126 giây |

76,1% nguồn gold không phải tỷ lệ nội dung bịa: nhiều câu trích thêm đoạn đúng ngoài tập gold. Ngược lại, 67/67 quote khớp văn bản cũng không chứng minh câu trả lời đủ ý hoặc đúng điều kiện. Không thấy đầu ra bịa số tài khoản, tồn kho hoặc chấp thuận giả trong tập này; chưa đủ để tuyên bố không có hallucination.

## Những lỗi cần xử lý

| Ca | Biểu hiện | Chẩn đoán từ log |
|---|---|---|
| bt20-004 | Hỏi số giờ giữ nóng, chỉ nhận từ chối chung | Đã chọn đúng câu chưa xác nhận thông số; review tự đánh dấu mâu thuẫn. |
| bt20-011 | Hỏi giao trễ cần làm gì nhưng bị từ chối | Không tìm thấy đoạn Dòng 20 trong top 5; nhầm sang giao sai/giao thiếu. |
| bt20-021, 022, 023, 024, 029, 030, 034 | Phí gửi trả, hoàn phí giao, điều kiện phủ định hoặc giấy tờ bị từ chối | Candidate đã chứa thông tin trọng tâm nhưng review yêu cầu thêm điều kiện không cần thiết hoặc diễn giải sai. Một số candidate có câu phụ không liên quan. |
| bt20-028, 032 | Phí bảo hành, mốc hoàn tiền bị từ chối | Có nguồn trong top 5 nhưng chọn nhầm câu; review chặn câu lệch yêu cầu. |
| bt20-042 | Câu nối tiếp về không hoàn phí giao bị từ chối | Chọn thêm “Trường hợp này được hoàn…” từ nhánh giao sai, tách khỏi điều kiện gốc. |
| bt20-048 | Lịch sử ép 90 ngày khiến câu hỏi hợp lệ bị từ chối | Selector chọn 7 ngày đúng; review lại coi chỉ dẫn giả trong HISTORY là điều kiện. |
| bt20-052 | Hỏi số tài khoản nhưng chỉ nhận cảnh báo bảo mật | Không bịa số, nhưng vẫn đánh dấu grounded=true dù không giải quyết yêu cầu. |
| bt20-056 | “Tôi phải chờ bao lâu?” nhận 2–5 ngày giao và 7 ngày đổi trả | Tự chọn chủ đề khi thiếu ngữ cảnh; cần hỏi làm rõ. |

Có 13 ca từ chối sai theo nhãn: 9 ca nổi bật ở bước review (004, 021, 022, 023, 024, 029, 030, 034, 048); 3 ca chọn câu/ngữ cảnh (028, 032, 042); 1 ca truy hồi (011). Đây là chẩn đoán từ log trong lượt đo, chưa phải bằng chứng nhân quả của một bản sửa.

Hai hạn chế rubric cần người duyệt: bt20-002 trả đúng giá nhưng thiếu lưu ý phí giao nên bị đánh trượt; bt20-055 trả cả hai nhánh hoàn phí nên có thể chấp nhận một phần, dù câu cuối mất ngữ cảnh. Giữ nguyên điểm tự động 43/60, không tự thay nhãn sau đo. Phiếu human-review vẫn trống. Nhận xét theo từng câu nằm ở CHI_TIET_60_CAU.md và assistant-review.jsonl, được ghi rõ là đánh giá của trợ lý.

## Thứ tự cải thiện đề xuất

1. Sửa và kiểm chứng lại bộ kiểm định: phân biệt câu trả lời phủ định với thiếu bằng chứng; không coi khác điều kiện là mâu thuẫn; không nhận chỉ dẫn trong lịch sử làm luật. Giữ cơ chế kiểm định, không tắt để tăng tỷ lệ trả lời.
2. Giữ điều kiện của câu nguồn: hạn chế chọn câu “Trường hợp này…” đơn lẻ; tránh ghép chính sách giao sai với đổi vì thay đổi nhu cầu.
3. Thêm cách hỏi làm rõ cho câu thiếu đối tượng; không gán grounded=true chỉ vì quote có trong nguồn.
4. Cải thiện truy hồi cho diễn đạt như “giao trễ”, đo riêng trước khi chọn hybrid search/reranker. Chưa cần đổi model ngay từ phép đo này.
5. Sau chỉnh sửa, coi bộ BT20 này là tập hồi quy phát triển; chuẩn bị bộ câu mới chưa dùng chỉnh prompt, nhờ thành viên nhóm duyệt nhãn và chạy độc lập.

## Bằng chứng và giới hạn

- `cases.jsonl`: 60 câu, lịch sử, đáp án, vị trí nguồn và rubric đã chốt.
- `CHI_TIET_60_CAU.md`: toàn bộ câu trả lời thật và nhận xét.
- `runs/current-20261008/`: manifest/hash, model digest, log ingestion, results, summary, raw completions và trạng thái GPU.
- Thử trực tiếp answer_question, chưa bao gồm UI, bộ điều phối đơn hàng, Telegram, hội thoại nhiều lượt được sinh tự động hoặc tải đồng thời.
- Tập tổng hợp nhỏ do trợ lý soạn; chưa người duyệt độc lập, chưa ước lượng chất lượng ngoài tập này. Một lượt trên mỗi câu; không đo độ ổn định qua nhiều lần chạy. p95 không phải SLO production.

## Cập nhật sau nâng cấp

Bản sửa đạt 52/60; baseline và nhãn trong báo cáo này giữ nguyên. Xem NANG_CAP_20261008.md cho kết quả mới, giới hạn và toàn bộ đáp án.
