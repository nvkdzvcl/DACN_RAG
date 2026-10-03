import tempfile
import unittest
import json
from datetime import datetime, timedelta, timezone
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.widget import snapshot
from app.api.inbox import conversation_detail
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
            query = 'Không cần gặp nhân viên, tra DH12345.'
            self.assertEqual(select_order_tool(unicodedata.normalize('NFD', query), 'DH12345'), LOOKUP)
            self.assertEqual(json.loads(transport.call_args.args[0][-1]['content'])['request'], query)
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
            internal = conversation_detail('chat', db)
            self.assertEqual(next(m['tool_trace'] for m in internal['messages'] if m['sender_type'] == 'customer'), trace)
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

    def test_malformed_order_token_never_looks_up_its_valid_prefix(self):
        with patch('app.services.message_service.select_order_tool', return_value=LOOKUP) as selector, patch(
                'app.services.message_service.lookup_order') as lookup, patch(
                'app.services.message_service.answer_question', return_value={'answer': 'Thiếu mã đơn hợp lệ.', 'citations': []}):
            for content in ('Tra đơn DH12345-EXTRA', 'Tra đơn x-DH12345', 'Tra đơn DH12345_ABC',
                            'Tra đơn DH1234ı', 'Tra đơn DH' + 'A' * 63):
                result = self.process(content)
                self.assertIsNone(result['order_lookup'])
                with Session(self.engine) as db:
                    self.assertIsNone(db.get(Message, result['message_id']).tool_trace)
                    self.assertNotIn('PRIVATE-TRACK', db.get(Message, result['ai_message_id']).content)
            selector.assert_not_called()
            lookup.assert_not_called()

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

    def test_order_followup_uses_customer_history_and_current_permissions(self):
        with Session(self.engine) as db:
            db.add(Message(id='context', conversation_id='chat', sender_type='customer', content='Tra DH12345'))
            db.commit()
        with patch('app.services.tool_service.chat', return_value=completion()) as model, patch(
                'app.services.message_service.answer_question', return_value={'answer': 'Policy', 'citations': []}):
            result = self.process(unicodedata.normalize('NFD', 'Mã vận đơn của ĐƠN\nĐÓ là gì?'), identity='followup')
            self.assertTrue(result['order_lookup']['found'])
            self.assertTrue(self.process(unicodedata.normalize('NFD', 'Mã vận đơn của ĐƠN\nĐÓ là gì?'), identity='followup')['duplicate'])
            self.assertEqual(model.call_count, 1)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Message, result['message_id']).tool_trace['order_id_source'], 'history')
            self.assertEqual(db.get(Message, result['message_id']).content,
                             unicodedata.normalize('NFD', 'Mã vận đơn của ĐƠN\nĐÓ là gì?'))
            db.get(Order, 'DH12345').customer_id = 'other'
            db.commit()
        with patch('app.services.tool_service.chat', return_value=completion()):
            result = self.process('Đơn đó đang ở đâu?')
        self.assertEqual(result['status'], 'handoff_requested')
        self.assertFalse(result['order_lookup']['found'])
        self.assertIsNone(result['ai_message_id'])

    def test_order_followup_does_not_guess_between_customer_codes(self):
        with Session(self.engine) as db:
            db.add(Message(id='context', conversation_id='chat', sender_type='customer', content='DH12345 và DH99999'))
            db.commit()
        with patch('app.services.tool_service.chat') as model, patch('app.services.message_service.answer_question',
                return_value={'answer': 'Policy', 'citations': []}) as rag:
            result = self.process('Đơn đó đang ở đâu?')
            model.assert_not_called()
            rag.assert_not_called()
        with Session(self.engine) as db:
            self.assertEqual(db.get(Message, result['message_id']).tool_trace['status'], 'clarification')
        with patch('app.services.tool_service.chat', return_value=completion()):
            self.assertTrue(self.process('Đơn đó là DH12345, tra giúp tôi')['order_lookup']['found'])

    def test_order_followup_ignores_ai_other_conversations_and_old_or_malformed_context(self):
        for sender, context, query, expired in [
                ('ai', 'DH12345', 'Đơn đó đang ở đâu?', False),
                ('customer', 'DH12345-EXTRA', 'Đơn đó đang ở đâu?', False),
                ('customer', 'DH12345', 'Đơn đó đang ở đâu?', True),
                ('customer', 'DH12345', 'Chính sách giao hàng là gì?', False),
                ('customer', 'DH12345', 'Tra đơn đó DH99999-EXTRA', False),
                ('customer', 'DH12345', 'Tra đơn đó x-DH99999', False)]:
            with self.subTest(sender=sender, context=context, query=query, expired=expired), Session(self.engine) as db:
                db.query(Message).delete()
                if not db.get(Conversation, 'other-chat'):
                    db.add(Conversation(id='other-chat', customer_id='owner'))
                    db.flush()
                db.add(Message(id='other-context', conversation_id='other-chat', sender_type='customer', content='DH12345'))
                db.add(Message(id='context', conversation_id='chat', sender_type=sender, content=context,
                               created_at=datetime.now(timezone.utc) - timedelta(minutes=10)))
                if expired:
                    db.add_all([Message(id=f'later-{i}', conversation_id='chat', sender_type='ai', content='Nội dung khác')
                                for i in range(4)])
                db.commit()
                with patch('app.services.tool_service.chat') as model, patch('app.services.message_service.answer_question',
                        return_value={'answer': 'Policy', 'citations': []}) as rag:
                    result = self.process(query)
                model.assert_not_called()
                rag.assert_called_once()
                self.assertIsNone(result['order_lookup'])

    def test_tool_selection_releases_lock_and_skips_after_new_message_or_handoff_or_close(self):
        for scenario in ['new_message', 'handoff', 'close', 'owner_change',
                         'history_new_message', 'history_handoff', 'history_close', 'history_owner_change']:
            action = scenario.removeprefix('history_')
            query = 'Đơn đó đang ở đâu?' if scenario.startswith('history_') else 'Đơn DH12345 đang ở đâu?'
            with self.subTest(scenario=scenario), Session(self.engine) as db:
                db.get(Conversation, 'chat').status = 'open'
                db.get(Order, 'DH12345').customer_id = 'owner'
                db.query(Message).delete()
                db.add(Message(id='context', conversation_id='chat', sender_type='customer', content='Tra DH12345'))
                db.commit()
            entered, release = Event(), Event()
            def slow(*args):
                entered.set()
                self.assertTrue(release.wait(8))
                return completion()
            with patch('app.services.tool_service.chat', side_effect=slow), patch(
                    'app.services.message_service.answer_question', return_value={'answer': 'New answer', 'citations': []}), ThreadPoolExecutor(max_workers=2) as pool:
                pending = pool.submit(self.process, query)
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
