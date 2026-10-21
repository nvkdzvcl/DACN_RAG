import hashlib
import json
from pathlib import Path

from app.evaluate_rag import load_cases


def main():
    root = Path.cwd()
    base = root / 'evals/independent-v1'
    manifest = json.loads((base / 'customer-v2/dataset-manifest.json').read_text(encoding='utf-8'))
    assert manifest['human_approved'] is False
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    allowed = {item['id']: item['after'] for item in manifest['changes']}
    changed = set()
    for partition in ('main', 'reserve'):
        old = load_cases(base / 'customer-v1' / partition / 'cases.jsonl')
        new = load_cases(base / 'customer-v2' / partition / 'cases.jsonl')
        assert len(old) == len(new)
        for before, after in zip(old, new, strict=True):
            assert before['id'] == after['id']
            update = allowed.get(before['id'], {})
            assert before | update == after, before['id']
            if before != after:
                changed.add(before['id'])
        original_files = {path.name: path.read_bytes() for path in (base / 'customer-v1' / partition / 'corpus').iterdir()}
        revised_files = {path.name: path.read_bytes() for path in (base / 'customer-v2' / partition / 'corpus').iterdir()}
        assert original_files == revised_files
    assert changed == set(allowed) == {'customer-024', 'customer-048', 'customer-051'}
    print('PASS: exactly three declared label edits; 60 questions and corpus unchanged; no human approval claimed.')


if __name__ == '__main__':
    main()
