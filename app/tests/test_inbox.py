import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.inbox import accept_conversation, add_agent_message, conversation_detail, list_conversations, AgentMessageCreate
from app.db.session import Base
from app.models.support import Conversation, Customer, Message, Ticket, User
from app.services.sla_service import RESPONSE_MINUTES, conversation_sla, ticket_slas
from app.services.ticket_service import complete_tickets


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

    def test_pagination_bounds_sla_work_and_orders_equal_timestamps(self):
        created = datetime.now(timezone.utc) + timedelta(days=1)
        self.db.add_all([Conversation(id=f'page-{i:03}', customer_id='a', created_at=created) for i in range(55)])
        self.db.commit()
        with patch('app.api.inbox.ticket_slas', wraps=ticket_slas) as slas:
            first = list_conversations(db=self.db)
            self.assertEqual(len(slas.call_args.args[1]), 25)
        second = list_conversations(db=self.db, offset=25)
        last = list_conversations(db=self.db, offset=50)
        self.assertEqual((first['count'], first['total'], first['has_more']), (25, 57, True))
        self.assertEqual([c['conversation_id'] for c in first['conversations']], [f'page-{i:03}' for i in range(25)])
        ids = [c['conversation_id'] for page in (first, second, last) for c in page['conversations']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual((last['count'], last['has_more']), (7, False))
        outside = list_conversations(db=self.db, offset=1000)
        self.assertEqual((outside['count'], outside['total'], outside['has_more']), (0, 57, False))

    def test_search_and_sla_filter_before_pagination_across_batches(self):
        created = datetime.now(timezone.utc) + timedelta(days=1)
        self.db.get(Customer, 'a').display_name = 'ĐẶNG 100%_'
        self.db.add_all([Conversation(id=f'page-{i:03}', customer_id='a', channel='telegram',
                                     status='handoff_requested', priority='high', created_at=created) for i in range(205)])
        self.db.flush()
        self.db.add_all([Ticket(id=f'sla-{i}', conversation_id=f'page-{i:03}', priority='high',
                               created_at=created - timedelta(days=2)) for i in range(195, 205)])
        self.db.commit()
        with patch('app.api.inbox.ticket_slas', wraps=ticket_slas) as slas:
            result = list_conversations(db=self.db, q='đặng 100%_', sla='overdue',
                                        status='handoff_requested', priority='high', offset=7, limit=2)
            self.assertTrue(all(len(call.args[1]) <= 200 for call in slas.call_args_list))
        self.assertEqual((result['count'], result['total'], result['has_more']), (2, 10, True))
        self.assertEqual([c['conversation_id'] for c in result['conversations']], ['page-202', 'page-203'])
        self.assertEqual(list_conversations(db=self.db, q='  TELEGRAM ', sla='none')['total'], 195)
        self.assertEqual(list_conversations(db=self.db, q='%_')['total'], 206)
        self.assertEqual(list_conversations(db=self.db, q='no match')['total'], 0)
        self.assertEqual(list_conversations(db=self.db, q='b website')['total'], 1)

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

    def test_message_pages_cover_tied_timestamps_without_skips_or_duplicates(self):
        created = datetime.now(timezone.utc) + timedelta(days=1)
        self.db.add_all([Message(id=f'page-{i:03}', conversation_id='second', sender_type='customer',
                                 content=f'Message {i}', created_at=created) for i in range(123)])
        self.db.commit()
        latest = conversation_detail('second', self.db)
        self.assertEqual([m['id'] for m in latest['messages']], [f'page-{i:03}' for i in range(73, 123)])
        self.assertEqual(latest['message_page'], {'limit': 50, 'before': None, 'has_more': True, 'next_before': 'page-073'})
        # New arrivals must not move a cursor anchored in the older history.
        self.db.add(Message(id='newest', conversation_id='second', sender_type='customer', content='New arrival',
                            created_at=created + timedelta(seconds=1)))
        self.db.commit()
        middle = conversation_detail('second', self.db, before=latest['message_page']['next_before'])
        oldest = conversation_detail('second', self.db, before=middle['message_page']['next_before'])
        ids = [m['id'] for page in (oldest, middle, latest) for m in page['messages']]
        self.assertEqual(ids, [f'page-{i:03}' for i in range(123)])
        self.assertEqual(oldest['message_page'], {'limit': 50, 'before': 'page-023', 'has_more': False, 'next_before': None})
        self.assertEqual(conversation_detail('second', self.db, limit=1)['messages'][0]['id'], 'newest')

    def test_message_cursor_is_scoped_and_page_refreshes_mutable_fields(self):
        for before in ('missing', 'earlier'):
            with self.subTest(before=before), self.assertRaises(HTTPException) as error:
                conversation_detail('second', self.db, before=before)
            self.assertEqual(error.exception.status_code, 404)
        page = conversation_detail('first', self.db, before='later', limit=1)
        self.assertEqual([m['id'] for m in page['messages']], ['earlier'])
        self.db.get(Message, 'earlier').tool_trace = {'status': 'provider_error'}
        self.db.commit()
        refreshed = conversation_detail('first', self.db, before='later', limit=1)
        self.assertEqual(refreshed['messages'][0]['tool_trace'], {'status': 'provider_error'})
        self.assertEqual(refreshed['tickets'], page['tickets'])
        empty = conversation_detail('first', self.db, before='earlier')
        self.assertEqual(empty['messages'], [])
        self.assertFalse(empty['message_page']['has_more'])

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
        complete_tickets(self.db, 'first', 'closed', self.user.id, 'Done')
        self.db.commit()
        self.assertEqual(ticket_slas(self.db, ['first'])['ticket']['status'], 'breached')
        self.db.query(Message).filter(Message.sender_type == 'agent').delete()
        self.db.add(Ticket(id='unanswered', conversation_id='first', priority='high'))
        self.db.flush()
        complete_tickets(self.db, 'first', 'closed')
        self.db.commit()
        self.assertEqual(ticket_slas(self.db, ['first'])['ticket']['status'], 'breached')
        self.assertEqual(ticket_slas(self.db, ['first'])['unanswered']['status'], 'cancelled')

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
