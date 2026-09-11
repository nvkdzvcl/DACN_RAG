from app.services.order_service import extract_order_id

def test_extract_order_id():
    assert extract_order_id("Kiểm tra đơn ORD-AB12CD") == "ORD-AB12CD"
    assert extract_order_id("Xin chào") is None
