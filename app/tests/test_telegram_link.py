"""Linking a Telegram chat to a verified web account, the /orders, /unlink and /start replies, and the web API."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.widget import COOKIE_PATH, _attempts
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import (Conversation, Customer, CustomerAccount, CustomerEmailToken, Message, Order,
                                TelegramDelivery, TelegramPeer, TelegramUpdate)
from app.services.order_service import lookup_order
from app.telegram import persist_updates, process_next, queue_outgoing

ACCOUNT = COOKIE_PATH + '/account'
PASSWORD = 'My customer password 2026!'


def incoming(update_id, content, chat_id=100):
    return {'update_id': update_id, 'message': {'message_id': update_id + 1, 'chat': {'id': chat_id, 'type': 'private'},
            'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Tele'}, 'text': content}}


class TelegramLinkTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'link.db'), connect_args={'check_same_thread': False})
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)

        def db_session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = db_session
        self.addCleanup(app.dependency_overrides.clear)
        _attempts.clear()
        username = patch('app.api.customer_auth.bot_username', return_value='shop_support_bot')
        username.start(); self.addCleanup(username.stop)
        self.web, self.web2 = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(2)]
        for client in (self.web, self.web2):
            self.addCleanup(client.close)
        self.customer_id = self.register(self.web, 'an@example.com')
        self.other_customer_id = self.register(self.web2, 'binh@example.com')
        with Session(self.engine) as db:
            db.add_all([Order(id='DH2611180001', customer_id=self.customer_id, status='shipping', tracking_code='VN00000001'),
                        Order(id='DH2611180002', customer_id=self.other_customer_id, status='delivered')])
            db.commit()
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.update_id = 0

    def register(self, client, email):
        response = client.post(ACCOUNT + '/register', json={'email': email, 'password': PASSWORD, 'display_name': email[:2]})
        self.assertEqual(response.status_code, 201, response.text)
        with Session(self.engine) as db:
            account = db.query(CustomerAccount).filter_by(email=email).one()
            account.email_verified = True
            db.commit()
            return account.customer_id

    def link_url(self, client=None):
        response = (client or self.web).post(ACCOUNT + '/telegram-link')
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        return response.json()['url']

    def send(self, content, chat_id=100):
        """One Telegram message through the bot; returns the bot's latest reply text."""
        self.update_id += 1
        persist_updates(self.db, '42', [incoming(self.update_id, content, chat_id)])
        while process_next(self.db, '42'):
            pass
        peer = self.db.get(TelegramPeer, f'42:{chat_id}')
        conversation = self.db.get(Conversation, peer.conversation_id)
        return self.db.query(Message).filter_by(conversation_id=conversation.id, sender_type='system').order_by(
            Message.created_at.desc(), Message.id.desc()).first().content

    def peer(self, chat_id=100):
        return self.db.get(TelegramPeer, f'42:{chat_id}')

    def test_link_then_orders_and_chat_lookup(self):
        self.assertIn('Chào bạn', self.send('/start'))
        self.assertIn('chưa kết nối', self.send('/orders'))
        url = self.link_url()
        self.assertRegex(url, r'^https://t\.me/shop_support_bot\?start=link_[A-Za-z0-9_-]{32}$')
        code = url.split('start=')[1]
        reply = self.send('/start ' + code)
        self.assertIn('Đã kết nối Telegram với tài khoản an***@example.com', reply)
        self.assertEqual(self.peer().customer_id, self.customer_id)
        # The single-use code is not stored anywhere in clear text.
        self.assertFalse(any(code[5:] in (u.content or '') for u in self.db.query(TelegramUpdate)))
        self.assertFalse(any(code[5:] in m.content for m in self.db.query(Message)))
        orders = self.send('/orders')
        self.assertIn('DH2611180001 · Đang giao · Vận đơn VN00000001', orders)
        self.assertNotIn('DH2611180002', orders)
        # The AI order tool in the new Telegram conversation sees the same orders as the website.
        conversation = self.peer().conversation_id
        self.assertTrue(lookup_order(self.db, 'DH2611180001', self.customer_id, conversation)['found'])
        self.assertFalse(lookup_order(self.db, 'DH2611180002', self.customer_id, conversation)['found'])
        # Replies go to Telegram; the account's website conversations are not queued for Telegram.
        web_chat = self.db.query(Conversation).filter_by(customer_id=self.customer_id, channel='website').first()
        self.db.add(Message(id='web-ai', conversation_id=web_chat.id, sender_type='ai', content='Trả lời trên web'))
        self.db.commit()
        queue_outgoing(self.db, '42')
        queued = {d.message_id for d in self.db.query(TelegramDelivery)}
        website = self.db.query(Message.id).join(Conversation, Conversation.id == Message.conversation_id).filter(Conversation.channel == 'website').all()
        self.assertIn('web-ai', {m.id for m in website})
        self.assertNotIn('web-ai', queued)
        self.assertTrue(self.web.get(ACCOUNT + '/telegram').json()['linked'])

    def test_code_is_single_use_expires_and_is_replaced(self):
        code = self.link_url().split('start=')[1]
        self.assertIn('Đã kết nối', self.send('/start ' + code))
        self.assertIn('không hợp lệ', self.send('/start ' + code, chat_id=200))
        self.assertNotEqual(self.peer(200).customer_id, self.customer_id)
        first = self.link_url().split('start=')[1]
        second = self.link_url().split('start=')[1]
        self.assertIn('không hợp lệ', self.send('/start ' + first, chat_id=300))
        with Session(self.engine) as db:
            db.query(CustomerEmailToken).filter_by(purpose='telegram_link', used=False).update({'expires_at': int(time.time()) - 1})
            db.commit()
        self.assertIn('không hợp lệ', self.send('/start ' + second, chat_id=300))
        self.assertIn('không hợp lệ', self.send('/start link_short', chat_id=300))
        self.assertEqual(self.peer().customer_id, self.customer_id)

    def test_relink_moves_old_chat_and_unlink_from_bot_and_web(self):
        self.send('/start ' + self.link_url().split('start=')[1])
        # A second Telegram chat linked to the same account replaces the first one.
        self.assertIn('Đã kết nối', self.send('/start ' + self.link_url().split('start=')[1], chat_id=200))
        self.assertEqual(self.peer(200).customer_id, self.customer_id)
        self.assertNotEqual(self.peer(100).customer_id, self.customer_id)
        self.assertIn('chưa kết nối', self.send('/orders', chat_id=100))
        self.assertIn('Đã gỡ kết nối', self.send('/unlink', chat_id=200))
        self.assertIn('chưa kết nối', self.send('/orders', chat_id=200))
        self.assertIn('chưa kết nối với tài khoản web nào', self.send('/unlink', chat_id=200))
        self.assertFalse(self.web.get(ACCOUNT + '/telegram').json()['linked'])
        self.send('/start ' + self.link_url().split('start=')[1], chat_id=200)
        self.assertEqual(self.web.delete(ACCOUNT + '/telegram').json(), {'linked': False})
        self.db.expire_all()
        self.assertNotEqual(self.peer(200).customer_id, self.customer_id)
        # Another account's code links that account only.
        self.send('/start ' + self.link_url(self.web2).split('start=')[1], chat_id=200)
        self.assertIn('DH2611180002', self.send('/orders', chat_id=200))

    def test_unverified_account_and_disabled_telegram(self):
        code = self.link_url().split('start=')[1]
        with Session(self.engine) as db:
            db.query(CustomerAccount).filter_by(email='an@example.com').update({'email_verified': False})
            db.commit()
        self.assertEqual(self.web.post(ACCOUNT + '/telegram-link').status_code, 403)
        self.assertIn('chưa xác minh email', self.send('/start ' + code))
        self.assertNotEqual(self.peer().customer_id, self.customer_id)
        with patch('app.api.customer_auth.bot_username', return_value=None):
            self.assertEqual(self.web2.post(ACCOUNT + '/telegram-link').status_code, 503)
            self.assertEqual(self.web2.get(ACCOUNT + '/telegram').json(), {'available': False, 'linked': False})
        guest = TestClient(app, headers={'X-CSRF-Protection': '1'}); self.addCleanup(guest.close)
        guest.post(COOKIE_PATH + '/session', json={'display_name': 'Guest'})
        self.assertEqual(guest.post(ACCOUNT + '/telegram-link').status_code, 401)


if __name__ == '__main__':
    unittest.main()
