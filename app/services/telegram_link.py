"""Link a Telegram chat to a verified web account, and the bot's /orders, /unlink and /start replies.

The web account page issues a one-time code (10 minutes, stored as a SHA-256 hash). The customer opens
t.me/<bot>?start=link_<code>; Telegram then sends "/start link_<code>" from their own private chat, which
proves they control that Telegram account. The chat's TelegramPeer is pointed at the account's Customer,
so the chat sees the same orders as the website (order_service.lookup_order uses the conversation's customer).
"""
import re
import secrets
import time
from uuid import uuid4

from app.core.auth import token_hash
from app.models.support import Customer, CustomerAccount, CustomerEmailToken, TelegramPeer

LINK_PURPOSE = 'telegram_link'
LINK_SECONDS = 600
CODE = re.compile(r'[A-Za-z0-9_-]{20,58}')

def issue_link_code(db, account):
    """A new code replaces any unused one for this account."""
    db.query(CustomerEmailToken).filter(CustomerEmailToken.account_id == account.id,
                                        CustomerEmailToken.purpose == LINK_PURPOSE).delete(synchronize_session=False)
    code, now = secrets.token_urlsafe(24), int(time.time())
    db.add(CustomerEmailToken(token_hash=token_hash(code), account_id=account.id, purpose=LINK_PURPOSE,
                              created_at=now, expires_at=now + LINK_SECONDS, used=False))
    return code, now + LINK_SECONDS


def linked_account(db, peer):
    return db.query(CustomerAccount).filter(CustomerAccount.customer_id == peer.customer_id).first()


def detach(db, peer):
    """Give the chat a fresh Customer of its own; its next message starts a new conversation."""
    customer = Customer(id=str(uuid4()), display_name='Khách Telegram')
    db.add(customer)
    db.flush()
    peer.customer_id, peer.conversation_id = customer.id, None
    db.flush()


def link_peer(db, peer, code):
    """Returns 'ok', 'invalid' or 'unverified'. Runs in the caller's transaction."""
    if not CODE.fullmatch(code or ''):
        return 'invalid'
    challenge = db.get(CustomerEmailToken, token_hash(code))
    if (challenge is None or challenge.purpose != LINK_PURPOSE or challenge.used
            or challenge.expires_at <= int(time.time())):
        return 'invalid'
    challenge.used = True
    account = db.get(CustomerAccount, challenge.account_id)
    if account is None:
        return 'invalid'
    if not account.email_verified:
        return 'unverified'
    if peer.customer_id == account.customer_id:
        return 'ok'
    # One Telegram chat per customer: a chat linked before is moved back to a Customer of its own.
    previous = db.query(TelegramPeer).filter(TelegramPeer.customer_id == account.customer_id).first()
    if previous is not None:
        detach(db, previous)
    peer.customer_id, peer.conversation_id = account.customer_id, None
    db.flush()
    return 'ok'


def unlink_peer(db, peer):
    if linked_account(db, peer) is None:
        return 'none'
    detach(db, peer)
    return 'ok'


def masked(email):
    name, _, domain = email.partition('@')
    return (name[:2] + '***@' + domain) if domain else '***'
