"""Self-managed customer accounts with verified-email recovery."""
import os
import re
import secrets
import time
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.widget import (COOKIE, COOKIE_PATH, SESSION_SECONDS, check_csrf, find_session,
                            no_cache, rate_limit, require_session, snapshot)
from app.core.auth import hash_password, token_hash, verify_password
from app.db.session import get_db
from app.models.support import Conversation, Customer, CustomerAccount, CustomerEmailToken, CustomerSession
from app.services.customer_email import deliver_challenge, mail_settings

router = APIRouter(prefix=COOKIE_PATH + '/account', tags=['customer accounts'],
                   dependencies=[Depends(check_csrf), Depends(no_cache)])
_dummy_hash = hash_password(secrets.token_urlsafe(32))

class EmailAddress(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().lower()
        # ponytail: ASCII email only; use email-validator before supporting internationalized addresses.
        local, separator, domain = value.partition('@')
        if (not separator or len(local) > 64 or not re.fullmatch(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*", local)
                or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', domain)):
            raise ValueError('Email không hợp lệ.')
        return value

class Credentials(EmailAddress):
    password: SecretStr

class Register(Credentials):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator('display_name')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Vui lòng nhập tên hiển thị.')
        return value.strip()

class ChangePassword(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current_password: SecretStr
    new_password: SecretStr

def password_text(secret, minimum=1):
    value = secret.get_secret_value()
    if not minimum <= len(value) <= 128 or not value.strip():
        raise HTTPException(422, f'Mật khẩu phải có {minimum}–128 ký tự và không chỉ gồm khoảng trắng.')
    return value

def require_account(session=Depends(require_session)):
    if not isinstance(session, CustomerSession):
        raise HTTPException(401, 'Vui lòng đăng nhập tài khoản khách hàng.')
    return session

def issue_session(db, request, response, account):
    previous = find_session(request, db)
    if previous:
        db.delete(previous)
    now = int(time.time())
    db.execute(delete(CustomerSession).where(CustomerSession.expires_at <= now))
    conversation = db.query(Conversation).filter(
        Conversation.customer_id == account.customer_id, Conversation.channel == 'website',
        Conversation.status != 'closed').order_by(Conversation.created_at.desc(), Conversation.id.desc()).first()
    if conversation is None:
        conversation = Conversation(id=str(uuid4()), customer_id=account.customer_id, channel='website')
        db.add(conversation)
        db.flush()
    token = secrets.token_urlsafe(32)
    session = CustomerSession(token_hash=token_hash(token), account_id=account.id,
                              conversation_id=conversation.id, expires_at=now + SESSION_SECONDS)
    db.add(session)
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True, samesite='strict',
                        secure=os.getenv('APP_ENV', 'development').lower() != 'development', path=COOKIE_PATH)
    return snapshot(db, session)

@router.post('/register', status_code=201)
def register(payload: Register, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(request, 'customer-register', 6)
    password = password_text(payload.password, 15)
    customer = Customer(id=str(uuid4()), display_name=payload.display_name)
    account = CustomerAccount(id=str(uuid4()), customer_id=customer.id, email=payload.email,
                              password_hash=hash_password(password))
    db.add(customer)
    db.flush()
    db.add(account)
    try:
        db.flush()
        return issue_session(db, request, response, account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Không thể đăng ký bằng email này. Nếu đã có tài khoản, hãy đăng nhập.')

@router.post('/login')
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(request, 'customer-login', 10)
    password = password_text(payload.password)
    account = db.query(CustomerAccount).filter_by(email=payload.email).first()
    valid = verify_password(password, account.password_hash if account else _dummy_hash)
    if not account or not valid:
        raise HTTPException(401, 'Email hoặc mật khẩu không đúng.')
    # Serialize session issuance with password changes; a stale password cannot mint a new session.
    current = db.execute(update(CustomerAccount).where(
        CustomerAccount.id == account.id, CustomerAccount.password_hash == account.password_hash
    ).values(password_hash=CustomerAccount.password_hash))
    if current.rowcount != 1:
        db.rollback()
        raise HTTPException(401, 'Email hoặc mật khẩu không đúng.')
    return issue_session(db, request, response, account)

@router.post('/logout')
def logout(response: Response, session=Depends(require_account), db: Session = Depends(get_db)):
    db.delete(session)
    db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return {'status': 'logged_out'}

@router.post('/password')
def change_password(payload: ChangePassword, request: Request, response: Response,
                    session=Depends(require_account), db: Session = Depends(get_db)):
    rate_limit(request, 'customer-password', 5)
    current = password_text(payload.current_password)
    new = password_text(payload.new_password, 15)
    account = db.get(CustomerAccount, session.account_id)
    if not verify_password(current, account.password_hash):
        raise HTTPException(400, 'Mật khẩu hiện tại không đúng.')
    if current == new:
        raise HTTPException(400, 'Mật khẩu mới phải khác mật khẩu hiện tại.')
    updated = db.execute(update(CustomerAccount).where(
        CustomerAccount.id == account.id, CustomerAccount.password_hash == account.password_hash
    ).values(password_hash=hash_password(new)))
    if updated.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Mật khẩu đã thay đổi. Vui lòng đăng nhập lại.')
    db.execute(update(CustomerEmailToken).where(CustomerEmailToken.account_id == account.id).values(used=True))
    db.execute(delete(CustomerSession).where(CustomerSession.account_id == account.id))
    db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return {'status': 'password_changed'}

@router.get('/conversations')
def conversations(session=Depends(require_account), db: Session = Depends(get_db),
                  offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=50)] = 20):
    account = db.get(CustomerAccount, session.account_id)
    query = db.query(Conversation).filter_by(customer_id=account.customer_id, channel='website')
    total = query.count()
    rows = query.order_by(Conversation.created_at.desc(), Conversation.id.desc()).offset(offset).limit(limit).all()
    return {'total': total, 'has_more': offset + len(rows) < total,
            'items': [{'id': row.id, 'created_at': row.created_at, 'status': row.status} for row in rows]}

@router.get('/conversations/{conversation_id}')
def conversation_history(conversation_id: str, session=Depends(require_account), db: Session = Depends(get_db),
                         before: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
                         limit: Annotated[int, Query(ge=1, le=100)] = 50):
    account = db.get(CustomerAccount, session.account_id)
    conversation = db.query(Conversation).filter_by(id=conversation_id, customer_id=account.customer_id, channel='website').first()
    if conversation is None:
        raise HTTPException(404, 'Không tìm thấy hội thoại.')
    context = CustomerSession(conversation_id=conversation.id, account_id=account.id, expires_at=session.expires_at)
    return snapshot(db, context, before, limit)


class EmailChallenge(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: SecretStr

class VerifyEmail(EmailChallenge):
    password: SecretStr

class ResetPassword(EmailChallenge):
    new_password: SecretStr


def configured_mail():
    try:
        return mail_settings()
    except ValueError:
        raise HTTPException(503, 'Gửi email chưa sẵn sàng. Vui lòng liên hệ cửa hàng hoặc thử lại sau.') from None


def challenge_account(db, secret, purpose):
    token = secret.get_secret_value()
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
        raise HTTPException(400, 'Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng.')
    challenge = db.get(CustomerEmailToken, token_hash(token))
    if not challenge or challenge.used or challenge.purpose != purpose or challenge.expires_at <= int(time.time()):
        raise HTTPException(400, 'Liên kết không hợp lệ, đã hết hạn hoặc đã được sử dụng.')
    account = db.get(CustomerAccount, challenge.account_id)
    if account is None:
        raise HTTPException(400, 'Liên kết không còn hiệu lực.')
    return challenge, account


def consume_challenge(db, challenge, account):
    # Serialize against password changes and other challenge consumers, then recheck the one-time token.
    locked = db.execute(update(CustomerAccount).where(CustomerAccount.id == account.id,
                        CustomerAccount.password_hash == account.password_hash).values(email_verified=CustomerAccount.email_verified))
    consumed = db.execute(update(CustomerEmailToken).where(CustomerEmailToken.token_hash == challenge.token_hash,
                          CustomerEmailToken.used.is_(False), CustomerEmailToken.expires_at > int(time.time())).values(used=True))
    if locked.rowcount != 1 or consumed.rowcount != 1:
        db.rollback()
        raise HTTPException(400, 'Liên kết không còn hiệu lực. Vui lòng yêu cầu liên kết mới.')


@router.get('/email-status')
def email_status():
    try:
        mail_settings()
        enabled = True
    except ValueError:
        enabled = False
    return {'configured': enabled}


@router.post('/verification-request', status_code=202)
def request_verification(request: Request, background: BackgroundTasks,
                         session=Depends(require_account), db: Session = Depends(get_db)):
    rate_limit(request, 'customer-verify-request', 3)
    settings = configured_mail()
    background.add_task(deliver_challenge, db.get_bind(), settings, 'verify', account_id=session.account_id)
    return {'message': 'Đã tiếp nhận yêu cầu xác minh. Kiểm tra hộp thư và thư rác; nếu chưa nhận, chờ ít nhất một phút trước khi gửi lại.'}


@router.post('/verify-email')
def verify_email(payload: VerifyEmail, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, 'customer-verify', 10)
    password = password_text(payload.password)
    challenge, account = challenge_account(db, payload.token, 'verify')
    if not verify_password(password, account.password_hash):
        raise HTTPException(400, 'Mật khẩu không đúng. Nhập mật khẩu của tài khoản đã yêu cầu xác minh.')
    consume_challenge(db, challenge, account)
    db.execute(update(CustomerAccount).where(CustomerAccount.id == account.id).values(email_verified=True))
    db.execute(update(CustomerEmailToken).where(CustomerEmailToken.account_id == account.id,
               CustomerEmailToken.purpose == 'verify').values(used=True))
    db.commit()
    return {'message': 'Đã xác minh email. Bạn có thể dùng email này để khôi phục mật khẩu.'}


@router.post('/forgot-password', status_code=202)
def forgot_password(payload: EmailAddress, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    rate_limit(request, 'customer-forgot', 5)
    settings = configured_mail()
    # Same response and foreground work for existing, unverified and unknown email addresses.
    background.add_task(deliver_challenge, db.get_bind(), settings, 'reset', email=payload.email)
    return {'message': 'Nếu email thuộc tài khoản đã xác minh, hệ thống sẽ gửi liên kết đặt lại mật khẩu. Kiểm tra hộp thư và thư rác; chờ ít nhất một phút trước khi gửi lại.'}


@router.post('/reset-password')
def reset_password(payload: ResetPassword, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit(request, 'customer-reset', 10)
    password = password_text(payload.new_password, 15)
    challenge, account = challenge_account(db, payload.token, 'reset')
    if not account.email_verified:
        raise HTTPException(400, 'Email chưa được xác minh.')
    if verify_password(password, account.password_hash):
        raise HTTPException(400, 'Mật khẩu mới phải khác mật khẩu hiện tại.')
    encoded = hash_password(password)
    consume_challenge(db, challenge, account)
    db.execute(update(CustomerAccount).where(CustomerAccount.id == account.id).values(password_hash=encoded))
    db.execute(update(CustomerEmailToken).where(CustomerEmailToken.account_id == account.id).values(used=True))
    current = find_session(request, db)
    if isinstance(current, CustomerSession) and current.account_id == account.id:
        response.delete_cookie(COOKIE, path=COOKIE_PATH)
    db.execute(delete(CustomerSession).where(CustomerSession.account_id == account.id))
    db.commit()
    return {'message': 'Đã đặt lại mật khẩu và đăng xuất mọi thiết bị. Vui lòng đăng nhập bằng mật khẩu mới.'}
