import importlib
import json
from pathlib import Path
import tempfile
import unittest

report = importlib.import_module('evals.independent-v1.quality-20261021.report')


class ReportTests(unittest.TestCase):
    def test_complete_run_is_rescored_without_mutating_saved_results(self):
        case = {'id': 'test-001', 'query': 'Question?', 'history': [], 'evidence': [],
                'should_answer': False, 'required_patterns': [], 'forbidden_patterns': []}
        row = {**case, 'answer': {'answer': 'Unknown.', 'grounded': False, 'citations': []},
               'error': None, 'scores': {'fact_pattern_pass': False}}
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory)
            run = dataset / 'runs/example'
            run.mkdir(parents=True)
            manifest = {'status': 'complete', 'case_ids': [case['id']], 'completed_cases': 1}
            (run / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            results = run / 'results.jsonl'
            results.write_text(json.dumps(row) + '\n', encoding='utf-8')
            original = results.read_bytes()
            self.assertEqual(report.passed(report.load_run(dataset, 'example', [case])), 1)
            self.assertEqual(results.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, 'different inputs'):
                report.load_run(dataset, 'example', [{**case, 'query': 'Other?'}])
            results.write_text((json.dumps(row) + '\n') * 2, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Missing, duplicate'):
                report.load_run(dataset, 'example', [case])
            (run / 'manifest.json').write_text(json.dumps({**manifest, 'status': 'incomplete'}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Incomplete'):
                report.load_run(dataset, 'example', [case])


if __name__ == '__main__':
    unittest.main()
