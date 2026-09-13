import copy
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.evaluate_rag import ROOT, chat_model, embedding_model, load_cases, percentile, run, score_case, summarize


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

    def test_document_fixtures_have_real_pages_paragraphs_and_table_rows(self):
        cases = load_cases(ROOT / 'evals/rag-documents/cases.jsonl')
        self.assertEqual(len(cases), 24)
        self.assertEqual(sum(c['should_answer'] for c in cases), 14)
        evidence = [e for c in cases for e in c['evidence']]
        self.assertEqual({e['page'] for e in evidence if e['source'].endswith('.pdf')}, {1, 2, 3})
        self.assertTrue(any(e['location'].startswith('Đoạn ') for e in evidence))
        self.assertTrue(any(e['location'].startswith('Bảng ') for e in evidence))
        self.assertTrue(all(c['review_status'] == 'pending_human_review' for c in cases))

    def test_pdf_scoring_requires_matching_page_even_if_location_matches(self):
        case = load_cases(ROOT / 'evals/rag-documents/cases.jsonl')[0]
        evidence = case['evidence'][0]
        answer = {'answer': evidence['quote'], 'grounded': True, 'citations': [evidence],
                  'results': [evidence | {'content': evidence['quote']}]}
        self.assertTrue(score_case(case, answer)['fact_pattern_pass'])
        wrong = copy.deepcopy(answer)
        wrong['citations'][0]['page'] = 2
        wrong['results'][0]['page'] = 2
        score = score_case(case, wrong)
        self.assertEqual(score['recall']['5'], 0)
        self.assertEqual(score['gold_citation_count'], 0)

    def test_gold_validation_rejects_wrong_location_or_escaping_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'corpus').mkdir()
            (root / 'corpus/test-source.txt').write_text('Policy 36 hours.', encoding='utf-8')
            case = copy.deepcopy(self.case)
            case['split'] = 'test'
            case['evidence'] = [{'source': 'test-source.txt', 'location': 'Dòng 1', 'quote': 'Policy 36 hours.'}]
            def load(evidence):
                (root / 'cases.jsonl').write_text(json.dumps(case | {'evidence': [evidence]}), encoding='utf-8')
                return load_cases(root / 'cases.jsonl')
            gold = case['evidence'][0]
            self.assertEqual(len(load(gold)), 1)
            for bad in [gold | {'location': 'Dòng 2'}, gold | {'quote': 'Policy 72 hours.'}, gold | {'page': 9}]:
                with self.subTest(evidence=bad), self.assertRaises(ValueError):
                    load(bad)
            for name in ['../test-source.txt', 'test-dir/source.txt', 'test-dir\\source.txt', 'test-source.txt:stream']:
                with self.subTest(source=name), patch('app.evaluate_rag.extract_sections') as extract, self.assertRaises(ValueError):
                    load(gold | {'source': name})
                extract.assert_not_called()

    def test_run_imports_binary_corpus_and_records_serializable_ingestion(self):
        case = load_cases(ROOT / 'evals/rag-documents/cases.jsonl')[0]
        models = {'models': [{'name': name, 'digest': 'mock-digest'} for name in (chat_model(), embedding_model())]}
        with tempfile.TemporaryDirectory() as directory, patch('app.evaluate_rag.load_cases', return_value=[case]), patch(
                'app.evaluate_rag.call', return_value=models), patch('app.evaluate_rag.VectorStore'), patch(
                'app.evaluate_rag.save_document', return_value={'created_at': datetime.now(), 'status': 'indexed',
                'chunks': 3, 'error_message': None}) as save, patch('app.evaluate_rag.answer_question', return_value={
                'grounded': False, 'answer': 'No evidence', 'citations': [], 'results': []}):
            output = Path(directory) / 'run'
            self.assertEqual(run('test', output, ROOT / 'evals/rag-documents')['cases'], 1)
            self.assertEqual({Path(c.args[1]).suffix for c in save.call_args_list}, {'.pdf', '.docx'})
            ingestion = json.loads((output / 'ingestion.json').read_text())
            self.assertEqual(len(ingestion), 2)
            self.assertTrue(all(row['status'] == 'indexed' and row['chunks'] == 3 for row in ingestion))
            self.assertEqual(json.loads((output / 'manifest.json').read_text())['status'], 'complete')
            with self.assertRaises(FileExistsError):
                run('test', output, ROOT / 'evals/rag-documents')


if __name__ == '__main__':
    unittest.main()
