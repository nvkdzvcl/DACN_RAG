import os
import secrets
import time
from collections import deque
from threading import BoundedSemaphore, Lock
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core.auth import check_csrf, token_hash
from app.db.session import get_db
from app.models.support import Conversation, Customer, Message, Ticket, WidgetSession
from app.services.handoff_service import classify_message
from app.services.message_service import process_message

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
    session = db.get(WidgetSession, token_hash(token)) if token else None
    return session if session and session.expires_at > int(time.time()) else None


def require_session(request: Request, db: Session = Depends(get_db)):
    session = find_session(request, db)
    if session is None:
        raise HTTPException(401, 'Phiên trò chuyện đã hết hạn. Vui lòng bắt đầu phiên mới.')
    return session


def snapshot(db, session):
    conversation = db.get(Conversation, session.conversation_id)
    if conversation is None:
        raise HTTPException(401, 'Phiên trò chuyện không còn hiệu lực.')
    # ponytail: show the latest 200 messages; add cursor pagination for long conversations.
    recent = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at.desc(), Message.id.desc()).limit(201).all()
    return {'conversation_id': conversation.id, 'display_name': conversation.customer.display_name,
            'status': conversation.status, 'expires_at': session.expires_at, 'history_truncated': len(recent) > 200,
            'messages': [{'id': m.id, 'sender_type': m.sender_type, 'content': m.content, 'created_at': m.created_at,
                          'client_message_id': m.external_message_id if m.sender_type == 'customer' else None,
                          'citations': [{k: c.get(k) for k in ('source', 'page', 'location', 'quote')} for c in (m.citations or [])]}
                         for m in reversed(recent[:200])]}


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
def get_session(session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    return snapshot(db, session)


@router.post('/messages')
def send_message(payload: WidgetMessage, request: Request, session: WidgetSession = Depends(require_session), db: Session = Depends(get_db)):
    rate_limit(request, 'message', 10)
    conversation = db.get(Conversation, session.conversation_id)
    needs_slot = conversation.status == 'open' and not classify_message(payload.content)[1]
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
    db.execute(update(Ticket).where(Ticket.conversation_id == session.conversation_id,
                                  Ticket.status.in_(['open', 'assigned'])).values(status='closed'))
    db.delete(session)
    db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return {'status': 'ended'}
