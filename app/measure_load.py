"""Bounded loopback HTTP load on disposable stores; never targets a running user's API."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import secrets
import socket
import subprocess
import sys
import tempfile
from threading import Barrier, Lock
import time
from uuid import uuid4

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.auth import token_hash
from app.db.migrations import migrate
from app.models.support import AuthSession, Conversation, Customer, Message, Ticket, User, WidgetSession


def summarize(samples):
    result = {}
    for label in sorted({s['operation'] for s in samples}):
        rows = [s for s in samples if s['operation'] == label]
        times = sorted(s['seconds'] for s in rows)
        result[label] = {'requests': len(rows), 'unexpected': sum(not s['expected'] for s in rows),
                         'statuses': {str(code): sum(s['status'] == code for s in rows) for code in sorted({s['status'] for s in rows})},
                         'p50_ms': round(times[math.ceil(len(times) * .5) - 1] * 1000, 3),
                         'p95_ms': round(times[math.ceil(len(times) * .95) - 1] * 1000, 3)}
    return result


def run(clients, rounds, conversations, output):
    root_repo = Path(__file__).resolve().parent.parent
    output.mkdir(parents=True, exist_ok=False)
    samples, mutex = [], Lock()
    report = {'complete': False, 'started_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Loopback, one Uvicorn worker, seeded sessions, no LLM/Telegram/browser',
              'load': {'clients': clients, 'rounds': rounds, 'conversations': conversations, 'seed_messages_per_chat': 10,
                       'inbox_page_size': 25,
                       'schedule': 'Closed loop; no think time; latency includes HTTP wait, excludes setup/startup'},
              'runtime': {'python': platform.python_version(), 'os': platform.system(), 'cpu_count': os.cpu_count(),
                          'packages': {name: importlib.metadata.version(name) for name in ('fastapi', 'uvicorn', 'sqlalchemy', 'httpx')}},
              'source_sha256': {p.relative_to(root_repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((root_repo / 'app').rglob('*.py'))}}
    (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    try:
        with tempfile.TemporaryDirectory(prefix='rag-load-') as temporary, ExitStack() as stack:
            root = Path(temporary)
            database_url = 'sqlite:///' + (root / 'support.db').as_posix()
            engine = create_engine(database_url)
            stack.callback(engine.dispose)
            migrate(engine)
            staff_tokens = [secrets.token_urlsafe(32) for _ in range(clients)]
            guest_tokens = [secrets.token_urlsafe(32) for _ in range(clients + 1)]
            expiry = int(time.time()) + 3600
            with Session(engine) as db:
                for i, token in enumerate(staff_tokens):
                    db.add(User(id=f'agent-{i}', username=f'agent-{i}', display_name='Load agent',
                                password_hash='disabled-for-load-run', role='agent'))
                    db.add(AuthSession(token_hash=token_hash(token), user_id=f'agent-{i}', expires_at=expiry))
                for i in range(conversations + 1):
                    db.add(Customer(id=f'customer-{i}', display_name='Load customer'))
                    db.add(Conversation(id=f'chat-{i}', customer_id=f'customer-{i}', status='assigned' if i < conversations else 'open',
                                        assigned_agent_id=f'agent-{i % clients}' if i < conversations else None))
                    if i < conversations:
                        db.add(Ticket(id=f'ticket-{i}', conversation_id=f'chat-{i}', status='assigned'))
                        for n in range(10):
                            db.add(Message(id=f'message-{i}-{n}', conversation_id=f'chat-{i}', sender_type='customer', content='Seed history'))
                for i, token in enumerate(guest_tokens):
                    db.add(WidgetSession(token_hash=token_hash(token), conversation_id=f'chat-{i if i < clients else conversations}', expires_at=expiry))
                db.commit()
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            environment = {**os.environ, 'DATABASE_URL': database_url, 'QDRANT_PATH': str(root / 'vectors'),
                           'KNOWLEDGE_PATH': str(root / 'files'), 'TELEGRAM_ENABLED': 'false', 'SERVE_FRONTEND': 'false',
                           'APP_ENV': 'development', 'OLLAMA_HOST': 'http://127.0.0.1:1'}
            log = stack.enter_context((output / 'server.log').open('w', encoding='utf-8'))
            process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                                        '--port', str(port), '--no-access-log'], cwd=root_repo, env=environment,
                                       stdout=log, stderr=log)
            def stop():
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            stack.callback(stop)
            def client(cookie, token):
                connection = stack.enter_context(httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=30,
                    trust_env=False, headers={'X-CSRF-Protection': '1'}))
                connection.cookies.set(cookie, token)
                return connection
            staff = [client('rag_session', token) for token in staff_tokens]
            guests = [client('rag_widget_session', token) for token in guest_tokens]
            for _ in range(200):
                if process.poll() is not None:
                    raise RuntimeError('Load server exited; inspect server.log')
                try:
                    if staff[0].get('/api/v1/health').status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError('Load server startup timed out')

            def request(connection, operation, method, path, expected=(200,), **kwargs):
                started = time.perf_counter()
                code = 0
                try:
                    response = connection.request(method, '/api/v1' + path, **kwargs)
                    code = response.status_code
                finally:
                    with mutex:
                        samples.append({'operation': operation, 'status': code, 'expected': code in expected,
                                        'seconds': round(time.perf_counter() - started, 6)})
                assert code in expected, (operation, code)
                return response

            gate = Barrier(clients)
            def workload(i):
                gate.wait(timeout=30)
                for _ in range(rounds):
                    listing = request(staff[i], 'inbox_list', 'GET', '/inbox/conversations').json()
                    assert listing['total'] == conversations + 1
                    assert listing['count'] == len(listing['conversations']) == min(25, conversations + 1)
                    detail = request(staff[i], 'inbox_detail', 'GET', f'/inbox/conversations/chat-{i}').json()
                    assert detail['customer_id'] == f'customer-{i}'
                    public = request(guests[i], 'widget_poll', 'GET', '/widget/session').json()
                    assert public['conversation_id'] == f'chat-{i}'
                    payload = {'content': 'Load reply', 'client_message_id': str(uuid4())}
                    first = request(staff[i], 'staff_send', 'POST', f'/inbox/conversations/chat-{i}/messages', json=payload).json()
                    retry = request(staff[i], 'staff_retry', 'POST', f'/inbox/conversations/chat-{i}/messages', json=payload).json()
                    assert first['message_id'] == retry['message_id']
            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=clients) as pool:
                list(pool.map(workload, range(clients)))
            elapsed = time.perf_counter() - started
            report['workload_seconds'] = round(elapsed, 3)
            report['workload_requests_per_second'] = round(clients * rounds * 5 / elapsed, 3)
            handoff_id = str(uuid4())
            request(guests[-1], 'handoff', 'POST', '/widget/handoff', json={'client_message_id': handoff_id})
            gate = Barrier(clients)
            def accept(i):
                gate.wait(timeout=30)
                return request(staff[i], 'accept_race', 'POST', f'/inbox/conversations/chat-{conversations}/accept',
                               expected=(200, 409)).status_code
            with ThreadPoolExecutor(max_workers=clients) as pool:
                codes = list(pool.map(accept, range(clients)))
            assert codes.count(200) == 1 and codes.count(409) == clients - 1
            # Six handoffs per IP/minute, including the initial handoff. Keep production limits intact.
            for i in range(6):
                response = request(guests[-1], 'handoff_retry_limit', 'POST', '/widget/handoff',
                                   expected=(429,) if i == 5 else (200,), json={'client_message_id': handoff_id})
                if i == 5:
                    assert response.headers.get('Retry-After') == '60'
            with Session(engine) as db:
                assert db.query(Message).filter_by(sender_type='agent').count() == clients * rounds
                assert db.query(Message).filter_by(sender_type='ai').count() == 0
                assert db.query(Message).filter_by(conversation_id=f'chat-{conversations}', sender_type='customer').count() == 1
                assert db.query(Ticket).filter_by(conversation_id=f'chat-{conversations}').count() == 1
            report['invariants'] = 'passed: distinct guests, UUID retries, one owner/ticket, handoff dedup, rate limit, no AI'
            report['complete'] = True
    finally:
        report['operations'] = summarize(samples)
        report['samples'] = samples
        (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'samples', 'source_sha256'}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clients', type=int, default=5, help='1-20 concurrent clients')
    parser.add_argument('--rounds', type=int, default=10, help='1-100 rounds per client')
    parser.add_argument('--conversations', type=int, default=100, help='1-5000 seeded conversations, plus one handoff chat')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not (1 <= args.clients <= 20 and 1 <= args.rounds <= 100 and args.clients <= args.conversations <= 5000):
        parser.error('Require clients 1-20, rounds 1-100, and clients <= conversations <= 5000')
    run(args.clients, args.rounds, args.conversations, args.output.resolve())


if __name__ == '__main__':
    main()
