import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.auth import _attempts
from app.api.inbox import accept_conversation
from app.core.auth import COOKIE_NAME, hash_password, verify_password
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, Conversation, Customer, Message, Ticket, User
from app.services.message_service import process_message


class AuthHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = 'Testing-password-2026'
        cls.password_hash = hash_password(cls.password)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.directory.name) / 'test.db'), connect_args={'check_same_thread': False, 'timeout': 10})
        migrate(self.engine)
        with Session(self.engine) as db:
            db.add_all([User(id=name, username=name, display_name=name, role='admin' if name == 'admin' else 'agent', password_hash=self.password_hash) for name in ('admin', 'one', 'two')])
            db.add(Customer(id='customer', display_name='Test customer'))
            db.flush()
            db.add(Conversation(id='chat', customer_id='customer'))
            db.commit()
        def test_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        _attempts.clear()
        self.client = TestClient(app)  # No lifespan: migrations use only the isolated test DB.
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.client.close)

    def login(self, name='one', client=None):
        client = client or self.client
        client.headers['X-CSRF-Protection'] = '1'
        result = client.post('/api/v1/auth/login', json={'username': name, 'password': self.password})
        self.assertEqual(result.status_code, 200, result.text)
        return result

    def test_password_and_cookie_session_lifecycle(self):
        self.assertTrue(verify_password(self.password, self.password_hash))
        self.assertFalse(verify_password('incorrect', self.password_hash))
        self.assertFalse(verify_password(self.password, 'broken'))
        result = self.login()
        self.assertIn('HttpOnly', result.headers['set-cookie'])
        self.assertIn('SameSite=strict', result.headers['set-cookie'])
        self.assertNotIn('password_hash', result.json())
        token = self.client.cookies.get(COOKIE_NAME)
        with Session(self.engine) as db:
            self.assertNotEqual(db.query(AuthSession).one().token_hash, token)
        self.assertEqual(self.client.get('/api/v1/auth/me').json()['id'], 'one')
        self.assertEqual(self.client.post('/api/v1/auth/logout').status_code, 200)
        self.client.cookies.set(COOKIE_NAME, token)
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)

    def test_expired_and_disabled_sessions(self):
        self.login()
        with Session(self.engine) as db:
            db.query(AuthSession).update({'expires_at': int(time.time()) - 1})
            db.commit()
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)
        self.login()
        with Session(self.engine) as db:
            db.get(User, 'one').active = False
            db.commit()
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)

    def test_auth_roles_csrf_and_forged_agent(self):
        self.assertEqual(self.client.get('/api/v1/inbox/conversations').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/documents/chat/chunks').status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={'username': 'one', 'password': self.password}).status_code, 403)
        self.login()
        self.assertEqual(self.client.post('/api/v1/demo/seed').status_code, 403)
        payload = {'username': 'new', 'password': self.password, 'display_name': 'New agent'}
        self.assertEqual(self.client.post('/api/v1/auth/users', json=payload).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/messages', json={'content': 'Hi', 'agent_id': 'admin'}).status_code, 422)
        self.client.headers.pop('X-CSRF-Protection')
        self.assertEqual(self.client.post('/api/v1/conversations/chat/process', json={'content': 'Hello'}).status_code, 403)
        self.login('admin')
        self.assertEqual(self.client.post('/api/v1/auth/users', json=payload).status_code, 201)
        self.assertEqual(self.client.post('/api/v1/auth/users', json=payload).status_code, 409)

    def test_login_errors_and_rate_limit(self):
        self.client.headers['X-CSRF-Protection'] = '1'
        for _ in range(10):
            self.assertEqual(self.client.post('/api/v1/auth/login', json={'username': 'missing', 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={'username': 'one', 'password': self.password}).status_code, 429)

    def test_api_flow_persists_ai_and_stops_on_handoff(self):
        self.login()
        created = self.client.post('/api/v1/conversations', json={'customer_id': 'customer', 'channel': 'website'})
        self.assertEqual(created.status_code, 200, created.text)
        self.assertTrue(created.json()['conversation_id'])
        answer = {'answer': 'Grounded answer', 'citations': [{'source': 'policy.pdf', 'chunk_id': '1'}]}
        with patch('app.services.message_service.answer_question', return_value=answer) as rag:
            response = self.client.post('/api/v1/conversations/chat/messages', json={'content': 'Policy question', 'external_message_id': 'event-1'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()['ai_message_id'])
            duplicate = self.client.post('/api/v1/conversations/chat/messages', json={'content': 'Policy question', 'external_message_id': 'event-1'})
            self.assertTrue(duplicate.json()['duplicate'])
            for endpoint in ('process', 'messages'):
                response = self.client.post('/api/v1/conversations/chat/' + endpoint, json={'content': 'Tôi muốn gặp nhân viên'})
                self.assertEqual(response.json()['status'], 'handoff_requested')
                self.assertIsNone(response.json()['rag'])
            accepted = self.client.post('/api/v1/inbox/conversations/chat/accept?agent_id=admin')
            self.assertEqual(accepted.status_code, 200, accepted.text)
            self.assertEqual(accepted.json()['agent_id'], 'one')
            response = self.client.post('/api/v1/conversations/chat/process', json={'content': 'Tôi khiếu nại đơn ORD-DEMO01'})
            self.assertEqual(response.json()['status'], 'assigned')
            self.assertIsNone(response.json()['order_lookup'])
            self.assertEqual(rag.call_count, 1)
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/messages', json={'content': '   '}).status_code, 422)
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/messages', json={'content': 'Staff reply'}).status_code, 200)
        detail = self.client.get('/api/v1/inbox/conversations/chat').json()
        self.assertEqual(len(detail['tickets']), 1)
        self.assertIn('Policy question', detail['tickets'][0]['summary'])
        self.assertEqual(detail['messages'][1]['citations'], answer['citations'])
        self.assertEqual(detail['messages'][-1]['agent_id'], 'one')
        self.login('two')
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/accept').status_code, 409)
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/messages', json={'content': 'Wrong owner'}).status_code, 409)

    def test_closed_and_blank_input(self):
        self.login()
        self.assertEqual(self.client.post('/api/v1/conversations/chat/process', json={'content': '   '}).status_code, 422)
        self.assertEqual(self.client.post('/api/v1/inbox/conversations/chat/accept').status_code, 409)
        with Session(self.engine) as db:
            db.get(Conversation, 'chat').status = 'closed'
            db.commit()
        self.assertEqual(self.client.post('/api/v1/conversations/chat/process', json={'content': 'Hi'}).status_code, 409)
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).count(), 0)

    def test_manual_ticket_does_not_invent_customer_messages(self):
        self.login()
        first = self.client.post('/api/v1/conversations/chat/tickets')
        second = self.client.post('/api/v1/conversations/chat/tickets')
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()['ticket_id'], second.json()['ticket_id'])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).count(), 0)
            self.assertEqual(db.get(Conversation, 'chat').status, 'handoff_requested')

    def test_two_agents_race_to_accept(self):
        with Session(self.engine) as db:
            db.get(Conversation, 'chat').status = 'handoff_requested'
            db.commit()
        barrier = Barrier(2)
        def accept(name):
            with Session(self.engine) as db:
                user = db.get(User, name)
                barrier.wait(timeout=5)
                try:
                    return accept_conversation('chat', db, user)['agent_id']
                except HTTPException as exc:
                    return exc.status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(accept, ['one', 'two']))
        self.assertEqual(results.count(409), 1)
        with Session(self.engine) as db:
            self.assertIn(db.get(Conversation, 'chat').assigned_agent_id, results)

    def test_inflight_message_then_handoff_remains_silent(self):
        entered, release = Event(), Event()
        def answer(_, **kwargs):
            entered.set()
            self.assertTrue(release.wait(5))
            return {'answer': 'Earlier answer', 'citations': []}
        def process(content):
            with Session(self.engine) as db:
                return process_message(db, db.get(Conversation, 'chat'), content)
        with patch('app.services.message_service.answer_question', side_effect=answer) as rag:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(process, 'Question')
                self.assertTrue(entered.wait(5))
                handoff = pool.submit(process, 'gặp nhân viên')
                try:
                    self.assertEqual(handoff.result(timeout=3)['status'], 'handoff_requested')
                    with Session(self.engine) as db:
                        accept_conversation('chat', db, db.get(User, 'one'))
                finally:
                    release.set()
                result = first.result(timeout=10)
                self.assertEqual(result['status'], 'assigned')
                self.assertIsNone(result['rag'])
                self.assertIsNone(result['ai_message_id'])
            self.assertIsNone(process('Another question')['rag'])
            self.assertEqual(rag.call_count, 1)
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).filter_by(sender_type='ai').count(), 0)

    def test_migration_preserves_legacy_records_and_is_repeatable(self):
        legacy = create_engine('sqlite://')
        self.addCleanup(legacy.dispose)
        with legacy.begin() as connection:
            connection.execute(text('CREATE TABLE conversations (id VARCHAR PRIMARY KEY, status VARCHAR)'))
            connection.execute(text("INSERT INTO conversations VALUES ('old', 'assigned')"))
            connection.execute(text('CREATE TABLE messages (id VARCHAR PRIMARY KEY, content TEXT, conversation_id VARCHAR, sender_type VARCHAR, agent_id VARCHAR, created_at TIMESTAMP)'))
            connection.execute(text("INSERT INTO messages (id, content) VALUES ('message', 'Keep this content')"))
            connection.execute(text("INSERT INTO messages VALUES ('reply', 'Legacy reply', 'old', 'agent', 'one', '2026-09-14 00:01:00.000000')"))
            connection.execute(text('CREATE TABLE tickets (id VARCHAR PRIMARY KEY, conversation_id VARCHAR, status VARCHAR, priority VARCHAR, summary TEXT, created_at TIMESTAMP)'))
            connection.execute(text("INSERT INTO tickets VALUES ('answered', 'old', 'closed', 'high', 'Keep summary', '2026-09-14 00:00:00.000000'), ('unanswered', 'old', 'resolved', 'high', 'No reply', '2026-09-14 01:00:00.000000')"))
        migrate(legacy)
        with legacy.begin() as connection:
            connection.execute(text("INSERT INTO messages VALUES ('future', 'Later cycle', 'old', 'agent', 'one', '2026-09-14 02:00:00.000000', NULL)"))
        migrate(legacy)
        with legacy.connect() as connection:
            self.assertEqual(connection.execute(text('SELECT status, assigned_agent_id FROM conversations')).one(), ('handoff_requested', None))
            self.assertEqual(connection.execute(text("SELECT content FROM messages WHERE id = 'message'")).scalar(), 'Keep this content')
            self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM schema_migrations')).scalar(), 4)
            self.assertEqual(connection.execute(text("SELECT first_response_at FROM tickets WHERE id = 'answered'")).scalar(), '2026-09-14 00:01:00.000000')
            self.assertIsNone(connection.execute(text("SELECT first_response_at FROM tickets WHERE id = 'unanswered'")).scalar())
            self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM tickets WHERE completed_at IS NOT NULL OR completed_by_id IS NOT NULL')).scalar(), 0)


if __name__ == '__main__':
    unittest.main()
