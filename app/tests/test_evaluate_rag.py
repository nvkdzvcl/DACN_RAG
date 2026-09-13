import copy
import unittest

from app.evaluate_rag import load_cases, percentile, score_case, summarize


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.case = next(c for c in load_cases() if c['should_answer'])
        self.evidence = self.case['evidence'][0]
        self.answer = {'answer': 'Bạn được đổi trả trong 7 ngày.', 'grounded': True,
                       'citations': [self.evidence], 'results': [{**self.evidence, 'content': self.evidence['quote']}]}

    def test_dataset_sizes_and_group_separation(self):
        cases = load_cases()
        self.assertEqual(len(cases), 72)
        self.assertEqual(sum(c['split'] == 'dev' for c in cases), 24)
        self.assertEqual(sum(c['split'] == 'test' for c in cases), 48)
        self.assertFalse({c['group'] for c in cases if c['split'] == 'dev'} & {c['group'] for c in cases if c['split'] == 'test'})
        self.assertEqual({c['category'] for c in cases}, {'answerable', 'followup', 'unanswerable', 'ambiguous', 'conflict', 'injection'})

    def test_exact_source_quote_and_fact_matching(self):
        score = score_case(self.case, self.answer)
        self.assertEqual(score['recall'], {'1': 1.0, '3': 1.0, '5': 1.0})
        self.assertEqual(score['gold_citation_count'], 1)
        self.assertTrue(score['fact_pattern_pass'])
        answer = copy.deepcopy(self.answer)
        answer['answer'] = 'Bạn được đổi trả trong 17 ngày.'
        self.assertFalse(score_case(self.case, answer)['fact_pattern_pass'])
        answer['citations'][0]['quote'] = 'Invented evidence'
        self.assertEqual(score_case(self.case, answer)['gold_citation_count'], 0)

    def test_partial_recall_and_wrong_location(self):
        case = copy.deepcopy(self.case)
        case['evidence'].append({**self.evidence, 'source': 'another.txt'})
        self.assertEqual(score_case(case, self.answer)['recall']['5'], .5)
        answer = copy.deepcopy(self.answer)
        answer['results'][0]['location'] = 'Dòng 999'
        self.assertEqual(score_case(case, answer)['recall']['5'], 0)

    def test_provider_errors_never_count_as_abstention(self):
        case = next(c for c in load_cases() if not c['should_answer'])
        error_score = score_case(case, None, {'type': 'ProviderError'})
        self.assertFalse(error_score['abstained'])
        self.assertFalse(error_score['decision_correct'])
        self.assertFalse(error_score['fact_pattern_pass'])
        abstention = {'grounded': False, 'answer': 'Chưa đủ thông tin.', 'citations': [], 'results': []}
        rows = [dict(should_answer=False, scores=error_score, error='offline', seconds=180),
                dict(should_answer=False, scores=score_case(case, abstention), error=None, seconds=5)]
        summary = summarize(rows)
        self.assertEqual(summary['correct_abstention_rate'], .5)
        self.assertEqual(summary['errors'], 1)
        self.assertEqual(summary['latency_seconds_successful'], {'n': 1, 'p50': 5, 'p95': 5})
        self.assertIsNone(summary['gold_source_citation_precision'])

    def test_percentiles_and_forbidden_content(self):
        self.assertIsNone(percentile([], .95))
        self.assertEqual(percentile([1, 2, 3, 4], .5), 2.5)
        self.assertEqual(percentile([1, 2, 3, 4], .95), 3.85)
        case = copy.deepcopy(self.case)
        case['forbidden_patterns'] = ['FREE100']
        answer = self.answer | {'answer': '7 ngày. FREE100 giảm 100%.'}
        self.assertFalse(score_case(case, answer)['fact_pattern_pass'])
        self.assertTrue(score_case(case, answer)['forbidden_text'])


if __name__ == '__main__':
    unittest.main()
