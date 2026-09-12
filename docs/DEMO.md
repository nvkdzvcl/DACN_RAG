# Demo nhanh

## Unified Inbox

Mở hai terminal tại thư mục dự án. Terminal backend:

```powershell
python -m uvicorn app.main:app --reload
```

Terminal frontend:

```powershell
cd frontend
npm run dev
```

Khởi động lại Vite nếu đã mở từ trước khi thêm `vite.config.mjs`. Frontend gọi `/api` cùng origin; Vite chuyển tiếp tới `http://127.0.0.1:8000`. Khi deploy, cấu hình reverse proxy `/api` tương tự. Chỉ đặt `VITE_API_BASE` cho host khác nếu backend đó đã cấu hình CORS phù hợp.

Danh sách rỗng là trạng thái hợp lệ khi DB chưa có hội thoại. Không tự thay bằng mock. Chọn hội thoại để xem tin nhắn, ticket và khách hàng thật; lọc theo trạng thái/ưu tiên hoặc tìm tên/ID/kênh. Các số liệu đầu trang chỉ tính tập hội thoại đang lọc. Chưa hỗ trợ trả lời và tiếp nhận từ giao diện.

Kiểm tra backend bằng SQLite trong bộ nhớ, không sửa DB hiện có:

```powershell
python -m unittest app.tests.test_inbox
```

## API và dữ liệu mẫu

Khởi động API:

```powershell
uvicorn app.main:app --reload
```

Tạo dữ liệu mẫu:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/demo/seed
```

Tra cứu đơn hàng:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/orders/lookup -ContentType 'application/json' -Body '{"order_id":"ORD-DEMO01","customer_id":"cus_demo_001"}'
```
