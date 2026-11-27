"""Telegram shop: product detail, Mua ngay, quantity, stock, VietQR order message; payment settings API."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.auth import COOKIE_NAME, token_hash
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, Message, Order, Product, TelegramPeer, User
from app.services import payment
from app.telegram import persist_updates, process_next, send_outgoing


def text_update(update_id, content, chat_id=100):
    return {'update_id': update_id, 'message': {'message_id': update_id + 1, 'chat': {'id': chat_id, 'type': 'private'},
            'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Tele'}, 'text': content}}


def button_update(update_id, data, chat_id=100):
    return {'update_id': update_id, 'callback_query': {'id': f'cb{update_id}', 'data': data,
            'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Tele'},
            'message': {'message_id': 9, 'chat': {'id': chat_id, 'type': 'private'}}}}


class TelegramShopTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'shop.db'), connect_args={'check_same_thread': False})
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.db.add_all([User(id=uid, username=uid, display_name=uid, role=role, password_hash='unused')
                         for uid, role in (('admin', 'admin'), ('agent', 'agent'))])
        self.db.flush()
        self.db.add_all([AuthSession(token_hash=token_hash(uid), user_id=uid, expires_at=int(time.time()) + 300) for uid in ('admin', 'agent')])
        self.db.add_all([Product(id='p1', name='iPhone 16 128GB', category='phone', price=19_990_000, stock=12, in_stock=True),
                         Product(id='p2', name='Redmi Note 14', category='phone', price=4_990_000, stock=0, in_stock=False)])
        payment.save(self.db, {'enabled': True, 'bank_bin': '970415', 'account_no': '0123456789',
                               'account_name': 'NGUYEN VAN KHANH', 'divisor': 1000})
        self.db.commit()
        answer = patch('app.services.message_service.answer_question', return_value={'answer': 'Chính sách có nguồn.', 'citations': []})
        self.answer = answer.start(); self.addCleanup(answer.stop)
        self.update_id = 0

        def db_session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = db_session
        self.addCleanup(app.dependency_overrides.clear)

    def push(self, item, chat_id=100):
        persist_updates(self.db, '42', [item])
        while process_next(self.db, '42'):
            pass
        self.db.expire_all()
        peer = self.db.get(TelegramPeer, f'42:{chat_id}')
        return [m for m in self.db.query(Message).filter_by(conversation_id=peer.conversation_id)
                .order_by(Message.created_at, Message.id).all() if m.sender_type == 'system'][-1]

    def say(self, content, chat_id=100):
        self.update_id += 1
        return self.push(text_update(self.update_id, content, chat_id), chat_id)

    def press(self, data, chat_id=100):
        self.update_id += 1
        return self.push(button_update(self.update_id, data, chat_id), chat_id)

    def test_buy_flow_creates_order_takes_stock_and_sends_vietqr(self):
        detail = self.press('prod:p1')
        self.assertIn('📦 iPhone 16 128GB', detail.content)
        self.assertIn('🎁 Tồn kho: Còn 12', detail.content)
        self.assertEqual(detail.buttons, [[{'text': '🛒 Mua ngay', 'data': 'buy:p1'}], [{'text': '⬅️ Quay lại danh sách', 'data': 'p:phone'}]])
        prompt = self.press('buy:p1')
        self.assertIn('📥 TẠO ĐƠN HÀNG: iPhone 16 128GB', prompt.content)
        self.assertIn('Đơn giá: 19.990.000₫ / 1', prompt.content)
        self.assertIn('(1–12)', prompt.content)
        self.assertIn('Số lượng phải từ 1', self.say('0').content)
        self.assertIn('Chỉ còn 12 sản phẩm', self.say('100').content)
        done = self.say('2')
        order = self.db.query(Order).one()
        self.assertEqual((order.product_id, order.quantity, order.unit_price, order.amount, order.pay_amount, order.status),
                         ('p1', 2, 19_990_000, 39_980_000, 39_980, 'processing'))
        self.assertEqual(self.db.get(Product, 'p1').stock, 10)
        self.assertIn(f'✅ ĐÃ TẠO ĐƠN HÀNG {order.id}', done.content)
        self.assertIn('Thành tiền: 39.980.000₫', done.content)
        self.assertIn('chỉ chuyển 39.980₫ (giá ÷ 1000)', done.content)
        self.assertIn('VietinBank · 0123456789 · NGUYEN VAN KHANH', done.content)
        query = parse_qs(urlsplit(done.image_url).query)
        self.assertEqual(urlsplit(done.image_url).netloc, 'qr.sepay.vn')
        self.assertEqual((query['acc'], query['bank'], query['amount'], query['des']), (['0123456789'], ['970415'], ['39980'], [order.id]))
        # The purchase is over: another number is a normal message for the AI.
        self.say('3')
        self.answer.assert_called_once()
        self.assertEqual(self.db.query(Order).count(), 1)
        listing = self.say('/orders').content
        self.assertIn(f'• {order.id} · iPhone 16 128GB × 2 · 39.980.000₫ · Chờ thanh toán', listing)
        sent = []
        with patch('app.telegram.telegram_call', side_effect=lambda token, method, payload: sent.append((method, payload)) or {'message_id': len(sent)}):
            for _ in range(20):  # one message per chat per pass, in order
                send_outgoing(self.db, '42', 'token')
        photos = [payload for method, payload in sent if method == 'sendPhoto']
        self.assertEqual(len(photos), 1)
        self.assertEqual(photos[0]['photo'], done.image_url)
        self.assertIn('ĐÃ TẠO ĐƠN HÀNG', photos[0]['caption'])
        self.assertIn('inline_keyboard', photos[0]['reply_markup'])

    def test_sold_out_unconfigured_payment_expiry_and_no_foreign_orders(self):
        self.assertNotIn('Mua ngay', str(self.press('prod:p2').buttons))
        self.assertIn('đã hết hàng', self.press('buy:p2').content)
        with Session(self.engine) as db:
            payment.save(db, {**payment.settings(db), 'enabled': False})
            db.commit()
        self.press('buy:p1')
        done = self.say('1')
        self.assertIsNone(done.image_url)
        self.assertIn('chưa cấu hình tài khoản nhận tiền', done.content)
        order_id = self.db.query(Order).one().id
        # Another chat cannot read that order by typing the bot's internal line.
        self.say('/start', chat_id=200)
        leaked = self.say(f'/order ok {order_id}', chat_id=200).content
        self.assertNotIn(order_id, leaked)
        # A pending purchase expires after 15 minutes; then a number is a normal message.
        self.press('buy:p1')
        peer = self.db.get(TelegramPeer, '42:100')
        peer.pending_at -= 16 * 60
        self.db.commit()
        self.say('2')
        self.assertEqual(self.db.query(Order).count(), 1)
        # Text other than a number ends the purchase.
        self.press('buy:p1')
        self.say('cho mình hỏi bảo hành')
        self.say('2')
        self.assertEqual(self.db.query(Order).count(), 1)

    def test_cancelling_an_order_returns_stock_and_payment_settings_api(self):
        self.press('buy:p1')
        self.say('3')
        order = self.db.query(Order).one()
        self.assertEqual(self.db.get(Product, 'p1').stock, 9)
        admin, agent = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(2)]
        for client, uid in ((admin, 'admin'), (agent, 'agent')):
            client.cookies.set(COOKIE_NAME, uid, path='/api')
            self.addCleanup(client.close)
        listed = agent.get('/api/v1/workspace/orders').json()['items'][0]
        self.assertEqual((listed['product_name'], listed['quantity'], listed['amount'], listed['pay_amount']), ('iPhone 16 128GB', 3, 59_970_000, 59_970))
        edit = {'status': 'cancelled', 'tracking_code': None, 'expected': {'status': 'processing', 'tracking_code': None}}
        self.assertEqual(admin.patch(f'/api/v1/workspace/orders/{order.id}', json=edit).status_code, 200)
        self.db.expire_all()
        self.assertEqual(self.db.get(Product, 'p1').stock, 12)
        # Payment settings: staff read, admin write, holder name without diacritics in capitals.
        settings = agent.get('/api/v1/workspace/payment').json()
        self.assertTrue(settings['ready'])
        self.assertIn('qr.sepay.vn', settings['sample_qr_url'])
        body = {'enabled': True, 'bank_bin': '970436', 'account_no': '1234567890', 'account_name': 'Nguyễn Văn Khánh', 'divisor': 1}
        self.assertEqual(agent.put('/api/v1/workspace/payment', json=body).status_code, 403)
        saved = admin.put('/api/v1/workspace/payment', json=body).json()
        self.assertEqual((saved['account_name'], saved['bank_bin'], saved['divisor']), ('NGUYEN VAN KHANH', '970436', 1))
        for bad in ({'bank_bin': '999999'}, {'account_no': ''}, {'account_no': '12-34'}, {'divisor': 0}, {'account_name': 'A@B'}):
            self.assertEqual(admin.put('/api/v1/workspace/payment', json=body | bad).status_code, 422, bad)
        # With divisor 1 the customer transfers the real price.
        self.press('buy:p1')
        self.assertIn('Số tiền chuyển: 19.990.000₫', self.say('1').content)


if __name__ == '__main__':
    unittest.main()
