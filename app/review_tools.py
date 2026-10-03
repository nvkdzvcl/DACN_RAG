"""Prepare label-review forms or score approved tool labels without calling models."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from app.evaluate_tools import Case, summarize


class Result(Case):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=False)
    route: Literal['lookup', 'handoff', 'rag', 'clarification', 'error', 'unknown']
    lookup: Literal['found', 'denied', 'none']
    trace: dict | None
    answer: str | None
    error: str | None
    seconds: float = Field(ge=0, allow_inf_nan=False)
    selector_calls: StrictInt = Field(ge=0)
    rag_stub_calls: StrictInt = Field(ge=0)
    private_data_leaked: StrictBool
    order_mutated: StrictBool
    passed: StrictBool


class Review(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    id: str
    run_sha256: str
    case: dict
    reviewer: str | None = Field(max_length=160)
    gold_label_approved: StrictBool | None
    notes: str = Field(max_length=4000)


def read_run(folder):
    # Parse and hash the same bytes so a concurrent save cannot change provenance.
    inputs = {name: (folder / name).read_bytes() for name in ('manifest.json', 'results.jsonl', 'summary.json')}
    manifest = json.loads(inputs['manifest.json'])
    rows = [Result.model_validate_json(line).model_dump() for line in inputs['results.jsonl'].splitlines() if line.strip()]
    if not rows or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Results require nonempty unique IDs')
    cases = [{key: row[key] for key in Case.model_fields} for row in rows]
    if not isinstance(manifest, dict) or manifest.get('cases') != cases:
        raise ValueError('Result cases must match the frozen manifest in order and content')
    for row in rows:
        passed = (row['error'] is None and row['route'] == row['expected_route'] and
                  row['expected_lookup'] in ('any', row['lookup']) and
                  not row['private_data_leaked'] and not row['order_mutated'])
        if row['passed'] != passed:
            raise ValueError('Stored pass flag does not match the routing evidence')
    if json.loads(inputs['summary.json']) != summarize(rows):
        raise ValueError('Run must be complete with a summary matching every result')
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in inputs.items()}
    run_hash = hashlib.sha256(b'\0'.join(inputs.values())).hexdigest()
    return rows, run_hash, hashes


def make_template(rows, run_hash):
    return [{'id': row['id'], 'run_sha256': run_hash, 'case': row,
             'reviewer': None, 'gold_label_approved': None, 'notes': ''} for row in rows]


def render_html(rows, run_hash, reviews=None):
    if reviews is not None:
        summarize_reviews(rows, run_hash, reviews)
    ratings = {row['id']: row for row in reviews or []}
    forms = make_template(rows, run_hash)
    for form in forms:
        form.update({key: ratings[form['id']][key] for key in ('reviewer', 'gold_label_approved', 'notes')}
                    if form['id'] in ratings else {})
        # Keep JSON number spellings: browser JSON.stringify turns 1.0 into 1, invalidating frozen evidence.
        form['case_json'] = json.dumps(form.pop('case'), ensure_ascii=False)
    payload = json.dumps(forms, ensure_ascii=True).replace('<', '\\u003c')
    template = Path(__file__).with_name('templates') / 'tool_review.html'
    return template.read_text(encoding='utf-8').replace('<!--REVIEW_DATA-->', payload).replace(
        '<!--REVIEW_HASH-->', hashlib.sha256(payload.encode('utf-8')).hexdigest())


def summarize_reviews(rows, run_hash, reviews):
    if not isinstance(reviews, list):
        raise ValueError('Review file must contain a JSON array')
    cases = {row['id']: row for row in rows}
    ratings = {}
    for item in reviews:
        rating = Review.model_validate(item)
        if rating.id not in cases or rating.id in ratings:
            raise ValueError('Review IDs must be unique and belong to the run')
        if (rating.run_sha256 != run_hash or
                json.dumps(rating.case, sort_keys=True) != json.dumps(cases[rating.id], sort_keys=True)):
            raise ValueError('Review belongs to a different run or its read-only case was changed')
        if rating.gold_label_approved is not None and not rating.reviewer:
            raise ValueError('Every decision requires a named reviewer')
        if rating.gold_label_approved is False and not rating.notes:
            raise ValueError('Rejected labels require a reason in notes')
        ratings[rating.id] = rating
    approved = [cases[key] for key, review in ratings.items() if review.gold_label_approved is True]
    rejected = [key for key, review in ratings.items() if review.gold_label_approved is False]
    decided = {row['id'] for row in approved} | set(rejected)
    return {
        'cases': len(rows), 'submitted_rows': len(reviews), 'approved_cases': len(approved),
        'rejected_case_ids': rejected, 'pending_case_ids': [key for key in cases if key not in decided],
        'all_labels_approved': len(approved) == len(rows),
        'passed_among_approved': sum(row['passed'] for row in approved),
        'accuracy_against_approved_labels': sum(row['passed'] for row in approved) / len(approved) if approved else None,
        'errors_among_approved': sum(row['error'] is not None for row in approved),
        'error_case_ids': [row['id'] for row in rows if row['error'] is not None],
        'by_category': {category: {'approved': sum(row['category'] == category for row in approved),
            'passed': sum(row['category'] == category and row['passed'] for row in approved)}
            for category in sorted({row['category'] for row in rows})},
        'rag_is_stubbed': True,
        'scope': 'Named label decisions only; reviewer identity is self-declared, not authenticated. '
                 'Score is recomputed from frozen routing evidence; errors remain in the approved denominator. '
                 'Partial or selected approvals do not estimate whole-dataset quality. '
                 'Label approval does not make a development set independent or assess RAG answer quality.',
    }


def merge_reviews(rows, run_hash, batches):
    forms = {form['id']: form for form in make_template(rows, run_hash)}
    edits = {}
    conflicts = set()
    for batch in batches:
        summarize_reviews(rows, run_hash, batch)
        for item in batch:
            rating = Review.model_validate(item)
            edit = {key: getattr(rating, key) for key in ('reviewer', 'gold_label_approved', 'notes')}
            if not rating.reviewer and rating.gold_label_approved is None and not rating.notes:
                continue
            if rating.id in edits and edits[rating.id] != edit:
                conflicts.add(rating.id)
            edits[rating.id] = edit
    if conflicts:
        raise ValueError('Conflicting review edits; reconcile these IDs before merging: ' + ', '.join(sorted(conflicts)))
    # ponytail: merge assigned subsets only; multiple reviewers per case need a separate adjudication format.
    for case_id, edit in edits.items():
        forms[case_id].update(edit)
    return list(forms.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='Complete tool evaluation directory')
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--reviews', type=Path, help='Filled copy of the JSON review form; omit to create a blank form')
    inputs.add_argument('--merge', type=Path, nargs='+', help='Merge assigned review subsets; conflicting edits fail')
    parser.add_argument('--html', action='store_true', help='Write an offline browser form, optionally seeded by --reviews')
    parser.add_argument('--output', type=Path, required=True, help='New JSON or HTML file; never overwrite')
    args = parser.parse_args()
    try:
        rows, run_hash, hashes = read_run(args.run)
        data = args.reviews.read_bytes() if args.reviews else None
        reviews = json.loads(data) if data is not None else None
        if data is not None and not isinstance(reviews, list):
            raise ValueError('Review file must contain a JSON array')
        if args.merge:
            reviews = merge_reviews(rows, run_hash, [json.loads(path.read_bytes()) for path in args.merge])
        if args.html:
            content = render_html(rows, run_hash, reviews)
        elif args.merge:
            output = reviews
        elif args.reviews is None:
            output = make_template(rows, run_hash)
        else:
            output = summarize_reviews(rows, run_hash, reviews)
            output.update(created_at_utc=datetime.now(timezone.utc).isoformat(), run_sha256=run_hash,
                          input_sha256=hashes, review_sha256=hashlib.sha256(data).hexdigest(),
                          scorer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if not args.html:
            content = json.dumps(output, ensure_ascii=False, indent=2) + '\n'
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(content)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Tool review failed: {exc}\n')
    print(f"{'Browser form' if args.html else 'Merged review form' if args.merge else 'Review summary' if args.reviews else 'Blank review form'} written: {args.output}")


if __name__ == '__main__':
    main()
