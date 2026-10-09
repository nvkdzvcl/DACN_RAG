from uuid import UUID, uuid4
from itertools import islice
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload
from app.core.auth import require_staff
from app.db.session import get_db
from app.models.support import Conversation, ConversationRead, Message, TelegramDelivery, Ticket, User, now_utc
from app.services.sla_service import conversation_sla, ticket_slas, utc
from app.services.ticket_service import complete_tickets

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])

class AgentMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=4000)
    client_message_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def nonblank_content(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()

class FinishConversation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['resolved', 'closed']
    ticket_id: str = Field(min_length=1, max_length=64)
    last_customer_message_id: str | None = Field(max_length=64)
    note: str = Field(min_length=1, max_length=2000)

    @field_validator('note')
    @classmethod
    def nonblank_note(cls, value):
        if not value.strip():
            raise ValueError('Completion note cannot be blank')
        return value.strip()


class RetryDelivery(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirm_uncertain: bool = False
    action: Literal['retry', 'skip'] = 'retry'

class ReadConversation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message_id: str = Field(min_length=1, max_length=64)

@router.post('/conversations/{conversation_id}/read')
def mark_conversation_read(conversation_id: str, payload: ReadConversation, db: Session = Depends(get_db),
                           user: User = Depends(require_staff)):
    locked = db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
    if not locked.rowcount:
        raise HTTPException(404, 'Conversation not found')
    message = db.get(Message, payload.message_id)
    if message is None or message.conversation_id != conversation_id:
        raise HTTPException(404, 'Message not found in this conversation')
    cursor = db.get(ConversationRead, (user.id, conversation_id), populate_existing=True)
    if cursor is None:
        cursor = ConversationRead(user_id=user.id, conversation_id=conversation_id,
                                  message_id=message.id, message_created_at=message.created_at)
        db.add(cursor)
    elif (utc(message.created_at), message.id) > (utc(cursor.message_created_at), cursor.message_id):
        cursor.message_id, cursor.message_created_at = message.id, message.created_at
    db.commit()
    return {'conversation_id': conversation_id, 'message_id': cursor.message_id}


@router.post('/messages/{message_id}/retry-delivery')
def retry_delivery(message_id: str, payload: RetryDelivery, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(404, 'Không tìm thấy tin nhắn.')
    owned = db.execute(update(Conversation).where(Conversation.id == message.conversation_id,
        Conversation.channel == 'telegram', Conversation.assigned_agent_id == user.id).values(status=Conversation.status))
    if owned.rowcount != 1:
        db.rollback()
        raise HTTPException(403, 'Chỉ nhân viên phụ trách được gửi lại.')
    delivery = db.get(TelegramDelivery, message_id)
    if delivery is None or delivery.state not in {'failed', 'uncertain'}:
        raise HTTPException(409, 'Tin nhắn không chờ gửi lại.')
    if payload.action == 'retry' and delivery.state == 'uncertain' and not payload.confirm_uncertain:
        raise HTTPException(409, 'Telegram có thể đã nhận tin. Xác nhận nguy cơ gửi trùng trước khi gửi lại.')
    delivery.state = 'pending' if payload.action == 'retry' else 'skipped'
    delivery.error = None if payload.action == 'retry' else 'skipped_by_staff'
    db.commit()
    return {'status': delivery.state}


@router.post('/conversations/{conversation_id}/finish')
def finish_conversation(conversation_id: str, payload: FinishConversation, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    try:
        locked = db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
        if not locked.rowcount:
            raise HTTPException(404, 'Conversation not found')
        conversation = db.get(Conversation, conversation_id)
        db.refresh(conversation)
        ticket = db.get(Ticket, payload.ticket_id)
        if ticket is None or ticket.conversation_id != conversation_id:
            raise HTTPException(404, 'Ticket not found')
        if ticket.status in {'resolved', 'closed'}:
            if ticket.status == payload.status and ticket.completed_by_id == user.id and ticket.completion_note == payload.note:
                db.commit()
                return {'status': conversation.status, 'duplicate': True}
            raise HTTPException(409, 'Ticket was already completed')
        if conversation.status != 'assigned' or conversation.assigned_agent_id != user.id:
            raise HTTPException(409, 'Only the assigned agent can complete this conversation')
        if conversation.last_customer_message_id != payload.last_customer_message_id:
            raise HTTPException(409, 'Có tin khách mới. Đọc lại hội thoại trước khi hoàn tất.')
        complete_tickets(db, conversation_id, payload.status, user.id, payload.note)
        conversation.status = payload.status
        content = ('Nhân viên đã đánh dấu yêu cầu được giải quyết. Nếu cần hỗ trợ thêm, bạn có thể nhắn tiếp.'
                   if payload.status == 'resolved' else 'Nhân viên đã đóng hội thoại. Tin nhắn tiếp theo sẽ bắt đầu hội thoại mới.'
                   if conversation.channel == 'telegram' else 'Nhân viên đã đóng hội thoại. Bạn có thể kết thúc phiên và bắt đầu cuộc trò chuyện mới.')
        db.add(Message(id=str(uuid4()), conversation_id=conversation_id, sender_type='system', content=content))
        db.commit()
        return {'status': conversation.status, 'duplicate': False}
    except Exception:
        db.rollback()
        raise

@router.get("/conversations")
def list_conversations(status: str | None = None, priority: str | None = None, db: Session = Depends(get_db),
                       sla: Literal['on_track', 'overdue', 'met', 'breached', 'cancelled', 'none'] | None = None,
                       q: Annotated[str, Query(max_length=160)] = '',
                       offset: Annotated[int, Query(ge=0, le=2**31 - 1)] = 0,
                       limit: Annotated[int, Query(ge=1, le=100)] = 25,
                       assignment: Literal['all', 'mine', 'unassigned'] = 'all',
                       user: User = Depends(require_staff)):
    latest = select(Message.created_at).where(Message.conversation_id == Conversation.id).order_by(
        Message.created_at.desc(), Message.id.desc()).limit(1).correlate(Conversation).scalar_subquery()
    query = db.query(Conversation).options(joinedload(Conversation.customer)).order_by(
        func.coalesce(latest, Conversation.created_at).desc(), Conversation.id)
    if assignment == 'mine': query = query.filter(Conversation.assigned_agent_id == user.id)
    elif assignment == 'unassigned': query = query.filter(Conversation.assigned_agent_id.is_(None))
    if status: query = query.filter(Conversation.status == status)
    if priority: query = query.filter(Conversation.priority == priority)
    search = q.strip().lower()
    scan = bool(search or sla)
    # ponytail: Unicode search and derived SLA scan bounded batches; index/materialize before scaling these filters.
    items = iter(query.yield_per(200) if scan else query.offset(offset).limit(limit).all())
    total = 0 if scan else query.order_by(None).count()
    result, now = [], now_utc()
    while batch := list(islice(items, 200)):
        if search:
            batch = [c for c in batch if search in f'{c.customer.display_name or c.customer_id} {c.customer_id} {c.channel}'.lower()]
        grouped = {}
        for item in ticket_slas(db, [c.id for c in batch], now=now).values() if batch else ():
            grouped.setdefault(item['conversation_id'], []).append(item)
        for c in batch:
            value = conversation_sla(grouped.get(c.id, []))
            if sla and (value['status'] if value else 'none') != sla:
                continue
            if scan:
                total += 1
                if not offset < total <= offset + limit:
                    continue
            result.append({"conversation_id": c.id, "customer_id": c.customer_id, "customer_name": c.customer.display_name,
                           "channel": c.channel, "status": c.status, "assigned_agent_id": c.assigned_agent_id,
                           "priority": c.priority, "created_at": c.created_at, "sla": value})
    ids = [item['conversation_id'] for item in result]
    latest_id = select(Message.id).where(Message.conversation_id == Conversation.id).order_by(
        Message.created_at.desc(), Message.id.desc()).limit(1).correlate(Conversation).scalar_subquery()
    messages = {message.conversation_id: message for message in db.query(Message).join(
        Conversation, Conversation.id == Message.conversation_id).filter(Conversation.id.in_(ids), Message.id == latest_id)} if ids else {}
    unread = dict(db.query(Message.conversation_id, func.count(Message.id)).outerjoin(ConversationRead,
        (ConversationRead.conversation_id == Message.conversation_id) & (ConversationRead.user_id == user.id)).filter(
        Message.conversation_id.in_(ids), Message.sender_type == 'customer',
        ConversationRead.message_id.is_(None) | (Message.created_at > ConversationRead.message_created_at) |
        ((Message.created_at == ConversationRead.message_created_at) & (Message.id > ConversationRead.message_id))
    ).group_by(Message.conversation_id).all()) if ids else {}
    for item in result:
        message = messages.get(item['conversation_id'])
        item.update(last_activity_at=message.created_at if message else item['created_at'],
                    last_message={'content': message.content[:160], 'sender_type': message.sender_type} if message else None,
                    unread_count=unread.get(item['conversation_id'], 0))
    return {"count": len(result), "total": total, "offset": offset, "limit": limit,
            "has_more": offset + len(result) < total, "conversations": result}

@router.get("/conversations/{conversation_id}")
def conversation_detail(conversation_id: str, db: Session = Depends(get_db),
                        before: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
                        limit: Annotated[int, Query(ge=1, le=100)] = 50):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    query = db.query(Message).filter_by(conversation_id=conversation_id)
    if before is not None:
        anchor = query.filter(Message.id == before).first()
        if anchor is None:
            raise HTTPException(404, 'Message cursor not found in this conversation')
        query = query.filter((Message.created_at < anchor.created_at) |
                             ((Message.created_at == anchor.created_at) & (Message.id < anchor.id)))
    # Use the indexed timestamp/ID pair so new arrivals do not shift older pages.
    messages = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1).all()
    has_more = len(messages) > limit
    messages = list(reversed(messages[:limit]))
    message_page = {'limit': limit, 'before': before, 'has_more': has_more,
                    'next_before': messages[0].id if has_more else None}
    tickets = db.query(Ticket).filter_by(conversation_id=conversation_id).order_by(Ticket.created_at.desc()).all()
    slas = ticket_slas(db, [conversation_id])
    completers = {u.id: u.display_name for u in db.query(User).filter(User.id.in_([t.completed_by_id for t in tickets if t.completed_by_id])).all()}
    deliveries = {d.message_id: {'state': d.state, 'error': d.error, 'sent_at': d.sent_at}
                  for d in db.query(TelegramDelivery).filter(TelegramDelivery.message_id.in_([m.id for m in messages]))}
    return {"conversation_id": conversation.id, "customer_id": conversation.customer_id, "customer_name": conversation.customer.display_name, "customer_email": conversation.customer.email, "channel": conversation.channel, "status": conversation.status, "assigned_agent_id": conversation.assigned_agent_id, "priority": conversation.priority, "sla": conversation_sla(list(slas.values())), "last_customer_message_id": conversation.last_customer_message_id, "message_page": message_page, "messages": [{"id": m.id, "sender_type": m.sender_type, "agent_id": m.agent_id, "content": m.content, "citations": m.citations or [], "tool_trace": m.tool_trace, "delivery": deliveries.get(m.id, {"state": "pending"} if conversation.channel == "telegram" and m.sender_type != "customer" else None), "created_at": m.created_at} for m in messages], "tickets": [{"id": t.id, "status": t.status, "priority": t.priority, "summary": t.summary, "created_at": t.created_at, "completed_at": t.completed_at, "completed_by_id": t.completed_by_id, "completed_by_name": completers.get(t.completed_by_id), "completion_note": t.completion_note, "sla": slas[t.id]} for t in tickets]}

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
    external_id = f'agent:{payload.client_message_id}' if payload.client_message_id else None
    message = db.query(Message).filter_by(conversation_id=conversation_id, external_message_id=external_id).first() if external_id else None
    if message and (message.sender_type != 'agent' or message.agent_id != user.id or message.content != payload.content):
        db.rollback()
        raise HTTPException(409, 'Mã gửi đã được dùng cho nội dung khác.')
    message = message or Message(id=str(uuid4()), conversation_id=conversation_id, sender_type="agent", agent_id=user.id,
                                 content=payload.content, external_message_id=external_id)
    db.add(message)
    db.commit()
    return {"message_id": message.id, "conversation_id": conversation_id, "sender_type": message.sender_type, "content": message.content, "status": conversation.status}
