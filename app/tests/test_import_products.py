"""python -m app.import_products: validates like the API, imports, updates by name, dry run writes nothing."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.support import Product

ROOT = Path(__file__).resolve().parents[2]


class ImportProductsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'catalogue.db'

    def run_cli(self, *args):
        env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + self.database.as_posix(), 'APP_ENV': 'development',
               'QDRANT_PATH': str(Path(self.directory.name) / 'vectors'), 'KNOWLEDGE_PATH': str(Path(self.directory.name) / 'kb')}
        return subprocess.run([sys.executable, '-m', 'app.import_products', *args], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding='utf-8')

    def products(self):
        engine = create_engine('sqlite:///' + self.database.as_posix())
        try:
            with Session(engine) as db:
                return {p.name: p for p in db.query(Product).all()}
        finally:
            engine.dispose()

    def write(self, products):
        path = Path(self.directory.name) / 'products.json'
        path.write_text(json.dumps({'products': products}, ensure_ascii=False), encoding='utf-8')
        return str(path)

    def test_demo_catalogue_imports_once_and_dry_run_writes_nothing(self):
        dry = self.run_cli('--dry-run')
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn('Dry run, nothing written: 24 new', dry.stdout)
        self.assertEqual(self.products(), {})
        first = self.run_cli()
        self.assertIn('Imported: 24 new, 0 updated, 0 unchanged', first.stdout, first.stderr)
        catalogue = self.products()
        self.assertEqual(catalogue['iPhone 16 128GB'].price, 19_990_000)
        self.assertEqual(catalogue['iPhone 16 128GB'].description, 'Giá minh họa cho bản demo đồ án.')
        self.assertFalse(catalogue['Xiaomi Redmi Note 14 8GB/128GB'].in_stock)
        again = self.run_cli()
        self.assertIn('0 new, 0 updated, 24 unchanged', again.stdout)

    def test_own_file_updates_by_name_and_rejects_invalid_rows(self):
        self.run_cli(self.write([{'name': 'Máy A', 'category': 'phone', 'price': 100}]))
        changed = self.run_cli(self.write([{'name': 'máy a', 'category': 'phone', 'price': 200, 'stock': 0},
                                           {'name': 'Máy B', 'category': 'other'}]))
        self.assertIn('1 new, 1 updated, 0 unchanged', changed.stdout, changed.stderr)
        catalogue = self.products()
        self.assertEqual((catalogue['máy a'].price, catalogue['máy a'].in_stock, catalogue['Máy B'].price), (200, False, None))
        for bad in ([{'name': 'X', 'category': 'car'}], [{'name': 'X', 'category': 'phone', 'url': 'http://x'}],
                    [{'name': 'X', 'category': 'phone'}, {'name': 'x', 'category': 'phone'}]):
            result = self.run_cli(self.write(bad))
            self.assertNotEqual(result.returncode, 0, bad)
        self.assertEqual(set(self.products()), {'máy a', 'Máy B'})


if __name__ == '__main__':
    unittest.main()
