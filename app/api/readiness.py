"""On-demand local dependency probe; does not generate answers or send messages."""
import os
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.support import DocumentChunk, KnowledgeDocument
from app.rag.ollama import call, chat_model, embedding_model
from app.rag.vector_store import document_lock, vector_store
from app.services.document_service import knowledge_root

router = APIRouter(prefix='/api/v1', tags=['operations'])


@router.get('/ready')
def readiness(db: Session = Depends(get_db)):
    checks = {'database': 'unchecked', 'knowledge': 'unchecked', 'vectors': 'unchecked', 'ollama': 'unchecked'}
    if not document_lock.acquire(blocking=False):
        return JSONResponse({'ready': False, 'checks': {**checks, 'knowledge': 'busy'}}, status_code=503,
                            headers={'Cache-Control': 'no-store'})
    try:
        try:
            versions = list(db.execute(text('SELECT version FROM schema_migrations ORDER BY version')).scalars())
            checks['database'] = 'ok' if versions == list(range(1, 11)) else 'schema_mismatch'
            documents = db.query(KnowledgeDocument).filter_by(status='indexed', embedding_model=embedding_model()).all()
            sources = [(d.id, d.filename, d.index_version) for d in documents]
            expected = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_([d[0] for d in sources])).count()
        except Exception:
            checks['database'] = 'error'
            sources, expected = [], 0
        finally:
            db.rollback()
        try:
            root = knowledge_root().resolve()
            paths = [(root / doc_id / filename).resolve() for doc_id, filename, _ in sources]
            checks['knowledge'] = ('empty' if not sources else 'ok' if all(
                path.is_relative_to(root) and path.is_file() for path in paths) else 'missing_source')
        except OSError:
            checks['knowledge'] = 'unavailable'
        if sources and expected and all(version for _, _, version in sources):
            try:
                from qdrant_client import models
                path = Path(vector_store.path or os.getenv('QDRANT_PATH', 'data/vectors'))
                if not path.is_dir():
                    checks['vectors'] = 'missing_store'
                else:
                    with vector_store.lock:
                        client = vector_store._client()
                        collection = vector_store.collection()
                        count = client.count(collection, exact=True, count_filter=models.Filter(must=[
                            models.FieldCondition(key='index_version', match=models.MatchAny(any=[d[2] for d in sources]))
                        ])).count if client.collection_exists(collection) else 0
                    checks['vectors'] = 'ok' if count == expected else 'count_mismatch'
            except Exception:
                checks['vectors'] = 'unavailable'
        else:
            checks['vectors'] = 'empty'
    finally:
        document_lock.release()
    try:
        installed = {item['name'] for item in call('/api/tags', timeout=5)['models']}
        checks['ollama'] = 'ok' if {chat_model(), embedding_model()} <= installed else 'missing_model'
    except Exception:
        checks['ollama'] = 'unavailable'
    ready = all(value == 'ok' for value in checks.values())
    return JSONResponse({'ready': ready, 'checks': checks}, status_code=200 if ready else 503,
                        headers={'Cache-Control': 'no-store'})
