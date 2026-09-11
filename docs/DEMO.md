# Demo nhanh

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
