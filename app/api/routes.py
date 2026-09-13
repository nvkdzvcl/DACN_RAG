from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import Conversation, Customer, Order, Ticket
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate
from app.services.message_service import process_message

router = APIRouter(prefix="/api/v1")

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    if db.get(Customer, payload.customer_id) is None:
        db.add(Customer(id=payload.customer_id, display_name=payload.customer_id))
    conversation = Conversation(id=str(uuid4()), customer_id=payload.customer_id, channel=payload.channel.value)
    db.add(conversation); db.commit(); db.refresh(conversation)
    return {"conversation_id": conversation.id, "status": conversation.status, "priority": conversation.priority, "created_at": conversation.created_at}

@router.post("/conversations/{conversation_id}/messages")
def add_message(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, **process_message(db, conversation, payload.content, payload.external_message_id)}

@router.post("/conversations/{conversation_id}/tickets")
def create_ticket(conversation_id: str, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
    db.refresh(conversation)
    if conversation.status in {"closed", "resolved"}:
        db.rollback()
        raise HTTPException(409, "Conversation is closed")
    if conversation.status == "open":
        conversation.status = "handoff_requested"
        conversation.priority = "high"
    ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation_id, Ticket.status.in_(["open", "assigned"])).first()
    if ticket is None:
        ticket = Ticket(id=str(uuid4()), conversation_id=conversation_id, status="assigned" if conversation.status == "assigned" else "open", priority=conversation.priority, summary="Nhân viên yêu cầu hỗ trợ trực tiếp.")
        db.add(ticket)
    db.commit()
    return {"ticket_id": ticket.id, "status": ticket.status, "priority": ticket.priority}

@router.get("/orders/{order_id}")
def get_order(order_id: str, customer_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}
