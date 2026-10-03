import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.widget import COOKIE_PATH, _attempts
from app.core.auth import COOKIE_NAME, token_hash
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, Conversation, Customer, Message, Order, OrderAccess, User, WidgetSession
from app.services.order_service import lookup_order

ACCESS_PATH = '/api/v1/workspace/orders/DH12345/access-code'


class OrderAccessTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'access.db'),
                                    connect_args={'check_same_thread': False, 'timeout': 10})
        self.addCleanup(directory.cleanup)
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        with Session(self.engine) as db:
            db.add_all([User(id=role, username=role, display_name=role, role=role, password_hash='unused')
                        for role in ('admin', 'agent')])
            db.add_all([Customer(id='owner', display_name='Same name'), Customer(id='other', display_name='Other')])
            db.flush()
            db.add_all([AuthSession(token_hash=token_hash(role), user_id=role, expires_at=int(time.time()) + 300)
                        for role in ('admin', 'agent')])
            db.add_all([Order(id=oid, customer_id='owner', status='shipped', tracking_code='PRIVATE-' + oid)
                        for oid in ('DH12345', 'DH99999')])
            db.commit()
        def test_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        self.addCleanup(app.dependency_overrides.clear)
        _attempts.clear()
        self.admin, self.client, self.other = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(3)]
        for client in (self.admin, self.client, self.other):
            self.addCleanup(client.close)
        self.admin.cookies.set(COOKIE_NAME, 'admin', path='/api')
        self.cid = self.start(self.client)
        self.other_cid = self.start(self.other)

    def start(self, client):
        response = client.post(COOKIE_PATH + '/session', json={'display_name': 'Same name'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['conversation_id']

    def issue(self):
        response = self.admin.post(ACCESS_PATH)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        return response.json()['code']

    def redeem(self, code, client=None, order_id='DH12345'):
        return (client or self.client).post(COOKIE_PATH + '/order-access', json={'order_id': order_id, 'code': code})

    def lookup(self, cid=None, order_id='DH12345'):
        with Session(self.engine) as db:
            conversation = db.get(Conversation, cid or self.cid)
            return lookup_order(db, order_id, conversation.customer_id, conversation.id)

    def test_permissions_csrf_validation_and_attempt_limit(self):
        self.assertEqual(self.client.post(ACCESS_PATH).status_code, 401)
        self.other.cookies.set(COOKIE_NAME, 'agent', path='/api')
        for method in ('post', 'delete'):
            self.assertEqual(getattr(self.other, method)(ACCESS_PATH).status_code, 403)
            self.assertEqual(getattr(self.admin, method)(ACCESS_PATH, headers={'X-CSRF-Protection': '0'}).status_code, 403)
        code = self.issue()
        self.assertEqual(self.client.post(COOKIE_PATH + '/order-access', json={
            'order_id': 'DH12345', 'code': code, 'customer_id': 'owner'}).status_code, 422)
        self.assertEqual(self.client.post(COOKIE_PATH + '/order-access', headers={'X-CSRF-Protection': '0'},
            json={'order_id': 'DH12345', 'code': code}).status_code, 403)
        with TestClient(app, headers={'X-CSRF-Protection': '1'}) as anonymous:
            self.assertEqual(self.redeem(code, anonymous).status_code, 401)
        for _ in range(6):
            self.assertEqual(self.redeem('x' * 43).status_code, 400)
        self.assertEqual(self.redeem(code).status_code, 429)
        self.assertFalse(self.lookup()['found'])

    def test_single_order_scope_private_storage_and_retry(self):
        self.assertFalse(self.lookup()['found'])
        code = self.issue()
        response = self.redeem(code)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertNotIn(code, response.text)
        self.assertNotIn(token_hash(code), response.text)
        self.assertEqual(response.json()['order_access'][0]['order_id'], 'DH12345')
        self.assertTrue(self.lookup()['found'])
        self.assertFalse(self.lookup(order_id='DH99999')['found'])
        self.assertFalse(self.lookup(self.other_cid)['found'])
        self.assertEqual(self.redeem(code).status_code, 200)
        self.assertEqual(self.redeem(code, self.other).status_code, 400)
        with Session(self.engine) as db:
            access = db.get(OrderAccess, 'DH12345')
            self.assertEqual(access.token_hash, token_hash(code))
            self.assertEqual(access.issued_by_id, 'admin')
            self.assertNotEqual(db.get(Conversation, self.cid).customer_id, 'owner')
            self.assertEqual(db.query(Message).count(), 0)
        with patch('app.services.message_service.select_order_tool', return_value={
                'name': 'lookup_order', 'arguments': {'order_id': 'DH12345'}}):
            result = self.client.post(COOKIE_PATH + '/messages', json={
                'content': 'Tra DH12345', 'client_message_id': str(uuid4())})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIn('PRIVATE-DH12345', result.text)
        self.assertNotIn('tool_trace', result.text)
        self.assertNotIn('PRIVATE-DH12345', self.other.get(COOKIE_PATH + '/session').text)

    def test_customer_order_view_requires_current_access(self):
        path = COOKIE_PATH + '/orders/DH12345'
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.other.get(path).status_code, 404)
        self.assertEqual(self.client.get(COOKIE_PATH + '/orders/DH99999').status_code, 404)
        code = self.issue()
        self.assertEqual(self.redeem(code).status_code, 200)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(response.json(), {'order_id': 'DH12345', 'status': 'shipped',
                                           'tracking_code': 'PRIVATE-DH12345'})
        self.assertEqual(self.other.get(path).status_code, 404)
        self.assertEqual(self.client.get(COOKIE_PATH + '/orders/DH99999').status_code, 404)
        self.assertEqual(self.admin.delete(ACCESS_PATH).status_code, 200)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_rotation_expiry_owner_change_and_revocation(self):
        old = self.issue()
        self.assertEqual(self.redeem(old).status_code, 200)
        new = self.issue()
        self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.redeem(old).status_code, 400)
        self.assertEqual(self.redeem(new).status_code, 200)
        with Session(self.engine) as db:
            db.get(Order, 'DH12345').customer_id = 'other'
            db.commit()
        self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.redeem(new).status_code, 400)
        new = self.issue()
        with Session(self.engine) as db:
            deadline = db.get(OrderAccess, 'DH12345').expires_at
        with patch('time.time', return_value=deadline):
            self.assertEqual(self.redeem(new).status_code, 400)
            self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.redeem(new).status_code, 200)
        self.assertEqual(self.admin.delete(ACCESS_PATH).status_code, 200)
        self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.admin.delete(ACCESS_PATH).status_code, 200)

    def test_session_end_expiry_closed_and_handoff_do_not_extend_access(self):
        code = self.issue()
        self.assertEqual(self.redeem(code).status_code, 200)
        with Session(self.engine) as db:
            session = db.query(WidgetSession).filter_by(conversation_id=self.cid).one()
            deadline = session.expires_at
            session.expires_at = int(time.time())
            db.commit()
        self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.redeem(code).status_code, 401)
        with Session(self.engine) as db:
            db.query(WidgetSession).filter_by(conversation_id=self.cid).one().expires_at = deadline
            db.get(Conversation, self.cid).status = 'handoff_requested'
            db.commit()
        response = self.redeem(code)
        self.assertEqual(response.json()['status'], 'handoff_requested')
        with Session(self.engine) as db:
            db.get(Conversation, self.cid).status = 'closed'
            db.commit()
        self.assertEqual(self.redeem(code).status_code, 409)
        self.assertFalse(self.lookup()['found'])
        self.assertEqual(self.client.delete(COOKIE_PATH + '/session').status_code, 200)
        self.assertFalse(self.lookup()['found'])
        self.start(self.client)
        self.assertEqual(self.redeem(code).status_code, 400)

    def test_concurrent_redemption_has_one_winner(self):
        code = self.issue()
        barrier = Barrier(2)
        def redeem(client):
            barrier.wait(timeout=5)
            return self.redeem(code, client).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(redeem, (self.client, self.other)))
        self.assertEqual(sorted(results), [200, 400])
        self.assertEqual(sum(self.lookup(cid)['found'] for cid in (self.cid, self.other_cid)), 1)

    def test_revocation_while_model_waits_blocks_late_order_answer(self):
        self.assertEqual(self.redeem(self.issue()).status_code, 200)
        entered, release = Event(), Event()
        def slow(*args):
            entered.set()
            self.assertTrue(release.wait(8))
            return {'name': 'lookup_order', 'arguments': {'order_id': 'DH12345'}}
        with patch('app.services.message_service.select_order_tool', side_effect=slow), ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(self.client.post, COOKIE_PATH + '/messages', json={
                'content': 'Tra DH12345', 'client_message_id': str(uuid4())})
            self.assertTrue(entered.wait(5))
            try:
                self.assertEqual(self.admin.delete(ACCESS_PATH).status_code, 200)
            finally:
                release.set()
            response = future.result(timeout=5)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['status'], 'handoff_requested')
        self.assertNotIn('PRIVATE-DH12345', response.text)

    def test_additive_migration_preserves_existing_data(self):
        with self.engine.begin() as connection:
            connection.execute(text('DROP TABLE order_access'))
            connection.execute(text('DELETE FROM schema_migrations WHERE version = 6'))
        migrate(self.engine)
        code = self.issue()
        self.redeem(code)
        migrate(self.engine)
        self.assertTrue(self.lookup()['found'])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Order).count(), 2)
            self.assertEqual(db.query(Conversation).count(), 2)


if __name__ == '__main__':
    unittest.main()
