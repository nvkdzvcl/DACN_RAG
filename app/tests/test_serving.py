import tempfile
import unittest
from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.auth import require_staff
from app.db.migrations import migrate
from app.db.session import get_db
from app.main import app
from app.models.support import User
from app.rag.ollama import ProviderError, chat_model, embedding_model
from app.rag.vector_store import VectorStore, document_lock
from app.services.document_service import save_document
from app.web import mount_frontend


class ServingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.root = Path(directory.name)
        self.engine = create_engine('sqlite:///' + (self.root / 'test.db').as_posix(),
                                    connect_args={'check_same_thread': False})
        migrate(self.engine)
        self.store = VectorStore(str(self.root / 'vectors'))
        self.addCleanup(directory.cleanup)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.store.close)
        self.addCleanup(app.dependency_overrides.clear)
        def database():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = database
        for target, value in [('app.api.readiness.vector_store', self.store),
                              ('app.services.document_service.vector_store', self.store)]:
            mock = patch(target, value)
            mock.start()
            self.addCleanup(mock.stop)
        environment = patch.dict('os.environ', {'KNOWLEDGE_PATH': str(self.root / 'files')})
        environment.start()
        self.addCleanup(environment.stop)
        self.models = patch('app.api.readiness.call', return_value={'models': [
            {'name': chat_model()}, {'name': embedding_model()}]})
        self.call = self.models.start()
        self.addCleanup(self.models.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def authorize(self):
        app.dependency_overrides[require_staff] = lambda: User(id='staff', role='agent')

    def index(self):
        with Session(self.engine) as db, patch('app.services.document_service.embed', return_value=[[1.0, 0.0]]):
            result = save_document(db, 'policy.txt', b'Returns within seven days.', self.root / 'files')
            self.assertEqual(result['status'], 'indexed')
            return result['document_id']

    def test_probe_requires_staff_and_health_remains_light(self):
        self.assertEqual(self.client.get('/api/v1/ready').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/health').status_code, 200)
        self.call.assert_not_called()
        self.authorize()
        response = self.client.get('/api/v1/ready')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['checks']['knowledge'], 'empty')
        self.assertFalse((self.root / 'vectors').exists())

    def test_real_vector_and_sources_ready_without_model_generation(self):
        self.authorize()
        self.index()
        def tags(*args, **kwargs):
            with self.engine.begin() as connection:
                connection.execute(text("INSERT INTO customers (id, display_name) VALUES ('probe', 'No SQL lock')"))
            return {'models': [{'name': chat_model()}, {'name': embedding_model()}]}
        self.call.side_effect = tags
        response = self.client.get('/api/v1/ready')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['ready'])
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.call.assert_called_once_with('/api/tags', timeout=5)

    def test_missing_source_vector_and_model_report_unready(self):
        self.authorize()
        document_id = self.index()
        (self.root / 'files' / document_id / 'policy.txt').unlink()
        self.store.delete(document_id)
        self.call.return_value = {'models': []}
        response = self.client.get('/api/v1/ready')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['checks'], {'database': 'ok', 'knowledge': 'missing_source',
                                                    'vectors': 'count_mismatch', 'ollama': 'missing_model'})

    def test_probe_redacts_provider_error_and_checks_schema(self):
        self.authorize()
        self.index()
        self.call.side_effect = ProviderError('secret://private-host/token')
        with self.engine.begin() as connection:
            connection.execute(text('DELETE FROM schema_migrations WHERE version=7'))
        response = self.client.get('/api/v1/ready')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['checks']['database'], 'schema_mismatch')
        self.assertEqual(response.json()['checks']['ollama'], 'unavailable')
        self.assertNotIn('secret', response.text)

    def test_probe_returns_busy_during_ingestion(self):
        self.authorize()
        entered, release = Event(), Event()
        def hold():
            with document_lock:
                entered.set()
                release.wait(10)
        worker = Thread(target=hold)
        worker.start()
        try:
            self.assertTrue(entered.wait(5))
            response = self.client.get('/api/v1/ready')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['checks']['knowledge'], 'busy')
            self.assertEqual(response.json()['checks']['database'], 'unchecked')
            self.call.assert_not_called()
        finally:
            release.set()
            worker.join(5)

    def test_built_pages_assets_and_no_private_or_api_fallback(self):
        build = self.root / 'dist'
        (build / 'assets').mkdir(parents=True)
        for name in ('index.html', 'widget-demo.html', 'widget.js'):
            (build / name).write_text('build-' + name, encoding='utf-8')
        (build / 'assets' / 'app.js').write_text('asset', encoding='utf-8')
        (build / '.env').write_text('private', encoding='utf-8')
        server = FastAPI()
        mount_frontend(server, build)
        with TestClient(server) as client:
            for route in ('/', '/index.html', '/chat', '/widget-demo.html', '/widget.js'):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['cache-control'], 'no-cache')
                self.assertEqual(client.head(route).content, b'')
            self.assertEqual(client.get('/assets/app.js').text, 'asset')
            for route in ('/.env', '/api/v1/typo', '/unknown', '/assets/%2e%2e/.env'):
                self.assertEqual(client.get(route).status_code, 404)
            self.assertEqual(client.post('/chat').status_code, 405)
        self.assertEqual(server.openapi()['paths'], {})

    def test_missing_build_fails_explicitly(self):
        with self.assertRaisesRegex(RuntimeError, 'Frontend build missing'):
            mount_frontend(FastAPI(), self.root / 'missing')


if __name__ == '__main__':
    unittest.main()
