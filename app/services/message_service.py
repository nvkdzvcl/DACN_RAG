from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.support import Conversation, Message, Ticket
from app.services.handoff_service import classify_message
from app.services.order_service import extract_order_id, lookup_order
from app.rag.answer_service import answer_question


def process_message(db: Session, conversation: Conversation, content: str, external_message_id: str | None = None) -> dict:
    content = content.strip()
    if not content or len(content) > 4000:
        raise HTTPException(422, "Message must contain 1-4000 nonblank characters")
    try:
        # ponytail: local retrieval only; move slow LLM calls to jobs before hosting.
        # Serialize state transitions and response persistence in one transaction.
        db.execute(update(Conversation).where(Conversation.id == conversation.id).values(status=Conversation.status))
        db.refresh(conversation)
        if conversation.status in {"closed", "resolved"}:
            raise HTTPException(409, "Conversation is closed")
        if external_message_id:
            previous = db.query(Message).filter_by(conversation_id=conversation.id, external_message_id=external_message_id).first()
            if previous:
                db.commit()
                return {"message_id": previous.id, "status": conversation.status, "duplicate": True}
        message = Message(id=str(uuid4()), conversation_id=conversation.id, sender_type="customer", content=content,
                          external_message_id=external_message_id)
        db.add(message)
        db.flush()
        sentiment, handoff = classify_message(content)
        order_result = rag = None
        ai_message = None
        if conversation.status == "open":
            order_id = extract_order_id(content)
            if not handoff and order_id:
                order_result = lookup_order(db, order_id, conversation.customer_id)
                handoff = not order_result["found"]
            if handoff:
                conversation.status = "handoff_requested"
                conversation.priority = "high"
                ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation.id, Ticket.status.in_(["open", "assigned"])).first()
                if ticket is None:
                    # Extractive handoff context; no invented LLM summary.
                    recent = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at.desc(), Message.id.desc()).limit(8).all()
                    summary = "\n".join(f"{item.sender_type}: {item.content[:400]}" for item in reversed(recent))
                    db.add(Ticket(id=str(uuid4()), conversation_id=conversation.id, priority="high", summary=summary))
            else:
                if order_result:
                    answer = f"Đơn hàng {order_result['order_id']}: {order_result['status']}."
                    if order_result["tracking_code"]:
                        answer += f" Mã vận đơn: {order_result['tracking_code']}."
                else:
                    rag = answer_question(content)
                    answer = rag["answer"]
                ai_message = Message(id=str(uuid4()), conversation_id=conversation.id, sender_type="ai", content=answer,
                                     citations=rag["citations"] if rag else [])
                db.add(ai_message)
        db.commit()
        return {"message_id": message.id, "ai_message_id": ai_message.id if ai_message else None,
                "status": conversation.status, "sentiment": sentiment,
                "needs_handoff": conversation.status in {"handoff_requested", "assigned"},
                "order_lookup": order_result, "rag": rag}
    except Exception:
        db.rollback()
        raise
