import os
import secrets
import time
from collections import deque
from threading import BoundedSemaphore, Lock
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core.auth import check_csrf, token_hash
from app.db.session import get_db
from app.models.support import Conversation, Customer, CustomerAccount, CustomerSession, Message, Order, OrderAccess, WidgetSession
from app.services.handoff_service import classify_message
from app.services.message_service import process_message, simple_reply
from app.services.ticket_service import complete_tickets
from app.services.order_service import active_order_access

COOKIE = 'rag_widget_session'
COOKIE_PATH = '/api/v1/widget'
SESSION_SECONDS = 24 * 60 * 60
_attempts = {}
_attempt_lock = Lock()
_answer_slot = BoundedSemaphore(1)


def no_cache(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix=COOKIE_PATH, tags=['widget'], dependencies=[Depends(check_csrf), Depends(no_cache)])


class StartSession(BaseModel):
    model_config = ConfigDict(extra='forbid')
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator('display_name')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Name cannot be blank')
        return value.strip()


class WidgetAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    client_message_id: UUID


class RedeemOrderAccess(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    order_id: str = Field(min_length=6, max_length=64, pattern=r'^(?:DH|ORD)[-_]?[A-Z0-9]{4,}$')
    code: SecretStr = Field(min_length=43, max_length=43)


class WidgetMessage(WidgetAction):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator('content')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Message cannot be blank')
        return value.strip()


def rate_limit(request, bucket, limit):
    # ponytail: one API worker; use shared limits before multi-worker/public hosting.
    now = time.monotonic()
    address = request.client.host if request.client else 'unknown'
    with _attempt_lock:
        for key in list(_attempts):
            if _attempts[key][-1] <= now - 60:
                del _attempts[key]
        attempts = _attempts.setdefault((bucket, address), deque(maxlen=limit))
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= limit:
            raise HTTPException(429, 'Gửi yêu cầu quá nhanh. Chờ một phút rồi thử lại.', headers={'Retry-After': '60'})
        attempts.append(now)


def find_session(request, db):
    token = request.cookies.get(COOKIE, '')
    session = (db.get(WidgetSession, token_hash(token)) or db.get(CustomerSession, token_hash(token))) if token else None
    return session if session and session.expires_at > int(time.time()) else None


def require_session(request: Request, db: Session = Depends(get_db)):
    session = find_session(request, db)
    if session is None:
        raise HTTPException(401, 'Phiên trò chuyện đã hết hạn. Vui lòng bắt đầu phiên mới.')
    return session


def snapshot(db, session, before=None, limit=50):
    conversation = db.get(Conversation, session.conversation_id)
    if conversation is None:
        raise HTTPException(401, 'Phiên trò chuyện không còn hiệu lực.')
    query = db.query(Message).filter_by(conversation_id=conversation.id)
    if before is not None:
        anchor = query.filter(Message.id == before).first()
        if anchor is None:
            raise HTTPException(404, 'Không tìm thấy mốc tin nhắn trong phiên này.')
        query = query.filter((Message.created_at < anchor.created_at) |
                             ((Message.created_at == anchor.created_at) & (Message.id < anchor.id)))
    recent = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1).all()
    has_more = len(recent) > limit
    messages = list(reversed(recent[:limit]))
    account = db.get(CustomerAccount, session.account_id) if isinstance(session, CustomerSession) else None
    return {'account': {'email': account.email, 'email_verified': account.email_verified} if account else None,
            'conversation_id': conversation.id, 'display_name': conversation.customer.display_name,
            'status': conversation.status, 'expires_at': session.expires_at, 'history_truncated': has_more,
            'message_page': {'limit': limit, 'before': before, 'has_more': has_more,
                             'next_before': messages[0].id if has_more else None},
            'order_access': [{'order_id': access.order_id, 'expires_at': min(access.expires_at, session.expires_at)}
                             for access in active_order_access(db, conversation.id)] if conversation.status != 'closed' else [],
            'messages': [{'id': m.id, 'sender_type': m.sender_type, 'content': m.content, 'created_at': m.created_at,
                          'client_message_id': m.external_message_id if m.sender_type == 'customer' else None,
                          'citations': [{k: c.get(k) for k in ('source', 'page', 'location', 'quote')} for c in (m.citations or [])]}
                         for m in messages]}


@router.post('/session', status_code=201)
def start_session(payload: StartSession, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(request, 'session', 6)
    session = find_session(request, db)
    if session:
        return snapshot(db, session)
    token = secrets.token_urlsafe(32)
    customer = Customer(id=str(uuid4()), display_name=payload.display_name)
    db.add(customer)
    db.flush()
    conversation = Conversation(id=str(uuid4()), customer_id=customer.id, channel='website')
    db.add(conversation)
    db.flush()
    session = WidgetSession(token_hash=token_hash(token), conversation_id=conversation.id,
                            expires_at=int(time.time()) + SESSION_SECONDS)
    db.execute(delete(WidgetSession).where(WidgetSession.expires_at <= int(time.time())))
    db.add(session)
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=os.getenv('APP_ENV', 'development') != 'development', samesite='strict', path=COOKIE_PATH)
    return snapshot(db, session)


@router.get('/session')
def get_session(session: WidgetSession = Depends(require_session), db: Session = Depends(get_db),
                before: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
                limit: Annotated[int, Query(ge=1, le=100)] = 50):
    return snapshot(db, session, before=before, limit=limit)


@router.post('/order-access')
def redeem_order_access(payload: RedeemOrderAccess, request: Request,
                        session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    rate_limit(request, 'order-access', 6)
    conversation_id = session.conversation_id
    db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
    # Re-read under the write lock: the session may have ended while this request waited.
    db.expire_all()
    session = require_session(request, db)
    conversation = db.get(Conversation, conversation_id)
    if conversation.status == 'closed':
        raise HTTPException(409, 'Hội thoại đã đóng. Vui lòng bắt đầu phiên mới.')
    owner = select(Order.customer_id).where(Order.id == payload.order_id).scalar_subquery()
    result = db.execute(update(OrderAccess).where(
        OrderAccess.order_id == payload.order_id,
        OrderAccess.token_hash == token_hash(payload.code.get_secret_value()),
        OrderAccess.expires_at > int(time.time()), OrderAccess.customer_id == owner,
        or_(OrderAccess.conversation_id.is_(None), OrderAccess.conversation_id == conversation_id)
    ).values(conversation_id=conversation_id).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(400, 'Mã không hợp lệ, đã hết hạn hoặc đã được dùng ở phiên khác.')
    db.commit()
    return snapshot(db, session)


@router.get('/orders/{order_id}')
def get_authorized_order(order_id: str, request: Request,
                         session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    rate_limit(request, 'order-read', 30)
    if len(order_id) > 64 or not active_order_access(db, session.conversation_id).filter(
            OrderAccess.order_id == order_id).first():
        raise HTTPException(404, 'Không tìm thấy đơn hoặc quyền truy cập đã hết hạn.')
    order = db.get(Order, order_id)
    return {'order_id': order.id, 'status': order.status, 'tracking_code': order.tracking_code}

@router.post('/messages')
def send_message(payload: WidgetMessage, request: Request, session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    rate_limit(request, 'message', 10)
    conversation = db.get(Conversation, session.conversation_id)
    needs_slot = conversation.status == 'open' and not classify_message(payload.content)[1] and simple_reply(payload.content) is None
    acquired = _answer_slot.acquire(blocking=False) if needs_slot else False
    if needs_slot and not acquired:
        raise HTTPException(429, 'AI đang bận. Tin nhắn chưa được gửi; thử lại hoặc chọn Gặp nhân viên.', headers={'Retry-After': '15'})
    try:
        result = process_message(db, conversation, payload.content, str(payload.client_message_id))
        # Public clients receive their messages and excerpts, never retrieval results or staff ticket notes.
        db.expunge_all()
        return {**snapshot(db, require_session(request, db)), 'message_id': result['message_id'], 'duplicate': result.get('duplicate', False),
                'ai_error': result.get('ai_error')}
    finally:
        if acquired:
            _answer_slot.release()


@router.post('/handoff')
def request_handoff(payload: WidgetAction, request: Request, session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    rate_limit(request, 'handoff', 6)
    process_message(db, db.get(Conversation, session.conversation_id), 'Tôi cần gặp nhân viên.', str(payload.client_message_id))
    db.expunge_all()
    return snapshot(db, require_session(request, db))


@router.delete('/session')
def end_session(response: Response, session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    db.execute(update(Conversation).where(Conversation.id == session.conversation_id).values(status='closed'))
    complete_tickets(db, session.conversation_id, 'closed')
    if isinstance(session, CustomerSession):
        account = db.get(CustomerAccount, session.account_id)
        conversation = Conversation(id=str(uuid4()), customer_id=account.customer_id, channel='website')
        db.add(conversation)
        db.flush()
        session.conversation_id = conversation.id
        db.commit()
        return snapshot(db, session)
    db.delete(session)
    db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return {'status': 'ended'}
