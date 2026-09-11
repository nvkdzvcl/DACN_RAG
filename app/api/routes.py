from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import Conversation, Customer, Message, Order, Ticket
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageCreate
from app.services.handoff_service import classify_message

router = APIRouter(prefix="/api/v1")

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    if db.get(Customer, payload.customer_id) is None:
        db.add(Customer(id=payload.customer_id, display_name=payload.customer_id))
    conversation = Conversation(id=str(uuid4()), customer_id=payload.customer_id, channel=payload.channel.value)
    db.add(conversation); db.commit(); db.refresh(conversation)
    return conversation

@router.post("/conversations/{conversation_id}/messages")
def add_message(conversation_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    message = Message(id=str(uuid4()), conversation_id=conversation_id, sender_type="customer", content=payload.content, external_message_id=payload.external_message_id)
    sentiment, needs_handoff = classify_message(payload.content)
    db.add(message)
    if needs_handoff:
        conversation.status = "handoff_requested"
        conversation.priority = "high"
        db.add(Ticket(id=str(uuid4()), conversation_id=conversation_id, priority="high", summary="Tự động chuyển nhân viên: " + payload.content[:500]))
    db.commit()
    return {"message_id": message.id, "conversation_id": conversation_id, "status": "handoff_requested" if needs_handoff else "received", "sentiment": sentiment, "needs_handoff": needs_handoff}

@router.post("/conversations/{conversation_id}/tickets")
def create_ticket(conversation_id: str, db: Session = Depends(get_db)):
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    ticket = Ticket(id=str(uuid4()), conversation_id=conversation_id)
    db.add(ticket); db.commit(); db.refresh(ticket)
    return {"ticket_id": ticket.id, "status": ticket.status, "priority": ticket.priority}

@router.get("/orders/{order_id}")
def get_order(order_id: str, customer_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order.id, "status": order.status, "tracking_code": order.tracking_code}
