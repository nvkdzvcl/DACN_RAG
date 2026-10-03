import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.widget import COOKIE, COOKIE_PATH, _attempts
from app.core.auth import token_hash, verify_password, hash_password
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import Customer, CustomerAccount, CustomerSession, Conversation, Message, Order, OrderAccess, User

ACCOUNT = COOKIE_PATH + '/account'
PASSWORD = 'My customer password 2026!'

class CustomerAuthTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'accounts.db'),
                                    connect_args={'check_same_thread': False})
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        def db_session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = db_session
        self.addCleanup(app.dependency_overrides.clear)
        _attempts.clear()
        self.client, self.other = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(2)]
        self.addCleanup(self.client.close)
        self.addCleanup(self.other.close)

    def register(self, client=None, email='customer@example.com'):
        response = (client or self.client).post(ACCOUNT + '/register', json={
            'email': email, 'password': PASSWORD, 'display_name': 'Khách thử'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, client=None, email='customer@example.com', password=PASSWORD):
        return (client or self.client).post(ACCOUNT + '/login', json={'email': email, 'password': password})

    def test_registration_normalization_hash_cookie_and_staff_isolation(self):
        data = self.register(email='  Customer@Example.COM  ')
        self.assertEqual(data['account'], {'email': 'customer@example.com', 'email_verified': False})
        self.assertNotIn(PASSWORD, str(data))
        cookie = self.client.cookies.get(COOKIE)
        with Session(self.engine) as db:
            account = db.query(CustomerAccount).one()
            self.assertNotEqual(account.password_hash, PASSWORD)
            self.assertTrue(account.password_hash.startswith('pbkdf2_sha256$600000$'))
            self.assertEqual(db.query(CustomerSession).one().token_hash, token_hash(cookie))
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').headers['cache-control'], 'no-store')
        response = self.login(self.other)
        self.assertEqual(response.status_code, 200)
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertIn('SameSite=strict', response.headers['set-cookie'])

    def test_validation_duplicate_csrf_and_rate_limit(self):
        payload = {'email': 'customer@example.com', 'password': PASSWORD, 'display_name': 'Test'}
        self.assertEqual(self.client.post(ACCOUNT + '/register', json=payload,
                         headers={'X-CSRF-Protection': '0'}).status_code, 403)
        for email in ('bad', 'a..b@example.com', 'a@-example.com', 'a@example..com'):
            self.assertEqual(self.client.post(ACCOUNT + '/register', json={**payload, 'email': email}).status_code, 422)
        self.assertEqual(self.client.post(ACCOUNT + '/register', json={**payload, 'role': 'admin'}).status_code, 422)
        self.assertEqual(self.client.post(ACCOUNT + '/register', json={**payload, 'password': 'short'}).status_code, 422)
        self.register()
        self.assertEqual(self.client.post(ACCOUNT + '/register', json=payload).status_code, 409)
        with Session(self.engine) as db:
            self.assertEqual(db.query(CustomerAccount).count(), 1)
            self.assertEqual(db.query(Customer).count(), 1)
        bad = self.login(password='wrong').json()
        missing = self.login(email='missing@example.com').json()
        self.assertEqual(bad, missing)
        for _ in range(8):
            self.assertEqual(self.login(password='wrong').status_code, 401)
        self.assertEqual(self.login().status_code, 429)

    def test_devices_logout_password_and_expiry(self):
        first = self.register()
        second = self.login(self.other)
        self.assertEqual(second.json()['conversation_id'], first['conversation_id'])
        self.assertEqual(self.client.post(ACCOUNT + '/logout').status_code, 200)
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 401)
        self.assertEqual(self.other.get(COOKIE_PATH + '/session').status_code, 200)
        self.assertEqual(self.login().status_code, 200)
        response = self.client.post(ACCOUNT + '/password', json={
            'current_password': PASSWORD, 'new_password': 'Another secure password 2026!'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.other.get(COOKIE_PATH + '/session').status_code, 401)
        self.assertEqual(self.login().status_code, 401)
        self.assertEqual(self.login(password='Another secure password 2026!').status_code, 200)
        with Session(self.engine) as db:
            db.query(CustomerSession).update({'expires_at': int(time.time()) - 1})
            db.commit()
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 401)
        self.assertEqual(self.client.get(ACCOUNT + '/conversations').status_code, 401)

    def test_history_survives_new_chat_and_is_private(self):
        first = self.register()
        self.other.post(COOKIE_PATH + '/session', json={'display_name': 'Guest'})
        self.assertEqual(self.other.get(ACCOUNT + '/conversations').status_code, 401)
        own = first['conversation_id']
        with Session(self.engine) as db:
            for index in range(3):
                db.add(Message(id=str(uuid4()), conversation_id=own, sender_type='customer', content=f'private {index}'))
            db.commit()
        next_chat = self.client.delete(COOKIE_PATH + '/session')
        self.assertEqual(next_chat.status_code, 200, next_chat.text)
        self.assertNotEqual(next_chat.json()['conversation_id'], own)
        listed = self.client.get(ACCOUNT + '/conversations?limit=1').json()
        self.assertEqual(listed['total'], 2)
        self.assertTrue(listed['has_more'])
        history = self.client.get(ACCOUNT + f'/conversations/{own}?limit=2').json()
        self.assertEqual(len(history['messages']), 2)
        self.assertTrue(history['message_page']['has_more'])
        before = history['message_page']['next_before']
        self.assertEqual(len(self.client.get(ACCOUNT + f'/conversations/{own}?before={before}').json()['messages']), 1)
        self.register(self.other, 'other@example.com')
        self.assertEqual(self.other.get(ACCOUNT + f'/conversations/{own}').status_code, 404)
        self.assertEqual(self.other.get(ACCOUNT + '/conversations').json()['total'], 1)
        self.assertEqual(self.client.post(ACCOUNT + '/logout').status_code, 200)
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get(ACCOUNT + '/conversations').json()['total'], 2)

    def test_inflight_login_cannot_bypass_password_change(self):
        self.register()
        entered, release = Event(), Event()
        def delayed(password, encoded):
            valid = verify_password(password, encoded)
            entered.set()
            self.assertTrue(release.wait(10))
            return valid
        with patch('app.api.customer_auth.verify_password', side_effect=delayed), ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.login, self.other)
            try:
                self.assertTrue(entered.wait(5))
                with Session(self.engine) as db:
                    db.query(CustomerAccount).one().password_hash = hash_password('Changed elsewhere 2026!')
                    db.query(CustomerSession).delete()
                    db.commit()
            finally:
                release.set()
            self.assertEqual(pending.result(timeout=10).status_code, 401)
        with Session(self.engine) as db:
            self.assertEqual(db.query(CustomerSession).count(), 0)

    def test_email_never_claims_existing_customer_or_orders(self):
        with Session(self.engine) as db:
            db.add(Customer(id='owner', display_name='Khách thử', email='customer@example.com'))
            db.add(User(id='admin', username='admin', display_name='Admin', role='admin', password_hash='unused'))
            db.flush()
            db.add(Order(id='DH12345', customer_id='owner', status='shipped', tracking_code='PRIVATE'))
            db.commit()
        account = self.register()
        self.assertEqual(self.client.get(COOKIE_PATH + '/orders/DH12345').status_code, 404)
        with Session(self.engine) as db:
            self.assertNotEqual(db.query(CustomerAccount).one().customer_id, 'owner')
            db.add(OrderAccess(order_id='DH12345', customer_id='owner', issued_by_id='admin',
                               token_hash=token_hash('x' * 43), expires_at=int(time.time()) + 300))
            db.commit()
        response = self.client.post(COOKIE_PATH + '/order-access', json={'order_id': 'DH12345', 'code': 'x' * 43})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get(COOKIE_PATH + '/orders/DH12345').json()['tracking_code'], 'PRIVATE')
        self.assertEqual(self.login(self.other).status_code, 200)
        self.assertEqual(self.other.get(COOKIE_PATH + '/orders/DH12345').status_code, 200)
        self.client.post(ACCOUNT + '/logout')
        self.assertEqual(self.other.get(COOKIE_PATH + '/orders/DH12345').status_code, 200)
        migrate(self.engine)
        with Session(self.engine) as db:
            self.assertEqual(list(db.execute(text('SELECT version FROM schema_migrations ORDER BY version')).scalars()), list(range(1, 9)))
            self.assertEqual(db.query(CustomerAccount).count(), 1)

if __name__ == '__main__':
    unittest.main()
