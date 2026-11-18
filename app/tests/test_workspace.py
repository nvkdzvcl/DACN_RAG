import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.auth import _attempts
from app.core.auth import hash_password, verify_password
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import Conversation, Customer, DocumentChunk, KnowledgeDocument, Message, Order, Ticket, User
from app.rag.answer_service import ABSTENTION, CLARIFICATION


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = 'Workspace-test-password'
        cls.password_hash = hash_password(cls.password)

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'workspace.db'), connect_args={'check_same_thread': False})
        migrate(self.engine)
        with Session(self.engine) as db:
            db.add_all([User(id=role, username=role, display_name=role, role=role, password_hash=self.password_hash) for role in ('admin', 'agent')])
            db.add_all([Customer(id='alice', display_name='Alice', email='alice@example.test'), Customer(id='bob', display_name='Bob')])
            db.flush()
            db.add_all([Order(id='DH12345', customer_id='alice', status='processing'), Conversation(id='chat', customer_id='alice')])
            db.commit()
        def test_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        _attempts.clear()
        self.client = TestClient(app)
        self.addCleanup(directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(app.dependency_overrides.clear)
        self.addCleanup(self.client.close)

    def login(self, role='admin', client=None, password=None):
        client = client or self.client
        client.headers['X-CSRF-Protection'] = '1'
        result = client.post('/api/v1/auth/login', json={'username': role, 'password': password or self.password})
        self.assertEqual(result.status_code, 200, result.text)

    def test_auth_roles_csrf_and_private_fields(self):
        for path in ('customers', 'orders', 'summary', 'settings', 'users'):
            self.assertEqual(self.client.get('/api/v1/workspace/' + path).status_code, 401)
        self.login('agent')
        for path in ('customers', 'orders', 'summary', 'settings'):
            response = self.client.get('/api/v1/workspace/' + path)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertNotIn('password_hash', response.text)
        self.assertEqual(self.client.get('/api/v1/workspace/users').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/workspace/customers', json={'display_name': 'No'}).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/workspace/orders', json={'id': 'DH55555', 'customer_id': 'alice'}).status_code, 403)
        self.assertEqual(self.client.patch('/api/v1/workspace/orders/DH12345', json={'status': 'paid', 'expected': {'status': 'processing'}}).status_code, 403)
        self.assertEqual(self.client.patch('/api/v1/workspace/customers/alice', json={'display_name': 'No', 'expected': {'display_name': 'Alice', 'email': 'alice@example.test'}}).status_code, 403)
        self.login()
        del self.client.headers['X-CSRF-Protection']
        self.assertEqual(self.client.post('/api/v1/workspace/customers', json={'display_name': 'No'}).status_code, 403)
        self.assertNotIn('password_hash', self.client.get('/api/v1/workspace/users').text)

    def test_customers_search_paging_detail_and_conflict(self):
        self.login()
        path = '/api/v1/workspace/customers'
        response = self.client.get(path, params={'q': 'alice', 'limit': 1}).json()
        self.assertEqual(response['total'], 1)
        self.assertEqual(response['items'][0]['order_count'], 1)
        self.assertEqual(response['items'][0]['conversation_count'], 1)
        self.assertEqual(self.client.get(path, params={'offset': 1, 'limit': 1}).json()['items'][0]['id'], 'bob')
        self.assertEqual(self.client.get(path, params={'q': '%'}).json()['total'], 0)
        self.assertEqual(self.client.get(path, params={'limit': 101}).status_code, 422)
        self.assertEqual(self.client.get(path + '/bob').json()['orders'], [])
        self.assertEqual(self.client.get(path + '/missing').status_code, 404)
        self.assertEqual(self.client.post(path, json={'display_name': '  ', 'email': 'bad'}).status_code, 422)
        self.assertEqual(self.client.post(path, json={'display_name': 'New', 'customer_id': 'alice'}).status_code, 422)
        created = self.client.post(path, json={'display_name': ' New customer ', 'email': ''})
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()['display_name'], 'New customer')
        body = {'display_name': 'Alice Updated', 'email': None, 'expected': {'display_name': 'Alice', 'email': 'alice@example.test'}}
        self.assertEqual(self.client.patch(path + '/alice', json=body).status_code, 200)
        self.assertEqual(self.client.patch(path + '/alice', json=body).status_code, 409)
        self.assertEqual(self.client.get(path + '/alice').json()['display_name'], 'Alice Updated')

    def test_order_create_filter_update_conflict_and_owner_immutable(self):
        self.login()
        path = '/api/v1/workspace/orders'
        body = {'id': 'ORD-TEST01', 'customer_id': 'bob', 'status': 'shipping', 'tracking_code': 'VN-000001'}
        self.assertEqual(self.client.post(path, json=body).status_code, 201)
        self.assertEqual(self.client.post(path, json=body).status_code, 409)
        self.assertEqual(self.client.post(path, json=body | {'id': 'ORD-TEST02', 'customer_id': 'missing'}).status_code, 404)
        self.assertEqual(self.client.post(path, json=body | {'id': '../foo'}).status_code, 422)
        self.assertEqual(self.client.get(path, params={'status': 'bad'}).status_code, 422)
        self.assertEqual(self.client.get(path, params={'customer_id': 'bob', 'q': 'VN-', 'status': 'shipping'}).json()['total'], 1)
        edit = {'status': 'delivered', 'tracking_code': 'VN-000002', 'expected': {'status': 'shipping', 'tracking_code': 'VN-000001'}}
        self.assertEqual(self.client.patch(path + '/ORD-TEST01', json=edit | {'customer_id': 'alice'}).status_code, 422)
        self.assertEqual(self.client.patch(path + '/ORD-TEST01', json=edit).status_code, 200)
        self.assertEqual(self.client.patch(path + '/ORD-TEST01', json=edit).status_code, 409)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Order, 'ORD-TEST01').customer_id, 'bob')
            self.assertEqual(db.get(Order, 'ORD-TEST01').tracking_code, 'VN-000002')

    def test_order_id_generated_and_tracking_code_normalized(self):
        self.login()
        path = '/api/v1/workspace/orders'
        created = self.client.post(path, json={'customer_id': 'bob', 'status': 'shipping', 'tracking_code': ' vn 1234 5678 '})
        self.assertEqual(created.status_code, 201)
        order = created.json()
        self.assertRegex(order['id'], r'^DH\d{6}[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{4}$')
        self.assertEqual(order['tracking_code'], 'VN12345678')
        from app.services.order_service import ORDER_PATTERN
        self.assertTrue(ORDER_PATTERN.fullmatch(order['id']), 'generated IDs are recognized in chat')
        self.assertNotEqual(self.client.post(path, json={'customer_id': 'bob'}).json()['id'], order['id'])
        for bad in ['VN-1', '-VN123456', 'VN123456-', 'VN_123456', 'X' * 31]:
            self.assertEqual(self.client.post(path, json={'customer_id': 'bob', 'tracking_code': bad}).status_code, 422, bad)
        self.assertIsNone(self.client.post(path, json={'customer_id': 'bob', 'tracking_code': '   '}).json()['tracking_code'])
        with Session(self.engine) as db:
            db.add(Order(id='ORD-LEGACY1', customer_id='bob', status='processing', tracking_code='old free text'))
            db.commit()
        edit = {'status': 'shipping', 'tracking_code': 'vn-000003', 'expected': {'status': 'processing', 'tracking_code': 'old free text'}}
        updated = self.client.patch(path + '/ORD-LEGACY1', json=edit)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()['tracking_code'], 'VN-000003')

    def test_metrics_cohort_denominator_and_terminal_snapshot(self):
        self.login()
        now = datetime.now(timezone.utc)
        with Session(self.engine) as db:
            db.add(Conversation(id='old', customer_id='bob', created_at=now - timedelta(days=40)))
            db.flush()
            db.add_all([
                Ticket(id='met', conversation_id='chat', status='resolved', created_at=now - timedelta(hours=3), first_response_at=now - timedelta(hours=3) + timedelta(minutes=60)),
                Ticket(id='late', conversation_id='chat', status='resolved', created_at=now - timedelta(hours=2), first_response_at=now - timedelta(hours=2) + timedelta(minutes=61)),
                Ticket(id='pending', conversation_id='chat', created_at=now - timedelta(hours=2)),
                Ticket(id='cancelled', conversation_id='chat', status='closed', created_at=now - timedelta(hours=2)),
                Ticket(id='old', conversation_id='old', status='resolved', created_at=now - timedelta(days=40), first_response_at=now - timedelta(days=40) + timedelta(minutes=1)),
            ])
            db.commit()
        response = self.client.get('/api/v1/workspace/summary?days=7')
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['totals']['conversations'], 2)
        period = result['period']
        self.assertEqual(period['conversations'], 1)
        self.assertEqual(period['tickets'], 4)
        self.assertEqual(period['responded_tickets'], 2)
        self.assertEqual(period['sla_met_percent'], 50)
        self.assertEqual(period['mean_response_minutes'], 60.5)
        self.assertEqual(period['sla']['overdue'], 1)
        self.assertEqual(period['sla']['cancelled'], 1)
        self.assertEqual(sum(d['count'] for d in period['daily']), 1)
        self.assertEqual(len(period['daily']), 7)
        self.assertEqual(self.client.get('/api/v1/workspace/summary?days=90').json()['period']['tickets'], 5)
        self.assertEqual(self.client.get('/api/v1/workspace/summary?days=8').status_code, 422)

    def test_daily_metrics_use_vietnam_calendar_days(self):
        self.login()
        local = timezone(timedelta(hours=7))
        today = datetime.now(timezone.utc).astimezone(local).date()
        midnight = datetime.combine(today, datetime.min.time(), local).astimezone(timezone.utc)
        first_midnight = midnight - timedelta(days=6)
        with Session(self.engine) as db:
            # 00:00 local today is still "yesterday" in UTC; it must count for today.
            db.add_all([Conversation(id='local-midnight', customer_id='bob', created_at=midnight),
                        Conversation(id='first-instant', customer_id='bob', created_at=first_midnight),
                        Conversation(id='just-before', customer_id='bob', created_at=first_midnight - timedelta(seconds=1))])
            db.commit()
        result = self.client.get('/api/v1/workspace/summary?days=7').json()
        daily = result['period']['daily']
        self.assertEqual(result['timezone'], 'Asia/Ho_Chi_Minh')
        self.assertEqual(daily[-1], {'date': today.isoformat(), 'count': 2})  # setUp's chat (now) + local-midnight
        self.assertEqual(daily[0], {'date': (today - timedelta(days=6)).isoformat(), 'count': 1})
        self.assertEqual(result['period']['conversations'], 3)
        self.assertEqual(datetime.fromisoformat(result['start']).astimezone(local).date(), today - timedelta(days=6))

    def test_summary_reports_ai_outcomes_unanswered_questions_and_cited_documents(self):
        self.login()
        now = datetime.now(timezone.utc)
        cite = lambda doc, chunk: {'document_id': doc, 'chunk_id': chunk, 'source': doc + '.md', 'quote': 'q'}
        with Session(self.engine) as db:
            db.add_all([KnowledgeDocument(id='doi-tra', filename='doi-tra.md', status='indexed'),
                        KnowledgeDocument(id='giao-hang', filename='giao-hang.md', status='indexed')])
            db.flush()
            db.add(DocumentChunk(id='doi-tra-1', document_id='doi-tra', chunk_index=0, content='# Chính sách đổi trả', source='doi-tra.md'))
            rows = []
            for i, (question, reply, citations) in enumerate([
                    ('Đổi máy trong 30 ngày?', 'Đổi trả – ...', [cite('doi-tra', 'doi-tra-1'), cite('doi-tra', 'doi-tra-2')]),
                    ('Phí giao hàng?', 'Giao hàng – ...', [cite('giao-hang', 'giao-hang-1')]),
                    ('Shop có bán xe máy không?', ABSTENTION, []),
                    ('shop có bán  XE MÁY không?', ABSTENTION, []),
                    ('Còn laptop thì sao?', CLARIFICATION, []),
                    ('Đổi trả laptop?', 'Đổi trả – ...', [cite('doi-tra', 'doi-tra-1')])]):
                at = now - timedelta(minutes=60 - i)
                rows += [Message(id=f'q{i}', conversation_id='chat', sender_type='customer', content=question, created_at=at),
                         Message(id=f'a{i}', conversation_id='chat', sender_type='ai', content=reply, citations=citations, reply_to_id=f'q{i}', created_at=at)]
            db.add_all(rows)
            db.add(Ticket(id='handoff', conversation_id='chat', created_at=now - timedelta(minutes=5)))
            db.commit()
        period = self.client.get('/api/v1/workspace/summary?days=7').json()['period']
        self.assertEqual(period['ai_outcomes'], {'answered': 3, 'not_answered': 3, 'handoffs': 1})
        unanswered = period['unanswered_questions']
        self.assertEqual([(q['question'], q['count']) for q in unanswered], [('shop có bán  XE MÁY không?', 2), ('Còn laptop thì sao?', 1)])
        self.assertEqual([(d['document_id'], d['title'], d['count']) for d in period['top_documents']],
                         [('doi-tra', 'Chính sách đổi trả', 2), ('giao-hang', None, 1)])

    def test_empty_metrics_do_not_invent_percentages(self):
        self.login()
        period = self.client.get('/api/v1/workspace/summary').json()['period']
        self.assertIsNone(period['sla_met_percent'])
        self.assertIsNone(period['mean_response_minutes'])
        self.assertEqual(period['responded_tickets'], 0)

    def test_password_change_revokes_all_own_sessions_only(self):
        self.login('agent')
        second = TestClient(app)
        self.addCleanup(second.close)
        self.login('agent', second)
        admin = TestClient(app)
        self.addCleanup(admin.close)
        self.login('admin', admin)
        path = '/api/v1/workspace/password'
        body = {'current_password': 'wrong', 'new_password': 'New-workspace-password'}
        self.assertEqual(self.client.post(path, json=body).status_code, 400)
        self.assertEqual(self.client.post(path, json=body | {'current_password': self.password, 'new_password': 'short'}).status_code, 422)
        self.assertEqual(self.client.post(path, json=body | {'current_password': self.password}).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 401)
        self.assertEqual(second.get('/api/v1/auth/me').status_code, 401)
        self.assertEqual(admin.get('/api/v1/auth/me').status_code, 200)
        self.login('agent', password='New-workspace-password')

    def test_login_in_flight_cannot_reissue_session_after_password_change(self):
        self.login('agent')
        other = TestClient(app)
        other.headers['X-CSRF-Protection'] = '1'
        self.addCleanup(other.close)
        entered, release = Event(), Event()
        def delayed(password, encoded):
            valid = verify_password(password, encoded)
            entered.set()
            self.assertTrue(release.wait(8))
            return valid
        with patch('app.api.auth.verify_password', side_effect=delayed), ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(other.post, '/api/v1/auth/login', json={'username': 'agent', 'password': self.password})
            try:
                self.assertTrue(entered.wait(5))
                result = self.client.post('/api/v1/workspace/password', json={
                    'current_password': self.password, 'new_password': 'New-workspace-password'})
                self.assertEqual(result.status_code, 200, result.text)
            finally:
                release.set()
            self.assertEqual(pending.result(5).status_code, 401)
        self.assertEqual(other.get('/api/v1/auth/me').status_code, 401)
        self.login('agent', password='New-workspace-password')


if __name__ == '__main__':
    unittest.main()
