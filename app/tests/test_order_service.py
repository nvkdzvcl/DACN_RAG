import unittest
from app.services.order_service import extract_order_id

class OrderServiceTests(unittest.TestCase):
    def test_extract_order_id(self):
        self.assertEqual(extract_order_id("Kiểm tra đơn ORD-AB12CD"), "ORD-AB12CD")
        self.assertIsNone(extract_order_id("Xin chào"))

    def test_complete_ascii_codes_and_length_boundaries(self):
        for code in ('DH1234', 'ORD1234', 'dh_ab12', 'ord-ab12', 'DH' + 'A' * 62,
                     'ORD-' + 'A' * 60):
            with self.subTest(code=code):
                self.assertEqual(extract_order_id(f'Đơn ({code}), kiểm tra giúp.'), code.upper())

    def test_invalid_tokens_are_not_truncated_or_unicode_aliases(self):
        for code in ('DH12345-EXTRA', 'DH12345-', 'x-DH12345', 'DH12345_ABC',
                     'abcDH12345', 'DH12345é', 'DH1234K', 'DH1234ſ', 'DH1234İ',
                     'DH1234ı', 'DH' + 'A' * 63, 'ORD-' + 'A' * 61, 'DH123'):
            with self.subTest(code=code):
                self.assertIsNone(extract_order_id(f'Tra đơn {code}.'))
        self.assertEqual(extract_order_id('DH12345-EXTRA, rồi ORD-AB12'), 'ORD-AB12')
