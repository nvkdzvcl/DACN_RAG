"""Measure real tool routing against draft labels, using isolated synthetic stores."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from statistics import median
import time
from typing import Literal
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.migrations import migrate
from app.models.support import Conversation, Customer, Message, Order, OrderAccess, User, WidgetSession
from app.rag import ollama
from app.services.message_service import process_message
from app.services.tool_service import select_order_tool

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'evals/tools/cases.jsonl'


class HistoryMessage(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    sender: Literal['customer', 'ai']
    content: str = Field(min_length=1, max_length=4000)


class Case(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9-]+$')
    category: str = Field(min_length=1, max_length=64)
    query: str = Field(min_length=1, max_length=4000)
    scope: Literal['owner', 'anonymous', 'granted', 'expired']
    history: list[HistoryMessage] = Field(default_factory=list, max_length=4)
    expected_route: Literal['lookup', 'handoff', 'rag', 'clarification']
    expected_lookup: Literal['found', 'denied', 'none', 'any']
    rationale: str = Field(min_length=1, max_length=1000)


def load_cases(path):
    cases = [Case.model_validate_json(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not cases or len({case.id for case in cases}) != len(cases):
        raise ValueError('Dataset must be nonempty with unique IDs')
    return cases


def run_case(case):
    engine = create_engine('sqlite://')
    try:
        migrate(engine)
        with Session(engine) as db:
            db.add_all([Customer(id=name, display_name=name) for name in ('owner', 'visitor', 'other')])
            db.add(User(id='admin', username='admin', display_name='Fixture admin', password_hash='unused', role='admin'))
            db.flush()
            db.add_all([Order(id='DH78216', customer_id='owner', status='shipped', tracking_code='OWN-PRIVATE-TRACK'),
                        Order(id='ORD-93427', customer_id='other', status='paid', tracking_code='OTHER-PRIVATE-TRACK')])
            conversation = Conversation(id='chat', customer_id='owner' if case.scope == 'owner' else 'visitor')
            db.add(conversation)
            db.flush()
            if case.scope in {'granted', 'expired'}:
                db.add(WidgetSession(token_hash='fixture-session', conversation_id='chat', expires_at=int(time.time()) + 3600))
                db.add(OrderAccess(order_id='DH78216', customer_id='owner', token_hash='fixture-grant', issued_by_id='admin',
                                   conversation_id='chat', expires_at=int(time.time()) + (3600 if case.scope == 'granted' else -1)))
            for i, item in enumerate(case.history):
                db.add(Message(id=f'history-{i}', conversation_id='chat', sender_type=item.sender, content=item.content,
                               created_at=datetime.now(timezone.utc) - timedelta(minutes=5-i)))
            db.commit()
            orders_before = [(o.id, o.customer_id, o.status, o.tracking_code) for o in db.query(Order).order_by(Order.id)]
            started = time.perf_counter()
            result, trace, answer, error = {}, None, None, None
            # ponytail: routing only; use evaluate_rag separately for real retrieval/answer quality.
            with patch('app.services.message_service.answer_question', return_value={
                    'answer': 'EVAL_RAG_BRANCH_ONLY', 'citations': [], 'grounded': False}) as rag, patch(
                    'app.services.message_service.select_order_tool', wraps=select_order_tool) as selector:
                try:
                    result = process_message(db, conversation, case.query)
                    error = result.get('ai_error')
                    trace = db.get(Message, result['message_id']).tool_trace
                    ai = db.get(Message, result['ai_message_id']) if result.get('ai_message_id') else None
                    answer = ai.content if ai else None
                except Exception as exc:
                    db.rollback()
                    error = type(exc).__name__
                seconds = round(time.perf_counter() - started, 3)
            lookup = 'none' if result.get('order_lookup') is None else 'found' if result['order_lookup']['found'] else 'denied'
            route = ('error' if error else 'handoff' if result.get('needs_handoff') else 'lookup' if lookup == 'found'
                     else 'clarification' if trace and trace['status'] == 'clarification' else 'rag' if rag.called else 'unknown')
            visible = json.dumps({'answer': answer, 'order_lookup': result.get('order_lookup')})
            forbidden = ['OTHER-PRIVATE-TRACK'] + ([] if case.scope in {'owner', 'granted'} else ['OWN-PRIVATE-TRACK'])
            leaked = any(marker in visible for marker in forbidden)
            db.expire_all()
            mutated = orders_before != [(o.id, o.customer_id, o.status, o.tracking_code) for o in db.query(Order).order_by(Order.id)]
            return {**case.model_dump(), 'route': route, 'lookup': lookup, 'trace': trace, 'answer': answer,
                    'error': error, 'seconds': seconds, 'selector_calls': selector.call_count, 'rag_stub_calls': rag.call_count,
                    'private_data_leaked': leaked, 'order_mutated': mutated,
                    'passed': error is None and route == case.expected_route and
                              case.expected_lookup in ('any', lookup) and not leaked and not mutated}
    finally:
        engine.dispose()


def summarize(rows):
    return {'cases': len(rows), 'passed': sum(r['passed'] for r in rows),
            'accuracy_against_draft_labels': sum(r['passed'] for r in rows) / len(rows),
            'errors': sum(r['error'] is not None for r in rows),
            'private_data_leaks': sum(r['private_data_leaked'] for r in rows),
            'order_mutations': sum(r['order_mutated'] for r in rows),
            'selector_calls': sum(r['selector_calls'] for r in rows),
            'failed_ids': [r['id'] for r in rows if not r['passed']],
            'routing_seconds_median': median(r['seconds'] for r in rows),
            'by_category': {name: {'n': sum(r['category'] == name for r in rows),
                'passed': sum(r['category'] == name and r['passed'] for r in rows)} for name in sorted({r['category'] for r in rows})},
            'human_reviewed_cases': 0, 'rag_is_stubbed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=DATASET)
    parser.add_argument('--output', type=Path, required=True, help='New directory only; never overwrite results')
    args = parser.parse_args()
    try:
        cases = load_cases(args.dataset)
        args.output.mkdir(parents=True, exist_ok=False)
        model = ollama.chat_model()
        installed = next((m for m in ollama.call('/api/tags')['models'] if m['name'] == model), None)
        if installed is None:
            raise ValueError('Configured model is not installed')
        sources = ['app/services/tool_service.py', 'app/services/message_service.py', 'app/services/handoff_service.py',
                   'app/services/order_service.py', 'app/rag/ollama.py', 'app/evaluate_tools.py']
        manifest = {'started_at': datetime.now(timezone.utc).isoformat(), 'model': model, 'digest': installed['digest'],
                    'options': ollama.CHAT_OPTIONS, 'think': ollama.CHAT_THINK, 'keep_alive': ollama.KEEP_ALIVE,
                    'dataset_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                    'cases': [c.model_dump() for c in cases], 'labels': 'draft, not human-reviewed',
                    'method': 'Real selector and routing/permissions; in-memory SQLite; RAG branch stubbed; no Telegram/vector calls',
                    'sources': {name: (ROOT / name).read_text(encoding='utf-8') for name in sources}}
        (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        rows = []
        with (args.output / 'results.jsonl').open('x', encoding='utf-8') as output:
            for case in cases:
                row = run_case(case)
                output.write(json.dumps(row, ensure_ascii=False) + '\n')
                output.flush()
                rows.append(row)
                print(f"{case.id}: {'PASS' if row['passed'] else 'FAIL'} ({row['route']}, {row['seconds']}s)", flush=True)
        summary = summarize(rows)
        (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    except (OSError, ValueError, ollama.ProviderError) as exc:
        parser.exit(1, f'Evaluation failed: {exc}\n')


if __name__ == '__main__':
    main()
