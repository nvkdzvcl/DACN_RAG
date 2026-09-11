from sqlalchemy.orm import Session
from app.models.support import Order
import re

ORDER_PATTERN = re.compile(r"\b(?:DH|ORD)[-_]?[A-Z0-9]{4,}\b", re.IGNORECASE)

def extract_order_id(content: str) -> str | None:
    match = ORDER_PATTERN.search(content)
    return match.group(0).upper() if match else None

def lookup_order(db: Session, order_id: str, customer_id: str) -> dict:
    order = db.get(Order, order_id)
    if order is None or order.customer_id != customer_id:
        return {"found": False, "reason": "order_not_found_or_not_owned"}
    return {"found": True, "order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}
