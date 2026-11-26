"""Customer cancels a waiting handoff; staff internal notes and the conversation timeline."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.widget import COOKIE_PATH, _attempts
from app.core.auth import COOKIE_NAME, token_hash
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import AuthSession, ConversationEvent, Ticket, User

INBOX = '/api/v1/inbox/conversations/'


class InboxNotesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'notes.db'), connect_args={'check_same_thread': False})
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        with Session(self.engine) as db:
            db.add_all([User(id=uid, username=uid, display_name=name, role='agent', password_hash='unused')
                        for uid, name in (('lan', 'Chị Lan'), ('minh', 'Anh Minh'))])
            db.flush()
            db.add_all([AuthSession(token_hash=token_hash(uid), user_id=uid, expires_at=int(time.time()) + 300) for uid in ('lan', 'minh')])
            db.commit()

        def db_session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = db_session
        self.addCleanup(app.dependency_overrides.clear)
        _attempts.clear()
        answer = patch('app.services.message_service.answer_question', return_value={'answer': 'Chính sách có nguồn.', 'citations': []})
        answer.start(); self.addCleanup(answer.stop)
        self.customer, self.lan, self.minh = [TestClient(app, headers={'X-CSRF-Protection': '1'}) for _ in range(3)]
        for client in (self.customer, self.lan, self.minh):
            self.addCleanup(client.close)
        self.lan.cookies.set(COOKIE_NAME, 'lan', path='/api')
        self.minh.cookies.set(COOKIE_NAME, 'minh', path='/api')
        self.cid = self.customer.post(COOKIE_PATH + '/session', json={'display_name': 'Khách'}).json()['conversation_id']

    def handoff(self):
        response = self.customer.post(COOKIE_PATH + '/handoff', json={'client_message_id': str(uuid4())})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def kinds(self):
        return [event['kind'] for event in self.lan.get(INBOX + self.cid + '/timeline').json()['events']]

    def test_customer_cancels_waiting_handoff_and_ai_answers_again(self):
        self.assertIsNone(self.customer.get(COOKIE_PATH + '/session').json()['handoff'])
        waiting = self.handoff()
        self.assertEqual(waiting['status'], 'handoff_requested')
        self.assertTrue(waiting['handoff']['can_cancel'])
        self.assertIsNotNone(waiting['handoff']['due_at'])
        cancelled = self.customer.post(COOKIE_PATH + '/handoff/cancel')
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        data = cancelled.json()
        self.assertEqual(data['status'], 'open')
        self.assertIsNone(data['handoff'])
        self.assertIn('hủy yêu cầu gặp nhân viên', data['messages'][-1]['content'])
        with Session(self.engine) as db:
            ticket = db.query(Ticket).filter_by(conversation_id=self.cid).one()
            self.assertEqual((ticket.status, ticket.completed_by_id), ('closed', None))
        self.assertEqual(self.customer.post(COOKIE_PATH + '/handoff/cancel').status_code, 409)
        # The AI answers again after cancelling.
        reply = self.customer.post(COOKIE_PATH + '/messages', json={'content': 'Chính sách đổi trả?', 'client_message_id': str(uuid4())})
        self.assertEqual(reply.json()['messages'][-1]['sender_type'], 'ai')
        self.assertEqual(self.kinds(), ['created', 'handoff_requested', 'handoff_cancelled'])

    def test_accepted_handoff_cannot_be_cancelled_and_timeline_names_the_agent(self):
        self.handoff()
        self.assertEqual(self.lan.post(INBOX + self.cid + '/accept').status_code, 200)
        self.assertIsNone(self.customer.get(COOKIE_PATH + '/session').json()['handoff'])
        self.assertEqual(self.customer.post(COOKIE_PATH + '/handoff/cancel').status_code, 409)
        self.lan.post(INBOX + self.cid + '/messages', json={'content': 'Chào bạn, mình hỗ trợ nhé.'})
        events = self.lan.get(INBOX + self.cid + '/timeline').json()['events']
        self.assertEqual([e['kind'] for e in events], ['created', 'handoff_requested', 'accepted', 'first_response'])
        self.assertEqual(events[2]['actor'], 'Chị Lan')
        self.assertEqual(sorted(e['at'] for e in events), [e['at'] for e in events])

    def test_internal_notes_are_staff_only(self):
        self.handoff()
        # Any staff member may note, even without owning the conversation.
        note = self.minh.post(INBOX + self.cid + '/notes', json={'content': '  Khách VIP, ưu tiên gọi lại  '})
        self.assertEqual(note.status_code, 201, note.text)
        self.assertEqual(note.json()['content'], 'Khách VIP, ưu tiên gọi lại')
        self.assertEqual(self.minh.post(INBOX + self.cid + '/notes', json={'content': '   '}).status_code, 422)
        self.assertEqual(self.minh.post(INBOX + 'missing/notes', json={'content': 'x'}).status_code, 404)
        self.assertEqual(self.customer.post(INBOX + self.cid + '/notes', json={'content': 'x'}).status_code, 401)
        self.assertEqual(self.customer.get(INBOX + self.cid + '/timeline').status_code, 401)
        events = self.lan.get(INBOX + self.cid + '/timeline').json()['events']
        self.assertEqual(events[-1]['kind'], 'note')
        self.assertEqual(events[-1]['actor'], 'Anh Minh')
        # Never in the customer's view, nor in the staff message list that channels deliver from.
        self.assertNotIn('Khách VIP', self.customer.get(COOKIE_PATH + '/session').text)
        self.assertNotIn('Khách VIP', str(self.lan.get(INBOX + self.cid).json()['messages']))
        with Session(self.engine) as db:
            self.assertEqual(db.query(ConversationEvent).count(), 0)


if __name__ == '__main__':
    unittest.main()
