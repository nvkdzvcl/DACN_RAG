# Deploy lên Vercel + Railway

Kịch bản đưa bản `main` lên Internet: giao diện chạy trên **Vercel**, API, dữ liệu và mô hình AI chạy trên **Railway**. Làm lần lượt từ bước 1 đến bước 7; mỗi bước có phần kiểm tra trước khi sang bước sau.

## Kiến trúc

```
Trình duyệt ──https──> Vercel (frontend tĩnh, frontend/dist)
                         │  /api/* được Vercel chuyển tiếp, kèm header x-origin-secret
                         ▼
                  Railway service "api"  (Dockerfile ở gốc repo, 1 bản chạy)
                    ├─ volume /data: SQLite, Qdrant, tài liệu Kho tri thức
                    ├─ Telegram polling (nếu bật)
                    └─ http://ollama.railway.internal:11434  (mạng nội bộ Railway)
                                       ▼
                  Railway service "ollama"  (deploy/railway-ollama)
                    └─ volume /root/.ollama: qwen3:4b + embeddinggemma:300m
```

Vì sao làm như vậy:

- **Một domain cho trình duyệt.** Vercel chuyển tiếp `/api/*` sang Railway nên trình duyệt chỉ thấy domain Vercel. Cookie đăng nhập (HttpOnly, Secure, SameSite=Strict) và kiểm tra CSRF giữ nguyên như khi chạy một máy, không cần mở CORS.
- **Chỉ Vercel gọi được API.** Khi đặt `ORIGIN_SECRET`, API từ chối mọi request không có header `x-origin-secret` đúng (trả 403), trừ `/api/v1/health` cho Railway kiểm tra. Gọi thẳng domain Railway, kể cả `/docs`, đều bị chặn.
- **Giới hạn tần suất tính theo từng khách.** Với request có secret, API lấy IP khách từ `x-real-ip` mà Vercel ghi đè (khách không tự đặt được), thay vì coi cả Vercel là một khách.
- **Ollama không ra Internet.** Service `ollama` không có domain công khai; chỉ `api` gọi được qua mạng nội bộ.

## Cần biết trước

| Vấn đề | Chi tiết | Ảnh hưởng |
|---|---|---|
| Thời gian chờ của Vercel | Vercel chờ tối đa **120 giây** để API bắt đầu trả lời; quá hạn trả lỗi `ROUTER_EXTERNAL_TARGET_ERROR` ([Vercel Limits](https://vercel.com/docs/limits)) | Ollama chạy CPU trên Railway có thể mất 30–90 giây mỗi câu trả lời. Nếu vượt 120 giây, tin nhắn vẫn được lưu và câu trả lời hiện ra sau vài giây nhờ widget tự làm mới, nhưng khách thấy lỗi tạm thời. |
| Chi phí Railway | Gói Hobby $5/tháng, đã gồm $5 tài nguyên; RAM **$10/GB/tháng**, CPU **$20/vCPU/tháng**, tính theo mức dùng thực tế ([Railway Pricing](https://docs.railway.com/pricing/plans)) | qwen3:4b khi đang nạp chiếm khoảng 4–5 GB RAM. Để mô hình nạp liên tục có thể tốn vài chục USD/tháng; để nó tự giải phóng khi rảnh (`LLM_KEEP_ALIVE=5m`) thì rẻ hơn nhưng câu hỏi đầu sau khi rảnh chậm hơn. Xem mục Usage trên Railway sau vài ngày. |
| Volume | Mỗi service một volume; service có volume chỉ chạy **một bản** và mất kết nối vài giây mỗi lần deploy lại; Hobby mặc định 5 GB, tăng được ([Railway Volumes](https://docs.railway.com/volumes/reference)) | Không bật nhiều replica cho `api`. Hai model chiếm khoảng 3 GB trên volume của `ollama`. |
| Dữ liệu | Bản deploy bắt đầu với dữ liệu trống | Tạo lại tài khoản admin và tải lại 12 tài liệu Kho tri thức ở bước 6. Dữ liệu trên máy bạn không tự chuyển lên. |
| Telegram | Một bot chỉ được một nơi polling | Khi bật Telegram trên Railway, tắt Telegram ở backend trên máy (`TELEGRAM_ENABLED=false`). |

## Bước 1. Chuẩn bị

1. Repo đã lên GitHub (`nvkdzvcl/DACN_RAG`), nhánh `main` là bản cần deploy.
2. Tạo tài khoản [Railway](https://railway.com) (gói Hobby) và [Vercel](https://vercel.com), đăng nhập bằng GitHub.
3. Tạo một chuỗi bí mật dài cho `ORIGIN_SECRET` và lưu lại (dùng cho cả Railway và Vercel):

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

## Bước 2. Railway: service `ollama`

1. Railway → **New Project** → **Deploy from GitHub repo** → chọn repo.
2. Mở service vừa tạo → **Settings**:
   - **Service name**: `ollama` (tên này tạo địa chỉ nội bộ `ollama.railway.internal`).
   - **Root Directory**: `deploy/railway-ollama`.
   - Không bấm **Generate Domain** (không mở ra Internet).
3. **Volumes** → thêm volume, **Mount path** `/root/.ollama`.
4. **Variables** (không bắt buộc): `LLM_MODEL=qwen3:4b`, `EMBEDDING_MODEL=embeddinggemma:300m`. Nếu đổi model ở đây thì đổi cùng giá trị ở service `api`.
5. Deploy. Lần đầu tải model mất vài phút.

**Kiểm tra:** trong **Deploy Logs** có dòng `Ollama ready with qwen3:4b and embeddinggemma:300m`.

## Bước 3. Railway: service `api`

1. Trong cùng project → **New** → **GitHub Repo** → chọn lại repo.
2. **Settings**:
   - **Service name**: `api`.
   - **Root Directory**: để trống (gốc repo). Railway tự dùng `Dockerfile` ở gốc.
   - **Healthcheck Path**: `/api/v1/health`.
   - **Replicas**: 1.
   - **Networking** → **Generate Domain**. Ghi lại domain, ví dụ `api-production-1234.up.railway.app`.
3. **Volumes** → thêm volume, **Mount path** `/data`.
4. **Variables** (dán từng dòng, thay phần trong `< >`):

   ```
   APP_ENV=production
   SERVE_FRONTEND=false
   ORIGIN_SECRET=<chuỗi ở bước 1>
   CUSTOMER_PUBLIC_URL=<điền sau ở bước 5, tạm để https://example.com>
   OLLAMA_HOST=http://ollama.railway.internal:11434
   LLM_MODEL=qwen3:4b
   EMBEDDING_MODEL=embeddinggemma:300m
   LLM_KEEP_ALIVE=5m
   RAG_MIN_SCORE=0.35
   TELEGRAM_ENABLED=false
   ```

   `DATABASE_URL`, `QDRANT_PATH`, `KNOWLEDGE_PATH` đã có sẵn trong `Dockerfile` (trỏ vào `/data`), không cần đặt.
5. Deploy.

**Kiểm tra:**

- Mở `https://<domain api>/api/v1/health`: trả `{"status":"ok",...}`.
- Mở `https://<domain api>/api/v1/widget/session`: trả `403 Forbidden`. Đúng như mong đợi, vì chỉ Vercel được gọi API.

## Bước 4. Vercel: frontend

1. Sửa `frontend/vercel.json`: thay `YOUR-API.up.railway.app` bằng domain api ở bước 3. Commit và push lên `main`.
2. Vercel → **Add New Project** → import repo:
   - **Root Directory**: `frontend`.
   - **Framework Preset**: Vite (tự nhận). Build `npm run build`, output `dist` đã ghi trong `vercel.json`.
   - **Environment Variables**: `ORIGIN_SECRET` = cùng chuỗi ở bước 1, cho môi trường **Production**.
3. Deploy, ghi lại domain Vercel, ví dụ `dacn-rag.vercel.app`.

**Kiểm tra:** `https://<domain vercel>/api/v1/health` trả `ok` (đi qua Vercel sang Railway). Nếu trả 403 thì `ORIGIN_SECRET` hai bên chưa khớp. Nếu sửa biến môi trường trên Vercel thì phải deploy lại.

## Bước 5. Nối hai bên

Railway → service `api` → **Variables** → đặt `CUSTOMER_PUBLIC_URL=https://<domain vercel>` (không có dấu `/` ở cuối) → deploy lại. Biến này dùng cho link trong email xác minh và đặt lại mật khẩu.

## Bước 6. Khởi tạo dữ liệu

1. Cài Railway CLI rồi đăng nhập:

   ```bash
   npm install -g @railway/cli
   ```

   ```bash
   railway login
   ```

2. Trong thư mục repo, chọn project vừa tạo:

   ```bash
   railway link
   ```

3. Mở shell vào service `api` (chọn `api` khi được hỏi):

   ```bash
   railway ssh
   ```

4. Tạo admin (nhập mật khẩu 12–128 ký tự khi được hỏi):

   ```bash
   python -m app.create_user admin --role admin --name "Quản trị viên"
   ```

   Nhập danh mục sản phẩm minh họa (24 sản phẩm, giá tham khảo) cho `/products` và trang Sản phẩm, rồi `exit`. Chạy lại không tạo trùng; sửa hoặc ẩn sau ở trang **Sản phẩm**:

   ```bash
   python -m app.import_products
   ```

5. Mở `https://<domain vercel>/`, đăng nhập admin → **Kho tri thức** → **Tải tài liệu**: tải lần lượt 12 file trong `knowledge/fptshop/`. Mỗi file được lập chỉ mục bằng Ollama trên Railway.
6. **Cài đặt → Thanh toán chuyển khoản (VietQR)**: chọn ngân hàng, nhập số tài khoản và tên chủ tài khoản, giữ "Chia giá khi demo" = 1000 nếu chỉ thử. Khi đó mua qua bot Telegram sẽ nhận mã QR có số tiền.
7. (Tuỳ chọn) Tạo tài khoản nhân viên khác trong **Cài đặt**, tạo vài đơn hàng thử trong **Đơn hàng**.

**Kiểm tra:** Kho tri thức hiện 12 tài liệu "Đã lập chỉ mục". Tab **Thử hỏi AI** trả lời có nguồn. Ghi lại thời gian trả lời để biết còn cách giới hạn 120 giây bao xa.

## Bước 7. Kiểm thử sau deploy

Làm trên domain Vercel, cả máy tính và điện thoại:

- [ ] Khách: đăng ký, nhận email mã 6 số (cần SMTP ở mục bên dưới), hỏi chính sách và thấy nguồn, gặp nhân viên, hủy yêu cầu, Tra đơn.
- [ ] Nhân viên: Tổng quan, tiếp nhận hội thoại, trả lời, ghi chú nội bộ, Diễn biến, hoàn tất.
- [ ] Widget nhúng: `https://<domain vercel>/widget-demo.html`.
- [ ] Gọi thẳng domain Railway (ví dụ `/docs`) trả 403.
- [ ] Theo dõi mục Usage của Railway trong vài ngày đầu.

## Telegram và email (tuỳ chọn)

- **Telegram:**
  1. Tắt Telegram ở backend trên máy trước (`TELEGRAM_ENABLED=false` trong `.env`, khởi động lại).
  2. Trên Railway `api` đặt `TELEGRAM_ENABLED=true` và `TELEGRAM_BOT_TOKEN=<token>`, deploy lại.
  3. Gửi `/start` cho bot. Lần đầu bot nhận lại các tin chưa xử lý (nếu có).
- **Email (SMTP):** đặt `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` (`starttls` hoặc `ssl`), `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD` trên Railway `api`. Không đặt thông tin này ở Vercel.

## Cập nhật phiên bản

Push lên `main` thì Vercel và Railway tự deploy lại. Service `api` mất kết nối vài giây mỗi lần deploy, vì volume chỉ gắn với một bản chạy. Muốn chạy một tag cụ thể (ví dụ `v1.6.0`), chọn commit đó trong mục Deployments của từng bên.

## Sự cố thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Mọi trang báo lỗi, API trả `403 Forbidden` | `ORIGIN_SECRET` trên Vercel và Railway khác nhau, hoặc Vercel chưa deploy lại sau khi đặt biến | Đặt lại cho khớp, deploy lại Vercel |
| Đăng nhập xong vẫn bị đăng xuất | Mở domain Railway thay vì domain Vercel | Chỉ dùng domain Vercel |
| `503 Ollama chưa sẵn sàng` | Model đang tải, hoặc `OLLAMA_HOST` sai, hoặc service `ollama` thiếu RAM | Xem log service `ollama`; kiểm tra tên service là `ollama` |
| Thỉnh thoảng lỗi `ROUTER_EXTERNAL_TARGET_ERROR` khi hỏi AI | Câu trả lời mất hơn 120 giây | Tăng CPU cho service `ollama`; đặt `LLM_KEEP_ALIVE=30m` để tránh nạp lại mô hình; câu trả lời vẫn được lưu và hiện sau |
| Bot Telegram trả lời hai lần hoặc lỗi 409 | Có hai nơi cùng polling một bot | Tắt Telegram ở máy local |

## Giới hạn

- Một bản API, SQLite và Qdrant nhúng trên volume: hợp với demo và đồ án, chưa phù hợp tải lớn.
- Chưa có sao lưu tự động trên Railway. Công cụ `python -m app.backup` cần dừng API (`--offline`), nên chưa áp dụng được trực tiếp cho volume đang chạy.
- Thời gian trả lời phụ thuộc CPU Railway; chưa đo tải trên môi trường này.
