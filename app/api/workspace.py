"""Staff workspace: real operational totals and bounded management lists."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import hash_password, public_user, require_admin, require_staff, verify_password
from app.db.session import get_db
from app.models.support import AuthSession, Conversation, Customer, KnowledgeDocument, Message, Order, Ticket, User
from app.services.sla_service import RESPONSE_MINUTES, ticket_slas, utc

router = APIRouter(prefix='/api/v1/workspace', tags=['workspace'], dependencies=[Depends(require_staff)])
OrderStatus = Literal['processing', 'paid', 'shipping', 'shipped', 'delivered', 'cancelled']


class CustomerFields(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    display_name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=255, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

    @field_validator('email', mode='before')
    @classmethod
    def empty_email(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class CustomerEdit(CustomerFields):
    expected: CustomerFields


class OrderFields(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    status: OrderStatus = 'processing'
    tracking_code: str | None = Field(default=None, max_length=100)

    @field_validator('tracking_code', mode='before')
    @classmethod
    def empty_tracking(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class OrderCreate(OrderFields):
    id: str = Field(min_length=6, max_length=64, pattern=r'^(?:DH|ORD)[-_]?[A-Z0-9]{4,}$')
    customer_id: str = Field(min_length=1, max_length=64)


class OrderEdit(OrderFields):
    expected: OrderFields


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


def customer_data(customer):
    return {'id': customer.id, 'display_name': customer.display_name, 'email': customer.email}


def order_data(order, name):
    return {'id': order.id, 'customer_id': order.customer_id, 'customer_name': name,
            'status': order.status, 'tracking_code': order.tracking_code}


@router.get('/customers')
def customers(q: str = Query('', max_length=160), offset: int = Query(0, ge=0),
              limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Customer)
    if q.strip():
        query = query.filter(or_(*(column.contains(q.strip(), autoescape=True)
                                  for column in (Customer.id, Customer.display_name, Customer.email))))
    total = query.count()
    conv_count = select(func.count(Conversation.id)).where(Conversation.customer_id == Customer.id).correlate(Customer).scalar_subquery()
    order_count = select(func.count(Order.id)).where(Order.customer_id == Customer.id).correlate(Customer).scalar_subquery()
    rows = query.add_columns(conv_count, order_count).order_by(Customer.display_name, Customer.id).offset(offset).limit(limit).all()
    return {'total': total, 'items': [customer_data(c) | {'conversation_count': cc, 'order_count': oc} for c, cc, oc in rows]}


@router.get('/customers/{customer_id}')
def customer_detail(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(404, 'Không tìm thấy khách hàng.')
    chats = db.query(Conversation).filter_by(customer_id=customer_id).order_by(Conversation.created_at.desc(), Conversation.id).limit(20).all()
    orders_query = db.query(Order).filter_by(customer_id=customer_id)
    return customer_data(customer) | {
        'conversations': [{'id': c.id, 'channel': c.channel, 'status': c.status, 'created_at': c.created_at} for c in chats],
        'conversation_count': db.query(Conversation).filter_by(customer_id=customer_id).count(),
        'orders': [order_data(o, customer.display_name) for o in orders_query.order_by(Order.id).limit(20)],
        'order_count': orders_query.count()}


@router.post('/customers', status_code=201, dependencies=[Depends(require_admin)])
def add_customer(payload: CustomerFields, db: Session = Depends(get_db)):
    customer = Customer(id=str(uuid4()), **payload.model_dump())
    db.add(customer)
    db.commit()
    return customer_data(customer)


@router.patch('/customers/{customer_id}', dependencies=[Depends(require_admin)])
def edit_customer(customer_id: str, payload: CustomerEdit, db: Session = Depends(get_db)):
    result = db.execute(update(Customer).where(Customer.id == customer_id,
        Customer.display_name == payload.expected.display_name, Customer.email == payload.expected.email
    ).values(**payload.model_dump(exclude={'expected'})))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Khách hàng đã thay đổi hoặc không còn tồn tại. Tải lại trước khi sửa.')
    db.commit()
    return customer_data(db.get(Customer, customer_id))


@router.get('/orders')
def orders(q: str = Query('', max_length=160), status: OrderStatus | None = None,
           customer_id: str | None = Query(None, max_length=64), offset: int = Query(0, ge=0),
           limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Order, Customer.display_name).join(Customer, Order.customer_id == Customer.id)
    if q.strip():
        query = query.filter(or_(*(column.contains(q.strip(), autoescape=True)
                                  for column in (Order.id, Customer.display_name, Order.tracking_code))))
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    return {'total': query.count(), 'items': [order_data(o, name) for o, name in query.order_by(Order.id).offset(offset).limit(limit)]}


@router.post('/orders', status_code=201, dependencies=[Depends(require_admin)])
def add_order(payload: OrderCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(404, 'Không tìm thấy khách hàng.')
    order = Order(**payload.model_dump())
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Mã đơn đã tồn tại.')
    return order_data(order, customer.display_name)


@router.patch('/orders/{order_id}', dependencies=[Depends(require_admin)])
def edit_order(order_id: str, payload: OrderEdit, db: Session = Depends(get_db)):
    result = db.execute(update(Order).where(Order.id == order_id, Order.status == payload.expected.status,
        Order.tracking_code == payload.expected.tracking_code).values(**payload.model_dump(exclude={'expected'})))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Đơn hàng đã thay đổi hoặc không còn tồn tại. Tải lại trước khi sửa.')
    db.commit()
    order = db.get(Order, order_id)
    return order_data(order, db.get(Customer, order.customer_id).display_name)


@router.get('/summary')
def summary(days: int = Query(7), db: Session = Depends(get_db)):
    if days not in (7, 30, 90):
        raise HTTPException(422, 'Khoảng thống kê phải là 7, 30 hoặc 90 ngày.')
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    chats = db.query(Conversation).filter(Conversation.created_at >= start, Conversation.created_at <= now).all()
    tickets = db.query(Ticket).filter(Ticket.created_at >= start, Ticket.created_at <= now).all()
    # ponytail: demo-sized ticket cohorts; use SQL aggregation before large deployments.
    slas = ticket_slas(db, list({t.conversation_id for t in tickets}), now)
    sla_counts = Counter(slas[t.id]['status'] for t in tickets)
    response_minutes = [(datetime.fromisoformat(slas[t.id]['responded_at']) - utc(t.created_at)).total_seconds() / 60
                        for t in tickets if slas[t.id]['responded_at']]
    daily = Counter(utc(c.created_at).date().isoformat() for c in chats)
    grouped = lambda model, field: dict(db.query(field, func.count()).select_from(model).group_by(field).all())
    totals = {name: db.query(model).count() for name, model in [('customers', Customer), ('orders', Order), ('conversations', Conversation), ('documents', KnowledgeDocument)]}
    return {'days': days, 'start': start, 'end': now, 'timezone': 'UTC', 'totals': totals,
            'conversation_statuses': grouped(Conversation, Conversation.status),
            'order_statuses': grouped(Order, Order.status),
            'period': {'conversations': len(chats), 'tickets': len(tickets),
                       'messages': db.query(Message).filter(Message.created_at >= start, Message.created_at <= now).count(),
                       'channels': dict(Counter(c.channel for c in chats)),
                       'daily': [{'date': (start + timedelta(days=i)).date().isoformat(),
                                  'count': daily[(start + timedelta(days=i)).date().isoformat()]} for i in range(days)],
                       'sla': {key: sla_counts[key] for key in ('met', 'breached', 'on_track', 'overdue', 'cancelled')},
                       'responded_tickets': len(response_minutes),
                       'sla_met_percent': round(100 * sla_counts['met'] / len(response_minutes), 1) if response_minutes else None,
                       'mean_response_minutes': round(sum(response_minutes) / len(response_minutes), 1) if response_minutes else None}}


@router.get('/settings')
def settings(user: User = Depends(require_staff)):
    return {'user': public_user(user), 'sla_minutes': RESPONSE_MINUTES, 'sla_schedule': '24/7',
            'channels': [{'name': 'Website Widget', 'status': 'available'}, {'name': 'Kênh thứ hai', 'status': 'not_connected'}]}


@router.get('/users', dependencies=[Depends(require_admin)])
def users(offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(User)
    return {'total': query.count(), 'items': [public_user(u) | {'active': u.active} for u in query.order_by(User.username).offset(offset).limit(limit)]}


@router.post('/password')
def change_password(payload: PasswordChange, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, 'Mật khẩu hiện tại không đúng.')
    if payload.current_password == payload.new_password:
        raise HTTPException(422, 'Mật khẩu mới phải khác mật khẩu hiện tại.')
    result = db.execute(update(User).where(User.id == user.id, User.password_hash == user.password_hash)
                        .values(password_hash=hash_password(payload.new_password)))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Mật khẩu đã thay đổi. Đăng nhập lại để tiếp tục.')
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.commit()
    return {'message': 'Đã đổi mật khẩu và đăng xuất tất cả phiên. Hãy đăng nhập lại.'}
