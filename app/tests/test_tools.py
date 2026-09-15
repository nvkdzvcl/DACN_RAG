import tempfile
import unittest
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.widget import snapshot
from app.db.migrations import migrate
from app.models.support import Conversation, Customer, Message, Order, Ticket, WidgetSession
from app.rag.ollama import ProviderError
from app.services.message_service import process_message
from app.services.tool_service import select_order_tool

LOOKUP = {'name': 'lookup_order', 'arguments': {'order_id': 'DH12345'}}


def completion(function=LOOKUP):
    return json.dumps(function)


class ToolTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'tools.db'),
                                    connect_args={'check_same_thread': False, 'timeout': 10})
        self.addCleanup(directory.cleanup)
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        with Session(self.engine) as db:
            db.add_all([Customer(id='owner', display_name='Owner'), Customer(id='other', display_name='Other')])
            db.flush()
            db.add_all([Conversation(id='chat', customer_id='owner'),
                        Order(id='DH12345', customer_id='owner', status='shipped', tracking_code='PRIVATE-TRACK'),
                        Order(id='DH99999', customer_id='other', status='paid', tracking_code='OTHER-TRACK')])
            db.commit()

    def process(self, content='Đơn DH12345 đang ở đâu?', identity=None):
        with Session(self.engine) as db:
            return process_message(db, db.get(Conversation, 'chat'), content, identity)

    def test_structured_tool_schema_rejects_forgery_and_malformed_calls(self):
        with patch('app.services.tool_service.chat', return_value=completion()) as transport:
            self.assertEqual(select_order_tool('Track DH12345', 'DH12345'), LOOKUP)
            schema = transport.call_args.args[1]
            self.assertEqual(schema['properties']['arguments']['properties']['order_id']['enum'], ['DH12345'])
            self.assertNotIn('customer_id', str(schema))
        for invalid in [completion({'name': 'delete_order', 'arguments': {}}),
                        completion({'name': 'lookup_order', 'arguments': {'order_id': 'DH99999'}}),
                        completion({'name': 'lookup_order', 'arguments': {'order_id': 'DH12345', 'customer_id': 'other'}}),
                        completion({'name': 'handoff', 'arguments': {'url': 'https://example.com'}}),
                        completion({'name': 'lookup_order', 'arguments': '{"order_id":"DH12345"}'}),
                        completion(LOOKUP | {'customer_id': 'other'}), completion(LOOKUP | {'name': []}),
                        'null', '[]', '{}', 'invalid JSON', None]:
            with self.subTest(invalid=invalid), patch('app.services.tool_service.chat', return_value=invalid), self.assertRaises(ProviderError):
                select_order_tool('Track DH12345', 'DH12345')

    def test_owned_lookup_is_deterministic_private_and_idempotent(self):
        with patch('app.services.tool_service.chat', return_value=completion()) as transport:
            result = self.process(identity='retry')
            self.assertTrue(result['order_lookup']['found'])
            self.assertTrue(self.process(identity='retry')['duplicate'])
            self.assertEqual(transport.call_count, 1)
        with Session(self.engine) as db:
            ai = db.query(Message).filter_by(sender_type='ai').one()
            self.assertEqual(ai.content, 'Đơn hàng DH12345: shipped. Mã vận đơn: PRIVATE-TRACK.')
            trace = db.query(Message).filter_by(sender_type='customer').one().tool_trace
            self.assertEqual(trace['outcome'], 'found')
            self.assertNotIn('PRIVATE-TRACK', str(trace))
            public = snapshot(db, WidgetSession(conversation_id='chat', expires_at=9999999999))
            self.assertNotIn('tool_trace', str(public))

    def test_denied_missing_and_changed_owner_never_disclose_order(self):
        for customer in ['other', 'missing']:
            with self.subTest(customer=customer), Session(self.engine) as db:
                db.get(Conversation, 'chat').status = 'open'
                if customer == 'missing':
                    db.delete(db.get(Order, 'DH12345'))
                else:
                    db.get(Order, 'DH12345').customer_id = customer
                db.commit()
            with patch('app.services.tool_service.chat', return_value=completion()):
                result = self.process()
            self.assertEqual(result['status'], 'handoff_requested')
            self.assertFalse(result['order_lookup']['found'])
            self.assertIsNone(result['ai_message_id'])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Ticket).count(), 1)
            self.assertEqual(db.query(Message).filter_by(sender_type='ai').count(), 0)

    def test_no_call_falls_back_and_ambiguity_or_rules_skip_model(self):
        with patch('app.services.tool_service.chat', return_value=completion(LOOKUP | {'name': 'rag'})), patch(
                'app.services.message_service.answer_question', return_value={'answer': 'Policy only', 'citations': []}) as rag:
            result = self.process('Chính sách bảo hành áp dụng đơn DH12345 thế nào?')
            self.assertIsNone(result['order_lookup'])
            self.assertEqual(rag.call_count, 1)
        with patch('app.services.tool_service.chat') as model:
            self.process('Tra DH12345 và DH99999')
            self.assertEqual(self.process('gặp nhân viên')['status'], 'handoff_requested')
            self.process()
            model.assert_not_called()

    def test_explicit_tool_handoff_provider_and_database_failures_preserve_inbound(self):
        with patch('app.services.tool_service.chat', side_effect=ProviderError('Offline')):
            self.assertEqual(self.process()['ai_error'], 'Offline')
        with patch('app.services.tool_service.chat', return_value=completion()), patch(
                'app.services.message_service.lookup_order', side_effect=SQLAlchemyError('Unavailable')), self.assertLogs(
                'app.services.message_service', level='ERROR'), self.assertRaises(HTTPException) as error:
            self.process()
        self.assertEqual(error.exception.status_code, 503)
        with patch('app.services.tool_service.chat', return_value=completion(LOOKUP | {'name': 'handoff'})):
            self.assertEqual(self.process('Hủy đơn DH12345')['status'], 'handoff_requested')
        with Session(self.engine) as db:
            traces = [m.tool_trace['status'] for m in db.query(Message).filter_by(sender_type='customer').order_by(Message.created_at)]
            self.assertEqual(traces, ['provider_error', 'pending', 'executed'])
            self.assertEqual(db.query(Message).filter_by(sender_type='ai').count(), 0)

    def test_tool_selection_releases_lock_and_skips_after_new_message_or_handoff_or_close(self):
        for action in ['new_message', 'handoff', 'close', 'owner_change']:
            with self.subTest(action=action), Session(self.engine) as db:
                db.get(Conversation, 'chat').status = 'open'
                db.get(Order, 'DH12345').customer_id = 'owner'
                db.commit()
            entered, release = Event(), Event()
            def slow(*args):
                entered.set()
                self.assertTrue(release.wait(8))
                return completion()
            with patch('app.services.tool_service.chat', side_effect=slow), patch(
                    'app.services.message_service.answer_question', return_value={'answer': 'New answer', 'citations': []}), ThreadPoolExecutor(max_workers=2) as pool:
                pending = pool.submit(self.process)
                self.assertTrue(entered.wait(5))
                try:
                    if action in {'new_message', 'handoff'}:
                        pool.submit(self.process, 'gặp nhân viên' if action == 'handoff' else 'New question').result(3)
                    else:
                        with Session(self.engine) as db:
                            if action == 'close':
                                db.execute(update(Conversation).where(Conversation.id == 'chat').values(status='closed'))
                            else:
                                db.get(Order, 'DH12345').customer_id = 'other'
                            db.commit()
                finally:
                    release.set()
                result = pending.result(5)
                self.assertIsNone(result['ai_message_id'])
                self.assertNotIn('PRIVATE-TRACK', str(result))
                with Session(self.engine) as db:
                    trace = db.get(Message, result['message_id']).tool_trace
                    self.assertEqual(trace['status'], 'executed' if action == 'owner_change' else 'skipped')


if __name__ == '__main__':
    unittest.main()
