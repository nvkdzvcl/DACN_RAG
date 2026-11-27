"""Telegram menu: commands, inline buttons, /products from the catalogue; staff product API."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.auth import COOKIE_NAME, token_hash
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import (AuthSession, Conversation, ConversationEvent, Message, Product, TelegramDelivery,
                                TelegramPeer, Ticket, User)
from app.telegram import persist_updates, process_next, send_outgoing


def text_update(update_id, content, chat_id=100):
    return {'update_id': update_id, 'message': {'message_id': update_id + 1, 'chat': {'id': chat_id, 'type': 'private'},
            'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Tele'}, 'text': content}}


def button_update(update_id, data, chat_id=100, chat_type='private'):
    return {'update_id': update_id, 'callback_query': {'id': f'cb{update_id}', 'data': data,
            'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Tele'},
            'message': {'message_id': 9, 'chat': {'id': chat_id, 'type': chat_type}}}}


class TelegramMenuTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'menu.db'), connect_args={'check_same_thread': False})
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.db.add_all([User(id=uid, username=uid, display_name=uid, role=role, password_hash='unused')
                         for uid, role in (('admin', 'admin'), ('agent', 'agent'))])
        self.db.flush()
        self.db.add_all([AuthSession(token_hash=token_hash(uid), user_id=uid, expires_at=int(time.time()) + 300) for uid in ('admin', 'agent')])
        self.db.commit()
        answer = patch('app.services.message_service.answer_question', return_value={'answer': 'Chính sách có nguồn.', 'citations': []})
        self.answer = answer.start(); self.addCleanup(answer.stop)
        self.update_id = 0

        def db_session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = db_session
        self.addCleanup(app.dependency_overrides.clear)

    def push(self, item):
        persist_updates(self.db, '42', [item])
        while process_next(self.db, '42'):
            pass
        self.db.expire_all()
        peer = self.db.get(TelegramPeer, '42:100')
        return self.db.query(Message).filter_by(conversation_id=peer.conversation_id).order_by(Message.created_at, Message.id).all()

    def say(self, content):
        self.update_id += 1
        return self.push(text_update(self.update_id, content))

    def press(self, data, **kw):
        self.update_id += 1
        return self.push(button_update(self.update_id, data, **kw))

    def reply(self, messages):
        return [m for m in messages if m.sender_type == 'system'][-1]

    def add_products(self):
        self.db.add_all([Product(id='p1', name='iPhone 16 128GB', category='phone', price=19_990_000, in_stock=True),
                         Product(id='p2', name='Galaxy S25', category='phone', price=None, in_stock=False, url='https://example.com/s25'),
                         Product(id='p3', name='MacBook Air M3', category='laptop', price=26_490_000),
                         Product(id='p4', name='Máy ẩn', category='tablet', price=1, active=False)])
        self.db.commit()

    def test_start_menu_has_buttons_and_delivery_sends_the_keyboard(self):
        start = self.reply(self.say('/start'))
        self.assertIn('Chào bạn', start.content)
        self.assertEqual(start.buttons[0][0], {'text': '🛒 Sản phẩm', 'data': 'cmd:/products'})
        sent = []
        with patch('app.telegram.telegram_call', side_effect=lambda token, method, payload: sent.append(payload) or {'message_id': len(sent)}):
            send_outgoing(self.db, '42', 'token')
        keyboard = sent[-1]['reply_markup']['inline_keyboard']
        self.assertEqual(keyboard[0][0], {'text': '🛒 Sản phẩm', 'callback_data': 'cmd:/products'})
        self.assertEqual(self.db.query(TelegramDelivery).filter_by(state='sent').count(), len(sent))
        self.answer.assert_not_called()

    def test_products_by_category_hides_inactive_items(self):
        self.assertIn('chưa đăng sản phẩm', self.reply(self.say('/products')).content)
        self.add_products()
        menu = self.reply(self.press('cmd:/products'))
        labels = [button['text'] for row in menu.buttons for button in row]
        self.assertIn('📱 Điện thoại (2)', labels)
        self.assertIn('💻 Laptop (1)', labels)
        self.assertFalse(any('bảng' in label for label in labels), labels)
        phones = self.reply(self.press('p:phone')).content
        self.assertIn('• iPhone 16 128GB — 19.990.000₫ · Còn hàng', phones)
        self.assertIn('• Galaxy S25 — Liên hệ · Hết hàng', phones)
        self.assertIn('https://example.com/s25', phones)
        self.assertNotIn('MacBook', phones)
        self.assertNotIn('Máy ẩn', self.reply(self.say('/products tablet')).content)
        self.answer.assert_not_called()

    def test_policy_button_asks_the_ai_and_foreign_buttons_are_ignored(self):
        self.assertEqual(len(self.reply(self.say('/policies')).buttons), 4)
        messages = self.press('ask:1')
        self.assertEqual([m.sender_type for m in messages][-2:], ['customer', 'ai'])
        self.assertEqual(messages[-2].content, 'Thời gian bảo hành bắt đầu tính từ khi nào?')
        before = self.db.query(Message).count()
        persist_updates(self.db, '42', [button_update(90, 'cmd:/evil'), button_update(91, 'cmd:/products', chat_type='group')])
        self.assertFalse(process_next(self.db, '42'))
        self.assertEqual(self.db.query(Message).count(), before)

    def test_human_status_cancel_and_new_conversation(self):
        self.press('cmd:/human')
        status = self.reply(self.say('/status')).content
        self.assertRegex(status, r'Đang chờ nhân viên · đã chờ \d+ phút · nhân viên phản hồi trước \d\d:\d\d')
        self.assertIn('Đã hủy yêu cầu', self.reply(self.say('/cancel')).content)
        peer = self.db.get(TelegramPeer, '42:100')
        self.assertEqual(self.db.get(Conversation, peer.conversation_id).status, 'open')
        self.assertEqual(self.db.query(ConversationEvent).filter_by(kind='handoff_cancelled').count(), 1)
        self.assertIn('không có yêu cầu', self.reply(self.say('/cancel')).content)
        # After staff accept, /cancel cannot take the conversation back.
        self.say('/human')
        conversation = self.db.get(Conversation, peer.conversation_id)
        conversation.status, conversation.assigned_agent_id = 'assigned', 'agent'
        self.db.commit()
        self.assertIn('không hủy được', self.reply(self.say('/cancel')).content)
        old = peer.conversation_id
        self.assertIn('cuộc trò chuyện mới', self.reply(self.say('/new')).content)
        self.db.expire_all()
        self.assertNotEqual(self.db.get(TelegramPeer, '42:100').conversation_id, old)
        self.assertEqual(self.db.get(Conversation, old).status, 'closed')
        self.assertFalse(self.db.query(Ticket).filter(Ticket.conversation_id == old, Ticket.status.in_(['open', 'assigned'])).count())

    def test_contact_help_and_unknown_commands_do_not_call_the_ai(self):
        self.assertIn('1800 6601', self.reply(self.say('/contact')).content)
        self.assertIn('/products', self.reply(self.say('/help@shop_bot')).content)
        unknown = self.reply(self.say('/wallet'))
        self.assertIn('chưa hiểu lệnh', unknown.content)
        self.answer.assert_not_called()

    def test_product_api_staff_read_admin_write(self):
        admin, agent = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(2)]
        for client, uid in ((admin, 'admin'), (agent, 'agent')):
            client.cookies.set(COOKIE_NAME, uid, path='/api')
            self.addCleanup(client.close)
        body = {'name': ' iPad Air M2 ', 'category': 'tablet', 'price': 16990000, 'in_stock': True, 'url': 'https://fptshop.com.vn/ipad', 'description': ''}
        self.assertEqual(agent.post('/api/v1/workspace/products', json=body).status_code, 403)
        created = admin.post('/api/v1/workspace/products', json=body)
        self.assertEqual(created.status_code, 201, created.text)
        product = created.json()
        self.assertEqual((product['name'], product['description'], product['active']), ('iPad Air M2', None, True))
        for bad in ({'category': 'car'}, {'price': -1}, {'url': 'http://insecure.example'}, {'name': ''}):
            self.assertEqual(admin.post('/api/v1/workspace/products', json=body | bad).status_code, 422, bad)
        hidden = admin.patch(f"/api/v1/workspace/products/{product['id']}", json=body | {'active': False, 'in_stock': False})
        self.assertEqual((hidden.json()['active'], hidden.json()['in_stock']), (False, False))
        self.assertEqual(admin.patch('/api/v1/workspace/products/missing', json=body).status_code, 404)
        listing = agent.get('/api/v1/workspace/products', params={'category': 'tablet', 'q': 'iPad'}).json()
        self.assertEqual(listing['total'], 1)
        self.assertEqual(agent.get('/api/v1/workspace/products', params={'category': 'car'}).status_code, 422)


if __name__ == '__main__':
    unittest.main()
