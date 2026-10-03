import os
import subprocess
import sys
import tempfile
import time
import unittest
from io import StringIO
from getpass import GetPassWarning
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.api.auth import _attempts
from app.api.inbox import accept_conversation
from app.core.auth import COOKIE_NAME, hash_password, verify_password
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, Conversation, Customer, Message, Ticket, User
from app.reset_password import main as reset_password
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

    def reset(self, username='ADMIN', passwords=None):
        self.reset_output = StringIO()
        with patch('sys.argv', ['reset_password', username]), \
                patch('app.reset_password.getpass', side_effect=passwords or ['New-password-2026'] * 2), \
                patch('app.db.session.SessionLocal', sessionmaker(bind=self.engine)), \
                patch('sys.stdout', self.reset_output), patch('sys.stderr', self.reset_output):
            reset_password()

    def test_password_reset_revokes_only_target_sessions_and_preserves_account(self):
        self.login('admin')
        other = TestClient(app)
        agent = TestClient(app)
        self.addCleanup(other.close)
        self.addCleanup(agent.close)
        self.login('admin', other)
        self.login('one', agent)
        self.reset()
        self.assertIn('Password reset: admin', self.reset_output.getvalue())
        self.assertNotIn('New-password-2026', self.reset_output.getvalue())
        for client in (self.client, other):
            self.assertEqual(client.get('/api/v1/auth/me').status_code, 401)
        self.assertEqual(agent.get('/api/v1/auth/me').status_code, 200)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={
            'username': 'admin', 'password': self.password}).status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={
            'username': 'admin', 'password': 'New-password-2026'}).status_code, 200)
        with Session(self.engine) as db:
            user = db.get(User, 'admin')
            self.assertEqual((user.username, user.role, user.display_name, user.active), ('admin', 'admin', 'admin', True))
            self.assertEqual(db.query(User).count(), 3)

    def test_password_reset_keeps_disabled_agent_disabled(self):
        with Session(self.engine) as db:
            db.get(User, 'one').active = False
            db.commit()
        self.reset('one')
        with Session(self.engine) as db:
            user = db.get(User, 'one')
            self.assertFalse(user.active)
            self.assertEqual(user.role, 'agent')
            self.assertTrue(verify_password('New-password-2026', user.password_hash))
        self.client.headers['X-CSRF-Protection'] = '1'
        self.assertEqual(self.client.post('/api/v1/auth/login', json={
            'username': 'one', 'password': 'New-password-2026'}).status_code, 401)

    def test_password_reset_rejects_invalid_input_without_changes(self):
        self.login('admin')
        for name, passwords in [('missing', ['New-password-2026'] * 2), ('bad user', ['New-password-2026'] * 2),
                                ('admin', ['short'] * 2), ('admin', ['x' * 129] * 2),
                                ('admin', ['New-password-2026', 'Mismatch-password']), ('admin', [self.password] * 2)]:
            with self.subTest(username=name, length=len(passwords[0])):
                with self.assertRaises(SystemExit) as error:
                    self.reset(name, passwords)
                self.assertEqual(error.exception.code, 2)
                self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 200)
                with Session(self.engine) as db:
                    self.assertEqual(db.get(User, 'admin').password_hash, self.password_hash)
                    self.assertEqual(db.query(User).count(), 3)
        for failure in (EOFError, KeyboardInterrupt, GetPassWarning):
            with self.assertRaises(SystemExit) as error:
                self.reset(passwords=failure)
            self.assertEqual(error.exception.code, 1)

    def test_password_reset_rolls_back_if_session_revocation_fails(self):
        self.login('admin')
        def fail_delete(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('DELETE FROM auth_sessions'):
                raise SQLAlchemyError('Injected failure')
        event.listen(self.engine, 'before_cursor_execute', fail_delete)
        try:
            with self.assertRaises(SystemExit) as error:
                self.reset()
            self.assertEqual(error.exception.code, 1)
        finally:
            event.remove(self.engine, 'before_cursor_execute', fail_delete)
        self.assertNotIn('Injected failure', self.reset_output.getvalue())
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 200)
        with Session(self.engine) as db:
            self.assertEqual(db.get(User, 'admin').password_hash, self.password_hash)

    def test_login_in_flight_cannot_issue_session_after_local_password_reset(self):
        entered, release = Event(), Event()
        self.client.headers['X-CSRF-Protection'] = '1'
        def delayed(password, encoded):
            valid = verify_password(password, encoded)
            entered.set()
            self.assertTrue(release.wait(10))
            return valid
        with patch('app.api.auth.verify_password', side_effect=delayed), ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(self.client.post, '/api/v1/auth/login', json={'username': 'admin', 'password': self.password})
            try:
                self.assertTrue(entered.wait(5))
                self.reset()
            finally:
                release.set()
            self.assertEqual(pending.result(timeout=10).status_code, 401)
        with Session(self.engine) as db:
            self.assertEqual(db.query(AuthSession).count(), 0)

    def test_password_reset_loads_explicit_env_before_database_and_respects_override(self):
        config = Path(self.directory.name) / 'recovery.env'
        config.write_text(f'DATABASE_URL={self.engine.url}\n', encoding='utf-8')
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
        environment.pop('DATABASE_URL', None)
        for password in ('First-recovery-2026', 'Second-recovery-2026'):
            code = f'from app import reset_password as cli; cli.getpass = lambda prompt: {password!r}; cli.main()'
            result = subprocess.run([sys.executable, '-c', code, 'admin', '--env-file', str(config)],
                                    cwd=self.directory.name, env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            with Session(self.engine) as db:
                self.assertTrue(verify_password(password, db.get(User, 'admin').password_hash))
            environment['DATABASE_URL'] = str(self.engine.url)
            config.write_text('DATABASE_URL=sqlite:///missing/no.db\n', encoding='utf-8')

    def test_inbox_pagination_validates_bounds_and_requires_staff(self):
        endpoint = '/api/v1/inbox/conversations'
        self.assertEqual(self.client.get(endpoint, params={'limit': 1}).status_code, 401)
        self.login()
        for params in ({'limit': 0}, {'limit': 101}, {'offset': -1}, {'offset': 2**63}, {'limit': 'bad'}, {'q': 'x' * 161}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(endpoint, params=params).status_code, 422)
        result = self.client.get(endpoint, params={'q': 'Test customer', 'limit': 1}).json()
        self.assertEqual((result['count'], result['total'], result['offset'], result['limit']), (1, 1, 0, 1))
        self.assertFalse(result['has_more'])

    def test_message_pagination_validates_bounds_and_requires_staff(self):
        endpoint = '/api/v1/inbox/conversations/chat'
        self.assertEqual(self.client.get(endpoint).status_code, 401)
        self.login()
        for params in ({'limit': 0}, {'limit': 101}, {'limit': 'bad'}, {'before': ''}, {'before': 'x' * 65}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(endpoint, params=params).status_code, 422)
        self.assertEqual(self.client.get(endpoint, params={'before': 'unknown'}).status_code, 404)
        page = self.client.get(endpoint, params={'limit': 100}).json()
        self.assertEqual(page['messages'], [])
        self.assertEqual(page['message_page'], {'limit': 100, 'before': None, 'has_more': False, 'next_before': None})

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
            connection.execute(text("INSERT INTO messages (id, content, conversation_id, sender_type, agent_id, created_at) VALUES ('future', 'Later cycle', 'old', 'agent', 'one', '2026-09-14 02:00:00.000000')"))
            connection.execute(text("UPDATE messages SET tool_trace = '{\"status\": \"pending\"}' WHERE id = 'future'"))
            # Existing v7 stores created before the load fix have no composite indexes.
            connection.execute(text('DROP INDEX ix_messages_conversation_created_id'))
            connection.execute(text('DROP INDEX ix_tickets_conversation_created'))
        migrate(legacy)
        with legacy.connect() as connection:
            self.assertEqual(connection.execute(text('SELECT status, assigned_agent_id FROM conversations')).one(), ('handoff_requested', None))
            self.assertEqual(connection.execute(text("SELECT content FROM messages WHERE id = 'message'")).scalar(), 'Keep this content')
            self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM schema_migrations')).scalar(), 8)
            plan = connection.execute(text("EXPLAIN QUERY PLAN SELECT id FROM messages WHERE conversation_id = 'old' ORDER BY created_at, id")).all()
            self.assertTrue(any('ix_messages_conversation_created_id' in row[-1] for row in plan))
            plan = connection.execute(text("EXPLAIN QUERY PLAN SELECT id FROM tickets WHERE conversation_id = 'old' ORDER BY created_at")).all()
            self.assertTrue(any('ix_tickets_conversation_created' in row[-1] for row in plan))
            self.assertIsNone(connection.execute(text("SELECT tool_trace FROM messages WHERE id = 'message'")).scalar())
            self.assertEqual(connection.execute(text("SELECT tool_trace FROM messages WHERE id = 'future'")).scalar(), '{"status": "pending"}')
            self.assertEqual(connection.execute(text("SELECT first_response_at FROM tickets WHERE id = 'answered'")).scalar(), '2026-09-14 00:01:00.000000')
            self.assertIsNone(connection.execute(text("SELECT first_response_at FROM tickets WHERE id = 'unanswered'")).scalar())
            self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM tickets WHERE completed_at IS NOT NULL OR completed_by_id IS NOT NULL')).scalar(), 0)


if __name__ == '__main__':
    unittest.main()
