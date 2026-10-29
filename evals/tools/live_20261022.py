import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.auth import require_staff
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import Conversation, Customer, Message, Order, Ticket, User
from app.rag import ollama
from app.rag.vector_store import VectorStore
from app.services.document_service import save_document
from app.services.message_service import process_message

ROOT = Path(__file__).resolve().parents[2]
POLICY = 'Chính sách giao hàng thử nghiệm: Giao hàng tiêu chuẩn trong 3 ngày làm việc kể từ khi xác nhận đơn.'


class LiveFlowTests(unittest.TestCase):
    records = []

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix='tools-live-')))
        self.engine = create_engine('sqlite:///' + str(self.root / 'test.db'), connect_args={'check_same_thread': False})
        self.stack.callback(self.engine.dispose)
        migrate(self.engine)
        self.store = VectorStore(str(self.root / 'vectors'))
        self.stack.callback(self.store.close)
        for target in ('app.rag.answer_service.vector_store', 'app.services.document_service.vector_store'):
            self.stack.enter_context(patch(target, self.store))
        with Session(self.engine) as db:
            db.add_all([Customer(id=name, display_name=name) for name in ('owner', 'other')])
            db.add_all([User(id=name, username=name, display_name=name, role='agent', password_hash='unused')
                        for name in ('agent', 'second')])
            db.flush()
            db.add_all([Order(id='DH78216', customer_id='owner', status='shipped', tracking_code='OWN-TRACK'),
                        Order(id='ORD-93427', customer_id='other', status='paid', tracking_code='OTHER-PRIVATE')])
            db.commit()
            ingestion = save_document(db, 'policy.txt', POLICY.encode('utf-8'), self.root / 'files')
            self.assertEqual(ingestion['status'], 'indexed', ingestion)
        self.staff = 'agent'
        def database():
            with Session(self.engine) as db:
                yield db
        def staff():
            with Session(self.engine) as db:
                return db.get(User, self.staff)
        self.stack.enter_context(patch.dict(app.dependency_overrides, {get_db: database, require_staff: staff}))
        self.client = TestClient(app)
        self.stack.callback(self.client.close)
        self.client.headers['X-CSRF-Protection'] = '1'

    def conversation(self, name, channel='website'):
        with Session(self.engine) as db:
            db.add(Conversation(id=name, customer_id='owner', channel=channel))
            db.commit()

    def send(self, name, query, key=None):
        started = time.perf_counter()
        with Session(self.engine) as db:
            result = process_message(db, db.get(Conversation, name), query, external_message_id=key)
            reply = db.get(Message, result['ai_message_id']) if result.get('ai_message_id') else None
            self.records.append({'test': self.id(), 'conversation': name, 'query': query, 'result': result,
                                 'answer': reply.content if reply else None, 'seconds': time.perf_counter() - started})
            self.assertFalse(result.get('ai_error'), result)
            return result

    def test_rag_handoff_agent_completion_and_reentry(self):
        for channel in ('website', 'telegram'):
            with self.subTest(channel=channel):
                name = channel
                self.conversation(name, channel)
                result = self.send(name, 'Giao hàng tiêu chuẩn trong bao lâu?', 'rag-1')
                self.assertTrue(result['rag']['grounded'], result)
                self.assertTrue(result['rag']['citations'])
                self.assertIn('3 ngày', result['rag']['answer'])
                with patch('app.services.message_service.answer_question', side_effect=AssertionError('Unexpected RAG')):
                    duplicate = self.send(name, 'Giao hàng tiêu chuẩn trong bao lâu?', 'rag-1')
                    self.assertTrue(duplicate['duplicate'])
                    handoff = self.send(name, 'Tôi cần gặp nhân viên, đơn chưa giao.', 'handoff-1')
                    self.assertEqual(handoff['status'], 'handoff_requested')
                    self.assertIsNone(handoff['ai_message_id'])
                    self.send(name, 'Bổ sung: vui lòng gọi lại sau.', 'waiting-1')
                    with Session(self.engine) as db:
                        tickets = db.query(Ticket).filter_by(conversation_id=name).all()
                        self.assertEqual(len(tickets), 1)
                        self.assertIn('Giao hàng tiêu chuẩn', tickets[0].summary)
                        self.assertIn('Tôi cần gặp nhân viên', tickets[0].summary)
                        self.assertNotIn('OTHER-PRIVATE', tickets[0].summary)
                        ticket_id = tickets[0].id
                        self.records.append({'test': self.id(), 'channel': channel, 'summary': tickets[0].summary})
                    path = '/api/v1/inbox/conversations/' + name
                    self.assertEqual(self.client.post(path + '/accept').status_code, 200)
                    self.staff = 'second'
                    self.assertEqual(self.client.post(path + '/accept').status_code, 409)
                    self.assertEqual(self.client.post(path + '/messages', json={'content': 'Unauthorized'}).status_code, 409)
                    self.staff = 'agent'
                    self.assertEqual(self.client.post(path + '/messages', json={'content': 'Nhân viên đã tiếp nhận yêu cầu.'}).status_code, 200)
                    latest = self.send(name, 'Cảm ơn, đây là thông tin bổ sung.', 'assigned-1')
                    self.assertIsNone(latest['ai_message_id'])
                    stale = {'status': 'resolved', 'ticket_id': ticket_id, 'last_customer_message_id': handoff['message_id'], 'note': 'Done'}
                    self.assertEqual(self.client.post(path + '/finish', json=stale).status_code, 409)
                    finish = stale | {'last_customer_message_id': latest['message_id']}
                    self.assertEqual(self.client.post(path + '/finish', json=finish).status_code, 200)
                    self.assertTrue(self.client.post(path + '/finish', json=finish).json()['duplicate'])
                    reopened = self.send(name, 'Tôi cần hỗ trợ thêm.', 'reentry-1')
                    self.assertEqual(reopened['status'], 'handoff_requested')
                    self.assertIsNone(reopened['ai_message_id'])
                    with Session(self.engine) as db:
                        tickets = db.query(Ticket).filter_by(conversation_id=name).all()
                        self.assertEqual(len(tickets), 2)
                        open_ticket = next(ticket for ticket in tickets if ticket.status == 'open')
                        ticket_id = open_ticket.id
                    self.assertEqual(self.client.post(path + '/accept').status_code, 200)
                    self.assertEqual(self.client.post(path + '/messages', json={'content': 'Đã xử lý phần bổ sung.'}).status_code, 200)
                    finish = {'status': 'closed', 'ticket_id': ticket_id, 'last_customer_message_id': reopened['message_id'], 'note': 'Closed'}
                    self.assertEqual(self.client.post(path + '/finish', json=finish).status_code, 200)
                    with Session(self.engine) as db:
                        from fastapi import HTTPException
                        with self.assertRaises(HTTPException) as error:
                            process_message(db, db.get(Conversation, name), 'Không lưu vào hội thoại đã đóng')
                        self.assertEqual(error.exception.status_code, 409)

    def test_real_selector_permissions_and_no_order_mutation(self):
        for name, query, denied in [('owned', 'Tra trạng thái đơn DH78216', False),
                                    ('foreign', 'Tra trạng thái đơn ORD-93427', True),
                                    ('cancel', 'Tra DH78216, nếu chưa giao thì hủy giúp tôi.', True)]:
            with self.subTest(name=name):
                self.conversation(name)
                result = self.send(name, query)
                if denied:
                    self.assertTrue(result['needs_handoff'], result)
                    self.assertNotIn('OTHER-PRIVATE', json.dumps(result))
                else:
                    self.assertTrue(result['order_lookup']['found'], result)
                    self.assertFalse(result['needs_handoff'])
                with Session(self.engine) as db:
                    self.assertEqual(db.get(Order, 'DH78216').status, 'shipped')
                    self.assertEqual(db.get(Order, 'ORD-93427').status, 'paid')

    def test_provider_failure_keeps_customer_message_and_allows_handoff(self):
        self.conversation('failure')
        with patch('app.rag.answer_service.chat', side_effect=ollama.ProviderError('Injected transport failure')):
            with Session(self.engine) as db:
                result = process_message(db, db.get(Conversation, 'failure'), 'Giao hàng tiêu chuẩn trong bao lâu?')
                self.assertTrue(result['ai_error'])
                self.assertIsNone(result['ai_message_id'])
                self.assertIsNotNone(db.get(Message, result['message_id']))
        result = self.send('failure', 'Tôi muốn gặp nhân viên.')
        self.assertTrue(result['needs_handoff'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    load_dotenv(ROOT / '.env', override=False)
    files = [Path(__file__).resolve(), *sorted((ROOT / 'app').rglob('*.py'))]
    manifest = {'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'running',
                'sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                'models': ollama.call('/api/tags')['models'], 'policy': POLICY,
                'limitations': ['Staff authentication dependency supplies fixture users; login is not tested here.',
                                'Telegram channel uses backend only; no Bot API, delivery worker or real device.',
                                'Fault-injection case mocks chat failure; all other model calls are real.',
                                'Summary assertions check excerpts, not independent semantic quality approval.']}
    target = args.output / 'manifest.json'
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveFlowTests))
    (args.output / 'results.json').write_text(json.dumps(LiveFlowTests.records, ensure_ascii=False, indent=2), encoding='utf-8')
    stable = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in manifest['sha256'].items())
    manifest.update(status='passed' if result.wasSuccessful() and stable else 'failed', tests=result.testsRun,
                    failures=len(result.failures), errors=len(result.errors), runtime_unchanged=stable,
                    finished_at=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    if not result.wasSuccessful() or not stable:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
