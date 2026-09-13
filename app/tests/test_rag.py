import io
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

from docx import Document
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.auth import require_staff
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import Conversation, Customer, DocumentChunk, KnowledgeDocument, Message, User
from app.rag.answer_service import answer_question
from app.rag.ollama import ProviderError, embed, embedding_model
from app.rag.vector_store import VectorStore
from app.services.document_service import extract_sections, save_document
from app.services.message_service import process_message


class RagTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.engine = create_engine('sqlite:///' + str(self.root / 'test.db'), connect_args={'check_same_thread': False})
        migrate(self.engine)
        self.store = VectorStore(str(self.root / 'vectors'))
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.store.close)
        self.addCleanup(app.dependency_overrides.clear)
        for target, value in [('app.services.document_service.vector_store', self.store), ('app.rag.answer_service.vector_store', self.store)]:
            p = patch(target, value); p.start(); self.addCleanup(p.stop)
        p = patch.dict(os.environ, {'KNOWLEDGE_PATH': str(self.root / 'files'), 'RAG_MIN_SCORE': '0.35'})
        p.start(); self.addCleanup(p.stop)
        def database():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[require_staff] = lambda: User(id='admin', role='admin')
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def upload(self, content=b'Returns accepted within 7 days.', filename='policy.txt'):
        with patch('app.services.document_service.embed', side_effect=lambda texts: [[1.0, 0.0] for _ in texts]):
            result = self.client.post('/api/v1/documents/upload', files={'file': (filename, content)})
        self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(result.json()['status'], 'indexed', result.text)
        return result.json()['document_id']

    def test_persistent_vectors_metadata_duplicate_reindex_delete(self):
        document_id = self.upload()
        self.store.close()
        with patch('app.rag.vector_store.embed', return_value=[[1.0, 0.0]]), Session(self.engine) as db:
            results = self.store.search('How long can I return an item?', db=db)
        self.assertEqual(results[0]['document_id'], document_id)
        self.assertEqual(results[0]['location'], 'Dòng 1')
        self.assertIsNone(results[0]['page'])
        self.assertEqual(self.client.post('/api/v1/documents/upload', files={'file': ('copy.txt', b'Returns accepted within 7 days.')}).status_code, 409)
        with patch('app.services.document_service.embed', return_value=[[1.0, 0.0]]):
            self.assertEqual(self.client.post(f'/api/v1/documents/{document_id}/reindex').json()['status'], 'indexed')
        with Session(self.engine) as db:
            self.assertNotEqual(db.get(KnowledgeDocument, document_id).index_version, results[0]['index_version'])
        self.assertEqual(self.client.get(f'/api/v1/documents/{document_id}/chunks/{results[0]["chunk_id"]}', params={'index_version': results[0]['index_version']}).status_code, 409)
        self.assertEqual(self.client.delete(f'/api/v1/documents/{document_id}').status_code, 200)
        self.assertFalse((self.root / 'files' / document_id).exists())
        with Session(self.engine) as db, patch('app.rag.vector_store.embed') as embedding:
            self.assertEqual(self.store.search('return policy', db=db), [])
            embedding.assert_not_called()
            self.assertEqual(db.query(DocumentChunk).count(), 0)
        self.assertEqual(self.client.get(f'/api/v1/documents/{document_id}/chunks').status_code, 404)
        self.assertEqual(self.store._client().count(self.store.collection()).count, 0)

    def test_failed_embedding_can_retry_and_non_admin_cannot_mutate(self):
        with patch('app.services.document_service.embed', side_effect=ProviderError('Ollama offline')):
            result = self.client.post('/api/v1/documents/upload', files={'file': ('policy.txt', b'Policy text for recovery.')})
        self.assertEqual(result.json()['status'], 'failed')
        document_id = result.json()['document_id']
        with Session(self.engine) as db, patch('app.rag.vector_store.embed') as embedding:
            self.assertEqual(self.store.search('policy', db=db), [])
            embedding.assert_not_called()
        with patch('app.services.document_service.embed', return_value=[[1.0, 0.0]]):
            self.assertEqual(self.client.post(f'/api/v1/documents/{document_id}/reindex').json()['status'], 'indexed')
        app.dependency_overrides[require_staff] = lambda: User(id='agent', role='agent')
        self.assertEqual(self.client.get('/api/v1/documents').status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/documents/{document_id}/chunks').status_code, 200)
        self.assertEqual(self.client.delete(f'/api/v1/documents/{document_id}').status_code, 403)
        self.assertEqual(self.client.post(f'/api/v1/documents/{document_id}/reindex').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/documents/upload', files={'file': ('x.txt', b'x')}).status_code, 403)

    def test_input_validation_and_docx_table_location(self):
        for filename, content in [('x.exe', b'x'), ('empty.txt', b''), ('large.txt', b'x' * (10 * 1024 * 1024 + 1))]:
            self.assertEqual(self.client.post('/api/v1/documents/upload', files={'file': (filename, content)}).status_code, 400)
        self.assertEqual(self.client.post('/api/v1/rag/answer', json={'query': '   '}).status_code, 422)
        self.assertEqual(self.client.post('/api/v1/rag/search', json={'query': '   '}).status_code, 422)
        document = Document()
        document.add_paragraph('Warranty policy')
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = 'Coverage'
        table.cell(0, 1).text = '12 months'
        data = io.BytesIO(); document.save(data)
        document_id = self.upload(data.getvalue(), 'warranty.docx')
        chunks = self.client.get(f'/api/v1/documents/{document_id}/chunks').json()['chunks']
        self.assertEqual(chunks[0]['location'], 'Đoạn 1')
        self.assertEqual(chunks[1]['location'], 'Bảng 1, hàng 1')
        self.assertIn('12 months', chunks[1]['content'])
        with patch('app.services.document_service.PdfReader') as reader:
            reader.return_value.is_encrypted = False
            reader.return_value.pages = [unittest.mock.Mock(extract_text=lambda: 'First page'), unittest.mock.Mock(extract_text=lambda: 'Second page')]
            self.assertEqual([s[1] for s in extract_sections(Path('test.pdf'))], [1, 2])

    def test_validated_citations_abstention_and_history(self):
        self.upload()
        valid = {'supported': True, 'answer': 'You can return items within 7 days.', 'citations': [{'source_id': 1, 'quote': 'Returns accepted within 7 days.'}]}
        history = [{'role': 'user', 'content': 'Tell me about returns'}]
        with Session(self.engine) as db, patch('app.rag.vector_store.embed', return_value=[[1.0, 0.0]]), patch('app.rag.answer_service.chat', return_value=json.dumps(valid)) as chat:
            result = answer_question('How many days?', history=history, db=db)
            self.assertTrue(result['grounded'])
            self.assertIn('Tell me about returns', chat.call_args.args[0][-1]['content'])
            self.assertEqual(result['citations'][0]['location'], 'Dòng 1')
            for response in ['not JSON', json.dumps(valid | {'citations': [{'source_id': 9, 'quote': 'Returns accepted within 7 days.'}]}),
                             json.dumps(valid | {'citations': [{'source_id': 1, 'quote': 'Invented source text.'}]}),
                             json.dumps(valid | {'supported': False})]:
                chat.return_value = response
                answer = answer_question('Returns?', db=db)
                self.assertFalse(answer['grounded'])
                self.assertEqual(answer['citations'], [])
        with Session(self.engine) as db, patch('app.rag.vector_store.embed', return_value=[[0.0, 1.0]]), patch('app.rag.answer_service.chat') as chat:
            self.assertFalse(answer_question('Unrelated?', db=db)['grounded'])
            chat.assert_not_called()

    def test_deleted_source_during_generation_is_not_returned(self):
        document_id = self.upload()
        def generate(*args):
            with Session(self.engine) as other:
                other.get(KnowledgeDocument, document_id).status = 'deleting'
                other.commit()
            return json.dumps({'supported': True, 'answer': '7 days', 'citations': [{'source_id': 1, 'quote': 'Returns accepted within 7 days.'}]})
        with Session(self.engine) as db, patch('app.rag.vector_store.embed', return_value=[[1.0, 0.0]]), patch('app.rag.answer_service.chat', side_effect=generate):
            result = answer_question('Returns?', db=db)
        self.assertFalse(result['grounded'])
        self.assertEqual(result['results'], [])

    def test_provider_error_preserves_customer_and_newer_message_suppresses_stale_ai(self):
        with Session(self.engine) as db:
            db.add(Customer(id='customer', display_name='Test'))
            db.flush(); db.add(Conversation(id='chat', customer_id='customer')); db.commit()
        def process(content):
            with Session(self.engine) as db:
                return process_message(db, db.get(Conversation, 'chat'), content)
        with patch('app.services.message_service.answer_question', side_effect=ProviderError('Offline')):
            result = process('First question')
            self.assertEqual(result['ai_error'], 'Offline')
            self.assertIsNone(result['ai_message_id'])
        entered, release = Event(), Event()
        def generate(query, **kwargs):
            if query == 'Slow question':
                entered.set(); self.assertTrue(release.wait(5))
            return {'answer': query, 'citations': [], 'grounded': False}
        with patch('app.services.message_service.answer_question', side_effect=generate), ThreadPoolExecutor(max_workers=2) as pool:
            earlier = pool.submit(process, 'Slow question')
            self.assertTrue(entered.wait(5))
            try:
                latest = pool.submit(process, 'Latest question').result(timeout=3)
                self.assertIsNotNone(latest['ai_message_id'])
            finally:
                release.set()
            self.assertIsNone(earlier.result(timeout=5)['ai_message_id'])
        with Session(self.engine) as db:
            self.assertEqual(db.query(Message).filter_by(sender_type='customer').count(), 3)
            self.assertEqual(db.query(Message).filter_by(sender_type='ai').one().content, 'Latest question')

    def test_invalid_embeddings_and_provider_http_error(self):
        for value in [[], [[float('nan')]], [[0.0, 0.0]], [[True, False]], ['bad']]:
            with patch('app.rag.ollama.call', return_value={'embeddings': value}), self.assertRaises(ProviderError):
                embed(['question'])
        with patch('app.api.answer.answer_question', side_effect=ProviderError('Unavailable')):
            result = self.client.post('/api/v1/rag/answer', json={'query': 'Policy?'})
            self.assertEqual(result.status_code, 503)
            self.assertEqual(result.json()['detail'], 'Unavailable')


if __name__ == '__main__':
    unittest.main()
