import json
import os
from pathlib import Path
import sqlite3
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine

from app.backup import backup, digest, restore, verify
from app.db.migrations import migrate


class BackupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = self.root / 'source.db'
        engine = create_engine('sqlite:///' + self.database.as_posix())
        migrate(engine)
        engine.dispose()
        db = sqlite3.connect(self.database)
        try:
            db.execute("INSERT INTO customers (id, display_name) VALUES ('customer', 'Test')")
            db.execute("INSERT INTO auth_sessions (token_hash, user_id, expires_at) VALUES ('session', 'staff', 9999999999)")
            db.execute("INSERT INTO widget_sessions (token_hash, conversation_id, expires_at) VALUES ('widget', 'chat', 9999999999)")
            db.execute("INSERT INTO order_access (order_id, customer_id, token_hash, issued_by_id, expires_at) VALUES ('DH12345', 'customer', 'grant', 'staff', 9999999999)")
            db.commit()
        finally:
            db.close()
        self.vectors, self.knowledge = self.root / 'vectors', self.root / 'knowledge'
        self.vectors.mkdir()
        self.knowledge.mkdir()
        (self.vectors / 'storage.sqlite').write_bytes(b'test vector bytes')
        (self.knowledge / 'policy.txt').write_text('Test policy', encoding='utf-8')
        self.snapshot = self.root / 'snapshot'

    def create(self, **kwargs):
        return backup(self.snapshot, self.database, self.vectors, self.knowledge, offline=True, **kwargs)

    def test_round_trip_preserves_data_and_revokes_only_restored_access(self):
        from qdrant_client import QdrantClient, models
        client = QdrantClient(path=str(self.vectors))
        try:
            client.create_collection('qa', vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
            client.upsert('qa', [models.PointStruct(id=1, vector=[1.0, 0.0], payload={'source': 'policy.txt'})])
        finally:
            client.close()
        original = digest(self.database)
        manifest = self.create()
        self.assertEqual(verify(self.snapshot), manifest)
        restored = self.root / 'restored'
        restore(self.snapshot, restored)
        db = sqlite3.connect(restored / 'database.sqlite')
        try:
            self.assertEqual(db.execute('SELECT display_name FROM customers').fetchone(), ('Test',))
            for table in ('auth_sessions', 'widget_sessions', 'order_access'):
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)
        finally:
            db.close()
        self.assertEqual(digest(self.database), original)
        self.assertEqual(digest(restored / 'knowledge/policy.txt'), digest(self.knowledge / 'policy.txt'))
        self.assertTrue((restored / 'RESTORED.txt').exists())
        self.assertFalse((restored / 'manifest.json').exists())
        client = QdrantClient(path=str(restored / 'vectors'))
        try:
            self.assertEqual(client.query_points('qa', query=[1.0, 0.0], limit=1).points[0].payload['source'], 'policy.txt')
        finally:
            client.close()
        verify(self.snapshot)

    def test_corrupted_missing_and_extra_files_rejected_before_restore(self):
        self.create()
        policy = self.snapshot / 'knowledge/policy.txt'
        policy.write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            restore(self.snapshot, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())
        policy.unlink()
        with self.assertRaises(ValueError):
            verify(self.snapshot)
        policy.write_text('Test policy', encoding='utf-8')
        (self.snapshot / 'extra').write_text('unexpected', encoding='utf-8')
        with self.assertRaises(ValueError):
            verify(self.snapshot)

    def test_only_root_qdrant_lock_is_excluded_from_backup_and_restore(self):
        (self.vectors / '.lock').write_text('Runtime lock', encoding='utf-8')
        files = {'knowledge/.lock': 'Knowledge metadata', 'knowledge/nested/.lock': 'Nested metadata',
                 'vectors/nested/.lock': 'Nested vector data'}
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        manifest = self.create()
        self.assertNotIn('vectors/.lock', manifest['files'])
        self.assertFalse((self.snapshot / 'vectors/.lock').exists())
        for name in files:
            self.assertIn(name, manifest['files'])
        # A vector client may create its transient root lock while inspecting a snapshot.
        (self.snapshot / 'vectors/.lock').write_text('Transient inspection lock', encoding='utf-8')
        verify(self.snapshot)
        restored = self.root / 'restored'
        restore(self.snapshot, restored)
        self.assertFalse((restored / 'vectors/.lock').exists())
        for name, content in files.items():
            self.assertEqual((restored / name).read_text(encoding='utf-8'), content)
            self.assertEqual((self.root / name).read_text(encoding='utf-8'), content)

    def test_unmanifested_or_modified_knowledge_lock_is_rejected(self):
        lock = self.knowledge / '.lock'
        lock.write_text('Required metadata', encoding='utf-8')
        self.create()
        copied = self.snapshot / 'knowledge/.lock'
        copied.write_text('Modified', encoding='utf-8')
        with self.assertRaises(ValueError):
            verify(self.snapshot)
        copied.write_text('Required metadata', encoding='utf-8')
        verify(self.snapshot)
        (self.snapshot / 'knowledge/nested').mkdir()
        (self.snapshot / 'knowledge/nested/.lock').write_text('Unexpected', encoding='utf-8')
        with self.assertRaises(ValueError):
            restore(self.snapshot, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())

    def test_no_overwrite_overlap_or_missing_sources(self):
        with self.assertRaises(ValueError):
            backup(self.snapshot, self.database, self.vectors, self.knowledge)
        with self.assertRaises(ValueError):
            backup(self.vectors / 'nested', self.database, self.vectors, self.knowledge, offline=True)
        with self.assertRaises(ValueError):
            backup(self.snapshot, self.database, self.root / 'missing', self.knowledge, offline=True)
        self.create()
        with self.assertRaises(FileExistsError):
            self.create()
        existing = self.root / 'existing'
        existing.mkdir()
        (existing / 'keep').write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            restore(self.snapshot, existing)
        self.assertEqual((existing / 'keep').read_text(), 'keep')

    def test_copy_failure_never_publishes_manifest(self):
        with patch('app.backup.shutil.copytree', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.create()
        self.assertFalse((self.snapshot / 'manifest.json').exists())
        self.assertTrue(self.database.exists())

    def test_changed_source_and_unsafe_manifest_rejected(self):
        from app.backup import shutil
        copy = shutil.copytree
        def mutate(*args, **kwargs):
            result = copy(*args, **kwargs)
            (self.vectors / 'storage.sqlite').write_bytes(b'changed during copy')
            return result
        with patch('app.backup.shutil.copytree', side_effect=mutate):
            with self.assertRaises(ValueError):
                self.create()
        self.assertFalse((self.snapshot / 'manifest.json').exists())
        self.snapshot = self.root / 'second'
        self.create()
        path = self.snapshot / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['files']['../outside'] = 'fake'
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            verify(self.snapshot)

    def test_schema_and_link_rejected(self):
        db = sqlite3.connect(self.database)
        try:
            db.execute('DELETE FROM schema_migrations WHERE version=7')
            db.commit()
        finally:
            db.close()
        with self.assertRaises(ValueError):
            self.create()
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaises(ValueError):
                verify(self.snapshot)

    def test_cli_loads_explicit_config_without_copying_secrets(self):
        config = self.root / '.env'
        config.write_text(f'DATABASE_URL=sqlite:///{self.database.as_posix()}\n'
                          f'QDRANT_PATH={self.vectors.as_posix()}\n'
                          f'KNOWLEDGE_PATH={self.knowledge.as_posix()}\n'
                          'TELEGRAM_BOT_TOKEN=never-copy-this-secret\n', encoding='utf-8')
        env = {key: value for key, value in os.environ.items()
               if key not in {'DATABASE_URL', 'QDRANT_PATH', 'KNOWLEDGE_PATH'}}
        for args in [('--env-file', str(config), 'create', str(self.snapshot), '--offline'),
                     ('verify', str(self.snapshot)),
                     ('restore', str(self.snapshot), str(self.root / 'restored'))]:
            result = subprocess.run([sys.executable, '-m', 'app.backup', *args],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('never-copy', result.stdout + result.stderr)
        self.assertFalse((self.snapshot / '.env').exists())
        self.assertNotIn('never-copy', (self.snapshot / 'manifest.json').read_text())


if __name__ == '__main__':
    unittest.main()
