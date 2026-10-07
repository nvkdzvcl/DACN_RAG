"""Offline SQLite/Qdrant/file backup. Run python -m app.backup --help."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from sqlalchemy.engine import make_url


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def plain_path(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError('Symlinks and junctions are not supported')
    return path.resolve()


def inventory(root, ignored_lock=None):
    result = {}
    for path in sorted(root.rglob('*')):
        plain_path(path)
        if path == ignored_lock and path.is_file():
            continue
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path)
        elif not path.is_dir():
            raise ValueError('Only regular files and directories are supported')
    return result


def check_database(path):
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('SQLite integrity check failed')
        versions = [row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
        if versions not in (list(range(1, 8)), list(range(1, 9)), list(range(1, 10))):
            raise ValueError('Backup requires schema v7/v8/v9; use matching application version')
    return versions


def separate(paths):
    for i, left in enumerate(paths):
        for right in paths[i + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError('Source and destination paths must not overlap')


def backup(destination, database, vectors, knowledge, *, offline=False):
    if not offline:
        raise ValueError('Stop all API/ingestion processes first, then pass --offline')
    destination, database, vectors, knowledge = map(plain_path, (destination, database, vectors, knowledge))
    separate([destination, database, vectors, knowledge])
    if not database.is_file() or not vectors.is_dir() or not knowledge.is_dir():
        raise ValueError('Database, vector and knowledge paths must all exist')
    versions = check_database(database)
    before = {name: inventory(root, vectors / '.lock') for name, root in [('vectors', vectors), ('knowledge', knowledge)]}
    destination.mkdir(parents=True, exist_ok=False)
    # ponytail: offline operator procedure; use coordinated snapshots before supporting live backup.
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(destination / 'database.sqlite')) as target:
            source.backup(target)
    for name, root in [('vectors', vectors), ('knowledge', knowledge)]:
        # Only Qdrant's root lock is transient; identically named files elsewhere are data.
        shutil.copytree(root, destination / name, ignore=lambda directory, names:
                        ['.lock'] if Path(directory) == vectors and (vectors / '.lock').is_file() else [])
        if (inventory(root, vectors / '.lock') != before[name]
                or inventory(destination / name, destination / 'vectors/.lock') != before[name]):
            raise ValueError('Source changed or copy failed; backup is incomplete')
    check_database(destination / 'database.sqlite')
    manifest = {'format': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                'schema_versions': versions, 'files': inventory(destination)}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def verify(source):
    source = plain_path(source)
    plain_path(source / 'manifest.json')
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or manifest.get('format') != 1 or not isinstance(manifest.get('files'), dict):
        raise ValueError('Invalid backup manifest')
    actual = inventory(source, source / 'vectors/.lock')
    actual.pop('manifest.json', None)
    if actual != manifest['files'] or not {'database.sqlite'} <= actual.keys():
        raise ValueError('Backup files do not match SHA-256 manifest')
    if any(name != 'database.sqlite' and not name.startswith(('vectors/', 'knowledge/')) for name in actual):
        raise ValueError('Unexpected backup path')
    if not (source / 'vectors').is_dir() or not (source / 'knowledge').is_dir():
        raise ValueError('Missing backup directories')
    if check_database(source / 'database.sqlite') != manifest.get('schema_versions'):
        raise ValueError('Schema does not match manifest')
    return manifest


def restore(source, destination):
    source, destination = map(plain_path, (source, destination))
    separate([source, destination])
    verify(source)
    shutil.copytree(source, destination, ignore=lambda directory, names:
                    ['.lock'] if Path(directory) == source / 'vectors' and (source / 'vectors/.lock').is_file() else [])
    verify(destination)
    # A restored database must not revive old browser sessions or order grants.
    with closing(sqlite3.connect(destination / 'database.sqlite')) as db, db:
        for table in ('auth_sessions', 'widget_sessions', 'customer_sessions', 'customer_email_tokens', 'order_access'):
            if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                continue
            db.execute(f'DELETE FROM {table}')
    (destination / 'manifest.json').unlink()
    (destination / 'RESTORED.txt').write_text(
        'Restore completed; sessions and order grants revoked.\n'
        'Keep TELEGRAM_ENABLED=false. Review delivery history before enabling a restored bot.\n'
        'Use database.sqlite, vectors/ and knowledge/ together; keep original data unchanged.\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, help='Explicit local configuration; never included in backup')
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('destination', type=Path)
    create.add_argument('--offline', action='store_true', help='Confirm all API/ingestion processes have stopped')
    check = commands.add_parser('verify')
    check.add_argument('source', type=Path)
    recover = commands.add_parser('restore')
    recover.add_argument('source', type=Path)
    recover.add_argument('destination', type=Path, help='New directory only; never overwrite active data')
    args = parser.parse_args()
    try:
        if args.env_file:
            from dotenv import load_dotenv
            if not args.env_file.is_file():
                raise ValueError('Environment file does not exist')
            load_dotenv(args.env_file, override=False)
        if args.command == 'create':
            url = make_url(os.getenv('DATABASE_URL', 'sqlite:///./data/customer_support.db'))
            if url.get_backend_name() != 'sqlite' or not url.database or url.database == ':memory:' or url.query:
                raise ValueError('Only file-backed SQLite without URL query options is supported')
            backup(args.destination, url.database, os.getenv('QDRANT_PATH', 'data/vectors'),
                   os.getenv('KNOWLEDGE_PATH', 'data/knowledge_base'), offline=args.offline)
        elif args.command == 'verify':
            verify(args.source)
        else:
            restore(args.source, args.destination)
    except (OSError, ValueError, sqlite3.Error):
        parser.exit(1, 'Operation failed. Check paths, schema v7/v8/v9, offline state and file integrity. '
                    'Existing data was not overwritten; any new incomplete directory must not be used.\n')
    print(f'{args.command}: OK')


if __name__ == '__main__':
    main()
