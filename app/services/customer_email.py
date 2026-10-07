"""SMTP mail and bounded, single-use customer email challenges."""
import logging
import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from urllib.parse import urlsplit

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core.auth import token_hash
from app.models.support import CustomerAccount, CustomerEmailToken

logger = logging.getLogger(__name__)


def mail_settings():
    host = os.getenv('SMTP_HOST', '').strip()
    sender = os.getenv('SMTP_FROM', '').strip()
    origin = os.getenv('CUSTOMER_PUBLIC_URL', '').rstrip('/')
    parsed = urlsplit(origin)
    tls = os.getenv('SMTP_SECURITY', 'starttls').lower()
    user, password = os.getenv('SMTP_USERNAME', ''), os.getenv('SMTP_PASSWORD', '')
    try:
        port = int(os.getenv('SMTP_PORT', '587'))
    except ValueError:
        raise ValueError('Invalid mail configuration') from None
    local = parsed.hostname in {'localhost', '127.0.0.1', '[::1]', '::1'}
    if (not host or not sender or '@' not in sender or any(c in host + sender + user for c in '\r\n')
            or tls not in {'starttls', 'ssl'} or not 1 <= port <= 65535 or bool(user) != bool(password)
            or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {'', '/'} or any(c.isspace() for c in origin)
            or (parsed.scheme != 'https' and not (parsed.scheme == 'http' and local and os.getenv('APP_ENV', 'development') == 'development'))):
        raise ValueError('Invalid mail configuration')
    return dict(host=host, port=port, sender=sender, origin=origin, security=tls, user=user, password=password)


def send_link(settings, email, purpose, token):
    action = 'Xác minh email' if purpose == 'verify' else 'Đặt lại mật khẩu'
    minutes = 60 if purpose == 'verify' else 15
    url = settings['origin'] + '/chat#' + purpose + '=' + token
    message = EmailMessage()
    message['Subject'] = 'AI Support - ' + action
    message['From'], message['To'] = settings['sender'], email
    extra = ('Bạn cần nhập mật khẩu hiện tại để xác minh. Nếu không tự tạo tài khoản, hãy bỏ qua thư này.'
             if purpose == 'verify' else 'Sau khi đặt lại mật khẩu, mọi phiên đăng nhập cũ sẽ hết hiệu lực.')
    message.set_content(f'{action} cho tài khoản AI Support.\n\n{url}\n\nLiên kết có hạn {minutes} phút, dùng một lần. {extra}\n\nKhông chia sẻ liên kết này. Nếu không yêu cầu, hãy bỏ qua thư.\n')
    context = ssl.create_default_context()
    factory = smtplib.SMTP_SSL if settings['security'] == 'ssl' else smtplib.SMTP
    options = {'context': context} if settings['security'] == 'ssl' else {}
    with factory(settings['host'], settings['port'], timeout=10, **options) as smtp:
        if settings['security'] == 'starttls':
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
        if settings['user']:
            smtp.login(settings['user'], settings['password'])
        if smtp.send_message(message):
            raise smtplib.SMTPException('Mail not accepted')


def deliver_challenge(engine, settings, purpose, *, account_id=None, email=None):
    # ponytail: in-process background delivery; use a durable outbox before multi-worker or guaranteed mail delivery.
    digest = None
    try:
        with Session(engine) as db:
            query = db.query(CustomerAccount)
            account = (query.filter_by(id=account_id) if account_id else query.filter_by(email=email)).first()
            if not account:
                return
            db.execute(update(CustomerAccount).where(CustomerAccount.id == account.id).values(email_verified=CustomerAccount.email_verified))
            db.refresh(account)
            if (purpose == 'reset') != account.email_verified:
                return
            now = int(time.time())
            recent = db.query(CustomerEmailToken).filter(CustomerEmailToken.account_id == account.id,
                         CustomerEmailToken.purpose == purpose, CustomerEmailToken.created_at > now - 3600)
            if recent.count() >= 3 or recent.filter(CustomerEmailToken.created_at > now - 60).first():
                return
            db.execute(delete(CustomerEmailToken).where(CustomerEmailToken.created_at < now - 86400))
            token = secrets.token_urlsafe(32)
            digest = token_hash(token)
            db.add(CustomerEmailToken(token_hash=digest, account_id=account.id, purpose=purpose,
                   created_at=now, expires_at=now + (3600 if purpose == 'verify' else 900)))
            recipient = account.email
            db.commit()
        send_link(settings, recipient, purpose, token)
    except Exception:
        # Never log a recipient, token, SMTP credentials or exception containing message content.
        logger.warning('Customer email delivery failed; check SMTP configuration and availability.')
        if digest:
            try:
                with Session(engine) as db:
                    db.execute(update(CustomerEmailToken).where(CustomerEmailToken.token_hash == digest).values(used=True))
                    db.commit()
            except Exception:
                logger.warning('Could not revoke failed customer email challenge.')
