"""Import a product catalogue (JSON) into the database; products with the same name are updated.

    python -m app.import_products --env-file .env               # the demo catalogue in app/demo/products.json
    python -m app.import_products my-products.json --dry-run    # check a file without writing

File format: {"products": [{"name", "category", "price", "in_stock", "active", "url", "description"}, ...]}.
Fields are checked with the same rules as the staff API (POST /workspace/products).
"""
import argparse
import json
from pathlib import Path
from uuid import uuid4

DEFAULT_FILE = Path(__file__).parent / 'demo' / 'products.json'
DEMO_NOTE = 'Giá minh họa cho bản demo đồ án.'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', nargs='?', type=Path, default=DEFAULT_FILE)
    parser.add_argument('--env-file', type=Path, help='Explicit configuration; existing environment takes precedence')
    parser.add_argument('--dry-run', action='store_true', help='Validate and report without writing')
    args = parser.parse_args(argv)
    if args.env_file:
        from dotenv import load_dotenv
        if not args.env_file.is_file():
            parser.error('Environment file does not exist')
        load_dotenv(args.env_file, override=False)

    # Load configuration before importing the application's database engine.
    from pydantic import ValidationError
    from app.api.workspace import ProductFields
    from app.db.migrations import migrate
    from app.db.session import SessionLocal, engine
    from app.models.support import Product, now_utc

    try:
        items = json.loads(args.file.read_text(encoding='utf-8'))['products']
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(f'Cannot read catalogue {args.file}: {exc}')
    rows = []
    for number, item in enumerate(items, 1):
        try:
            if args.file == DEFAULT_FILE and isinstance(item, dict):
                item = {'description': DEMO_NOTE, **item}
            rows.append(ProductFields(**item).model_dump())
        except (ValidationError, TypeError) as exc:
            parser.error(f'Product {number} is invalid: {exc}')
    names = [row['name'].casefold() for row in rows]
    if len(set(names)) != len(names):
        parser.error('The file lists the same product name twice')

    migrate(engine)
    created = updated = unchanged = 0
    with SessionLocal() as db:
        existing = {product.name.casefold(): product for product in db.query(Product).all()}
        for row in rows:
            product = existing.get(row['name'].casefold())
            if product is None:
                db.add(Product(id=str(uuid4()), **row, in_stock=row['stock'] > 0))
                created += 1
            elif any(getattr(product, key) != value for key, value in row.items()):
                for key, value in row.items():
                    setattr(product, key, value)
                product.in_stock = product.stock > 0
                product.updated_at = now_utc()
                updated += 1
            else:
                unchanged += 1
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    mode = 'Dry run, nothing written' if args.dry_run else 'Imported'
    print(f'{mode}: {created} new, {updated} updated, {unchanged} unchanged ({len(rows)} in {args.file.name}).')


if __name__ == '__main__':
    main()
