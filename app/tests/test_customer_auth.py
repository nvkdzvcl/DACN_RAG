import os
import smtplib
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
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
from app.models.support import Customer, CustomerAccount, CustomerEmailToken, CustomerSession, Conversation, Message, Order, OrderAccess, User

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
            self.assertEqual(list(db.execute(text('SELECT version FROM schema_migrations ORDER BY version')).scalars()), list(range(1, 10)))
            self.assertEqual(db.query(CustomerAccount).count(), 1)


    def mail_config(self):
        config = {'SMTP_HOST': 'smtp.example.com', 'SMTP_PORT': '587', 'SMTP_SECURITY': 'starttls',
                  'SMTP_FROM': 'support@example.com', 'SMTP_USERNAME': 'sender', 'SMTP_PASSWORD': 'private-test-secret',
                  'CUSTOMER_PUBLIC_URL': 'http://localhost:5173', 'APP_ENV': 'development'}
        self.enterContext(patch.dict(os.environ, config))
        return self.enterContext(patch('app.services.customer_email.send_link'))

    def challenge(self, purpose='verify', expired=False, used=False):
        import secrets
        token = secrets.token_urlsafe(32)
        with Session(self.engine) as db:
            account = db.query(CustomerAccount).filter_by(email='customer@example.com').one()
            db.add(CustomerEmailToken(token_hash=token_hash(token), account_id=account.id, purpose=purpose,
                   created_at=int(time.time()), expires_at=int(time.time()) + (-1 if expired else 900), used=used))
            db.commit()
        return token

    def test_email_verification_recovery_and_all_device_revocation(self):
        delivery = self.mail_config()
        original = self.register()
        self.login(self.other)
        response = self.client.post(ACCOUNT + '/verification-request')
        self.assertEqual(response.status_code, 202, response.text)
        delivery.assert_called_once()
        token = delivery.call_args.args[3]
        self.assertNotIn(token, response.text)
        with Session(self.engine) as db:
            self.assertEqual(db.query(CustomerEmailToken).one().token_hash, token_hash(token))
        verify = {'token': token, 'password': PASSWORD}
        self.assertEqual(self.other.post(ACCOUNT + '/verify-email', json={**verify, 'password': 'wrong'}).status_code, 400)
        self.assertEqual(self.other.post(ACCOUNT + '/verify-email', json=verify).status_code, 200)
        self.assertEqual(self.client.post(ACCOUNT + '/verify-email', json=verify).status_code, 400)
        self.assertTrue(self.client.get(COOKIE_PATH + '/session').json()['account']['email_verified'])
        response = self.client.post(ACCOUNT + '/forgot-password', json={'email': 'CUSTOMER@example.com'})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(delivery.call_args.args[2], 'reset')
        reset = delivery.call_args.args[3]
        self.assertNotIn(reset, response.text)
        newer = self.challenge('reset')
        body = {'token': reset, 'new_password': 'New customer password 2026!'}
        self.assertEqual(self.client.post(ACCOUNT + '/reset-password', json=body).status_code, 200)
        self.assertEqual(self.other.get(COOKIE_PATH + '/session').status_code, 401)
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 401)
        self.assertEqual(self.client.post(ACCOUNT + '/reset-password', json=body).status_code, 400)
        self.assertEqual(self.client.post(ACCOUNT + '/reset-password', json={**body, 'token': newer}).status_code, 400)
        self.assertEqual(self.login().status_code, 401)
        self.assertEqual(self.login(password=body['new_password']).status_code, 200)
        history = self.client.get(ACCOUNT + '/conversations').json()
        self.assertEqual(history['items'][0]['id'], original['conversation_id'])
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)

    def test_email_requests_hide_existence_and_bound_mail_volume(self):
        delivery = self.mail_config()
        self.register()
        response = self.client.post(ACCOUNT + '/forgot-password', json={'email': 'customer@example.com'})
        missing = self.other.post(ACCOUNT + '/forgot-password', json={'email': 'missing@example.com'})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), missing.json())
        delivery.assert_not_called()  # Unverified email is not a recovery authority.
        self.assertEqual(self.other.post(ACCOUNT + '/verification-request').status_code, 401)
        self.assertEqual(self.client.post(ACCOUNT + '/verification-request', headers={'X-CSRF-Protection': '0'}).status_code, 403)
        self.client.post(ACCOUNT + '/verification-request')
        self.client.post(ACCOUNT + '/verification-request')
        self.assertEqual(delivery.call_count, 1)
        from app.services.customer_email import deliver_challenge, mail_settings
        with Session(self.engine) as db:
            account = db.query(CustomerAccount).one()
            account_id = account.id
        base = int(time.time())
        for delta in (61, 122, 183):
            with patch('app.services.customer_email.time.time', return_value=base + delta):
                deliver_challenge(self.engine, mail_settings(), 'verify', account_id=account_id)
        self.assertEqual(delivery.call_count, 3)
        with Session(self.engine) as db:
            self.assertEqual(db.query(CustomerEmailToken).count(), 3)
        for _ in range(3):
            self.client.post(ACCOUNT + '/forgot-password', json={'email': 'missing@example.com'})
        self.assertEqual(self.client.post(ACCOUNT + '/forgot-password', json={'email': 'missing@example.com'}).status_code, 429)

    def test_email_token_scope_expiry_validation_and_password_change(self):
        self.register()
        token = self.challenge()
        body = {'token': token, 'new_password': 'Recovery replacement 2026!'}
        self.assertEqual(self.client.post(ACCOUNT + '/reset-password', json=body).status_code, 400)
        for invalid in ('bad-token', self.challenge(expired=True), self.challenge(used=True), self.challenge('reset')):
            response = self.client.post(ACCOUNT + '/verify-email', json={'token': invalid, 'password': PASSWORD})
            self.assertEqual(response.status_code, 400)
            self.assertNotIn(invalid, response.text)
        self.assertEqual(self.client.post(ACCOUNT + '/verify-email', json={'token': token, 'password': PASSWORD}, headers={'X-CSRF-Protection': '0'}).status_code, 403)
        self.assertEqual(self.client.post(ACCOUNT + '/password', json={'current_password': PASSWORD, 'new_password': body['new_password']}).status_code, 200)
        self.assertEqual(self.client.post(ACCOUNT + '/verify-email', json={'token': token, 'password': body['new_password']}).status_code, 400)
        with Session(self.engine) as db:
            self.assertTrue(all(row.used for row in db.query(CustomerEmailToken)))
            self.assertFalse(db.query(CustomerAccount).one().email_verified)

    def test_email_delivery_failure_and_configuration_fail_closed(self):
        delivery = self.mail_config()
        self.register()
        with patch.dict(os.environ, {'SMTP_HOST': ''}):
            self.assertFalse(self.client.get(ACCOUNT + '/email-status').json()['configured'])
            self.assertEqual(self.client.post(ACCOUNT + '/verification-request').status_code, 503)
            self.assertEqual(self.client.post(ACCOUNT + '/forgot-password', json={'email': 'missing@example.com'}).status_code, 503)
        delivery.side_effect = smtplib.SMTPException('private-test-secret customer@example.com')
        with self.assertLogs('app.services.customer_email', level='WARNING') as logs:
            self.assertEqual(self.client.post(ACCOUNT + '/verification-request').status_code, 202)
        self.assertNotIn('private-test-secret', str(logs.output))
        self.assertNotIn('customer@example.com', str(logs.output))
        with Session(self.engine) as db:
            self.assertTrue(db.query(CustomerEmailToken).one().used)
        from app.services.customer_email import mail_settings
        for changes in ({'APP_ENV': 'production'}, {'SMTP_SECURITY': 'none'}, {'SMTP_PORT': 'bad'},
                        {'CUSTOMER_PUBLIC_URL': 'https://evil@example.com'}, {'SMTP_FROM': 'a@example.com\nBcc:x@y.com'},
                        {'CUSTOMER_PUBLIC_URL': 'https://example.com/#secret'}, {'SMTP_PASSWORD': ''}):
            with patch.dict(os.environ, changes), self.assertRaises(ValueError):
                mail_settings()

    def test_smtp_uses_tls_and_fragment_links_without_host_header(self):
        from app.services import customer_email
        real_send = customer_email.send_link
        delivery = self.mail_config()
        self.register()
        self.client.post(ACCOUNT + '/verification-request', headers={'X-Forwarded-Host': 'evil.example'})
        settings, recipient, purpose, token = delivery.call_args.args
        for security, factory in [('starttls', 'SMTP'), ('ssl', 'SMTP_SSL')]:
            with patch('app.services.customer_email.smtplib.' + factory) as transport:
                smtp = transport.return_value.__enter__.return_value
                smtp.send_message.return_value = {}
                real_send({**settings, 'security': security}, recipient, purpose, token)
                message = smtp.send_message.call_args.args[0]
                self.assertEqual(message['To'], 'customer@example.com')
                self.assertIn('http://localhost:5173/chat#verify=' + token, message.get_content())
                self.assertNotIn('evil.example', message.get_content())
                self.assertNotIn('private-test-secret', message.get_content())
                smtp.login.assert_called_once_with('sender', 'private-test-secret')
                self.assertEqual(transport.call_args.kwargs['timeout'], 10)
                if security == 'starttls':
                    smtp.starttls.assert_called_once()
                    self.assertEqual(smtp.starttls.call_args.kwargs['context'].verify_mode, 2)
                else:
                    self.assertEqual(transport.call_args.kwargs['context'].verify_mode, 2)

    def test_concurrent_reset_token_can_only_be_consumed_once(self):
        self.register()
        with Session(self.engine) as db:
            db.query(CustomerAccount).update({'email_verified': True})
            db.commit()
        token = self.challenge('reset')
        barrier = Barrier(2)
        def synchronized_hash(password):
            encoded = hash_password(password)
            barrier.wait(timeout=10)
            return encoded
        body = {'token': token, 'new_password': 'Concurrent recovery 2026!'}
        with patch('app.api.customer_auth.hash_password', side_effect=synchronized_hash), ThreadPoolExecutor(2) as pool:
            first = pool.submit(self.client.post, ACCOUNT + '/reset-password', json=body)
            second = pool.submit(self.other.post, ACCOUNT + '/reset-password', json=body)
            statuses = sorted([first.result(timeout=20).status_code, second.result(timeout=20).status_code])
        self.assertEqual(statuses, [200, 400])
        with Session(self.engine) as db:
            self.assertEqual(db.query(CustomerSession).count(), 0)

    def test_v8_migration_preserves_accounts_as_unverified(self):
        self.register()
        with self.engine.begin() as connection:
            connection.execute(text('ALTER TABLE customer_accounts DROP COLUMN email_verified'))
            connection.execute(text('DELETE FROM schema_migrations WHERE version = 9'))
            connection.execute(text('DROP TABLE customer_email_tokens'))
        migrate(self.engine)
        migrate(self.engine)
        with Session(self.engine) as db:
            account = db.query(CustomerAccount).one()
            self.assertFalse(account.email_verified)
            self.assertTrue(verify_password(PASSWORD, account.password_hash))
            self.assertEqual(db.query(CustomerSession).count(), 1)
            self.assertEqual(db.query(CustomerEmailToken).count(), 0)

if __name__ == '__main__':
    unittest.main()
