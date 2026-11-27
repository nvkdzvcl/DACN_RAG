from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from uuid import uuid4
from app.models.support import Customer, Order, Product

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
    customer_id = "cus_demo_001"
    if db.get(Customer, customer_id) is None:
        db.add(Customer(id=customer_id, display_name="Nguyễn Khách Demo", email="demo@example.com"))
    orders = [
        Order(id="ORD-DEMO01", customer_id=customer_id, status="shipping", tracking_code="VN123456"),
        Order(id="ORD-DEMO02", customer_id=customer_id, status="delivered", tracking_code="VN654321"),
    ]
    created = 0
    for order in orders:
        if db.get(Order, order.id) is None:
            db.add(order); created += 1
    # Illustrative catalogue for the Telegram /products demo; added only when the catalogue is empty.
    demo_products = [
        ('iPhone 16 128GB', 'phone', 19_990_000, True), ('Samsung Galaxy S25 256GB', 'phone', 21_990_000, True),
        ('Xiaomi Redmi Note 14 128GB', 'phone', 4_990_000, False), ('MacBook Air M3 13 inch 256GB', 'laptop', 26_490_000, True),
        ('ASUS Vivobook 15 i5', 'laptop', 14_990_000, True), ('iPad Air M2 11 inch WiFi 128GB', 'tablet', 16_990_000, True),
        ('Apple Watch SE 2 40mm', 'watch', 5_990_000, True), ('Tai nghe AirPods 4', 'accessory', 3_490_000, True),
    ]
    added_products = 0
    if db.query(Product).count() == 0:
        for name, category, price, in_stock in demo_products:
            db.add(Product(id=str(uuid4()), name=name, category=category, price=price, in_stock=in_stock,
                           stock=15 if in_stock else 0, description='Giá minh họa cho bản demo đồ án.'))
            added_products += 1
    db.commit()
    return {"customer_id": customer_id, "created_orders": created, "order_ids": [o.id for o in orders],
            "created_products": added_products}
