from uuid import uuid4
from contextlib import nullcontext

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.support import Conversation, Message, Ticket
from app.services.handoff_service import classify_message
from app.services.order_service import extract_order_id, lookup_order
from app.rag.answer_service import answer_question, sources_current
from app.rag.ollama import ProviderError
from app.rag.vector_store import document_lock


def process_message(db: Session, conversation: Conversation, content: str, external_message_id: str | None = None) -> dict:
    content = content.strip()
    if not content or len(content) > 4000:
        raise HTTPException(422, "Message must contain 1-4000 nonblank characters")
    conversation_id = conversation.id
    try:
        db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
        db.refresh(conversation)
        if conversation.status == "closed":
            raise HTTPException(409, "Conversation is closed")
        if external_message_id:
            previous = db.query(Message).filter_by(conversation_id=conversation_id, external_message_id=external_message_id).first()
            if previous:
                if previous.sender_type != "customer" or previous.content != content:
                    raise HTTPException(409, "Message ID was already used for different content")
                response = {"message_id": previous.id, "status": conversation.status, "duplicate": True}
                db.commit()
                return response
        message_id = str(uuid4())
        message = Message(id=message_id, conversation_id=conversation_id, sender_type="customer", content=content,
                          external_message_id=external_message_id)
        db.add(message)
        conversation.last_customer_message_id = message_id
        db.flush()
        sentiment, handoff = classify_message(content)
        order_result = rag = None
        answer = error = None
        should_generate = False
        history = []
        if conversation.status in {"open", "resolved"}:
            if conversation.status == "resolved":
                handoff = True
                conversation.assigned_agent_id = None
            order_id = extract_order_id(content)
            if not handoff and order_id:
                order_result = lookup_order(db, order_id, conversation.customer_id)
                handoff = not order_result["found"]
            if handoff:
                conversation.status = "handoff_requested"
                conversation.priority = "high"
                ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation_id, Ticket.status.in_(["open", "assigned"])).first()
                if ticket is None:
                    recent = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc(), Message.id.desc()).limit(8).all()
                    summary = "\n".join(f"{item.sender_type}: {item.content[:400]}" for item in reversed(recent))
                    db.add(Ticket(id=str(uuid4()), conversation_id=conversation_id, priority="high", summary=summary))
            elif order_result:
                answer = f"Đơn hàng {order_result['order_id']}: {order_result['status']}."
                if order_result["tracking_code"]:
                    answer += f" Mã vận đơn: {order_result['tracking_code']}."
            else:
                should_generate = True
                recent = db.query(Message).filter(Message.conversation_id == conversation_id, Message.id != message_id,
                    Message.sender_type.in_(["customer", "ai"])).order_by(Message.created_at.desc(), Message.id.desc()).limit(4).all()
                history = [{"role": "user" if m.sender_type == "customer" else "assistant", "content": m.content[:500]} for m in reversed(recent)]
        # Persist inbound first. Ollama must never hold the conversation write lock.
        db.commit()
        if should_generate:
            try:
                rag = answer_question(content, history=history, db=db)
                answer = rag["answer"]
            except ProviderError as exc:
                error = str(exc)
            finally:
                db.rollback()
        ai_message_id = None
        # Recheck after generation and serialize with document deletion/reindex.
        with document_lock if answer else nullcontext():
            db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
            db.refresh(conversation)
            current = conversation.status == "open" and conversation.last_customer_message_id == message_id
            valid_sources = not rag or not rag.get("grounded") or sources_current(db, rag.get("reviewed_sources", rag["citations"]))
            if answer and current and valid_sources:
                ai_message_id = str(uuid4())
                db.add(Message(id=ai_message_id, conversation_id=conversation_id, sender_type="ai", content=answer,
                               citations=rag["citations"] if rag else []))
            else:
                rag = None
                if not current:
                    order_result = None
                    error = None
            status = conversation.status
            db.commit()
        return {"message_id": message_id, "ai_message_id": ai_message_id, "status": status, "sentiment": sentiment,
                "needs_handoff": status in {"handoff_requested", "assigned"}, "order_lookup": order_result,
                "rag": rag, "ai_error": error}
    except Exception:
        db.rollback()
        raise
