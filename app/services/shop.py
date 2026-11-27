"""Telegram shop: "Mua ngay" remembers the product; the next number the customer sends is the quantity.

Placing the order takes the units from stock in one conditional UPDATE (two buyers cannot take the
same last units), creates a processing order with the transfer amount, and clears the pending product.
"""
import time
from datetime import datetime, timezone

from sqlalchemy import update

from app.models.support import Order, Product
from app.services import payment

PENDING_SECONDS = 15 * 60


def pending(peer, now=None):
    now = now or int(time.time())
    return peer.pending_product_id if peer.pending_product_id and peer.pending_at and now - peer.pending_at <= PENDING_SECONDS else None


def buyable(product):
    return product is not None and product.active and product.price is not None and product.stock > 0


def start(db, peer, product_id):
    product = db.get(Product, product_id)
    if not buyable(product):
        peer.pending_product_id, peer.pending_at = None, None
        return 'none'
    peer.pending_product_id, peer.pending_at = product.id, int(time.time())
    return 'ok'


def place(db, peer, quantity):
    """Returns (outcome, order or None). Outcomes: ok, zero, over, gone."""
    from app.api.workspace import new_order_id
    product = db.get(Product, peer.pending_product_id)
    if quantity < 1:
        return 'zero', None
    if not buyable(product):
        peer.pending_product_id, peer.pending_at = None, None
        return 'gone', None
    taken = db.execute(update(Product).where(Product.id == product.id, Product.stock >= quantity)
                       .values(stock=Product.stock - quantity))
    if taken.rowcount != 1:
        return 'over', None
    db.refresh(product)
    product.in_stock = product.stock > 0
    config = payment.settings(db)
    amount = product.price * quantity
    order = Order(id=new_order_id(db), customer_id=peer.customer_id, status='processing', product_id=product.id,
                  quantity=quantity, unit_price=product.price, amount=amount, pay_amount=payment.pay_amount(amount, config),
                  created_at=datetime.now(timezone.utc))
    db.add(order)
    peer.pending_product_id, peer.pending_at = None, None
    db.flush()
    return 'ok', order
