from sqlalchemy.orm import Session
from app.models.support import Conversation, Message, Ticket
from app.services.handoff_service import classify_message
from app.services.order_service import extract_order_id, lookup_order
from app.rag.answer_service import answer_question
from uuid import uuid4

def process_message(db: Session, conversation: Conversation, content: str) -> dict:
    sentiment, handoff = classify_message(content)
    order_id = extract_order_id(content)
    order_result = lookup_order(db, order_id, conversation.customer_id) if order_id else None
    if order_id and (not order_result or not order_result["found"]):
        handoff = True
    message = Message(id=str(uuid4()), conversation_id=conversation.id, sender_type="customer", content=content)
    db.add(message)
    if handoff:
        conversation.status = "handoff_requested"; conversation.priority = "high"
        db.add(Ticket(id=str(uuid4()), conversation_id=conversation.id, priority="high", summary=content[:500]))
    db.commit()
    return {"message_id": message.id, "sentiment": sentiment, "needs_handoff": handoff, "order_lookup": order_result, "rag": None if order_id else answer_question(content)}
