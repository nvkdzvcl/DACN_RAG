import hashlib
import json
from pathlib import Path

from app.evaluate_rag import load_cases


def validate():
    directory = Path(__file__).resolve().parent
    root = directory.parents[2]
    manifest = json.loads((directory / 'dataset-manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen dataset changed: ' + name)
    all_ids, all_queries = set(), set()
    for partition, count in manifest['counts'].items():
        cases = load_cases(directory / partition / 'cases.jsonl')
        if len(cases) != count:
            raise ValueError('Wrong case count: ' + partition)
        prefix = (directory / partition / 'corpus').relative_to(root).as_posix() + '/'
        actual = {path.relative_to(root).as_posix() for path in (directory / partition / 'corpus').iterdir() if path.is_file()}
        if actual != {name for name in manifest['sha256'] if name.startswith(prefix)}:
            raise ValueError('Corpus file list changed: ' + partition)
        for case in cases:
            identity = (case['query'].casefold(), json.dumps(case['history'], sort_keys=True, ensure_ascii=False))
            if case['id'] in all_ids or identity in all_queries:
                raise ValueError('Duplicate case: ' + case['id'])
            all_ids.add(case['id'])
            all_queries.add(identity)
    print(f'PASS: {len(all_ids)} cases, frozen hashes, evidence locations, patterns and corpus file lists')


if __name__ == '__main__':
    validate()
