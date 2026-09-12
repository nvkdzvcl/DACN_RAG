from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.support import Conversation, Message, Ticket

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])

class AgentMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    agent_id: str = Field(min_length=1, max_length=64)

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

@router.post("/conversations/{conversation_id}/accept")
def accept_conversation(conversation_id: str, agent_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not agent_id.strip():
        raise HTTPException(status_code=422, detail="agent_id is required")
    conversation.status = "assigned"
    tickets = db.query(Ticket).filter_by(conversation_id=conversation_id, status="open").all()
    for ticket in tickets:
        ticket.status = "assigned"
    db.commit()
    return {"conversation_id": conversation_id, "status": conversation.status, "ticket_ids": [ticket.id for ticket in tickets], "agent_id": agent_id}

@router.post("/conversations/{conversation_id}/messages")
def add_agent_message(conversation_id: str, payload: AgentMessageCreate, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.status != "assigned":
        raise HTTPException(status_code=409, detail="Conversation must be assigned before an agent can reply")
    message = Message(id=str(uuid4()), conversation_id=conversation_id, sender_type="agent", content=payload.content.strip())
    db.add(message)
    db.commit()
    return {"message_id": message.id, "conversation_id": conversation_id, "sender_type": message.sender_type, "content": message.content, "status": conversation.status}
