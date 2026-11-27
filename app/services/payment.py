"""Bank transfer (VietQR) settings and the QR image for Telegram shop orders.

The QR image comes from SePay's free VietQR image link (qr.sepay.vn), which returns a PNG that
Telegram can send as a photo; img.vietqr.io now serves SVG only. The payload is the bank, account,
amount and the order ID as transfer content, so any Vietnamese banking app can scan it.
Payments are confirmed by staff (order status "Đã thanh toán"); there is no bank webhook.
"""
from urllib.parse import urlencode

from app.models.support import AppSetting

# BIN codes (State Bank of Vietnam) for the bank picker in Cài đặt.
BANKS = {'970436': 'Vietcombank', '970415': 'VietinBank', '970418': 'BIDV', '970405': 'Agribank',
         '970407': 'Techcombank', '970422': 'MB Bank', '970416': 'ACB', '970432': 'VPBank', '970423': 'TPBank',
         '970403': 'Sacombank', '970441': 'VIB', '970437': 'HDBank', '970443': 'SHB', '970448': 'OCB',
         '970426': 'MSB', '970440': 'SeABank', '970431': 'Eximbank', '970449': 'LPBank', '970428': 'Nam A Bank',
         '970409': 'Bac A Bank'}
DEFAULTS = {'enabled': False, 'bank_bin': '', 'account_no': '', 'account_name': '', 'divisor': 1000}


def settings(db):
    row = db.get(AppSetting, 'payment')
    return {**DEFAULTS, **(row.value if row else {})}


def save(db, value):
    row = db.get(AppSetting, 'payment')
    if row is None:
        db.add(AppSetting(key='payment', value=value))
    else:
        row.value = value


def ready(config):
    return bool(config['enabled'] and config['bank_bin'] in BANKS and config['account_no'] and config['account_name'])


def pay_amount(amount, config):
    """What the customer transfers: the order total divided by the demo divisor (1 = real price), at least 1 VND."""
    return max(1, amount // max(1, int(config.get('divisor') or 1)))


def qr_url(config, amount, content):
    query = urlencode({'acc': config['account_no'], 'bank': config['bank_bin'], 'amount': amount, 'des': content,
                       'template': 'compact'})
    return f'https://qr.sepay.vn/img?{query}'
