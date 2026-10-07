import tempfile
import unittest
import unicodedata
from datetime import timedelta
from http.client import BadStatusLine, IncompleteRead
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from threading import Event
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.inbox import (AgentMessageCreate, RetryDelivery, accept_conversation,
                           add_agent_message, conversation_detail, retry_delivery)
from app.db.migrations import migrate
from app.models.support import (Conversation, Customer, Message, TelegramCursor,
    TelegramDelivery, TelegramPeer, TelegramUpdate, Ticket, User, now_utc)
from app.services.sla_service import ticket_slas
from app.services.handoff_service import queue_handoff
from app.services.message_service import process_message
from app.telegram import (TelegramError, persist_updates, process_next, queue_outgoing,
                         recover_sends, run_telegram, send_outgoing, start_telegram, telegram_call, telegram_status)


def incoming(update_id=1, chat_id=100, content='Chính sách đổi trả?'):
    return {'update_id': update_id, 'message': {'message_id': update_id + 1,
        'chat': {'id': chat_id, 'type': 'private'},
        'from': {'id': chat_id, 'is_bot': False, 'first_name': 'Same name'}, 'text': content}}


class TelegramTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(directory.name) / 'telegram.db'),
                                    connect_args={'check_same_thread': False, 'timeout': 2})
        self.addCleanup(directory.cleanup)
        self.addCleanup(self.engine.dispose)
        migrate(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.db.add(Customer(id='website', display_name='Same name'))
        self.db.add_all([User(id=uid, username=uid, display_name=uid, role='agent', password_hash='unused') for uid in ('agent', 'other')])
        self.db.commit()
        answer = patch('app.services.message_service.answer_question', return_value={
            'answer': 'Chính sách có nguồn.', 'citations': [{'source':'policy.pdf','location':'Trang 1'}]})
        self.answer = answer.start()
        self.addCleanup(answer.stop)

    def receive(self, *items, bot_id='42'):
        persist_updates(self.db, bot_id, list(items))
        while process_next(self.db, bot_id):
            pass
        return self.db.query(Conversation).filter_by(channel='telegram').order_by(Conversation.created_at).all()

    def test_identity_scoped_to_bot_and_user_and_receipt_is_durable(self):
        persist_updates(self.db, '42', [incoming(), incoming()])
        self.db.close()
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.assertEqual(self.db.get(TelegramCursor, '42').next_update_id, 2)
        self.assertTrue(process_next(self.db, '42'))
        persist_updates(self.db, '42', [incoming()])
        self.assertFalse(process_next(self.db, '42'))
        self.receive(incoming(2, 101))
        self.receive(incoming(), bot_id='43')
        peers = self.db.query(TelegramPeer).all()
        self.assertEqual(len(peers), 3)
        self.assertEqual(len({p.customer_id for p in peers}), 3)
        self.assertNotIn('website', {p.customer_id for p in peers})
        self.assertEqual(self.db.query(Message).filter_by(sender_type='customer').count(), 3)

    def test_unicode_handoff_preserves_text_and_receipt_deduplication(self):
        content = unicodedata.normalize('NFD', 'Tôi cần gặp\u00a0nhân viên.')
        chats = self.receive(incoming(content=content))
        self.assertEqual(chats[0].status, 'handoff_requested')
        self.receive(incoming(content=content))
        self.answer.assert_not_called()
        self.assertEqual(self.db.query(Ticket).count(), 1)
        message = self.db.query(Message).filter_by(sender_type='customer').one()
        self.assertEqual(message.content, content)

    def test_private_only_and_invalid_inputs_do_not_advance_cursor(self):
        group = incoming(1)
        group['message']['chat']['type'] = 'group'
        mismatch = incoming(2)
        mismatch['message']['from']['id'] = 999
        edited = {'update_id':3, 'edited_message':incoming()['message']}
        persist_updates(self.db, '42', [group, mismatch, edited])
        self.assertEqual(self.db.query(TelegramPeer).count(), 0)
        self.assertEqual(self.db.get(TelegramCursor, '42').next_update_id, 4)
        for bad in [{'update_id':True}, {'update_id':-1}, {'update_id':'4'}]:
            with self.assertRaises(TelegramError):
                persist_updates(self.db, '42', [bad])
        self.assertEqual(self.db.get(TelegramCursor, '42').next_update_id, 4)
        media = incoming(4)
        del media['message']['text']
        chats = self.receive(media)
        self.assertEqual(chats[0].status, 'handoff_requested')
        self.answer.assert_not_called()

    def test_start_handoff_and_closed_chat_new_conversation(self):
        chat = self.receive(incoming(content='/start'))[0]
        self.answer.assert_not_called()
        self.receive(incoming(2, content='/human'))
        self.assertEqual(chat.status, 'handoff_requested')
        agent = self.db.get(User, 'agent')
        accept_conversation(chat.id, self.db, agent)
        self.receive(incoming(3, content='Thông tin thêm'))
        self.answer.assert_not_called()
        chat.status = 'closed'
        self.db.commit()
        chats = self.receive(incoming(4))
        self.assertEqual(len(chats), 2)
        self.assertEqual(chats[0].status, 'closed')
        self.assertEqual(chats[0].customer_id, chats[1].customer_id)
        self.receive(incoming(1))
        self.assertEqual(self.db.query(Conversation).count(), 2)
        self.assertEqual(self.answer.call_count, 1)

    def test_restart_after_inbound_commit_hands_off_without_regenerating(self):
        chat = self.receive(incoming())[0]
        message = self.db.query(Message).filter_by(sender_type='ai').one()
        self.db.delete(message)
        self.db.get(TelegramUpdate, '42:1').state = 'processing'
        self.db.commit()
        process_next(self.db, '42')
        self.assertEqual(self.answer.call_count, 1)
        self.assertEqual(self.db.query(Message).filter_by(sender_type='customer').count(), 1)
        self.assertEqual(chat.status, 'handoff_requested')
        self.assertEqual(self.db.get(TelegramUpdate, '42:1').state, 'done')

    def test_handoff_notice_survives_restart_after_message_commit(self):
        persist_updates(self.db, '42', [incoming(content='/human')])

        def interrupt_after_commit(*args):
            process_message(*args)
            raise RuntimeError('simulated worker interruption')

        with patch('app.telegram.process_message', side_effect=interrupt_after_commit):
            with self.assertRaisesRegex(RuntimeError, 'simulated worker interruption'):
                process_next(self.db, '42')
        self.db.close()
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        self.assertEqual(self.db.query(Conversation).one().status, 'handoff_requested')
        self.assertEqual(self.db.get(TelegramUpdate, '42:1').state, 'processing')
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 1)
        process_next(self.db, '42')
        self.receive(incoming(2, content='Thông tin thêm'), incoming(3, content='/human'))
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 1)
        self.assertEqual(self.db.query(Ticket).count(), 1)
        self.answer.assert_not_called()
        with patch('app.telegram.telegram_call', return_value={'message_id': 888}) as call:
            send_outgoing(self.db, '42', 'test-token')
            send_outgoing(self.db, '42', 'test-token')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(self.db.query(TelegramDelivery).one().state, 'sent')

    def test_handoff_notice_rolls_back_and_new_round_gets_new_notice(self):
        chat = self.receive(incoming())[0]
        queue_handoff(self.db, chat)
        queue_handoff(self.db, chat)
        self.db.flush()
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 1)
        self.db.rollback()
        self.assertEqual(chat.status, 'open')
        self.assertEqual(self.db.query(Ticket).count(), 0)
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 0)
        self.receive(incoming(2, content='/human'))
        chat.status = 'resolved'
        self.db.query(Ticket).one().status = 'resolved'
        self.db.commit()
        self.receive(incoming(3, content='Cần hỗ trợ thêm'))
        self.assertEqual(chat.status, 'handoff_requested')
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 2)
        self.assertEqual(self.db.query(Ticket).count(), 2)

    def test_start_racing_staff_close_moves_to_new_conversation(self):
        persist_updates(self.db, '42', [incoming(content='/start')])
        commit = self.db.commit
        closed = []
        def close_after_commit():
            commit()
            if not closed:
                with Session(self.engine) as other:
                    chat = other.query(Conversation).one()
                    chat.status = 'closed'
                    closed.append(chat.id)
                    other.commit()
        with patch.object(self.db, 'commit', side_effect=close_after_commit):
            process_next(self.db, '42')
        self.assertEqual(self.db.query(Message).count(), 0)
        process_next(self.db, '42')
        self.assertEqual(self.db.query(Conversation).count(), 2)
        self.assertTrue(all(m.conversation_id != closed[0] for m in self.db.query(Message).all()))

    def test_recovery_of_closed_chat_does_not_block_later_updates(self):
        chat = self.receive(incoming())[0]
        chat.status = 'closed'
        self.db.get(TelegramUpdate, '42:1').state = 'processing'
        self.db.commit()
        chats = self.receive(incoming(2))
        self.assertEqual(len(chats), 2)
        self.assertEqual(self.db.get(TelegramUpdate, '42:1').state, 'done')
        self.assertEqual(self.answer.call_count, 2)

    def test_send_success_no_duplicate_and_no_transaction_during_http(self):
        chat = self.receive(incoming())[0]
        def send(token, method, payload):
            self.assertEqual(method, 'sendMessage')
            self.assertEqual(payload['chat_id'], '100')
            self.assertIn('Nguồn: policy.pdf', payload['text'])
            self.assertNotIn('parse_mode', payload)
            with Session(self.engine) as other:
                other.add(Customer(id='network-write', display_name='No lock'))
                other.commit()
            return {'message_id':888}
        with patch('app.telegram.telegram_call', side_effect=send) as call:
            send_outgoing(self.db, '42', 'test-token')
            send_outgoing(self.db, '42', 'test-token')
        self.assertEqual(call.call_count, 1)
        delivery = self.db.query(TelegramDelivery).one()
        self.assertEqual(delivery.state, 'sent')
        self.assertEqual(delivery.external_message_id, '888')
        detail = conversation_detail(chat.id, self.db)
        self.assertEqual(detail['messages'][-1]['delivery']['state'], 'sent')

    def test_failure_uncertain_blocks_order_and_requires_assigned_retry(self):
        chat = self.receive(incoming(content='/human'))[0]
        agent = self.db.get(User, 'agent')
        accept_conversation(chat.id, self.db, agent)
        with patch('app.telegram.telegram_call', side_effect=TelegramError('timeout', True)) as call:
            send_outgoing(self.db, '42', 'test-token')
            delivery = self.db.query(TelegramDelivery).one()
            add_agent_message(chat.id, AgentMessageCreate(content='Staff reply'), self.db, agent)
            send_outgoing(self.db, '42', 'test-token')
            self.assertEqual(call.call_count, 1)
        self.assertEqual(delivery.state, 'uncertain')
        with self.assertRaises(HTTPException) as error:
            retry_delivery(delivery.message_id, RetryDelivery(), self.db, self.db.get(User,'other'))
        self.assertEqual(error.exception.status_code, 403)
        with self.assertRaises(HTTPException) as error:
            retry_delivery(delivery.message_id, RetryDelivery(), self.db, agent)
        self.assertEqual(error.exception.status_code, 409)
        self.db.rollback()
        retry_delivery(delivery.message_id, RetryDelivery(action='skip'), self.db, agent)
        with patch('app.telegram.telegram_call', return_value={'message_id':1000}) as call:
            send_outgoing(self.db, '42', 'test-token')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(self.db.get(TelegramDelivery, delivery.message_id).state, 'skipped')

    def test_recovery_marks_inflight_uncertain_and_ai_is_cancelled_after_handoff(self):
        chat = self.receive(incoming())[0]
        queue_outgoing(self.db, '42')
        delivery = self.db.query(TelegramDelivery).one()
        delivery.state = 'sending'
        self.db.commit()
        recover_sends(self.db, '42')
        recover_sends(self.db, '42')
        self.assertEqual(self.db.query(Message).filter_by(sender_type='system').count(), 1)
        self.assertEqual(delivery.state, 'uncertain')
        with patch('app.telegram.telegram_call') as call:
            send_outgoing(self.db, '42', 'test-token')
            call.assert_not_called()
        delivery.state = 'pending'
        chat.status = 'handoff_requested'
        self.db.commit()
        with patch('app.telegram.telegram_call') as call:
            send_outgoing(self.db, '42', 'test-token')
            call.assert_not_called()
        self.assertEqual(delivery.state, 'skipped')

    def test_sla_counts_telegram_ack_not_local_queue_time(self):
        chat = self.receive(incoming(content='/human'))[0]
        agent = self.db.get(User,'agent')
        accept_conversation(chat.id, self.db, agent)
        reply = add_agent_message(chat.id, AgentMessageCreate(content='Reply'), self.db, agent)
        ticket = self.db.query(Ticket).one()
        self.assertIsNone(ticket_slas(self.db,[chat.id])[ticket.id]['responded_at'])
        queue_outgoing(self.db,'42')
        delivery = self.db.get(TelegramDelivery, reply['message_id'])
        delivery.state, delivery.sent_at = 'sent', now_utc() + timedelta(minutes=16)
        self.db.commit()
        self.assertEqual(ticket_slas(self.db,[chat.id])[ticket.id]['status'], 'breached')

    def test_new_received_update_suppresses_queued_ai_before_dispatch(self):
        persist_updates(self.db,'42',[incoming(),incoming(2,content='/human')])
        process_next(self.db,'42')
        with patch('app.telegram.telegram_call') as call:
            send_outgoing(self.db,'42','test-token')
            call.assert_not_called()
        self.assertEqual(self.db.query(TelegramDelivery).one().state,'skipped')
        process_next(self.db,'42')
        self.assertEqual(self.db.query(Conversation).one().status,'handoff_requested')

    def test_agent_retry_reuses_message_and_confirmed_delivery_retry(self):
        chat = self.receive(incoming(content='/human'))[0]
        agent = self.db.get(User,'agent')
        accept_conversation(chat.id, self.db, agent)
        payload = AgentMessageCreate(content='Reply', client_message_id=uuid4())
        first = add_agent_message(chat.id, payload, self.db, agent)
        self.assertEqual(add_agent_message(chat.id, payload, self.db, agent)['message_id'], first['message_id'])
        queue_outgoing(self.db,'42')
        delivery = self.db.get(TelegramDelivery,first['message_id'])
        delivery.state = 'uncertain'
        self.db.commit()
        retry_delivery(delivery.message_id, RetryDelivery(confirm_uncertain=True), self.db, agent)
        self.assertEqual(delivery.state,'pending')
        with self.assertRaises(HTTPException):
            add_agent_message(chat.id, AgentMessageCreate(content='Changed',client_message_id=payload.client_message_id), self.db,agent)

    def test_worker_polling_uses_committed_offset_and_never_removes_webhook(self):
        stop = Event()
        calls = []
        def call(token, method, payload):
            calls.append(method)
            if method == 'getMe': return {'id':42,'is_bot':True}
            if method == 'getWebhookInfo': return {'url':''}
            if method == 'sendMessage': return {'message_id':77}
            if payload['offset'] == 0: return [incoming(content='/start')]
            with Session(self.engine) as db:
                self.assertEqual(db.get(TelegramUpdate,'42:1').state,'done')
            stop.set()
            return []
        with patch('app.telegram.SessionLocal',side_effect=lambda:Session(self.engine)), patch('app.telegram.telegram_call',side_effect=call):
            run_telegram(stop,'test-token')
        self.assertEqual(calls, ['getMe','getWebhookInfo','getUpdates','sendMessage','getUpdates'])
        self.assertEqual(self.db.query(TelegramDelivery).one().state,'sent')
        with patch('app.telegram.telegram_call', side_effect=[{'id':42,'is_bot':True},{'url':'https://existing.example/webhook'}]) as call:
            run_telegram(Event(),'test-token')
            self.assertEqual(call.call_count,2)
        self.assertEqual(telegram_status()['detail'],'telegram_webhook_active')

    def test_poll_failure_does_not_block_committed_incoming_queue(self):
        persist_updates(self.db, '42', [incoming(content='/human'), incoming(2, chat_id=101)])
        self.db.get(TelegramUpdate, '42:2').state = 'processing'
        self.db.commit()
        stop = Event()
        polls, waits, sends = [], [], []

        def call(token, method, payload):
            if method == 'getMe': return {'id': 42, 'is_bot': True}
            if method == 'getWebhookInfo': return {'url': ''}
            if method == 'sendMessage':
                sends.append(payload)
                return {'message_id': len(sends) + 100}
            self.assertEqual(method, 'getUpdates')
            polls.append(payload['offset'])
            if len(polls) == 1:
                raise TelegramError('telegram_network_or_response')
            return [incoming(3), {'update_id': True}]

        def wait(seconds):
            waits.append(telegram_status())
            with Session(self.engine) as db:
                self.assertEqual(db.get(TelegramCursor, '42').next_update_id, 3)
                self.assertEqual(db.query(TelegramUpdate).filter_by(state='done').count(), len(waits))
                self.assertIsNone(db.get(TelegramUpdate, '42:3'))
            if len(waits) == 2:
                stop.set()

        with patch('app.telegram.SessionLocal', side_effect=lambda: Session(self.engine)), \
                patch('app.telegram.telegram_call', side_effect=call), patch.object(stop, 'wait', side_effect=wait):
            run_telegram(stop, 'test-token')
        self.assertEqual(polls, [3, 3])
        self.assertEqual([item['status'] for item in waits], ['error', 'error'])
        self.assertEqual([item['detail'] for item in waits],
                         ['telegram_network_or_response', 'telegram_invalid_updates'])
        self.assertEqual(len(sends), 2)
        self.assertEqual(self.answer.call_count, 1)
        with Session(self.engine) as db:
            self.assertFalse(process_next(db, '42'))
            self.assertEqual(db.query(Message).filter_by(sender_type='customer').count(), 2)
            self.assertEqual(db.query(Ticket).count(), 1)
            self.assertEqual(db.query(TelegramDelivery).filter_by(state='sent').count(), 2)

    def test_startup_retries_transient_errors_before_recovering_or_polling(self):
        stop = Event()
        calls, waits, recovered = [], [], []
        replies = iter([TelegramError('telegram_network_or_response'),
                        {'id': 42, 'is_bot': True}, TelegramError('telegram_http_503'),
                        {'id': 42, 'is_bot': True}, {'url': ''}])

        def call(token, method, payload):
            calls.append(method)
            if method == 'getUpdates':
                stop.set()
                return []
            reply = next(replies)
            if isinstance(reply, Exception):
                raise reply
            return reply

        def wait(seconds):
            waits.append((seconds, telegram_status(), len(recovered)))

        with patch('app.telegram.SessionLocal', side_effect=lambda: Session(self.engine)), \
                patch('app.telegram.telegram_call', side_effect=call), patch.object(stop, 'wait', side_effect=wait), \
                patch('app.telegram.recover_sends', side_effect=lambda db, bot_id: recovered.append(bot_id)):
            run_telegram(stop, 'test-token')
        self.assertEqual(calls, ['getMe', 'getMe', 'getWebhookInfo', 'getMe', 'getWebhookInfo', 'getUpdates'])
        self.assertEqual(recovered, ['42'])
        self.assertEqual([entry[0] for entry in waits], [5, 5])
        self.assertEqual([entry[1]['status'] for entry in waits], ['error', 'error'])
        self.assertEqual([entry[1]['detail'] for entry in waits],
                         ['telegram_network_or_response', 'telegram_http_503'])
        self.assertEqual([entry[2] for entry in waits], [0, 0])
        self.answer.assert_not_called()

    def test_startup_retry_can_stop_and_permanent_errors_do_not_retry(self):
        stop = Event()
        with patch('app.telegram.telegram_call', side_effect=TelegramError('telegram_network_or_response')) as call, \
                patch.object(stop, 'wait', side_effect=lambda seconds: stop.set()) as wait, \
                patch('app.telegram.SessionLocal') as sessions:
            run_telegram(stop, 'test-token')
        self.assertEqual(call.call_count, 1)
        wait.assert_called_once_with(5)
        sessions.assert_not_called()
        self.assertEqual(telegram_status()['status'], 'not_connected')
        for replies, code in [([TelegramError('telegram_http_401')], 'telegram_http_401'),
                              ([{'id': True, 'is_bot': True}], 'telegram_invalid_bot'),
                              ([{'id': 42, 'is_bot': True}, {'url': 'https://example.invalid/hook'}], 'telegram_webhook_active')]:
            with self.subTest(code=code), patch('app.telegram.telegram_call', side_effect=replies) as call, \
                    patch('app.telegram.SessionLocal') as sessions:
                terminal_stop = Event()
                with patch.object(terminal_stop, 'wait') as terminal_wait:
                    run_telegram(terminal_stop, 'test-token')
                terminal_wait.assert_not_called()
                sessions.assert_not_called()
                self.assertEqual(call.call_count, len(replies))
                self.assertEqual(telegram_status()['detail'], code)

    def test_transport_redacts_token_and_classifies_ambiguous_sends(self):
        token = '42:' + 'secret' * 6
        for exc, uncertain in [(HTTPError(f'https://api.telegram.org/bot{token}/sendMessage',403,'forbidden',{},None),False),
                                (HTTPError('url',502,'server',{},None),True), (URLError(token),True),
                                (IncompleteRead(token.encode(), 100), True), (BadStatusLine(token), True)]:
            with patch('app.telegram.build_opener') as opener:
                opener.return_value.open.side_effect = exc
                with self.assertRaises(TelegramError) as error:
                    telegram_call(token,'sendMessage',{})
            self.assertNotIn(token,str(error.exception))
            self.assertEqual(error.exception.uncertain,uncertain)

    def test_truncated_send_response_is_uncertain_without_blocking_other_peers(self):
        self.receive(incoming(content='/human'), incoming(2, chat_id=101, content='/human'))
        token = '42:' + 'secret' * 6
        with patch('app.telegram.build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.read.side_effect = [IncompleteRead(token.encode(), 100),
                                        b'{"ok":true,"result":{"message_id":777}}']
            send_outgoing(self.db, '42', token)
            send_outgoing(self.db, '42', token)
            self.assertEqual(opener.return_value.open.call_count, 2)
        deliveries = self.db.query(TelegramDelivery).all()
        self.assertEqual(sorted(row.state for row in deliveries), ['sent', 'uncertain'])
        uncertain = next(row for row in deliveries if row.state == 'uncertain')
        self.assertEqual(uncertain.error, 'telegram_network_or_response')
        self.assertIsNone(uncertain.external_message_id)
        self.assertIsNone(uncertain.sent_at)
        self.assertNotIn(token, str([row.error for row in deliveries]))
        self.assertEqual(self.db.query(Ticket).count(), 2)
        self.answer.assert_not_called()
        with patch('app.telegram.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.side_effect = IncompleteRead(b'partial', 10)
            with self.assertRaises(TelegramError) as error:
                telegram_call(token, 'getUpdates', {})
            self.assertFalse(error.exception.uncertain)

    def test_disabled_or_missing_token_does_not_connect(self):
        for enabled in ('false','true'):
            with patch.dict('os.environ',{'TELEGRAM_ENABLED':enabled,'TELEGRAM_BOT_TOKEN':''}), patch('app.telegram.telegram_call') as call:
                self.assertIsNone(start_telegram())
                call.assert_not_called()
                self.assertNotIn('token',str(telegram_status()).lower().replace('telegram_bot_token',''))

    def test_migration_repeatable_preserves_receipts_and_delivery(self):
        self.receive(incoming())
        queue_outgoing(self.db,'42')
        self.db.commit()
        migrate(self.engine)
        self.assertEqual(self.db.query(TelegramUpdate).count(),1)
        self.assertEqual(self.db.query(TelegramDelivery).count(),1)
        self.assertEqual(self.db.execute(text('SELECT COUNT(*) FROM schema_migrations')).scalar(),9)


if __name__ == '__main__':
    unittest.main()
