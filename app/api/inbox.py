from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.support import Conversation, Message, Ticket

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])

@router.get("/conversations")
def list_conversations(status: str | None = None, priority: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Conversation).options(joinedload(Conversation.customer)).order_by(Conversation.created_at.desc(), Conversation.id)
    if status: query = query.filter(Conversation.status == status)
    if priority: query = query.filter(Conversation.priority == priority)
    items = query.all()
    return {"count": len(items), "conversations": [{"conversation_id": c.id, "customer_id": c.customer_id, "customer_name": c.customer.display_name, "channel": c.channel, "status": c.status, "priority": c.priority, "created_at": c.created_at} for c in items]}

@router.get("/conversations/{conversation_id}")
def conversation_detail(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    tickets = db.query(Ticket).filter_by(conversation_id=conversation_id).order_by(Ticket.created_at.desc()).all()
    return {"conversation_id": conversation.id, "customer_id": conversation.customer_id, "customer_name": conversation.customer.display_name, "customer_email": conversation.customer.email, "channel": conversation.channel, "status": conversation.status, "priority": conversation.priority, "messages": [{"id": m.id, "sender_type": m.sender_type, "content": m.content, "created_at": m.created_at} for m in messages], "tickets": [{"id": t.id, "status": t.status, "priority": t.priority, "summary": t.summary, "created_at": t.created_at} for t in tickets]}
