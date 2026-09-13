import unittest
from app.services.order_service import extract_order_id

class OrderServiceTests(unittest.TestCase):
    def test_extract_order_id(self):
        self.assertEqual(extract_order_id("Kiểm tra đơn ORD-AB12CD"), "ORD-AB12CD")
        self.assertIsNone(extract_order_id("Xin chào"))
