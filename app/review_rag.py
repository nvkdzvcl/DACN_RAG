"""Summarize human RAG ratings without calling models or changing benchmark results."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

METRICS = ('answer_correct', 'all_claims_supported', 'citation_entailment_correct', 'abstention_correct')
FIELDS = {'id', 'gold_label_approved', 'reviewer', 'notes', *METRICS}


def summarize_reviews(results, reviews):
    if not isinstance(results, list) or not isinstance(reviews, list):
        raise ValueError('Results and reviews must be lists of records')
    cases, ratings = {}, {}
    for row in results:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip() or row['id'] in cases:
            raise ValueError('Results need unique nonempty case IDs')
        if type(row.get('should_answer')) is not bool or 'error' not in row:
            raise ValueError('Results need should_answer and error fields')
        answer = row.get('answer')
        if row['error'] is None and (not isinstance(answer, dict) or type(answer.get('grounded')) is not bool):
            raise ValueError('Successful results need a grounded boolean')
        cases[row['id']] = row
    if not cases:
        raise ValueError('Results must not be empty')
    for row in reviews:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or row['id'] not in cases or row['id'] in ratings:
            raise ValueError('Reviews need unique IDs matching results')
        if set(row) - FIELDS or any(row.get(k) is not None and type(row[k]) is not bool for k in ('gold_label_approved', *METRICS)):
            raise ValueError('Ratings must be booleans or null; unknown fields are not allowed')
        if (row.get('reviewer') is not None and not isinstance(row['reviewer'], str)) or not isinstance(row.get('notes', ''), str):
            raise ValueError('Reviewer and notes must be text')
        if any(row.get(k) is not None for k in ('gold_label_approved', *METRICS)) and not (row.get('reviewer') or '').strip():
            raise ValueError('A named reviewer is required for every rating')
        if row.get('gold_label_approved') is False and not row.get('notes', '').strip():
            raise ValueError('Rejected gold labels need a reason in notes')
        case = cases[row['id']]
        applicable = METRICS[:3] if case['error'] is None and case['answer']['grounded'] else METRICS[3:]
        if any(row.get(k) is not None for k in METRICS if case['error'] is not None or k not in applicable):
            raise ValueError('Provider errors and inapplicable metrics must keep null ratings')
        ratings[row['id']] = row
    approved = {i: r for i, r in ratings.items() if r.get('gold_label_approved') is True}
    eligible = {i: r for i, r in approved.items() if cases[i]['error'] is None}
    metrics = {}
    for key in METRICS:
        values = [r[key] for r in eligible.values() if r.get(key) is not None]
        metrics[key] = {'correct': sum(values), 'rated': len(values), 'rate': sum(values) / len(values) if values else None}
    complete = [i for i, r in eligible.items()
                if all(r.get(k) is not None for k in (METRICS[:3] if cases[i]['answer']['grounded'] else METRICS[3:]))]
    rejected = [i for i, r in ratings.items() if r.get('gold_label_approved') is False]
    return {'cases': len(cases), 'submitted_rows': len(ratings), 'gold_approved_cases': len(approved),
            'gold_rejected_case_ids': rejected, 'gold_pending_cases': len(cases) - len(approved) - len(rejected),
            'provider_error_case_ids': [i for i, c in cases.items() if c['error'] is not None],
            'completed_review_cases': len(complete), 'pending_review_case_ids': [i for i in cases if i not in complete],
            'metrics': metrics,
            'scope': 'Only named human ratings with approved gold labels; each metric has its own denominator. '
                     'Grounded answers use the first three metrics; abstentions use abstention_correct. '
                     'Provider errors are excluded. Partial or selected reviews do not estimate whole-dataset quality.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path, help='Existing benchmark run directory')
    parser.add_argument('--reviews', required=True, type=Path, help='Human-filled copy of human-review.jsonl')
    parser.add_argument('--output', required=True, type=Path, help='New JSON report; never overwrites a file')
    args = parser.parse_args()
    paths = [args.run / 'manifest.json', args.run / 'results.jsonl', args.reviews, Path(__file__)]
    try:
        # Hash the same bytes that are parsed, even if a reviewer saves their file during this command.
        inputs = {str(p.resolve()): p.read_bytes() for p in paths}
        manifest = json.loads(inputs[str(paths[0].resolve())])
        results, reviews = [[json.loads(s) for s in inputs[str(p.resolve())].decode('utf-8').splitlines() if s.strip()]
                            for p in paths[1:3]]
        if (not isinstance(manifest, dict) or not all(isinstance(r, dict) for r in results) or
                manifest.get('status') not in ('complete', 'complete_with_errors') or
                manifest.get('case_ids') != [r.get('id') for r in results]):
            raise ValueError('Run must be complete and case IDs must match its manifest')
        report = summarize_reviews(results, reviews)
        report.update(created_at_utc=datetime.now(timezone.utc).isoformat(),
                      sha256={p: hashlib.sha256(data).hexdigest() for p, data in inputs.items()})
        content = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(content)
    except (OSError, ValueError, AttributeError) as exc:
        parser.exit(1, f'Review report failed: {exc}\n')
    print(content, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
