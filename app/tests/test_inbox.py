import unittest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.inbox import accept_conversation, add_agent_message, conversation_detail, list_conversations, AgentMessageCreate
from app.db.session import Base
from app.models.support import Conversation, Customer, Message, Ticket, User
from app.services.sla_service import RESPONSE_MINUTES, conversation_sla, ticket_slas


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.db.add_all([Customer(id='a', display_name='Customer A', email='a@example.test'), Customer(id='b', display_name='Customer B')])
        self.user = User(id='agent-1', username='agent-1', display_name='Agent One', password_hash='unused', role='agent')
        self.db.add(self.user)
        self.db.flush()
        self.db.add_all([Conversation(id='first', customer_id='a', status='handoff_requested', priority='high'), Conversation(id='second', customer_id='b')])
        self.db.flush()
        now = datetime.now(timezone.utc)
        self.db.add_all([
            Message(id='later', conversation_id='first', sender_type='ai', content='Reply', created_at=now),
            Message(id='earlier', conversation_id='first', sender_type='customer', content='Question', created_at=now - timedelta(seconds=1)),
            Ticket(id='ticket', conversation_id='first', priority='high', summary='Needs help'),
        ])
        self.db.commit()

    def test_filters_and_customer_name(self):
        result = list_conversations(status='handoff_requested', priority='high', db=self.db)
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['conversations'][0]['customer_name'], 'Customer A')
        self.assertEqual(list_conversations(status='closed', db=self.db)['conversations'], [])

    def test_detail_order_and_customer_isolation(self):
        first = conversation_detail('first', self.db)
        self.assertEqual([m['id'] for m in first['messages']], ['earlier', 'later'])
        self.assertEqual(first['customer_email'], 'a@example.test')
        self.assertEqual(first['tickets'][0]['summary'], 'Needs help')
        second = conversation_detail('second', self.db)
        self.assertEqual(second['customer_name'], 'Customer B')
        self.assertIsNone(second['customer_email'])
        self.assertEqual(second['messages'], [])
        self.assertEqual(second['tickets'], [])

    def test_missing_conversation(self):
        with self.assertRaises(HTTPException) as error:
            conversation_detail('missing', self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_accept_and_agent_reply(self):
        accepted = accept_conversation('first', self.db, self.user)
        self.assertEqual(accepted['status'], 'assigned')
        self.assertEqual(accepted['ticket_ids'], ['ticket'])
        reply = add_agent_message('first', AgentMessageCreate(content='Đã kiểm tra, tôi sẽ hỗ trợ ngay.'), self.db, self.user)
        self.assertEqual(reply['sender_type'], 'agent')
        with self.assertRaises(HTTPException) as error:
            add_agent_message('second', AgentMessageCreate(content='Không được gửi trước khi nhận.'), self.db, self.user)
        self.assertEqual(error.exception.status_code, 409)

    def test_sla_deadline_acceptance_and_sender_isolation(self):
        started = datetime(2026, 9, 14, 0, 0, tzinfo=timezone.utc)
        self.db.get(Ticket, 'ticket').created_at = started
        self.db.add_all([
            Message(id='old-staff', conversation_id='first', sender_type='agent', agent_id=self.user.id, content='Old', created_at=started - timedelta(seconds=1)),
            Message(id='other-staff', conversation_id='second', sender_type='agent', agent_id=self.user.id, content='Other', created_at=started + timedelta(seconds=1)),
            Message(id='fake-staff', conversation_id='first', sender_type='agent', content='No authenticated staff', created_at=started + timedelta(seconds=1)),
            Message(id='ai-after', conversation_id='first', sender_type='ai', content='AI is not staff', created_at=started + timedelta(seconds=2)),
        ])
        self.db.commit()
        due = started + timedelta(minutes=15)
        self.assertEqual(ticket_slas(self.db, ['first'], due)['ticket']['status'], 'on_track')
        accept_conversation('first', self.db, self.user)
        late = ticket_slas(self.db, ['first'], due + timedelta(microseconds=1))['ticket']
        self.assertEqual(late['status'], 'overdue')
        self.assertEqual(late['due_at'], due.isoformat())
        self.assertIsNone(late['responded_at'])
        self.assertEqual(ticket_slas(self.db, ['second'], due), {})
        for priority, minutes in RESPONSE_MINUTES.items():
            self.db.get(Ticket, 'ticket').priority = priority
            self.db.flush()
            self.assertEqual(ticket_slas(self.db, ['first'], started)['ticket']['due_at'], (started + timedelta(minutes=minutes)).isoformat())

    def test_sla_first_reply_boundary_late_and_cancelled(self):
        started = datetime(2026, 9, 14, 0, 0, tzinfo=timezone.utc)
        self.db.get(Ticket, 'ticket').created_at = started
        due = started + timedelta(minutes=15)
        reply = Message(id='staff-first', conversation_id='first', sender_type='agent', agent_id=self.user.id, content='First response', created_at=due)
        self.db.add(reply)
        self.db.add(Message(id='staff-later', conversation_id='first', sender_type='agent', agent_id=self.user.id, content='Later', created_at=due + timedelta(hours=1)))
        self.db.commit()
        result = ticket_slas(self.db, ['first'], due + timedelta(days=1))['ticket']
        self.assertEqual(result['status'], 'met')
        self.assertEqual(result['responded_at'], due.isoformat())
        reply.created_at = due + timedelta(microseconds=1)
        self.db.commit()
        self.assertEqual(ticket_slas(self.db, ['first'])['ticket']['status'], 'breached')
        self.db.get(Ticket, 'ticket').status = 'closed'
        self.db.commit()
        self.assertEqual(ticket_slas(self.db, ['first'])['ticket']['status'], 'breached')
        self.db.query(Message).filter(Message.sender_type == 'agent').delete()
        self.db.commit()
        self.assertEqual(ticket_slas(self.db, ['first'])['ticket']['status'], 'cancelled')

    def test_sla_filters_and_earliest_pending_ticket(self):
        now = datetime.now(timezone.utc)
        self.db.get(Ticket, 'ticket').created_at = now - timedelta(minutes=20)
        self.db.add(Ticket(id='new-ticket', conversation_id='first', priority='normal', created_at=now))
        self.db.commit()
        slas = list(ticket_slas(self.db, ['first'], now).values())
        self.assertEqual(conversation_sla(slas)['ticket_id'], 'ticket')
        self.assertEqual(list_conversations(db=self.db, sla='overdue')['count'], 1)
        self.assertEqual(list_conversations(db=self.db, sla='on_track')['count'], 0)
        self.assertEqual(list_conversations(db=self.db, sla='none')['conversations'][0]['conversation_id'], 'second')
        self.assertEqual(conversation_detail('first', self.db)['sla']['status'], 'overdue')
        self.assertEqual(len(conversation_detail('first', self.db)['tickets']), 2)
        self.db.get(Conversation, 'first').status = 'closed'
        self.db.commit()
        self.assertEqual(list_conversations(db=self.db, sla='cancelled')['count'], 1)
        self.assertEqual(list_conversations(db=self.db, sla='overdue')['count'], 0)


if __name__ == '__main__':
    unittest.main()
