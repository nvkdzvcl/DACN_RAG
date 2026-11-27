"""Telegram bot commands: replies, inline buttons and the "/" menu registered with setMyCommands.

Commands answer from the database and never call the model. Buttons send callback data that
telegram.parse_update turns back into a command line (or, for policy topics, into a question that
the AI answers with sources as usual).
"""
from datetime import datetime, timedelta, timezone

from app.models.support import PRODUCT_CATEGORIES, Conversation, Order
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


def callback_content(data):
    """Callback data from our own buttons → the text the bot processes; anything else is ignored."""
    if not isinstance(data, str):
        return None
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
    items = visible(db, category)
    lines = [f'{CATEGORY_LABELS[category]} ({len(items)} sản phẩm)']
    for product in items[:10]:
        lines.append(f'• {product.name} — {price_text(product.price)} · {"Còn hàng" if product.in_stock else "Hết hàng"}')
        if product.url:
            lines.append(f'  {product.url}')
    if len(items) > 10:
        lines.append(f'… và {len(items) - 10} sản phẩm khác trên website.')
    lines.append('Giá tham khảo, có thể thay đổi. Hỏi trợ lý về bảo hành, trả góp hoặc gửi /human để được tư vấn.')
    return '\n'.join(lines), keyboard(pick + [BACK])


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
    if command == '/policies':
        rows = [[(label, f'ask:{i}') for i, (label, _) in enumerate(POLICY_TOPICS)][j:j + 2] for j in range(0, len(POLICY_TOPICS), 2)]
        return '📋 Chọn chủ đề, trợ lý sẽ trả lời kèm nguồn chính sách:', keyboard(rows + [BACK])
    if command == '/orders':
        if account is None:
            return ('Telegram này chưa kết nối với tài khoản web. Đăng nhập trang hỗ trợ, mở Tài khoản và bấm '
                    '"Kết nối Telegram", rồi mở link trên điện thoại.'), None
        orders = db.query(Order).filter(Order.customer_id == peer.customer_id).order_by(Order.id.desc()).limit(10).all()
        if not orders:
            return 'Tài khoản của bạn chưa có đơn hàng nào được gắn. Nếu bạn đã đặt hàng, gửi /human để nhân viên kiểm tra.', None
        lines = [f'• {o.id} · {ORDER_STATUS_LABELS.get(o.status, o.status)}' + (f' · Vận đơn {o.tracking_code}' if o.tracking_code else '')
                 for o in orders]
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
