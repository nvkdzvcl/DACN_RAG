import argparse
from pathlib import Path
import re
from unittest.mock import patch

from dotenv import load_dotenv

from app.evaluate_rag import load_cases, run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--include-controls', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.name):
        raise ValueError('Invalid run name')
    root = Path(__file__).resolve().parents[3]
    load_dotenv(root / '.env', override=False)
    datasets = {
        'evals/independent-v1/customer-v2/main': {'customer-022'},
        'evals/independent-v1/customer-v2/reserve': {'customer-053'},
        'evals/rag-context': {'context-005', 'context-008'},
    }
    if args.include_controls:
        datasets['evals/independent-v1/customer-v2/main'].update({'customer-021', 'customer-026', 'customer-035'})
    failures = []
    for repeat in range(1, 4):
        for name, ids in datasets.items():
            dataset = root / name
            cases = [case for case in load_cases(dataset / 'cases.jsonl') if case['id'] in ids]
            assert {case['id'] for case in cases} == ids
            output = dataset / 'runs' / f'{args.name}-r{repeat}'
            with patch('app.evaluate_rag.load_cases', return_value=cases):
                summary = run('test', output, dataset)
            if summary['errors'] or summary['fact_pattern_pass_rate'] != 1:
                failures.append(str(output.relative_to(root)))
    if failures:
        raise AssertionError('Target failures: ' + ', '.join(failures))
    print(f'PASS: {sum(map(len, datasets.values()))} cases passed three sequential end-to-end runs; not independent acceptance.')


if __name__ == '__main__':
    main()
