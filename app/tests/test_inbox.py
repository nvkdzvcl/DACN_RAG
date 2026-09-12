import unittest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.inbox import accept_conversation, add_agent_message, conversation_detail, list_conversations, AgentMessageCreate
from app.db.session import Base
from app.models.support import Conversation, Customer, Message, Ticket


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.db.add_all([Customer(id='a', display_name='Customer A', email='a@example.test'), Customer(id='b', display_name='Customer B')])
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
        accepted = accept_conversation('first', 'agent-1', self.db)
        self.assertEqual(accepted['status'], 'assigned')
        self.assertEqual(accepted['ticket_ids'], ['ticket'])
        reply = add_agent_message('first', AgentMessageCreate(content='Đã kiểm tra, tôi sẽ hỗ trợ ngay.', agent_id='agent-1'), self.db)
        self.assertEqual(reply['sender_type'], 'agent')
        with self.assertRaises(HTTPException) as error:
            add_agent_message('second', AgentMessageCreate(content='Không được gửi trước khi nhận.', agent_id='agent-1'), self.db)
        self.assertEqual(error.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
