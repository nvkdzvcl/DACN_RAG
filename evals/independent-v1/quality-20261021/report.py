import argparse
import hashlib
import json
from pathlib import Path
import re

from app.evaluate_rag import load_cases, normalize, score_case, summarize

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_run(dataset, name, cases):
    directory = dataset / 'runs' / name
    manifest = read_json(directory / 'manifest.json')
    if manifest['status'] not in {'complete', 'complete_with_errors'}:
        raise ValueError('Incomplete run: ' + str(directory))
    rows = [json.loads(line) for line in (directory / 'results.jsonl').read_text(encoding='utf-8').splitlines()]
    if ([row['id'] for row in rows] != [case['id'] for case in cases]
            or manifest['case_ids'] != [row['id'] for row in rows]
            or manifest['completed_cases'] != len(rows)):
        raise ValueError('Missing, duplicate or reordered cases: ' + str(directory))
    for row, case in zip(rows, cases, strict=True):
        if row['query'] != case['query'] or row['history'] != case['history']:
            raise ValueError('Cannot compare different inputs: ' + row['id'])
    return [{**row, **case, 'scores': score_case(case, row['answer'], row['error'])}
            for row, case in zip(rows, cases, strict=True)]


def passed(rows):
    return sum(row['scores']['fact_pattern_pass'] for row in rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.name):
        raise ValueError('Invalid run name')
    runtime = read_json(DIRECTORY / (args.name + '-runtime.json'))
    datasets = [ROOT / 'evals/independent-v1/customer-v2' / part for part in ('main', 'reserve')]
    datasets += [ROOT / 'evals' / name for name in ('rag', 'bt20', 'rag-context', 'rag-documents', 'rag-policy')]
    expected = [(dataset / 'runs' / args.name).relative_to(ROOT).as_posix() for dataset in datasets]
    if runtime['status'] != 'complete' or runtime['runs'] != expected:
        raise ValueError('All seven datasets must finish before reporting')
    report = {'run_name': args.name, 'human_approved': False, 'datasets': [], 'label_comparison': []}
    all_rows = []
    for dataset in datasets:
        cases = [case for case in load_cases(dataset / 'cases.jsonl') if case['split'] == 'test']
        rows = load_run(dataset, args.name, cases)
        manifest = read_json(dataset / 'runs' / args.name / 'manifest.json')
        if any(manifest['sha256'].get(name) != digest for name, digest in runtime['sha256'].items()):
            raise ValueError('Mixed runtime versions: ' + str(dataset))
        for name, digest in manifest['sha256'].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Frozen input changed: ' + name)
        previous = load_run(Path(str(dataset).replace('customer-v2', 'customer-v1')), 'safety-final-20261021', cases)
        mismatches = []
        for row in rows:
            answer = row['answer'] or {}
            for citation in answer.get('citations', []):
                if not normalize(citation.get('quote', '')) or not any(
                        citation.get('chunk_id') == source.get('chunk_id')
                        and citation.get('document_id') == source.get('document_id')
                        and normalize(citation['quote']) in normalize(source['content'])
                        for source in answer.get('results', [])):
                    mismatches.append(row['id'])
        report['datasets'].append({
            'dataset': dataset.relative_to(ROOT).as_posix(), 'summary': summarize(rows),
            'passed': passed(rows), 'previous_passed_same_labels': passed(previous),
            'quote_mismatch_cases': sorted(set(mismatches)),
            'gained': [row['id'] for old, row in zip(previous, rows, strict=True)
                       if not old['scores']['fact_pattern_pass'] and row['scores']['fact_pattern_pass']],
            'regressed': [row['id'] for old, row in zip(previous, rows, strict=True)
                          if old['scores']['fact_pattern_pass'] and not row['scores']['fact_pattern_pass']],
            'failures': [{'id': row['id'], 'category': row['category'], 'query': row['query'],
                          'expected': row['expected_answer'], 'answer': row['answer'], 'error': row['error']}
                         for row in rows if not row['scores']['fact_pattern_pass']],
        })
        all_rows.extend(rows)
    assert len(all_rows) == 240
    report['summary'] = summarize(all_rows)
    report['by_category'] = {category: summarize([row for row in all_rows if row['category'] == category])
                             for category in sorted({row['category'] for row in all_rows})}
    for run_name in ('baseline-20261021', 'safety-final-20261021', args.name):
        scores = {}
        for version in ('customer-v1', 'customer-v2'):
            rescored = []
            for part in ('main', 'reserve'):
                cases = load_cases(ROOT / 'evals/independent-v1' / version / part / 'cases.jsonl')
                source_version = 'customer-v2' if run_name == args.name else 'customer-v1'
                rescored.extend(load_run(ROOT / 'evals/independent-v1' / source_version / part, run_name, cases))
            scores[version] = passed(rescored)
        report['label_comparison'].append({'run': run_name, **scores})
    lines = ['# RAG quality regression - 2026-10-21', '',
             '240 real Ollama cases in temporary DB/Qdrant stores, not customer data. Labels v2 are AI proposals awaiting human approval.',
             'Regression only, not independent acceptance. Model unchanged; answer review remains mandatory.', '',
             '## Same-label comparison', '',
             '| Dataset | Safety (rescored on same labels) | This run | Service errors | p50 / p95 (s) |',
             '|---|---:|---:|---:|---:|']
    for item in report['datasets']:
        summary = item['summary']
        latency = summary['latency_seconds_successful']
        lines.append(f"| {item['dataset']} | {item['previous_passed_same_labels']}/{summary['cases']} | "
                     f"{item['passed']}/{summary['cases']} | {summary['errors']} | {latency['p50']} / {latency['p95']} |")
    lines += ['', '## Label changes versus runtime changes', '',
              'OFFLINE rescoring of saved answers, not additional Ollama calls. V1/v2 differ only in labels 024/048/051.', '',
              '| Runtime | Labels v1 /60 | Labels v2 /60 |', '|---|---:|---:|']
    for item in report['label_comparison']:
        lines.append(f"| {item['run']} | {item['customer-v1']} | {item['customer-v2']} |")
    lines += ['', '## Gains, regressions and failures', '']
    for item in report['datasets']:
        lines += [f"### {item['dataset']}", '', f"Gained: {', '.join(item['gained']) or 'none'}.",
                  f"Regressed: {', '.join(item['regressed']) or 'none'}.",
                  f"Quotes missing from retrieved chunks: {', '.join(item['quote_mismatch_cases']) or 'none'}.", '']
        for failure in item['failures']:
            lines += [f"#### {failure['id']} ({failure['category']})", '', failure['query'], '',
                      'Expected: ' + failure['expected'], '', 'Actual:', '',
                      (failure['answer'] or {}).get('answer', str(failure['error'])), '']
    lines += ['## Limits and next steps', '',
              '- Human review is still required for failures and three proposed labels; human-review.jsonl remains blank.',
              '- Freeze code/model/corpus and thresholds before another team authors a new held-out set; these 60 cases are development data.',
              '- Regex and role-block filters cover tested patterns, not arbitrary prompt injection.',
              '- Verbatim quotes do not prove semantic correctness/completeness. One run does not prove model stability.',
              '- Interrupted quality-v1-20261021 results are excluded from final counts.', '']
    (DIRECTORY / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DIRECTORY / 'KET_QUA.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'passed': passed(all_rows), 'cases': len(all_rows), 'errors': report['summary']['errors'],
                      'label_comparison': report['label_comparison']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
