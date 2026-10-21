import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import types
from unittest.mock import Mock, patch

from dotenv import load_dotenv

from app.evaluate_rag import score_case
from app.rag.ollama import call, chat


def main():
    root = Path.cwd()
    directory = Path(__file__).resolve().parent
    target = directory / 'comparison'
    target.mkdir(exist_ok=False)
    load_dotenv(root / '.env', override=False)
    source = (root / 'app/rag/answer_service.py').read_text(encoding='utf-8')
    addition = ('            "Permission and prohibition of the SAME action under the SAME conditions are incompatible policies, "\n'
                '            "even without different numeric values. Quoting both is NOT a resolution: sources_consistent=false. "\n')
    assert source.count(addition) == 1
    variants = {'safety': source, 'original_review': source.replace(addition, '')}
    variants['clause_review'] = variants['original_review'].replace(
        'First reason: briefly identify the exact fact requested and whether CANDIDATE supplies it. ',
        'First reason: quote the decisive source clause in its original language, then name any missing requested fact. '
        'Compare actual CANDIDATE text, never attribute a command from QUESTION to CANDIDATE. '
        'Check every requested subquestion. A short answer may omit unrequested details but not a requested step or data precaution. '
        'A conflict needs incompatible clauses for the same subject and conditions; duplicates and clauses about other services are not conflicts. ')
    modules = {}
    for name, text in variants.items():
        path = target / (name + '.py.txt')
        path.write_text(text, encoding='utf-8')
        module = types.ModuleType('rag_compare_' + name)
        sys.modules[module.__name__] = module
        exec(compile(text, str(path), 'exec'), module.__dict__)
        modules[name] = module
    selections = {
        'evals/independent-v1/customer-v1/main/runs/safety-final-20261021':
            ['customer-003', 'customer-014', 'customer-035', 'customer-043', 'customer-045'],
        'evals/bt20/runs/safety-final-20261021': ['bt20-008', 'bt20-045'],
        'evals/rag-context/runs/safety-final-20261021': ['context-008', 'context-013'],
    }
    cases, input_hashes = [], {}
    for name, ids in selections.items():
        path = root / name / 'results.jsonl'
        input_hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        selected = [row for row in map(json.loads, path.read_text(encoding='utf-8').splitlines()) if row['id'] in ids]
        assert len(selected) == len(ids)
        cases.extend(selected)
    manifest = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
                'kind': 'diagnostic_replay_not_end_to_end', 'rounds': 2, 'cases': len(cases),
                'retrieval': 'fixed saved hits; DB/source-version checks mocked, no ingestion or application DB access',
                'input_sha256': input_hashes, 'models': call('/api/tags'), 'ollama': call('/api/version'),
                'variants_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in variants.items()}}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = []
    for repeat in range(2):
        for index, case in enumerate(cases):
            names = list(modules)
            offset = (repeat + index) % len(names)
            for name in names[offset:] + names[:offset]:
                module = modules[name]
                completions = []
                def capture(*args):
                    response = chat(*args)
                    completions.append(response)
                    return response
                started = time.perf_counter()
                answer, error = None, None
                try:
                    with patch.object(module.vector_store, 'search', return_value=copy.deepcopy(case['answer']['results'])), \
                            patch.object(module, 'sources_current', return_value=True), patch.object(module, 'chat', side_effect=capture):
                        answer = module.answer_question(case['query'], history=case['history'], db=Mock())
                except Exception as exception:
                    error = {'type': type(exception).__name__, 'message': str(exception)}
                result = {'id': case['id'], 'variant': name, 'round': repeat + 1, 'answer': answer, 'error': error,
                          'seconds': round(time.perf_counter() - started, 3), 'scores': score_case(case, answer, error),
                          'raw_completions': completions}
                rows.append(result)
                with (target / 'results.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                print(name, repeat + 1, case['id'], result['scores']['fact_pattern_pass'], flush=True)
    summary = {name: {'pass': sum(row['scores']['fact_pattern_pass'] for row in rows if row['variant'] == name),
                      'cases': sum(row['variant'] == name for row in rows),
                      'errors': sum(row['error'] is not None for row in rows if row['variant'] == name)} for name in modules}
    (target / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    manifest.update(status='complete', finished_at_utc=datetime.now(timezone.utc).isoformat())
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(summary)


if __name__ == '__main__':
    main()
