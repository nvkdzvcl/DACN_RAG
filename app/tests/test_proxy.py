"""ORIGIN_SECRET: only the frontend proxy reaches the API, and rate limits count visitors, not the proxy."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.widget import COOKIE_PATH, _attempts
from app.main import app

SECRET = 'a' * 64


class ProxyTests(unittest.TestCase):
    def setUp(self):
        _attempts.clear()
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_without_secret_nothing_changes(self):
        with patch.dict('os.environ', {'ORIGIN_SECRET': ''}):
            self.assertEqual(self.client.get('/api/v1/health').status_code, 200)
            self.assertNotEqual(self.client.get(COOKIE_PATH + '/session').status_code, 403)

    def test_direct_requests_are_refused_except_the_health_check(self):
        with patch.dict('os.environ', {'ORIGIN_SECRET': SECRET}):
            self.assertEqual(self.client.get('/api/v1/health').status_code, 200)
            self.assertEqual(self.client.get(COOKIE_PATH + '/session').status_code, 403)
            self.assertEqual(self.client.get('/docs').status_code, 403)
            self.assertEqual(self.client.get(COOKIE_PATH + '/session', headers={'x-origin-secret': 'wrong'}).status_code, 403)
            self.assertEqual(self.client.get(COOKIE_PATH + '/session', headers={'x-origin-secret': SECRET}).status_code, 401)

    def test_rate_limit_counts_each_visitor_behind_the_proxy(self):
        def start(ip, secret=SECRET):
            return self.client.post(COOKIE_PATH + '/session', json={'display_name': 'Khách'},
                                    headers={'x-origin-secret': secret, 'x-real-ip': ip, 'X-CSRF-Protection': '1'})
        with patch.dict('os.environ', {'ORIGIN_SECRET': SECRET}), patch('app.api.widget.process_message'):
            # Six session starts per minute per visitor; a seventh from the same visitor is limited.
            statuses = [start('203.0.113.7').status_code for _ in range(7)]
            self.assertEqual(statuses[-1], 429, statuses)
            # Another visitor through the same proxy is not affected.
            self.assertNotEqual(start('198.51.100.20').status_code, 429)
            # A garbage x-real-ip falls back to the socket address instead of creating new buckets.
            start('not-an-ip')
            self.assertIn(('session', 'testclient'), _attempts)


if __name__ == '__main__':
    unittest.main()
