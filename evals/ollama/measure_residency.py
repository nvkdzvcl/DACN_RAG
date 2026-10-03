import sys
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

if len(sys.argv) != 2:
    raise SystemExit('Usage: python -m evals.ollama.measure_residency OUTPUT.json')
output = Path(sys.argv[1]).resolve()
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('x', encoding='utf-8') as stream:
    stream.write('{}')

os.environ.update(OLLAMA_HOST='http://127.0.0.1:11434', LLM_MODEL='qwen3:4b', EMBEDDING_MODEL='embeddinggemma:300m', TELEGRAM_ENABLED='false')
with tempfile.TemporaryDirectory(prefix='rag-residency-') as directory:
    root = Path(directory)
    os.environ.update(DATABASE_URL='sqlite:///' + (root / 'test.db').as_posix(), QDRANT_PATH=str(root/'vectors'), KNOWLEDGE_PATH=str(root/'files'))
    from app.db.session import engine
    from app.db.migrations import migrate
    from sqlalchemy.orm import Session
    from app.rag import ollama
    from app.rag.answer_service import answer_question
    from app.rag.vector_store import vector_store
    from app.services.document_service import save_document
    migrate(engine)
    original = ollama.call
    policy = 'Khách hàng được đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng. Sản phẩm phải còn nguyên tem và có hóa đơn mua hàng.'
    question = 'Tôi được trả lại hàng trong bao lâu?'
    report = {'complete':False, 'ollama_version':original('/api/version'), 'models':original('/api/tags'), 'question':question, 'policy':policy,
              'options':ollama.CHAT_OPTIONS, 'think':ollama.CHAT_THINK, 'trials':[]}
    with Session(engine) as db:
        assert save_document(db, 'policy.txt', policy.encode(), root/'files')['status'] == 'indexed'
    def measured(path, payload=None, **kwargs):
        if payload is not None and path in ('/api/chat','/api/embed'):
            payload = {**payload, 'keep_alive': strategy}
        started = time.perf_counter()
        result = original(path, payload, **kwargs)
        trial['calls'].append({'path':path, 'seconds':round(time.perf_counter()-started,3),
                               **{key:result.get(key) for key in ('load_duration','total_duration','prompt_eval_duration','eval_duration','prompt_eval_count','eval_count')}})
        return result
    try:
        for strategy in (0, '5m'):
            for i in range(3):
                trial = {'keep_alive':strategy, 'iteration':i+1, 'calls':[]}
                report['trials'].append(trial)
                started = time.perf_counter()
                with patch('app.rag.ollama.call', side_effect=measured), Session(engine) as db:
                    answer = answer_question(question, db=db)
                trial.update(seconds=round(time.perf_counter()-started,3), answer=answer,
                             resident_models=original('/api/ps')['models'])
                assert answer['grounded'] and '7' in answer['answer'] and answer['citations'], answer
                print(json.dumps({'keep_alive':strategy,'iteration':i+1,'seconds':trial['seconds'],
                                  'gpu':[(m['name'],m['size_vram'],m['size']) for m in trial['resident_models']]},ensure_ascii=False),flush=True)
                output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        report['complete'] = True
    finally:
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        vector_store.close()
        engine.dispose()
