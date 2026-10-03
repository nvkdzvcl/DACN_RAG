import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.evaluate_tools import Case, DATASET, load_cases, run_case, summarize
from app.rag.ollama import ProviderError


class EvaluateToolsTests(unittest.TestCase):
    def test_dataset_validation_and_unique_ids(self):
        cases = load_cases(DATASET)
        self.assertEqual(len(cases), 24)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cases.jsonl'
            for text in ('', cases[0].model_dump_json() + '\n' + cases[0].model_dump_json(),
                         json.dumps(cases[0].model_dump() | {'query': '   '}),
                         json.dumps(cases[0].model_dump() | {'expected_route': 'invented'})):
                path.write_text(text, encoding='utf-8')
                with self.subTest(text=text[:50]), self.assertRaises(ValueError):
                    load_cases(path)

    def test_real_routing_and_permission_scoring_with_mocked_transport(self):
        rows = []
        for scope, route, lookup in [('owner', 'lookup', 'found'), ('anonymous', 'handoff', 'denied'),
                                     ('granted', 'lookup', 'found'), ('expired', 'handoff', 'denied')]:
            case = Case(id=scope, category='access', query='Tra DH78216', scope=scope,
                        expected_route=route, expected_lookup=lookup, rationale='Fixture scope')
            with patch('app.services.tool_service.chat', return_value=json.dumps({
                    'name': 'lookup_order', 'arguments': {'order_id': 'DH78216'}})):
                row = run_case(case)
            self.assertTrue(row['passed'], row)
            self.assertEqual(row['selector_calls'], 1)
            self.assertEqual(row['rag_stub_calls'], 0)
            rows.append(row)
        with patch('app.services.tool_service.chat', side_effect=ProviderError('Unavailable')):
            failed = run_case(case)
        self.assertFalse(failed['passed'])
        self.assertEqual(failed['route'], 'error')
        result = summarize(rows + [failed])
        self.assertEqual((result['cases'], result['passed'], result['errors']), (5, 4, 1))
        self.assertEqual(result['accuracy_against_draft_labels'], .8)
        self.assertEqual(result['human_reviewed_cases'], 0)

    def test_rag_stub_is_explicit_and_wrong_route_is_not_a_pass(self):
        case = load_cases(DATASET)[0]
        with patch('app.services.tool_service.chat', return_value=json.dumps({
                'name': 'rag', 'arguments': {'order_id': 'DH78216'}})):
            row = run_case(case)
        self.assertEqual((row['route'], row['rag_stub_calls'], row['answer']), ('rag', 1, 'EVAL_RAG_BRANCH_ONLY'))
        self.assertFalse(row['passed'])

    def test_followup_rechecks_grants_and_keeps_policy_and_cancellation_routes(self):
        for scope in ('owner', 'anonymous', 'granted', 'expired'):
            for action, query in [('lookup_order', 'Mã vận đơn của đơn đó là gì?'),
                                  ('rag', 'Chính sách giao hàng của đơn đó thế nào?'),
                                  ('handoff', 'Đơn đó đang ở đâu? Nếu chưa giao thì hủy giúp tôi.')]:
                permitted = scope in ('owner', 'granted')
                route = ('lookup' if permitted else 'handoff') if action == 'lookup_order' else action
                lookup = ('found' if permitted else 'denied') if action == 'lookup_order' else 'none'
                case = Case(id='followup', category='followup', scope=scope, query=query,
                            history=[{'sender': 'customer', 'content': 'Tra DH78216'}],
                            expected_route=route, expected_lookup=lookup, rationale='Current grant and selected action')
                with self.subTest(scope=scope, action=action), patch('app.services.tool_service.chat', return_value=json.dumps({
                        'name': action, 'arguments': {'order_id': 'DH78216'}})):
                    row = run_case(case)
                    self.assertTrue(row['passed'], row)
                    self.assertEqual(row['trace']['order_id_source'], 'history')


if __name__ == '__main__':
    unittest.main()
