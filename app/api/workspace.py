"""Staff workspace: real operational totals and bounded management lists."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import hash_password, public_user, require_admin, require_staff, token_hash, verify_password
from app.db.session import get_db
from app.models.support import (PRODUCT_CATEGORIES, AuthSession, Conversation, Customer, CustomerAccount, KnowledgeDocument, Message,
                                Order, OrderAccess, Product, Ticket, User, now_utc)
from app.services.products import product_data
from app.services.sla_service import RESPONSE_MINUTES, ticket_slas, utc
from app.services import insights
from app.telegram import telegram_status

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


class OrderSnapshot(BaseModel):
    """The values the editor last saw; compared as stored, so older free-form tracking codes still match."""
    model_config = ConfigDict(extra='forbid')
    status: OrderStatus
    tracking_code: str | None = Field(default=None, max_length=100)


class OrderFields(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    status: OrderStatus = 'processing'
    # Typed by staff: normalized to upper case without spaces, then letters, digits and inner dashes only.
    tracking_code: str | None = Field(default=None, pattern=r'^[A-Z0-9][A-Z0-9-]{6,28}[A-Z0-9]$')

    @field_validator('tracking_code', mode='before')
    @classmethod
    def normalize_tracking(cls, value):
        if not isinstance(value, str):
            return value
        value = ''.join(value.split()).upper()
        return value or None


class OrderCreate(OrderFields):
    # Omitted by the staff form: the server generates one. Seeds and integrations may still pass a known ID.
    id: str | None = Field(default=None, min_length=6, max_length=64,
                           pattern=r'^(?:DH(?:[-_]?)[A-Z0-9]{4,}|ORD(?:[-_]?[A-Z0-9]{4,})(?:[-_][A-Z0-9]+)*)$')
    customer_id: str = Field(min_length=1, max_length=64)


class OrderEdit(OrderFields):
    expected: OrderSnapshot


ORDER_ID_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # no 0/O, 1/I/L: customers read these out or retype them


def new_order_id(db):
    """DH + order date (Vietnam time, yymmdd) + 4 random characters, e.g. DH2611187KQ4."""
    day = datetime.now(timezone(timedelta(hours=7))).strftime('%y%m%d')
    for _ in range(20):
        candidate = 'DH' + day + ''.join(secrets.choice(ORDER_ID_ALPHABET) for _ in range(4))
        if db.get(Order, candidate) is None:
            return candidate
    raise HTTPException(503, 'Không tạo được mã đơn mới. Vui lòng thử lại.')


ProductCategory = Literal[PRODUCT_CATEGORIES]


class ProductFields(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=160)
    category: ProductCategory
    price: int | None = Field(default=None, ge=0, le=10_000_000_000)
    stock: int = Field(default=0, ge=0, le=1_000_000)
    active: bool = True
    url: str | None = Field(default=None, max_length=500, pattern=r'^https://[^\s]+$')
    description: str | None = Field(default=None, max_length=500)

    @field_validator('url', 'description', mode='before')
    @classmethod
    def empty_text(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


def customer_data(customer, account_email=None):
    return {'id': customer.id, 'display_name': customer.display_name,
            'email': account_email or customer.email}


def order_data(order, name, product_name=None):
    return {'id': order.id, 'customer_id': order.customer_id, 'customer_name': name,
            'status': order.status, 'tracking_code': order.tracking_code, 'product_id': order.product_id,
            'product_name': product_name, 'quantity': order.quantity, 'unit_price': order.unit_price,
            'amount': order.amount, 'pay_amount': order.pay_amount, 'created_at': order.created_at}


@router.get('/customers')
def customers(q: str = Query('', max_length=160), offset: int = Query(0, ge=0),
              limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Customer, CustomerAccount.email).outerjoin(
        CustomerAccount, CustomerAccount.customer_id == Customer.id)
    if q.strip():
        query = query.filter(or_(Customer.id.contains(q.strip(), autoescape=True),
                                 Customer.display_name.contains(q.strip(), autoescape=True),
                                 Customer.email.contains(q.strip(), autoescape=True),
                                 CustomerAccount.email.contains(q.strip(), autoescape=True)))
    total = query.count()
    conv_count = select(func.count(Conversation.id)).where(Conversation.customer_id == Customer.id).correlate(Customer).scalar_subquery()
    order_count = select(func.count(Order.id)).where(Order.customer_id == Customer.id).correlate(Customer).scalar_subquery()
    rows = query.add_columns(conv_count, order_count).order_by(Customer.display_name, Customer.id).offset(offset).limit(limit).all()
    return {'total': total, 'items': [customer_data(c, account_email) | {'conversation_count': cc, 'order_count': oc}
                                     for c, account_email, cc, oc in rows]}


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


@router.get('/products')
def products(q: str = Query('', max_length=160), category: str | None = Query(None, max_length=16),
             offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Product)
    if q.strip():
        query = query.filter(Product.name.contains(q.strip(), autoescape=True))
    if category:
        if category not in PRODUCT_CATEGORIES:
            raise HTTPException(422, 'Nhóm sản phẩm không hợp lệ.')
        query = query.filter(Product.category == category)
    return {'total': query.count(), 'categories': list(PRODUCT_CATEGORIES),
            'items': [product_data(p) for p in query.order_by(Product.category, Product.name).offset(offset).limit(limit)]}


@router.post('/products', status_code=201, dependencies=[Depends(require_admin)])
def add_product(payload: ProductFields, db: Session = Depends(get_db)):
    product = Product(id=str(uuid4()), **payload.model_dump(), in_stock=payload.stock > 0)
    db.add(product)
    db.commit()
    return product_data(product)


@router.patch('/products/{product_id}', dependencies=[Depends(require_admin)])
def edit_product(product_id: str, payload: ProductFields, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, 'Không tìm thấy sản phẩm.')
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    product.in_stock = product.stock > 0
    product.updated_at = now_utc()
    db.commit()
    return product_data(product)


class PaymentSettings(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    enabled: bool = False
    bank_bin: str = Field(default='', max_length=6)
    account_no: str = Field(default='', max_length=19, pattern=r'^[A-Za-z0-9]*$')
    account_name: str = Field(default='', max_length=50)
    divisor: int = Field(default=1000, ge=1, le=1_000_000)

    @field_validator('account_name')
    @classmethod
    def plain_upper(cls, value):
        # Bank apps show the holder without diacritics in capitals, e.g. NGUYEN VAN KHANH.
        import unicodedata
        value = unicodedata.normalize('NFD', value.replace('đ', 'd').replace('Đ', 'D'))
        value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn').upper()
        if any(not (ch.isalpha() and ch.isascii() or ch == ' ') for ch in value):
            raise ValueError('Tên chủ tài khoản chỉ gồm chữ và khoảng trắng')
        return ' '.join(value.split())


@router.get('/payment')
def payment_settings(db: Session = Depends(get_db)):
    from app.services import payment
    config = payment.settings(db)
    sample = payment.qr_url(config, payment.pay_amount(100_000, config), 'DEMO') if payment.ready(config) else None
    return {**config, 'ready': payment.ready(config), 'banks': payment.BANKS, 'sample_qr_url': sample}


@router.put('/payment', dependencies=[Depends(require_admin)])
def save_payment_settings(payload: PaymentSettings, db: Session = Depends(get_db)):
    from app.services import payment
    value = payload.model_dump()
    if value['enabled'] and (value['bank_bin'] not in payment.BANKS or not value['account_no'] or not value['account_name']):
        raise HTTPException(422, 'Bật thanh toán cần chọn ngân hàng, nhập số tài khoản và tên chủ tài khoản.')
    if value['bank_bin'] and value['bank_bin'] not in payment.BANKS:
        raise HTTPException(422, 'Ngân hàng không hợp lệ.')
    payment.save(db, value)
    db.commit()
    return payment_settings(db)


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
    page = query.order_by(Order.id).offset(offset).limit(limit).all()
    names = {p.id: p.name for p in db.query(Product).filter(Product.id.in_([o.product_id for o, _ in page if o.product_id]))}
    return {'total': query.count(), 'items': [order_data(o, name, names.get(o.product_id)) for o, name in page]}


@router.post('/orders', status_code=201, dependencies=[Depends(require_admin)])
def add_order(payload: OrderCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(404, 'Không tìm thấy khách hàng.')
    generated = payload.id is None
    order = Order(**payload.model_dump(exclude={'id'}), id=payload.id or new_order_id(db))
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A generated ID can only collide with an order created in the same instant; ask for a retry.
        raise HTTPException(409, 'Mã đơn vừa sinh bị trùng. Vui lòng bấm tạo lại.' if generated else 'Mã đơn đã tồn tại.')
    return order_data(order, customer.display_name)


@router.patch('/orders/{order_id}', dependencies=[Depends(require_admin)])
def edit_order(order_id: str, payload: OrderEdit, db: Session = Depends(get_db)):
    # Cancelling a Telegram shop order puts its units back in stock (once, in the same transaction).
    before = db.get(Order, order_id)
    restock = (before is not None and before.product_id and before.quantity and payload.status == 'cancelled'
               and payload.expected.status != 'cancelled')
    result = db.execute(update(Order).where(Order.id == order_id, Order.status == payload.expected.status,
        Order.tracking_code == payload.expected.tracking_code).values(**payload.model_dump(exclude={'expected'})))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Đơn hàng đã thay đổi hoặc không còn tồn tại. Tải lại trước khi sửa.')
    if restock:
        db.execute(update(Product).where(Product.id == before.product_id).values(stock=Product.stock + before.quantity, in_stock=True))
    db.commit()
    order = db.get(Order, order_id)
    product = db.get(Product, order.product_id) if order.product_id else None
    return order_data(order, db.get(Customer, order.customer_id).display_name, product.name if product else None)


@router.post('/orders/{order_id}/access-code', status_code=201)
def issue_order_access(order_id: str, response: Response, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    # Serialize rotation with redemption and tool execution on the current SQLite store.
    result = db.execute(update(Order).where(Order.id == order_id).values(status=Order.status))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(404, 'Không tìm thấy đơn hàng.')
    order = db.get(Order, order_id)
    code = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + 15 * 60
    db.execute(delete(OrderAccess).where(OrderAccess.order_id == order_id))
    db.add(OrderAccess(order_id=order_id, customer_id=order.customer_id, token_hash=token_hash(code),
                       issued_by_id=user.id, expires_at=expires_at))
    db.commit()
    response.headers['Cache-Control'] = 'no-store'
    return {'order_id': order_id, 'code': code, 'expires_at': expires_at}


@router.delete('/orders/{order_id}/access-code', dependencies=[Depends(require_admin)])
def revoke_order_access(order_id: str, db: Session = Depends(get_db)):
    db.execute(delete(OrderAccess).where(OrderAccess.order_id == order_id))
    db.commit()
    return {'status': 'revoked'}


# Reports follow the shop's calendar day. Vietnam has no daylight saving, so a fixed offset is exact.
REPORT_TZ = timezone(timedelta(hours=7), 'Asia/Ho_Chi_Minh')


@router.get('/summary')
def summary(days: int = Query(7), db: Session = Depends(get_db)):
    if days not in (7, 30, 90):
        raise HTTPException(422, 'Khoảng thống kê phải là 7, 30 hoặc 90 ngày.')
    now = datetime.now(timezone.utc)
    first_day = now.astimezone(REPORT_TZ).date() - timedelta(days=days - 1)
    # Timestamps are stored in UTC, so the local midnight is converted back before filtering.
    start = datetime.combine(first_day, datetime.min.time(), REPORT_TZ).astimezone(timezone.utc)
    chats = db.query(Conversation).filter(Conversation.created_at >= start, Conversation.created_at <= now).all()
    tickets = db.query(Ticket).filter(Ticket.created_at >= start, Ticket.created_at <= now).all()
    # ponytail: demo-sized ticket cohorts; use SQL aggregation before large deployments.
    slas = ticket_slas(db, list({t.conversation_id for t in tickets}), now)
    sla_counts = Counter(slas[t.id]['status'] for t in tickets)
    response_minutes = [(datetime.fromisoformat(slas[t.id]['responded_at']) - utc(t.created_at)).total_seconds() / 60
                        for t in tickets if slas[t.id]['responded_at']]
    daily = Counter(utc(c.created_at).astimezone(REPORT_TZ).date().isoformat() for c in chats)
    grouped = lambda model, field: dict(db.query(field, func.count()).select_from(model).group_by(field).all())
    replies = insights.ai_replies(db, start, now)
    totals = {name: db.query(model).count() for name, model in [('customers', Customer), ('orders', Order), ('conversations', Conversation), ('documents', KnowledgeDocument)]}
    return {'days': days, 'start': start, 'end': now, 'timezone': REPORT_TZ.tzname(None), 'totals': totals,
            'conversation_statuses': grouped(Conversation, Conversation.status),
            'order_statuses': grouped(Order, Order.status),
            'period': {'conversations': len(chats), 'tickets': len(tickets),
                       'messages': db.query(Message).filter(Message.created_at >= start, Message.created_at <= now).count(),
                       'channels': dict(Counter(c.channel for c in chats)),
                       'daily': [{'date': (first_day + timedelta(days=i)).isoformat(),
                                  'count': daily[(first_day + timedelta(days=i)).isoformat()]} for i in range(days)],
                       'sla': {key: sla_counts[key] for key in ('met', 'breached', 'on_track', 'overdue', 'cancelled')},
                       'responded_tickets': len(response_minutes),
                       'sla_met_percent': round(100 * sla_counts['met'] / len(response_minutes), 1) if response_minutes else None,
                       'mean_response_minutes': round(sum(response_minutes) / len(response_minutes), 1) if response_minutes else None,
                       'ai_outcomes': insights.outcomes(db, replies, start, now),
                       'unanswered_questions': insights.unanswered_questions(db, replies),
                       'top_documents': insights.top_documents(db, replies)}}


@router.get('/settings')
def settings(user: User = Depends(require_staff)):
    return {'user': public_user(user), 'sla_minutes': RESPONSE_MINUTES, 'sla_schedule': '24/7',
            'channels': [{'name': 'Website Widget', 'status': 'available'}, telegram_status()]}


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
