from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv

from app.evaluate_rag import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name or any(character not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in args.name):
        raise ValueError('Run name must contain lowercase letters, digits or hyphens')
    root = Path.cwd()
    directory = Path(__file__).resolve().parent
    target = directory / (args.name + '-runtime.json')
    assert not target.exists(), 'Do not overwrite a prior run'
    load_dotenv(root / '.env', override=False)
    paths = sorted((root / 'app').rglob('*.py'))
    digests = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    approval_path = root / 'evals/independent-v1/customer-v2/label-approval.json'
    approval = json.loads(approval_path.read_text(encoding='utf-8')) if approval_path.exists() else None
    manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
                'sha256': digests, 'labels': 'customer-v2; see separate label approval, not independent acceptance',
                'label_approval': approval,
                'run_name': args.name, 'runs': []}
    target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    datasets = [root / 'evals/independent-v1/customer-v2' / partition for partition in ('main', 'reserve')]
    datasets += [root / 'evals' / name for name in ('rag', 'bt20', 'rag-context', 'rag-documents', 'rag-policy')]
    for dataset in datasets:
        for name, digest in digests.items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
        output = dataset / 'runs' / args.name
        print('DATASET', dataset.relative_to(root), flush=True)
        summary = run('test', output, dataset)
        manifest['runs'].append(output.relative_to(root).as_posix())
        target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('SUMMARY', dataset.relative_to(root), json.dumps(summary, ensure_ascii=False), flush=True)
    manifest.update(status='complete', finished_at_utc=datetime.now(timezone.utc).isoformat())
    target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
