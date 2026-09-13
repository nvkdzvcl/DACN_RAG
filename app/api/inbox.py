from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload
from app.core.auth import require_staff
from app.db.session import get_db
from app.models.support import Conversation, Message, Ticket, User

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])

class AgentMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def nonblank_content(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()

@router.get("/conversations")
def list_conversations(status: str | None = None, priority: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Conversation).options(joinedload(Conversation.customer)).order_by(Conversation.created_at.desc(), Conversation.id)
    if status: query = query.filter(Conversation.status == status)
    if priority: query = query.filter(Conversation.priority == priority)
    items = query.all()
    return {"count": len(items), "conversations": [{"conversation_id": c.id, "customer_id": c.customer_id, "customer_name": c.customer.display_name, "channel": c.channel, "status": c.status, "assigned_agent_id": c.assigned_agent_id, "priority": c.priority, "created_at": c.created_at} for c in items]}

@router.get("/conversations/{conversation_id}")
def conversation_detail(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    tickets = db.query(Ticket).filter_by(conversation_id=conversation_id).order_by(Ticket.created_at.desc()).all()
    return {"conversation_id": conversation.id, "customer_id": conversation.customer_id, "customer_name": conversation.customer.display_name, "customer_email": conversation.customer.email, "channel": conversation.channel, "status": conversation.status, "assigned_agent_id": conversation.assigned_agent_id, "priority": conversation.priority, "messages": [{"id": m.id, "sender_type": m.sender_type, "agent_id": m.agent_id, "content": m.content, "citations": m.citations or [], "created_at": m.created_at} for m in messages], "tickets": [{"id": t.id, "status": t.status, "priority": t.priority, "summary": t.summary, "created_at": t.created_at} for t in tickets]}

@router.post("/conversations/{conversation_id}/accept")
def accept_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    claimed = db.execute(update(Conversation).where(
        Conversation.id == conversation_id, Conversation.status == "handoff_requested", Conversation.assigned_agent_id.is_(None)
    ).values(status="assigned", assigned_agent_id=user.id))
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Conversation is no longer available for assignment")
    tickets = db.query(Ticket).filter_by(conversation_id=conversation_id, status="open").all()
    for ticket in tickets:
        ticket.status = "assigned"
    db.commit()
    return {"conversation_id": conversation_id, "status": "assigned", "ticket_ids": [ticket.id for ticket in tickets], "agent_id": user.id}

@router.post("/conversations/{conversation_id}/messages")
def add_agent_message(conversation_id: str, payload: AgentMessageCreate, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    owned = db.execute(update(Conversation).where(
        Conversation.id == conversation_id, Conversation.status == "assigned", Conversation.assigned_agent_id == user.id
    ).values(status="assigned"))
    if owned.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conversation must be assigned to the authenticated agent")
    message = Message(id=str(uuid4()), conversation_id=conversation_id, sender_type="agent", agent_id=user.id, content=payload.content)
    db.add(message)
    db.commit()
    return {"message_id": message.id, "conversation_id": conversation_id, "sender_type": message.sender_type, "content": message.content, "status": conversation.status}
