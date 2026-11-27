"""Telegram bot commands: replies, inline buttons and the "/" menu registered with setMyCommands.

Commands answer from the database and never call the model. Buttons send callback data that
telegram.parse_update turns back into a command line (or, for policy topics, into a question that
the AI answers with sources as usual).
"""
import re
from datetime import datetime, timedelta, timezone

from app.models.support import PRODUCT_CATEGORIES, Conversation, Order, Product
from app.services import payment
from app.services.handoff_service import waiting_info
from app.services.order_service import ORDER_STATUS_LABELS
from app.services.products import CATEGORY_LABELS, category_counts, price_text, visible
from app.services.telegram_link import linked_account, masked

VN = timezone(timedelta(hours=7))

# Shown when the customer types "/" (setMyCommands). /link and /unlink stay usable but unlisted.
BOT_COMMANDS = [('start', '👋 Mở menu chính'), ('products', '🛒 Xem sản phẩm'), ('orders', '📦 Đơn hàng của bạn'),
                ('policies', '📋 Chính sách cửa hàng'), ('human', '🙋 Gặp nhân viên'), ('cancel', '↩️ Hủy yêu cầu gặp nhân viên'),
                ('status', 'ℹ️ Trạng thái hỗ trợ'), ('new', '🆕 Bắt đầu cuộc trò chuyện mới'), ('contact', '☎️ Liên hệ cửa hàng'),
                ('help', '📖 Cách dùng bot')]
KNOWN = {'/' + name for name, _ in BOT_COMMANDS} | {'/link', '/unlink'}

# Same topics and questions as the website's Hỏi đáp page.
POLICY_TOPICS = [('↩️ Đổi trả', 'Điện thoại mới bị lỗi trong 30 ngày đầu có được đổi máy không?'),
                 ('🛡️ Bảo hành', 'Thời gian bảo hành bắt đầu tính từ khi nào?'),
                 ('🚚 Giao hàng', 'Giao tủ lạnh từ cửa hàng về nhà xa 40 km có mất phí không?'),
                 ('💳 Thanh toán', 'Cửa hàng nhận những phương thức thanh toán nào?'),
                 ('🧾 Trả góp', 'Trả góp qua Home PayLater cần điều kiện gì?'),
                 ('📣 Khiếu nại', 'Tổng đài chăm sóc khách hàng hoạt động mấy giờ?')]

# From knowledge/fptshop/lien-he-va-mua-hang.md and khieu-nai.md.
CONTACT = ('☎️ Liên hệ cửa hàng\n'
           '• Tư vấn mua hàng: 1800 6601, bấm nhánh 1 (miễn phí)\n'
           '• Hỗ trợ kỹ thuật: 1800 6601, bấm nhánh 2\n'
           '• Góp ý, khiếu nại: 1800 6616, từ 8 giờ đến 22 giờ\n'
           '• Website: fptshop.com.vn\n'
           'Muốn trao đổi ngay trong chat, gửi /human để gặp nhân viên.')

HELP = ('📖 Cách dùng bot\n'
        'Gõ câu hỏi bình thường, trợ lý AI trả lời kèm nguồn chính sách.\n'
        '/products – xem sản phẩm theo nhóm\n'
        '/orders – đơn hàng của bạn (cần kết nối tài khoản web)\n'
        '/policies – chọn nhanh chủ đề chính sách\n'
        '/human – gặp nhân viên · /cancel – hủy yêu cầu đang chờ\n'
        '/status – trạng thái hỗ trợ · /new – cuộc trò chuyện mới\n'
        '/contact – tổng đài, giờ làm việc\n'
        'Không gửi mật khẩu, mã OTP hoặc mã truy cập đơn vào chat.')

MENU = [[('🛒 Sản phẩm', 'cmd:/products'), ('📋 Chính sách', 'cmd:/policies')],
        [('📦 Đơn hàng', 'cmd:/orders'), ('ℹ️ Trạng thái', 'cmd:/status')],
        [('🙋 Gặp nhân viên', 'cmd:/human'), ('☎️ Liên hệ', 'cmd:/contact')]]
BACK = [('⬅️ Menu chính', 'cmd:/start')]


def keyboard(rows):
    return [[{'text': text, 'data': data} for text, data in row] for row in rows]


PRODUCT_ID = re.compile(r'[A-Za-z0-9-]{1,60}')


def callback_content(data):
    """Callback data from our own buttons → the text the bot processes; anything else is ignored."""
    if not isinstance(data, str):
        return None
    if data.startswith('prod:') and PRODUCT_ID.fullmatch(data[5:]):
        return '/product ' + data[5:]
    if data.startswith('buy:') and PRODUCT_ID.fullmatch(data[4:]):
        return '/buy ' + data[4:]
    if data.startswith('cmd:') and data[4:] in KNOWN | {'/human'}:
        return data[4:]
    if data.startswith('p:') and data[2:] in PRODUCT_CATEGORIES:
        return '/products ' + data[2:]
    if data.startswith('ask:') and data[4:].isdigit() and int(data[4:]) < len(POLICY_TOPICS):
        return POLICY_TOPICS[int(data[4:])][1]
    return None


def products_reply(db, category):
    counts = category_counts(db)
    if not counts:
        return 'Cửa hàng chưa đăng sản phẩm nào. Gửi /contact để hỏi tổng đài tư vấn.', keyboard([BACK])
    pick = [[(f'{CATEGORY_LABELS[c]} ({n})', f'p:{c}') for c, n in counts[i:i + 2]] for i in range(0, len(counts), 2)]
    if category not in PRODUCT_CATEGORIES or category not in dict(counts):
        return '🛒 Chọn nhóm sản phẩm:', keyboard(pick + [BACK])
    items = visible(db, category)[:30]
    label = CATEGORY_LABELS[category].split(' ', 1)[1].upper()
    lines = [f'{CATEGORY_LABELS[category].split(" ", 1)[0]} DANH MỤC: {label}', 'Chọn sản phẩm bạn quan tâm theo số bên dưới:', '']
    for number, product in enumerate(items, 1):
        lines += [f'{number}. {product.name}', f'{price_text(product.price)} · {stock_text(product)}', '']
    lines.append('Bấm số tương ứng để xem và mua sản phẩm.')
    numbers = [(str(n), f'prod:{p.id}') for n, p in enumerate(items, 1)]
    return '\n'.join(lines), keyboard([numbers[i:i + 3] for i in range(0, len(numbers), 3)] + [[('⬅️ Quay lại danh mục', 'cmd:/products')]])


def stock_text(product):
    return f'Còn {product.stock}' if product.stock > 0 else 'Hết hàng'


def product_reply(db, product_id):
    product = db.get(Product, product_id)
    if product is None or not product.active:
        return 'Sản phẩm này không còn bán.', keyboard([[('⬅️ Quay lại danh mục', 'cmd:/products')]])
    lines = [f'📦 {product.name}', '', f'💰 Giá: {price_text(product.price)}', f'🎁 Tồn kho: {stock_text(product)}']
    if product.description:
        lines.append(f'📝 {product.description}')
    if product.url:
        lines.append(f'🔗 {product.url}')
    rows = [[('🛒 Mua ngay', f'buy:{product.id}')]] if product.stock > 0 and product.price is not None else []
    if product.price is None:
        lines.append('Sản phẩm cần liên hệ để báo giá: gửi /human để gặp nhân viên.')
    return '\n'.join(lines), keyboard(rows + [[('⬅️ Quay lại danh sách', f'p:{product.category}')]])


def buy_reply(db, outcome, product_id):
    product = db.get(Product, product_id)
    if outcome != 'ok' or product is None:
        return 'Sản phẩm đã hết hàng hoặc không còn bán.', keyboard([[('⬅️ Quay lại danh mục', 'cmd:/products')]])
    return (f'📥 TẠO ĐƠN HÀNG: {product.name}\n\n'
            f'💰 Đơn giá: {price_text(product.price)} / 1\n'
            f'🎁 (Tồn kho hiện tại: {product.stock} sản phẩm sẵn sàng)\n\n'
            f'👉 Vui lòng nhập và gửi số lượng sản phẩm bạn muốn mua (1–{product.stock}) dưới đây:'), \
        keyboard([[('⬅️ Quay lại', f'prod:{product.id}')]])


def order_reply(db, peer, outcome, ref):
    """(text, buttons, image) after the customer sent a quantity."""
    if outcome == 'zero':
        return 'Số lượng phải từ 1 trở lên. Nhập lại số lượng bạn muốn mua.', None, None
    if outcome == 'over':
        product = db.get(Product, ref)
        left = product.stock if product else 0
        return (f'Chỉ còn {left} sản phẩm. Nhập số lượng từ 1 đến {left}.' if left else 'Sản phẩm vừa hết hàng.'), \
            keyboard([[('⬅️ Quay lại', f'prod:{ref}')]]), None
    if outcome != 'ok':
        return 'Sản phẩm không còn bán. Chọn sản phẩm khác trong /products.', keyboard([[('⬅️ Danh mục', 'cmd:/products')]]), None
    order = db.get(Order, ref)
    if order is None or order.customer_id != peer.customer_id:
        return 'Không tìm thấy đơn hàng.', None, None
    product = db.get(Product, order.product_id)
    config = payment.settings(db)
    lines = [f'✅ ĐÃ TẠO ĐƠN HÀNG {order.id}', '', f'📦 Sản phẩm: {product.name if product else ""}',
             f'🔢 Số lượng: {order.quantity}', f'💰 Thành tiền: {price_text(order.amount)}']
    if order.pay_amount != order.amount:
        lines.append(f'🧪 Bản demo: chỉ chuyển {price_text(order.pay_amount)} (giá ÷ {config["divisor"]})')
    image = None
    if payment.ready(config):
        image = payment.qr_url(config, order.pay_amount, order.id)
        lines += ['', f'🏦 {payment.BANKS[config["bank_bin"]]} · {config["account_no"]} · {config["account_name"]}',
                  f'💵 Số tiền chuyển: {price_text(order.pay_amount)}', f'📝 Nội dung: {order.id}', '',
                  'Quét mã QR bằng ứng dụng ngân hàng. Nhân viên xác nhận khi nhận được tiền; gửi /orders để xem trạng thái.']
    else:
        lines += ['', 'Cửa hàng chưa cấu hình tài khoản nhận tiền. Nhân viên sẽ liên hệ hướng dẫn thanh toán; gửi /human nếu cần ngay.']
    return '\n'.join(lines), keyboard([[('📦 Đơn hàng của tôi', 'cmd:/orders'), ('🛒 Mua tiếp', 'cmd:/products')]]), image


def order_line(order, names):
    status = 'Chờ thanh toán' if order.status == 'processing' and order.pay_amount else ORDER_STATUS_LABELS.get(order.status, order.status)
    item = f' · {names[order.product_id]} × {order.quantity} · {price_text(order.amount)}' if order.product_id in names else ''
    return f'• {order.id}{item} · {status}' + (f' · Vận đơn {order.tracking_code}' if order.tracking_code else '')


def status_reply(db, peer):
    conversation = db.get(Conversation, peer.conversation_id) if peer.conversation_id else None
    status = conversation.status if conversation else None
    if status == 'handoff_requested':
        info = waiting_info(db, conversation) or {}
        requested = info.get('requested_at')
        waited = ''
        if requested:
            requested = requested if requested.tzinfo else requested.replace(tzinfo=timezone.utc)
            waited = f' · đã chờ {max(1, round((datetime.now(timezone.utc) - requested).total_seconds() / 60))} phút'
        due = info.get('due_at')
        deadline = f' · nhân viên phản hồi trước {datetime.fromisoformat(due).astimezone(VN):%H:%M}' if due else ''
        return f'⏳ Đang chờ nhân viên{waited}{deadline}. Gửi /cancel để hủy và hỏi trợ lý AI.', None
    if status == 'assigned':
        return '👩‍💼 Nhân viên đang hỗ trợ bạn. Trợ lý AI tạm dừng; cứ nhắn tiếp cho nhân viên.', None
    if status == 'resolved':
        return '✅ Yêu cầu đã được giải quyết. Nhắn tiếp nếu bạn cần hỗ trợ thêm.', None
    return '🤖 Trợ lý AI đang hỗ trợ bạn. Gửi câu hỏi, hoặc /human để gặp nhân viên.', keyboard(MENU)


def command_reply(db, peer, content):
    """(text, buttons) for a stored command line; see telegram.process_next for what is stored."""
    words = content.split()
    command, arg = words[0].lower(), (words[1] if len(words) > 1 else '')
    account = linked_account(db, peer)
    if command == '/start':
        return ('👋 Chào bạn! Mình là trợ lý hỗ trợ khách hàng. Hỏi mình về chính sách cửa hàng, '
                'hoặc chọn một mục bên dưới.'), keyboard(MENU)
    if command == '/products':
        return products_reply(db, arg)
    if command == '/product':
        return product_reply(db, arg)
    if command == '/buy':
        return buy_reply(db, arg, words[2] if len(words) > 2 else '')
    if command == '/order':
        return order_reply(db, peer, arg, words[2] if len(words) > 2 else '')
    if command == '/policies':
        rows = [[(label, f'ask:{i}') for i, (label, _) in enumerate(POLICY_TOPICS)][j:j + 2] for j in range(0, len(POLICY_TOPICS), 2)]
        return '📋 Chọn chủ đề, trợ lý sẽ trả lời kèm nguồn chính sách:', keyboard(rows + [BACK])
    if command == '/orders':
        # Orders of this chat's customer: ones bought here, plus the web account's once linked.
        orders = db.query(Order).filter(Order.customer_id == peer.customer_id).order_by(Order.id.desc()).limit(10).all()
        if not orders:
            if account is None:
                return ('Bạn chưa có đơn hàng nào. Mua trong /products, hoặc kết nối tài khoản web (trang Tài khoản → '
                        '"Kết nối Telegram") để xem đơn đặt trên website.'), None
            return 'Tài khoản của bạn chưa có đơn hàng nào được gắn. Nếu bạn đã đặt hàng, gửi /human để nhân viên kiểm tra.', None
        names = {p.id: p.name for p in db.query(Product).filter(Product.id.in_([o.product_id for o in orders if o.product_id]))}
        lines = [order_line(o, names) for o in orders]
        return 'Đơn hàng của bạn:\n' + '\n'.join(lines) + '\n\nGửi mã đơn kèm câu hỏi để hỏi chi tiết, ví dụ: "' + orders[0].id + ' bao giờ giao?"', None
    if command == '/status':
        return status_reply(db, peer)
    if command == '/cancel':
        return {'ok': ('↩️ Đã hủy yêu cầu gặp nhân viên. Trợ lý AI tiếp tục hỗ trợ bạn.', None),
                'assigned': ('Nhân viên đã tiếp nhận nên không hủy được nữa. Cứ nhắn tiếp cho nhân viên nhé.', None),
                }.get(arg, ('Bạn không có yêu cầu gặp nhân viên nào đang chờ.', None))
    if command == '/new':
        return '🆕 Đã bắt đầu cuộc trò chuyện mới. Bạn cần hỗ trợ gì?', keyboard(MENU)
    if command == '/contact':
        return CONTACT, None
    if command == '/link':
        if arg == 'ok' and account:
            return f'Đã kết nối Telegram với tài khoản {masked(account.email)}. Gửi /orders để xem đơn của bạn.', None
        if arg == 'unverified':
            return 'Tài khoản web chưa xác minh email nên chưa kết nối được. Hãy xác minh email rồi lấy link mới ở trang Tài khoản.', None
        return 'Link kết nối không hợp lệ hoặc đã hết hạn. Mở trang Tài khoản trên web, bấm "Kết nối Telegram" để lấy link mới.', None
    if command == '/unlink':
        return ('Đã gỡ kết nối với tài khoản web. Đơn hàng của tài khoản không còn xem được ở đây.' if arg == 'ok'
                else 'Telegram này chưa kết nối với tài khoản web nào.'), None
    if command == '/help':
        return HELP, None
    return 'Mình chưa hiểu lệnh này.\n\n' + HELP, keyboard(MENU)
