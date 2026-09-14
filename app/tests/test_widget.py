import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.widget import COOKIE, COOKIE_PATH, _answer_slot, _attempts
from app.core.auth import COOKIE_NAME, token_hash
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, Conversation, Customer, Message, Order, Ticket, User, WidgetSession
from app.rag.ollama import ProviderError


class WidgetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.directory.name) / 'widget.db'),
                                    connect_args={'check_same_thread': False, 'timeout': 10})
        migrate(self.engine)
        def test_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        _attempts.clear()
        self.client = TestClient(app, headers={'X-CSRF-Protection': '1'})
        self.other = TestClient(app, headers={'X-CSRF-Protection': '1'})
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.client.close)
        self.addCleanup(self.other.close)

    def start(self, client=None, name='Khach thu'):
        response = (client or self.client).post(COOKIE_PATH + '/session', json={'display_name': name})
        self.assertEqual(response.status_code, 201, response.text)
        return response

    def send(self, content='Policy?', client=None, identity=None):
        return (client or self.client).post(COOKIE_PATH + '/messages', json={
            'content': content, 'client_message_id': identity or str(uuid4())})

    def staff(self):
        with Session(self.engine) as db:
            db.add(User(id='staff', username='staff', display_name='Agent', role='agent', password_hash='unused'))
            db.flush()
            db.add(AuthSession(token_hash=token_hash('staff-token'), user_id='staff', expires_at=int(time.time()) + 300))
            db.commit()
        self.other.cookies.set(COOKIE_NAME, 'staff-token', path='/api')

    def test_session_isolation_csrf_and_forged_fields(self):
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 401)
        self.client.headers.pop('X-CSRF-Protection')
        self.assertEqual(self.client.post(COOKIE_PATH + '/session', json={'display_name': 'Name'}).status_code, 403)
        self.client.headers['X-CSRF-Protection'] = '1'
        for payload in [{'display_name': ' '}, {'display_name': 'Name', 'customer_id': 'victim'}, {'display_name': 'N' * 81}]:
            self.assertEqual(self.client.post(COOKIE_PATH + '/session', json=payload).status_code, 422)
        first = self.start()
        self.assertIn('HttpOnly', first.headers['set-cookie'])
        self.assertIn('SameSite=strict', first.headers['set-cookie'])
        self.assertIn('Path=' + COOKIE_PATH, first.headers['set-cookie'])
        self.assertEqual(first.headers['cache-control'], 'no-store')
        cid = first.json()['conversation_id']
        self.assertEqual(self.start().json()['conversation_id'], cid)
        second = self.start(self.other).json()
        self.assertNotEqual(second['conversation_id'], cid)
        self.assertEqual(self.other.get(COOKIE_PATH + '/session', params={'conversation_id': cid}).json()['conversation_id'], second['conversation_id'])
        self.assertEqual(self.client.get('/api/v1/inbox/conversations').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/documents').status_code, 401)
        for extra in [{'conversation_id': second['conversation_id']}, {'sender_type': 'agent'}, {'customer_id': 'victim'}]:
            response = self.client.post(COOKIE_PATH + '/messages', json={'content': 'Hi', 'client_message_id': str(uuid4()), **extra})
            self.assertEqual(response.status_code, 422)
        with Session(self.engine) as db:
            self.assertNotEqual(db.query(WidgetSession).first().token_hash, self.client.cookies.get(COOKIE))
            self.assertNotEqual(db.get(Conversation, cid).customer_id, db.get(Conversation, second['conversation_id']).customer_id)
        self.client.headers.pop('X-CSRF-Protection')
        self.assertEqual(self.send().status_code, 403)

    def test_message_retry_public_payload_and_provider_failure(self):
        cid = self.start().json()['conversation_id']
        identity = str(uuid4())
        answer = {'answer': 'The policy says no.', 'grounded': False, 'citations': [
            {'source': 'policy.txt', 'quote': 'Policy excerpt.', 'page': None, 'location': 'Line 1', 'document_id': 'internal-id'}],
            'results': [{'content': 'Private retrieval context'}]}
        with patch('app.services.message_service.answer_question', return_value=answer) as rag:
            result = self.send(identity=identity)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertNotIn('Private retrieval context', result.text)
            self.assertNotIn('internal-id', result.text)
            self.assertNotIn('tickets', result.json())
            self.assertEqual(len(result.json()['messages']), 2)
            self.assertTrue(self.send(identity=identity).json()['duplicate'])
            self.assertEqual(self.send('Changed', identity=identity).status_code, 409)
            self.assertEqual(rag.call_count, 1)
        with patch('app.services.message_service.answer_question', side_effect=ProviderError('Offline')):
            result = self.send('Second message')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['ai_error'], 'Offline')
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).filter_by(conversation_id=cid, sender_type='customer').count(), 2)
        self.assertEqual(self.send(' ').status_code, 422)
        self.assertEqual(self.send(identity='invalid').status_code, 422)

    def test_handoff_agent_reply_end_and_expired_sessions(self):
        cid = self.start().json()['conversation_id']
        self.staff()
        identity = str(uuid4())
        with patch('app.services.message_service.answer_question') as rag:
            first = self.client.post(COOKIE_PATH + '/handoff', json={'client_message_id': identity})
            self.assertEqual(first.json()['status'], 'handoff_requested')
            self.client.post(COOKIE_PATH + '/handoff', json={'client_message_id': identity})
            self.assertEqual(self.other.post(f'/api/v1/inbox/conversations/{cid}/accept').status_code, 200)
            self.assertEqual(self.other.post(f'/api/v1/inbox/conversations/{cid}/messages', json={'content': 'Hello from staff'}).status_code, 200)
            self.assertEqual(self.send('More information').json()['status'], 'assigned')
            rag.assert_not_called()
        detail = self.client.get(COOKIE_PATH + '/session').json()
        self.assertIn('Hello from staff', str(detail['messages']))
        with Session(self.engine) as db:
            self.assertEqual(db.query(Ticket).filter_by(conversation_id=cid).count(), 1)
            self.assertEqual(db.query(Message).filter_by(conversation_id=cid, external_message_id=identity).count(), 1)
        token = self.client.cookies.get(COOKIE)
        self.assertEqual(self.client.delete(COOKIE_PATH + '/session').status_code, 200)
        self.client.cookies.set(COOKIE, token, path=COOKIE_PATH)
        self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 401)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Conversation, cid).status, 'closed')
            self.assertEqual(db.query(Ticket).filter_by(conversation_id=cid).one().status, 'closed')
        new = self.start().json()['conversation_id']
        self.assertNotEqual(new, cid)
        with Session(self.engine) as db:
            db.query(WidgetSession).update({'expires_at': int(time.time()) - 1})
            db.commit()
        self.assertEqual(self.send('Expired').status_code, 401)

    def test_unverified_name_cannot_claim_existing_order(self):
        with Session(self.engine) as db:
            db.add(Customer(id='victim', display_name='Khach thu'))
            db.flush()
            db.add(Order(id='DH12345', customer_id='victim', status='shipped', tracking_code='PRIVATE-TRACKING'))
            db.commit()
        self.start()
        with patch('app.services.message_service.answer_question') as rag:
            result = self.send('Don DH12345?')
            self.assertEqual(result.json()['status'], 'handoff_requested')
            self.assertNotIn('PRIVATE-TRACKING', result.text)
            rag.assert_not_called()

    def test_rate_limit_capacity_and_handoff_during_generation(self):
        cid = self.start().json()['conversation_id']
        entered, release = Event(), Event()
        def slow(*args, **kwargs):
            self.assertFalse(kwargs['db'].in_transaction())
            entered.set()
            self.assertTrue(release.wait(8))
            return {'answer': 'Late AI', 'grounded': False, 'citations': []}
        with patch('app.services.message_service.answer_question', side_effect=slow), ThreadPoolExecutor(max_workers=2) as pool:
            pending = pool.submit(self.send)
            self.assertTrue(entered.wait(5))
            try:
                self.assertEqual(self.send('Another question').status_code, 429)
                handoff = self.client.post(COOKIE_PATH + '/handoff', json={'client_message_id': str(uuid4())})
                self.assertEqual(handoff.json()['status'], 'handoff_requested')
            finally:
                release.set()
            response = pending.result(timeout=5)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertNotIn('Late AI', response.text)
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).filter_by(conversation_id=cid, sender_type='ai').count(), 0)
            self.assertEqual(db.query(Message).filter_by(conversation_id=cid, sender_type='customer').count(), 2)
        self.assertTrue(_answer_slot.acquire(blocking=False))
        _answer_slot.release()
        _attempts.clear()
        for _ in range(6):
            self.start()
        response = self.client.post(COOKIE_PATH + '/session', json={'display_name': 'Name'})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers['retry-after'], '60')

    def test_end_session_during_generation_prevents_late_disclosure(self):
        cid = self.start().json()['conversation_id']
        entered, release = Event(), Event()
        def slow(*args, **kwargs):
            entered.set(); self.assertTrue(release.wait(8))
            return {'answer': 'Late AI', 'grounded': False, 'citations': []}
        with patch('app.services.message_service.answer_question', side_effect=slow), ThreadPoolExecutor(max_workers=2) as pool:
            pending = pool.submit(self.send)
            self.assertTrue(entered.wait(5))
            try:
                self.assertEqual(self.client.delete(COOKIE_PATH + '/session').status_code, 200)
            finally:
                release.set()
            self.assertEqual(pending.result(timeout=5).status_code, 401)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Conversation, cid).status, 'closed')
            self.assertEqual(db.query(Message).filter_by(conversation_id=cid, sender_type='ai').count(), 0)


if __name__ == '__main__':
    unittest.main()
