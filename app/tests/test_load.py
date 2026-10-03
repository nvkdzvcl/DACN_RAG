import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.measure_load import run, summarize


class LoadMeasurementTests(unittest.TestCase):
    def test_nearest_rank_percentiles_keep_expected_conflicts_separate(self):
        samples = [{'operation': 'poll', 'seconds': i / 1000, 'status': 200, 'expected': True} for i in range(1, 21)]
        samples += [{'operation': 'accept', 'seconds': .03, 'status': 409, 'expected': True},
                    {'operation': 'accept', 'seconds': .1, 'status': 0, 'expected': False}]
        result = summarize(samples)
        self.assertEqual((result['poll']['p50_ms'], result['poll']['p95_ms']), (10, 19))
        self.assertEqual(result['accept']['unexpected'], 1)
        self.assertEqual(result['accept']['statuses'], {'0': 1, '409': 1})
        self.assertEqual(summarize([]), {})

    def test_failed_run_is_incomplete_and_existing_results_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'run'
            with patch('app.measure_load.migrate', side_effect=RuntimeError('setup failed')):
                with self.assertRaises(RuntimeError):
                    run(1, 1, 1, output)
            result = json.loads((output / 'results.json').read_text(encoding='utf-8'))
            self.assertFalse(result['complete'])
            self.assertEqual(result['samples'], [])
            original = (output / 'results.json').read_bytes()
            with self.assertRaises(FileExistsError):
                run(1, 1, 1, output)
            self.assertEqual((output / 'results.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
