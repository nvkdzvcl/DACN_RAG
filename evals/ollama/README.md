# Giữ model trong GPU ngày 25/09/2026

Máy kiểm chứng: RTX 3060 Laptop GPU 6 GiB, Windows, Ollama 0.34.4. Model giữ nguyên qwen3:4b và embeddinggemma:300m, digest trong JSON. Ollama đã dùng GPU trước thay đổi; thay đổi chính là keep_alive từ 0 sang 5m, tránh nạp lại sau mỗi lời gọi.

| Cấu hình | Lượt 1 | Lượt 2 | Lượt 3 |
|---|---:|---:|---:|
| keep_alive=0 | 15,315 s | 15,207 s | 16,066 s |
| keep_alive=5m | 10,704 s | 3,719 s | 3,351 s |

Đo cùng câu hỏi và tài liệu giả lập, một lượt embedding và hai lượt chat (chọn câu, kiểm định), không có lịch sử. Chạy ba lượt 0 rồi ba lượt 5m; model/cache hệ điều hành đã từng chạy trước phép đo. Đây không phải sáu lượt khởi động máy nguội. Hai lượt cuối giữ cả hai model trong GPU; API /api/ps báo size_vram bằng size cho cả hai, tổng 4,16 GiB. Thời gian load API giảm từ khoảng 3-5 giây xuống 7-10 ms khi model còn nạp. Mọi lượt đều có grounded=true, đáp án chứa 7 ngày và citation.

Raw output: residency-20260925.json. Smoke HTTP qua code ứng dụng sau sửa: smoke-m4-20260925.json, câu hỏi 3,675 giây, toàn luồng 6,569 giây; có upload, RAG, handoff, phản hồi nhân viên, giải quyết/đóng và cách ly phiên trên DB/vector tạm.

Chạy lại từ root repo khi Ollama và hai model đã sẵn sàng:

```powershell
python -m evals.ollama.measure_residency evals/ollama/residency-new.json
```

Runner chỉ thay keep_alive trong payload, gọi Ollama thật, không mock kết quả; giữ prompt/context/token/model. Đích phải chưa tồn tại. Store tạm được dọn; JSON thiếu complete=true là lượt chưa hoàn tất. Phép đo gọi model trên dịch vụ đang chạy và thay trạng thái nạp model; nên chạy khi không có người hỏi đồng thời.

Chỉ một tài liệu, một câu hỏi lặp, sáu mẫu và thứ tự cố định; có thể hưởng cache và không kiểm soát mọi tải nền. Không suy thành p95, chất lượng M3 hoặc tốc độ mọi câu hỏi. Lượt 143 giây trước đó có chi phí khởi động lớn, không dùng làm baseline so sánh này. Model có thể bị dỡ khi thiếu VRAM, hết 5 phút không dùng hoặc khởi động lại; không ép num_gpu hoặc giảm bước kiểm định để lấy tốc độ.
