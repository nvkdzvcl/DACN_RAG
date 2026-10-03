from sqlalchemy import exists, or_
from sqlalchemy.orm import Session
from app.models.support import Conversation, Order, OrderAccess, WidgetSession, CustomerSession
import re
import time

# Match a whole token up to the DB/API limit; only ASCII letters may ignore case.
ORDER_PATTERN = re.compile(r"(?<![\w-])(?=[\w-]{6,64}(?![\w-]))(?ai:(?:DH|ORD)[-_]?[A-Z0-9]{4,})(?![\w-])")

def extract_order_id(content: str) -> str | None:
    match = ORDER_PATTERN.search(content)
    return match.group(0).upper() if match else None


def active_order_access(db: Session, conversation_id: str):
    now = int(time.time())
    valid_session = or_(
        exists().where(WidgetSession.conversation_id == OrderAccess.conversation_id, WidgetSession.expires_at > now),
        exists().where(CustomerSession.conversation_id == OrderAccess.conversation_id, CustomerSession.expires_at > now))
    return db.query(OrderAccess).join(Order, Order.id == OrderAccess.order_id).join(
        Conversation, Conversation.id == OrderAccess.conversation_id).filter(
             Conversation.status != 'closed', OrderAccess.conversation_id == conversation_id, OrderAccess.expires_at > now,
             valid_session, OrderAccess.customer_id == Order.customer_id)

def lookup_order(db: Session, order_id: str, customer_id: str, conversation_id: str | None = None) -> dict:
    order = db.get(Order, order_id)
    permitted = order is not None and order.customer_id == customer_id
    if order is not None and not permitted and conversation_id:
        permitted = active_order_access(db, conversation_id).filter(OrderAccess.order_id == order_id).first() is not None
    if not permitted:
        return {"found": False, "reason": "order_not_found_or_not_owned"}
    return {"found": True, "order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}
