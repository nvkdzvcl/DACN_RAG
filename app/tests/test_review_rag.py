import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.review_rag import main, summarize_reviews


class HumanReviewTests(unittest.TestCase):
    def test_partial_reviews_and_invalid_annotations(self):
        cases = [{'id': str(i), 'should_answer': True, 'error': None, 'answer': {'grounded': i != 2}}
                 for i in range(5)]
        cases[4].update(error={'type': 'ProviderError'}, answer=None)
        rows = [
            {'id': '0', 'reviewer': 'Reviewer A', 'gold_label_approved': True, 'answer_correct': True,
             'all_claims_supported': True, 'citation_entailment_correct': False},
            {'id': '1', 'reviewer': 'Reviewer A', 'gold_label_approved': True, 'answer_correct': False},
            {'id': '2', 'reviewer': 'Reviewer A', 'gold_label_approved': True, 'abstention_correct': False},
            {'id': '3', 'reviewer': 'Reviewer B', 'gold_label_approved': False, 'notes': 'Gold needs correction',
             'answer_correct': True},
            {'id': '4', 'reviewer': 'Reviewer A', 'gold_label_approved': True},
        ]
        report = summarize_reviews(cases, rows)
        self.assertEqual(report['completed_review_cases'], 2)
        self.assertEqual(report['gold_rejected_case_ids'], ['3'])
        self.assertEqual(report['provider_error_case_ids'], ['4'])
        self.assertEqual(report['metrics']['answer_correct'], {'correct': 1, 'rated': 2, 'rate': .5})
        self.assertEqual(report['metrics']['abstention_correct'], {'correct': 0, 'rated': 1, 'rate': 0})
        blank = summarize_reviews(cases, [{'id': '0', 'reviewer': None, 'gold_label_approved': None}])
        self.assertEqual(blank['completed_review_cases'], 0)
        self.assertEqual(blank['gold_pending_cases'], 5)
        self.assertIsNone(blank['metrics']['answer_correct']['rate'])
        for invalid in [rows + [rows[0]], [{'id': 'unknown'}], [rows[0] | {'answer_correct': 'true'}],
                        [rows[0] | {'answer_correct': 1}], [rows[0] | {'reviewer': ' '}],
                        [rows[3] | {'notes': ''}], [rows[0] | {'extra': True}],
                        [rows[0] | {'abstention_correct': True}], [rows[4] | {'abstention_correct': True}]]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                summarize_reviews(cases, invalid)
        with self.assertRaises(ValueError):
            summarize_reviews(cases + [cases[0]], rows)

    def test_cli_checks_run_and_preserves_inputs_and_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'status': 'complete', 'case_ids': ['one']}), encoding='utf-8')
            result = root / 'results.jsonl'
            result.write_text(json.dumps({'id': 'one', 'should_answer': False, 'error': None,
                                          'answer': {'grounded': False}}) + '\n', encoding='utf-8')
            review = root / 'human-review.jsonl'
            review.write_text(json.dumps({'id': 'one', 'reviewer': 'Reviewer', 'gold_label_approved': True,
                                          'abstention_correct': True}) + '\n', encoding='utf-8')
            original = {p: p.read_bytes() for p in (manifest, result, review)}
            output = root / 'summary.json'
            args = ['review_rag', '--run', str(root), '--reviews', str(review), '--output', str(output)]
            with patch('sys.argv', args), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['completed_review_cases'], 1)
            for p, data in original.items():
                self.assertEqual(p.read_bytes(), data)
                self.assertEqual(report['sha256'][str(p.resolve())], hashlib.sha256(data).hexdigest())
            saved_output = output.read_bytes()
            with patch('sys.argv', args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertEqual(output.read_bytes(), saved_output)
            manifest.write_text(json.dumps({'status': 'complete', 'case_ids': ['wrong']}), encoding='utf-8')
            with patch('sys.argv', args[:-1] + [str(root / 'bad.json')]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertFalse((root / 'bad.json').exists())


if __name__ == '__main__':
    unittest.main()
