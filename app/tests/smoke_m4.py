"""Real Ollama and HTTP API lifecycle in temporary stores: python -m app.tests.smoke_m4."""
import json
import os
import secrets
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4


def main():
    with tempfile.TemporaryDirectory(prefix='rag-m4-') as directory, ExitStack() as stack:
        root = Path(directory)
        # Set storage before importing the app; lifespan migrations must stay isolated too.
        stack.enter_context(patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite:///' + (root / 'support.db').as_posix(),
            'QDRANT_PATH': str(root / 'vectors'), 'KNOWLEDGE_PATH': str(root / 'files'),
            'APP_ENV': 'development',
        }))
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session
        from app.api.auth import UserCreate, create_user
        from app.db.session import engine
        from app.main import app
        from app.rag.ollama import call, chat_model, embedding_model
        from app.rag.vector_store import vector_store

        stack.callback(engine.dispose)
        stack.callback(vector_store.close)
        started = time.perf_counter()
        installed = {m['name']: m['digest'] for m in call('/api/tags')['models']}
        assert chat_model() in installed and embedding_model() in installed, 'Required Ollama models missing'
        staff = stack.enter_context(TestClient(app, headers={'X-CSRF-Protection': '1'}))
        guest = TestClient(app, headers={'X-CSRF-Protection': '1'})
        stranger = TestClient(app, headers={'X-CSRF-Protection': '1'})
        stack.callback(guest.close)
        stack.callback(stranger.close)

        def request(client, method, path, expected=200, **kwargs):
            response = client.request(method, '/api/v1' + path, **kwargs)
            assert response.status_code == expected, (method, path, response.status_code, response.text)
            return response.json()

        password = secrets.token_urlsafe(24)
        with Session(engine) as db:
            create_user(db, UserCreate(username='m4admin', password=password, display_name='M4 QA', role='admin'))
        request(staff, 'POST', '/auth/login', json={'username': 'm4admin', 'password': password})
        policy = 'Khách hàng được đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng. Sản phẩm phải còn nguyên tem và có hóa đơn mua hàng.'
        document = request(staff, 'POST', '/documents/upload', 201,
                           files={'file': ('m4-policy.txt', policy.encode(), 'text/plain')})
        assert document['status'] == 'indexed', document
        vector_store.close()
        session = request(guest, 'POST', '/widget/session', 201, json={'display_name': 'M4 customer'})
        cid = session['conversation_id']
        base = '/inbox/conversations/' + cid
        identity = str(uuid4())
        question_started = time.perf_counter()
        answer = request(guest, 'POST', '/widget/messages', json={
            'content': 'Tôi được trả lại hàng trong bao lâu?', 'client_message_id': identity})
        question_seconds = round(time.perf_counter() - question_started, 3)
        ai = [m for m in answer['messages'] if m['sender_type'] == 'ai']
        assert not answer['ai_error'] and ai and ai[-1]['citations'], answer
        assert '7' in ai[-1]['content'] and all(c['quote'] in policy for c in ai[-1]['citations']), ai
        assert request(guest, 'POST', '/widget/messages', json={
            'content': 'Tôi được trả lại hàng trong bao lâu?', 'client_message_id': identity})['duplicate']
        assert request(guest, 'GET', '/widget/session')['conversation_id'] == cid
        other = request(stranger, 'POST', '/widget/session', 201, json={'display_name': 'M4 customer'})
        assert other['conversation_id'] != cid and not other['messages']
        request(guest, 'GET', base, 401)
        request(guest, 'POST', '/widget/handoff', json={'client_message_id': str(uuid4())})
        request(staff, 'POST', base + '/accept')
        request(staff, 'POST', base + '/messages', json={'content': 'Nhân viên đã kiểm tra yêu cầu.'})

        def finish(status):
            detail = request(staff, 'GET', base)
            ticket = next(t for t in detail['tickets'] if t['status'] in {'open', 'assigned'})
            payload = {'status': status, 'ticket_id': ticket['id'], 'note': 'M4 PRIVATE completion',
                       'last_customer_message_id': detail['last_customer_message_id']}
            request(staff, 'POST', base + '/finish', json=payload)
            return payload

        resolved = finish('resolved')
        old = request(staff, 'GET', base)['tickets'][0]
        assert old['sla']['status'] == 'met', old
        followup = request(guest, 'POST', '/widget/messages', json={
            'content': 'Tôi cần hỗ trợ thêm.', 'client_message_id': str(uuid4())})
        assert followup['status'] == 'handoff_requested'
        assert len([m for m in followup['messages'] if m['sender_type'] == 'ai']) == len(ai)
        assert 'M4 PRIVATE' not in json.dumps(followup)
        assert request(staff, 'POST', base + '/finish', json=resolved)['duplicate']
        detail = request(staff, 'GET', base)
        assert detail['assigned_agent_id'] is None and len(detail['tickets']) == 2
        assert next(t for t in detail['tickets'] if t['id'] == old['id'])['sla'] == old['sla']
        request(staff, 'POST', base + '/accept')
        finish('closed')
        public = request(guest, 'GET', '/widget/session')
        assert public['status'] == 'closed' and 'M4 PRIVATE' not in json.dumps(public)
        request(guest, 'POST', '/widget/messages', 409, json={'content': 'After close', 'client_message_id': str(uuid4())})
        request(guest, 'DELETE', '/widget/session')
        request(guest, 'GET', '/widget/session', 401)
        assert request(guest, 'POST', '/widget/session', 201, json={'display_name': 'New session'})['conversation_id'] != cid
        request(staff, 'POST', '/auth/logout')
        request(staff, 'GET', base, 401)
        print(json.dumps({'result': 'passed', 'scope': 'HTTP API with real Ollama; no browser or load test',
                          'question_seconds': question_seconds, 'total_seconds': round(time.perf_counter() - started, 3),
                          'models': {m: installed[m] for m in (chat_model(), embedding_model())}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
