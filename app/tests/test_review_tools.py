from copy import deepcopy
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.evaluate_tools import Case, summarize
from app.review_tools import main, make_template, merge_reviews, read_run, render_html, summarize_reviews


class ToolReviewTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        case = Case(id='correct', category='access', query='Tra DH78216', scope='owner',
                    expected_route='lookup', expected_lookup='found', rationale='Owned order').model_dump()
        row = dict(case, route='lookup', lookup='found', trace=None, answer='Order', error=None, seconds=1.0,
                   selector_calls=1, rag_stub_calls=0, private_data_leaked=False, order_mutated=False, passed=True)
        self.rows = [row, dict(row, id='wrong', route='rag', lookup='none', passed=False),
                     dict(row, id='offline', route='error', lookup='none', error='Unavailable', passed=False)]
        self.write('manifest.json', {'cases': [{key: row[key] for key in Case.model_fields} for row in self.rows]})
        (self.folder / 'results.jsonl').write_text('\n'.join(json.dumps(row) for row in self.rows), encoding='utf-8')
        self.write('summary.json', summarize(self.rows))
        self.rows, self.run_hash, _ = read_run(self.folder)
        self.reviews = make_template(self.rows, self.run_hash)

    def write(self, name, data):
        (self.folder / name).write_text(json.dumps(data), encoding='utf-8')

    def test_blank_and_partial_reviews_do_not_claim_full_quality(self):
        report = summarize_reviews(self.rows, self.run_hash, self.reviews)
        self.assertEqual(report['approved_cases'], 0)
        self.assertIsNone(report['accuracy_against_approved_labels'])
        self.assertEqual(len(report['pending_case_ids']), 3)
        self.reviews[0].update(reviewer='Tester', gold_label_approved=True)
        self.reviews[1].update(reviewer='Tester', gold_label_approved=False, notes='Ambiguous requirement')
        report = summarize_reviews(self.rows, self.run_hash, self.reviews[:2])
        self.assertEqual(report['accuracy_against_approved_labels'], 1)
        self.assertEqual(report['rejected_case_ids'], ['wrong'])
        self.assertEqual(report['pending_case_ids'], ['offline'])
        self.assertFalse(report['all_labels_approved'])

    def test_provider_errors_remain_in_approved_denominator(self):
        for review in self.reviews:
            review.update(reviewer='Tester', gold_label_approved=True)
        report = summarize_reviews(self.rows, self.run_hash, self.reviews)
        self.assertEqual(report['accuracy_against_approved_labels'], 1 / 3)
        self.assertEqual(report['errors_among_approved'], 1)
        self.assertEqual(report['error_case_ids'], ['offline'])
        self.assertTrue(report['all_labels_approved'])

    def test_merge_preserves_assigned_decisions_pending_notes_and_evidence(self):
        first, second = deepcopy(self.reviews), deepcopy(self.reviews)
        first[0].update(reviewer='Reviewer A', gold_label_approved=True)
        second[1].update(reviewer='Reviewer B', gold_label_approved=False, notes='Needs clarification')
        second[2].update(reviewer='Reviewer B', notes='Waiting for policy owner')
        inputs = deepcopy([first, second])
        merged = merge_reviews(self.rows, self.run_hash, [first, second, first])
        self.assertEqual([first, second], inputs)
        self.assertEqual(merged, merge_reviews(self.rows, self.run_hash, [second, first]))
        self.assertEqual([item['case'] for item in merged], self.rows)
        self.assertEqual(merged[2]['notes'], 'Waiting for policy owner')
        report = summarize_reviews(self.rows, self.run_hash, merged)
        self.assertEqual(report['approved_cases'], 1)
        self.assertEqual(report['rejected_case_ids'], ['wrong'])
        self.assertEqual(report['pending_case_ids'], ['offline'])
        self.assertEqual(merge_reviews(self.rows, self.run_hash, [[], self.reviews]), self.reviews)

    def test_merge_conflicts_and_invalid_inputs_never_write_or_overwrite(self):
        first = deepcopy(self.reviews)
        first[0].update(reviewer='Reviewer A', gold_label_approved=True)
        self.write('first.json', first)
        base = ['review_tools', '--run', str(self.folder), '--merge', str(self.folder/'first.json'),
                str(self.folder/'second.json'), '--output', str(self.folder/'merged.json')]
        second = deepcopy(self.reviews)
        for edit in ({'reviewer': 'Reviewer B', 'gold_label_approved': True},
                     {'reviewer': 'Reviewer A', 'gold_label_approved': False, 'notes': 'Disagree'},
                     {'reviewer': 'Reviewer A', 'notes': 'Pending discussion'}):
            second[0] = dict(self.reviews[0], **edit)
            self.write('second.json', second)
            with self.subTest(edit=edit), patch('sys.argv', base), self.assertRaisesRegex(SystemExit, '1'):
                main()
            self.assertFalse((self.folder/'merged.json').exists())
        for invalid in (None, [dict(first[0], run_sha256='wrong')], first + first[:1]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                merge_reviews(self.rows, self.run_hash, [first, invalid])
        self.write('second.json', self.reviews)
        original = {name: (self.folder/name).read_bytes() for name in ('first.json', 'second.json')}
        with patch('app.rag.ollama.call', side_effect=AssertionError('No model calls')), patch('builtins.print'):
            with patch('sys.argv', base):
                main()
            self.assertEqual(json.loads((self.folder/'merged.json').read_bytes()), first)
            saved = (self.folder/'merged.json').read_bytes()
            with patch('sys.argv', base), self.assertRaises(SystemExit):
                main()
            self.assertEqual((self.folder/'merged.json').read_bytes(), saved)
            with patch('sys.argv', base[:-1] + [str(self.folder/'merged.html'), '--html']):
                main()
            self.assertIn('Reviewer A', (self.folder/'merged.html').read_text(encoding='utf-8'))
        self.assertEqual(original, {name: (self.folder/name).read_bytes() for name in original})

    def test_rejects_wrong_run_changed_evidence_duplicates_and_invalid_decisions(self):
        invalid = [dict(self.reviews[0], run_sha256='wrong'), dict(self.reviews[0], id='foreign'),
                   dict(self.reviews[0], reviewer=' ', gold_label_approved=True),
                   dict(self.reviews[0], reviewer='Tester', gold_label_approved=False),
                   dict(self.reviews[0], reviewer='Tester', gold_label_approved='true'),
                   dict(self.reviews[0], reviewer='Tester', gold_label_approved=1),
                   dict(self.reviews[0], unexpected=True)]
        altered = deepcopy(self.reviews[0])
        altered['case']['passed'] = False
        invalid.append(altered)
        altered_type = deepcopy(self.reviews[0])
        altered_type['case']['passed'] = 1
        invalid.append(altered_type)
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                summarize_reviews(self.rows, self.run_hash, [item])
        with self.assertRaises(ValueError):
            summarize_reviews(self.rows, self.run_hash, self.reviews + self.reviews[:1])

    def test_incomplete_or_inconsistent_runs_are_rejected(self):
        for filename, data in [('manifest.json', {'cases': []}), ('summary.json', {})]:
            original = (self.folder / filename).read_bytes()
            self.write(filename, data)
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                read_run(self.folder)
            (self.folder / filename).write_bytes(original)
        self.rows[0]['passed'] = False
        (self.folder / 'results.jsonl').write_text('\n'.join(json.dumps(row) for row in self.rows), encoding='utf-8')
        self.write('summary.json', summarize(self.rows))
        with self.assertRaises(ValueError):
            read_run(self.folder)

    def test_cli_never_calls_model_or_overwrites_input(self):
        form = self.folder / 'reviews.json'
        report = self.folder / 'review-summary.json'
        inputs = {p.name: p.read_bytes() for p in self.folder.iterdir()}
        base = ['review_tools', '--run', str(self.folder)]
        with patch('app.rag.ollama.call', side_effect=AssertionError('No model calls')), patch('builtins.print'):
            with patch('sys.argv', base + ['--output', str(form)]):
                main()
            original = form.read_bytes()
            with patch('sys.argv', base + ['--reviews', str(form), '--output', str(report)]):
                main()
            self.assertIsNone(json.loads(report.read_text(encoding='utf-8'))['accuracy_against_approved_labels'])
            with patch('sys.argv', base + ['--output', str(form)]), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(form.read_bytes(), original)
        self.assertEqual(inputs, {name: (self.folder / name).read_bytes() for name in inputs})

    def test_html_preserves_frozen_json_and_escapes_untrusted_text(self):
        self.rows[0]['query'] = '</script><img src=x onerror=alert(1)>'
        page = render_html(self.rows, self.run_hash)
        self.assertNotIn(self.rows[0]['query'], page)
        payload = json.loads(re.search(r'<script type="application/json"[^>]*>(.*?)</script>', page, re.S).group(1))
        self.assertEqual(json.loads(payload[0]['case_json']), self.rows[0])
        self.assertIn('"seconds": 1.0', payload[0]['case_json'])
        self.assertTrue(all(row['gold_label_approved'] is None for row in payload))
        self.assertIn("connect-src 'none'", page)

    def test_html_resumes_only_valid_ratings_and_cli_rejects_null_input(self):
        self.reviews[0].update(reviewer='Tester', gold_label_approved=True)
        page = render_html(self.rows, self.run_hash, self.reviews[:1])
        payload = json.loads(re.search(r'<script type="application/json"[^>]*>(.*?)</script>', page, re.S).group(1))
        self.assertTrue(payload[0]['gold_label_approved'])
        self.assertIsNone(payload[1]['gold_label_approved'])
        self.reviews[0]['run_sha256'] = 'other-run'
        with self.assertRaises(ValueError):
            render_html(self.rows, self.run_hash, self.reviews)
        self.write('invalid.json', None)
        with patch('sys.argv', ['review_tools', '--run', str(self.folder), '--reviews', str(self.folder/'invalid.json'),
                               '--html', '--output', str(self.folder/'invalid.html')]), self.assertRaises(SystemExit):
            main()
        self.assertFalse((self.folder/'invalid.html').exists())


if __name__ == '__main__':
    unittest.main()
