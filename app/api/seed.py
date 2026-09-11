from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import Customer, Order

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
    db.commit()
    return {"customer_id": customer_id, "created_orders": created, "order_ids": [o.id for o in orders]}
