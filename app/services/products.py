"""Product catalogue shared by the staff API and the Telegram /products command."""
from app.models.support import PRODUCT_CATEGORIES, Product

CATEGORY_LABELS = {'phone': '📱 Điện thoại', 'laptop': '💻 Laptop', 'tablet': '📲 Máy tính bảng',
                   'watch': '⌚ Đồng hồ', 'accessory': '🎧 Phụ kiện', 'other': '📦 Khác'}
assert set(CATEGORY_LABELS) == set(PRODUCT_CATEGORIES)


def price_text(price):
    return 'Liên hệ' if price is None else f'{price:,}'.replace(',', '.') + '₫'


def product_data(product):
    return {'id': product.id, 'name': product.name, 'category': product.category, 'price': product.price,
            'in_stock': product.in_stock, 'active': product.active, 'url': product.url,
            'description': product.description, 'updated_at': product.updated_at}


def visible(db, category=None):
    """Active products for customers, by name."""
    query = db.query(Product).filter(Product.active.is_(True))
    if category:
        query = query.filter(Product.category == category)
    return query.order_by(Product.name).all()


def category_counts(db):
    counts = {}
    for product in visible(db):
        counts[product.category] = counts.get(product.category, 0) + 1
    return [(category, counts[category]) for category in PRODUCT_CATEGORIES if counts.get(category)]
