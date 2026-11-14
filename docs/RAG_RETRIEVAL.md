# Thử nghiệm retrieval: hybrid BM25 và chunking (14/11/2026)

## Câu hỏi

1. Thêm BM25 (hybrid với dense) có giúp tìm đúng nguồn hơn không?
2. Chia chunk theo cấu trúc tài liệu (heading, câu) có cần không?
3. Ngưỡng cosine 0,35 có đang chặn nhầm nguồn đúng không?

## Phương pháp: kho chung có nhiễu

Mỗi bộ eval end-to-end chỉ có 1–5 file, nên câu nào cũng dễ tìm. Công cụ `python -m app.evaluate_retrieval --output <thư mục mới>` nạp **toàn bộ 28 file của 8 bộ eval vào một kho chung**. Chính sách của các cửa hàng giả lập khác nhau rất giống nhau nhưng khác con số, nên chúng là nhiễu thật, như một kho tri thức lớn dần.

- Chỉ gọi embedding, không gọi LLM; chạy khoảng 3 phút.
- 305 câu, trong đó 241 câu có bằng chứng gold. Dev là 7 bộ cũ (215 câu), held-out là heldout-v1 (26 câu).
- Câu nối tiếp dùng dạng ghép lịch sử, không dùng bước viết lại câu hỏi bằng LLM.
- So trên cùng index: **legacy** (dense + điểm cộng bigram tối đa 0,12, bản đang chạy), **dense** (chỉ dense), **rrf w** (dense + BM25 hợp nhất bằng Reciprocal Rank Fusion, BM25 có trọng số w).
- BM25 tự viết trong `app/rag/lexical.py`: tách âm tiết, thêm bigram âm tiết để xấp xỉ từ ghép, bỏ dấu để khớp cả câu gõ không dấu.

## Kết quả

Recall@k là tỷ lệ quote gold nằm trong top-k.

| Chế độ | Dev R@1 | Dev R@5 | Held-out R@1 | Held-out R@5 |
|---|---:|---:|---:|---:|
| legacy (đang dùng) | **77,8%** | **98,3%** | 69,2% | **100%** |
| dense | 76,2% | 98,3% | 57,7% | **100%** |
| rrf 1.0 | 78,2% | 97,1% | 76,9% | 88,5% |
| rrf 0.5 | 77,8% | 96,7% | 73,1% | 88,5% |
| rrf 0.3 | 76,6% | 97,1% | 69,2% | 88,5% |
| rrf 0.15 | 76,2% | 97,9% | 65,4% | 88,5% |

Nguồn đúng lọt qua ngưỡng và tới được LLM (tỷ lệ câu có ít nhất một quote gold sau ngưỡng; "nhiễu" là số nguồn trung bình gửi cho LLM ở câu phải từ chối):

| Ngưỡng (xếp hạng legacy) | Dev | Held-out | Nhiễu dev | Nhiễu held-out |
|---|---:|---:|---:|---:|
| cosine ≥ 0,35 | 98,1% | 96,2% (1 câu bị chặn hết) | 4,69 | 4,67 |
| cosine ≥ 0,30 | 98,1% | **100%** | 4,95 | 4,80 |

Thêm luật "cho qua top-2 BM25 nếu cosine ≥ 0,20–0,25" không cải thiện thêm.

## Kết luận

1. **BM25 không đưa vào production.** Với mọi trọng số đã thử, BM25 làm R@5 giảm (held-out 100% xuống 88,5%). Trong kho nhiều cửa hàng có chính sách na ná nhau, từ khóa như "giao", "hoàn", "phí" xuất hiện khắp nơi, nên BM25 kéo chunk của cửa hàng khác lên. BM25 thường có ích hơn với mã sản phẩm, mã lỗi, tên riêng hoặc kho lớn có thuật ngữ đặc thù; cần đo lại khi có kho thật. Code và công cụ đo được giữ để tái lập.
2. **Không đổi chunker.** Trong 28 file chỉ có 2 đoạn dài hơn 180 từ (trang 1–2 của PDF) và bằng chứng gold ở đó đều được tìm thấy. Corpus hiện tại không đo được lợi ích của chunking theo cấu trúc; đổi mà không đo được chỉ thêm rủi ro. Cần bộ tài liệu dài thật (nhiều trang, có heading, bảng) trước khi thay đổi.
3. **Giữ ngưỡng cosine 0,35.** Trên kho gộp, 0,30 cứu được 1 câu held-out ở mức retrieval, nhưng chạy end-to-end thì tệ hơn (bảng dưới): thêm nguồn yếu khiến bước chọn câu trả lời luôn các câu mơ hồ thay vì hỏi lại. Ngưỡng retrieval vẫn là một lớp an toàn, không chỉ là bộ lọc recall.
4. **Các câu retrieval còn sót** (bt20-011, customer-030/055/056) là câu thiếu chủ thể ("gói này", "mã này", "làm hộ") hoặc không nêu sản phẩm trong kho gộp. Đây là việc của bước hỏi lại khách, không phải của xếp hạng.

## End-to-end với ngưỡng 0,30

Bản v4 (ngưỡng 0,35) so với cùng pipeline nhưng ngưỡng 0,30 (`generic-v5-gate030-20261114`):

| | v4, ngưỡng 0,35 | v5, ngưỡng 0,30 |
|---|---:|---:|
| Dev: rag / rag-policy / rag-context | 45 / 20 / 20 | 45 / 19 / 19 |
| Dev tổng (96 câu) | **85** | 83 |
| Held-out (41 câu) | **35** | 33 |
| Trả lời khi phải từ chối (dev + held-out) | **4** | 8 |

Các câu chuyển sang sai ở 0,30 chủ yếu là câu mơ hồ được trả lời bằng một nguồn yếu ("Bao lâu nữa?", "Sản phẩm mình mua bảo hành được bao lâu?", "Tiền ship ban đầu có được hoàn không?") và một câu bị đánh nhầm là mâu thuẫn. Vì vậy giữ 0,35.

Hai câu held-out 004 ("Shop có ship qua Mỹ không?") và 018 ("Giao trong ngày có áp dụng ở Huế không?") vẫn sai ở 0,30 dù nguồn đúng đã tới model: bước chọn câu không suy ra "Mỹ" là "nước ngoài", và hỏi lại khách thay vì suy ra "Huế không thuộc nội thành Đà Nẵng". Nút thắt ở đây là khả năng suy luận của model 4B, không phải retrieval.

## Tổng kết ưu tiên 4

- Không thay đổi hành vi production: vẫn dense + điểm cộng bigram, ngưỡng 0,35, chunker cũ.
- Thêm công cụ đo retrieval trên kho gộp và module BM25 để tái lập thí nghiệm.
- Hướng cải thiện tiếp theo có căn cứ: model chọn câu lớn hơn (ví dụ qwen3:8b nếu đủ VRAM) cho các câu cần suy luận; bộ tài liệu dài thật để đánh giá chunking; đo lại BM25 khi kho có mã sản phẩm hoặc thuật ngữ đặc thù.

## Bằng chứng

- `evals/retrieval/runs/hybrid-v1-20261114/`: lượt đầu (hybrid trọng số 1.0 tích hợp trong search).
- `evals/retrieval/runs/fusion-weights-20261114/`: so legacy, dense và 4 trọng số RRF; `results.jsonl` lưu top-5 từng chế độ cho từng câu.
