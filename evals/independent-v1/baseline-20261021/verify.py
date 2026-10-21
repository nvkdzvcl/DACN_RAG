import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import zipfile

from dotenv import load_dotenv


def verify():
    directory = Path(__file__).resolve().parent
    root = directory.parents[2]
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    failures = []
    archive = directory / 'snapshot.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        failures.append('snapshot.zip checksum')
    with zipfile.ZipFile(archive) as snapshot:
        if set(snapshot.namelist()) != set(manifest['files']):
            failures.append('snapshot file list')
        for name, digest in manifest['files'].items():
            if hashlib.sha256(snapshot.read(name)).hexdigest() != digest:
                failures.append('snapshot: ' + name)
            path = root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append('workspace: ' + name)
    current_sources = {path.relative_to(root).as_posix() for path in (root / 'app').rglob('*.py')}
    if current_sources != {name for name in manifest['files'] if name.startswith('app/')}:
        failures.append('app Python file list')
    for dataset in manifest['historical_comparison']:
        prefix = f'evals/{dataset}/corpus/'
        current_corpus = {path.relative_to(root).as_posix() for path in (root / prefix).rglob('*') if path.is_file()}
        if current_corpus != {name for name in manifest['files'] if name.startswith(prefix)}:
            failures.append('corpus file list: ' + dataset)
    load_dotenv(root / '.env', override=False)
    for key, expected in manifest['environment'].items():
        if os.getenv(key, manifest['defaults'][key]) != expected:
            failures.append('configuration: ' + key)
    for package, version in manifest['packages'].items():
        if importlib.metadata.version(package) != version:
            failures.append('package: ' + package)
    from app.rag.ollama import call
    models = {model['name']: model['digest'] for model in call('/api/tags', timeout=10)['models']}
    for name, digest in manifest['models'].items():
        if models.get(name) != digest:
            failures.append('model: ' + name)
    if call('/api/version', timeout=10)['version'] != manifest['ollama_version']:
        failures.append('Ollama version')
    if failures:
        raise SystemExit('BASELINE MISMATCH: ' + '; '.join(failures))
    print(f"PASS: {len(manifest['files'])} files, archive, configuration, packages and model digests")
    print('Independent dataset and human approval remain pending. No evaluation performed.')


if __name__ == '__main__':
    verify()
