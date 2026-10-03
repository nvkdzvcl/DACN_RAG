"""Private Telegram chats, durable receipt and explicit delivery outcomes."""
import json
import logging
import os
import re
from http.client import HTTPException as HTTPProtocolError
from threading import Event, Thread
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from sqlalchemy import update

from app.db.session import SessionLocal
from app.models.support import (Conversation, Customer, Message, TelegramCursor,
                                TelegramDelivery, TelegramPeer, TelegramUpdate, now_utc)
from app.services.handoff_service import queue_handoff
from app.services.message_service import process_message

_status = {'name': 'Telegram', 'status': 'not_connected', 'detail': 'Chưa bật kết nối.'}


class TelegramError(Exception):
    def __init__(self, code, uncertain=False):
        super().__init__(code)
        self.uncertain = uncertain


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def telegram_call(token, method, payload):
    # urllib does not log credential-bearing request URLs. Never expose raw transport errors.
    request = Request(f'https://api.telegram.org/bot{token}/{method}',
                      data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=20) as response:
            data = json.loads(response.read(2_000_000))
    except HTTPError as exc:
        raise TelegramError(f'telegram_http_{exc.code}', method == 'sendMessage' and exc.code >= 500) from None
    except (URLError, TimeoutError, OSError, ValueError, HTTPProtocolError):
        raise TelegramError('telegram_network_or_response', method == 'sendMessage') from None
    if not isinstance(data, dict) or data.get('ok') is not True:
        raise TelegramError('telegram_rejected', method == 'sendMessage')
    return data.get('result')


def telegram_status():
    return dict(_status)


def identifier(value):
    return type(value) is int and 0 < value < 2**52


def private_message(item):
    message = item.get('message')
    if not isinstance(message, dict) or not identifier(message.get('message_id')):
        return None
    chat, sender = message.get('chat'), message.get('from')
    if not isinstance(chat, dict) or not isinstance(sender, dict):
        return None
    if (chat.get('type') != 'private' or not identifier(chat.get('id')) or not identifier(sender.get('id'))
            or chat['id'] != sender.get('id') or sender.get('is_bot') is not False):
        return None
    content = message.get('text')
    if not isinstance(content, str) or not content.strip():
        content = 'Khách gửi nội dung không phải văn bản. Tôi cần gặp nhân viên.'
    elif len(content) > 4000:
        content = content[:3800] + '\n[Nội dung dài đã rút gọn. Tôi cần gặp nhân viên.]'
    content = content.strip()
    if content.split()[0].lower() == '/human':
        content = 'Tôi cần gặp nhân viên.'
    name = sender.get('first_name')
    name = name.strip()[:80] if isinstance(name, str) and name.strip() else 'Khách Telegram'
    return str(chat['id']), name, content


def persist_updates(db, bot_id, items):
    if not isinstance(items, list) or len(items) > 100 or any(
        not isinstance(item, dict) or type(item.get('update_id')) is not int or not 0 <= item['update_id'] < 2**52
        for item in items
    ):
        raise TelegramError('telegram_invalid_updates')
    cursor = db.get(TelegramCursor, bot_id)
    if cursor is None:
        cursor = TelegramCursor(bot_id=bot_id, next_update_id=0)
        db.add(cursor)
        db.flush()
    for item in sorted(items, key=lambda item: item['update_id']):
        if item['update_id'] < cursor.next_update_id:
            continue
        parsed = private_message(item)
        key = f"{bot_id}:{item['update_id']}"
        if parsed and db.get(TelegramUpdate, key) is None:
            chat_id, name, content = parsed
            peer_id = f'{bot_id}:{chat_id}'
            peer = db.get(TelegramPeer, peer_id)
            if peer is None:
                customer = Customer(id=str(uuid4()), display_name=name)
                db.add(customer)
                db.flush()
                peer = TelegramPeer(id=peer_id, bot_id=bot_id, chat_id=chat_id, customer_id=customer.id)
                db.add(peer)
                db.flush()
            db.add(TelegramUpdate(id=key, bot_id=bot_id, update_id=item['update_id'], peer_id=peer_id, content=content))
        cursor.next_update_id = item['update_id'] + 1
    # The next getUpdates acknowledges only updates already committed here.
    db.commit()


def process_next(db, bot_id):
    incoming = db.query(TelegramUpdate).filter(TelegramUpdate.bot_id == bot_id,
        TelegramUpdate.state.in_(['pending', 'processing'])).order_by(TelegramUpdate.update_id).first()
    if incoming is None:
        return False
    peer = db.get(TelegramPeer, incoming.peer_id)
    conversation = db.get(Conversation, incoming.conversation_id or peer.conversation_id) if incoming.conversation_id or peer.conversation_id else None
    if incoming.conversation_id and conversation.status == 'closed':
        if db.query(Message).filter_by(conversation_id=conversation.id, external_message_id=incoming.id).first():
            incoming.state = 'done'
            db.commit()
            return True
        incoming.conversation_id, conversation = None, None
    if incoming.conversation_id is None:
        if conversation is None or conversation.status == 'closed':
            conversation = Conversation(id=str(uuid4()), customer_id=peer.customer_id, channel='telegram')
            db.add(conversation)
            db.flush()
            peer.conversation_id = conversation.id
        incoming.conversation_id = conversation.id
    incoming.state = 'processing'
    update_key, content, conversation_id = incoming.id, incoming.content, conversation.id
    db.commit()
    if content.split()[0].lower() == '/start':
        db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
        db.refresh(conversation)
        if conversation.status == 'closed':
            db.get(TelegramUpdate, update_key).state = 'pending'
            db.commit()
            return True
        if not db.query(Message).filter_by(conversation_id=conversation_id, external_message_id=update_key).first():
            message = Message(id=str(uuid4()), conversation_id=conversation_id, sender_type='customer',
                              content=content, external_message_id=update_key)
            db.add(message)
            conversation.last_customer_message_id = message.id
            db.add(Message(id=str(uuid4()), conversation_id=conversation_id, sender_type='system',
                content='Bạn có thể hỏi chính sách cửa hàng bằng văn bản. Gửi /human để gặp nhân viên. Không gửi mật khẩu hoặc mã truy cập đơn vào chat.'))
        result = {}
    else:
        result = process_message(db, conversation, content, update_key)
        db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
        db.refresh(conversation)
        replied = db.query(Message).filter_by(reply_to_id=result.get('message_id'), sender_type='ai').first() if result.get('message_id') else None
        # After a crash, do not regenerate a possibly completed AI turn; hand off safely.
        if ((result.get('ai_error') or result.get('duplicate') and not replied)
                and conversation.status == 'open' and conversation.last_customer_message_id == result.get('message_id')):
            queue_handoff(db, conversation)
    db.get(TelegramUpdate, update_key).state = 'done'
    db.commit()
    return True


def queue_outgoing(db, bot_id):
    rows = db.query(Message).join(Conversation, Conversation.id == Message.conversation_id).join(
        TelegramPeer, TelegramPeer.customer_id == Conversation.customer_id).outerjoin(
        TelegramDelivery, TelegramDelivery.message_id == Message.id).filter(
        TelegramPeer.bot_id == bot_id, Conversation.channel == 'telegram',
        Message.sender_type.in_(['ai', 'agent', 'system']), TelegramDelivery.message_id.is_(None)).all()
    for message in rows:
        db.add(TelegramDelivery(message_id=message.id))
    db.commit()


def outgoing_text(message):
    text = message.content[:4000]
    for citation in (message.citations or [])[:3]:
        source = f"\nNguồn: {citation.get('source', '')} {citation.get('location') or ''}"
        if len(text) + len(source) <= 4096:
            text += source
    return text


def send_outgoing(db, bot_id, token):
    queue_outgoing(db, bot_id)
    rows = db.query(TelegramDelivery, Message, TelegramPeer).join(Message, Message.id == TelegramDelivery.message_id).join(
        Conversation, Conversation.id == Message.conversation_id).join(TelegramPeer, TelegramPeer.customer_id == Conversation.customer_id
    ).filter(TelegramPeer.bot_id == bot_id, TelegramDelivery.state.notin_(['sent', 'skipped'])).order_by(Message.created_at, Message.id).all()
    seen = set()
    for delivery, message, peer in rows:
        if peer.id in seen:
            continue
        seen.add(peer.id)
        if delivery.state != 'pending':
            continue
        message_id, chat_id = message.id, peer.chat_id
        claimed = db.execute(update(TelegramDelivery).where(TelegramDelivery.message_id == message_id,
            TelegramDelivery.state == 'pending').values(state='sending'))
        if claimed.rowcount != 1:
            db.rollback()
            continue
        db.refresh(message)
        conversation = db.get(Conversation, message.conversation_id)
        db.refresh(conversation)
        unread = db.query(TelegramUpdate.id).filter(TelegramUpdate.peer_id == peer.id,
            TelegramUpdate.state.in_(['pending', 'processing'])).first() if message.sender_type == 'ai' else None
        if message.sender_type == 'ai' and (conversation.status != 'open' or conversation.last_customer_message_id != message.reply_to_id or unread):
            delivery.state, delivery.error = 'skipped', 'stale_ai'
            db.commit()
            continue
        body = outgoing_text(message)
        db.commit()
        # No SQL transaction during network I/O; a timed-out send may have reached Telegram.
        try:
            result = telegram_call(token, 'sendMessage', {'chat_id': chat_id, 'text': body,
                'link_preview_options': {'is_disabled': True}})
            if not isinstance(result, dict) or not identifier(result.get('message_id')):
                raise TelegramError('telegram_invalid_send_result', True)
            state, error, external_id, sent_at = 'sent', None, str(result['message_id']), now_utc()
        except TelegramError as exc:
            state, error, external_id, sent_at = 'uncertain' if exc.uncertain else 'failed', str(exc), None, None
        db.execute(update(TelegramDelivery).where(TelegramDelivery.message_id == message_id).values(
            state=state, error=error, external_message_id=external_id, sent_at=sent_at))
        if state in {'failed', 'uncertain'}:
            db.refresh(conversation)
            if conversation.status == 'open':
                queue_handoff(db, conversation)
        db.commit()


def recover_sends(db, bot_id):
    message_ids = db.query(Message.id).join(Conversation, Conversation.id == Message.conversation_id).join(
        TelegramPeer, TelegramPeer.customer_id == Conversation.customer_id).filter(TelegramPeer.bot_id == bot_id)
    db.execute(update(TelegramDelivery).where(TelegramDelivery.message_id.in_(message_ids),
        TelegramDelivery.state == 'sending').values(state='uncertain', error='interrupted_send'))
    affected = db.query(Conversation).join(Message, Message.conversation_id == Conversation.id).join(
        TelegramDelivery, TelegramDelivery.message_id == Message.id).filter(Message.id.in_(message_ids),
        TelegramDelivery.state.in_(['failed', 'uncertain']), Conversation.status == 'open').all()
    for conversation in affected:
        queue_handoff(db, conversation)
    db.commit()


def run_telegram(stop, token):
    try:
        while not stop.is_set():
            try:
                bot = telegram_call(token, 'getMe', {})
                if not isinstance(bot, dict) or not identifier(bot.get('id')) or bot.get('is_bot') is not True:
                    raise TelegramError('telegram_invalid_bot')
                bot_id = str(bot['id'])
                info = telegram_call(token, 'getWebhookInfo', {})
                if not isinstance(info, dict) or info.get('url'):
                    raise TelegramError('telegram_webhook_active')
                break
            except TelegramError as exc:
                code = str(exc)
                # Retry read-only startup probes, never configuration errors or ambiguous sends.
                if code != 'telegram_network_or_response' and not re.fullmatch(r'telegram_http_5\d{2}', code):
                    raise
                _status.update(status='error', detail=code)
                logging.getLogger(__name__).warning('Telegram startup: %s', code)
                stop.wait(5)
        else:
            return
        if stop.is_set():
            return
        with SessionLocal() as db:
            recover_sends(db, bot_id)
        while not stop.is_set():
            try:
                with SessionLocal() as db:
                    send_outgoing(db, bot_id, token)
                    cursor = db.get(TelegramCursor, bot_id)
                    offset = cursor.next_update_id if cursor else 0
                    db.rollback()
                    poll_error = None
                    try:
                        items = telegram_call(token, 'getUpdates', {'offset': offset, 'timeout': 2, 'limit': 100, 'allowed_updates': ['message']})
                        persist_updates(db, bot_id, items)
                    except TelegramError as exc:
                        db.rollback()
                        poll_error = exc
                        _status.update(status='error', detail=str(exc))
                    if poll_error is None:
                        _status.update(status='connected', detail='Đã kết nối Telegram; chỉ nhận chat riêng và văn bản.')
                    # Committed updates must progress even when the next poll fails.
                    process_next(db, bot_id)
                    send_outgoing(db, bot_id, token)
                    if poll_error is not None:
                        raise poll_error
            except Exception as exc:
                code = str(exc) if isinstance(exc, TelegramError) else 'telegram_worker_error'
                _status.update(status='error', detail=code)
                logging.getLogger(__name__).warning('Telegram worker: %s', code)
                stop.wait(5)
    except Exception as exc:
        _status.update(status='error', detail=str(exc) if isinstance(exc, TelegramError) else 'telegram_start_failed')
    finally:
        if stop.is_set():
            _status.update(status='not_connected', detail='Đã dừng kết nối Telegram.')


def start_telegram():
    if os.getenv('TELEGRAM_ENABLED', '').lower() != 'true':
        _status.update(status='not_connected', detail='Chưa bật kết nối.')
        return None
    token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    if not re.fullmatch(r'[0-9]{1,20}:[A-Za-z0-9_-]{20,200}', token):
        _status.update(status='error', detail='Thiếu hoặc sai định dạng TELEGRAM_BOT_TOKEN.')
        return None
    # ponytail: one polling thread in one API worker; use a leased worker/queue before scaling.
    stop = Event()
    thread = Thread(target=run_telegram, args=(stop, token), name='telegram-polling', daemon=True)
    _status.update(status='connecting', detail='Đang kiểm tra kết nối Telegram.')
    thread.start()
    return stop, thread
