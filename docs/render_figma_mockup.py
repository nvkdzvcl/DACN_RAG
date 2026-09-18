from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Scale factor 2 for ultra-crisp 4K rendering
S = 2
WIDTH, HEIGHT = 1920, 1180
im = Image.new('RGB', (WIDTH * S, HEIGHT * S), '#F4F3EE')
d = ImageDraw.Draw(im)

# Palette
C_BG = '#F4F3EE'          # Canvas Warm Cream
C_DARK = '#163A32'        # Deep Forest Teal (Sidebar)
C_DARK_HOVER = '#204E44'  # Sidebar hover
C_PRIMARY = '#147D69'     # Primary Teal (Brand CTA)
C_PRIMARY_LIGHT = '#E6F4F0' # Light teal badge
C_AI_BUBBLE = '#EAF4F1'   # Agentic RAG bubble
C_WHITE = '#FFFFFF'       # Surface card
C_BORDER = '#E2E6E1'      # Subtle border
C_BORDER_DARK = '#CBD5E1' # Input border
C_INK = '#1E293B'         # Text ink primary
C_MUTED = '#64748B'       # Text muted
C_ALERT_BG = '#FEF3C7'    # Warning/Handoff yellow
C_ALERT_TXT = '#92400E'   # Warning text
C_SLA_BG = '#FEE2E2'      # Urgent SLA red
C_SLA_TXT = '#DC2626'     # Urgent SLA text
C_SUCCESS = '#10B981'     # Online green
C_SUCCESS_BG = '#DCFCE7'  # Online green light

def box(x, y, w, h, c, r=0, outline=None, width=1):
    d.rounded_rectangle(
        (x * S, y * S, (x + w) * S, (y + h) * S),
        radius=r * S,
        fill=c,
        outline=outline,
        width=width * S
    )

def text(x, y, t, size=13, c=C_INK, b=False):
    font_path = 'C:/Windows/Fonts/' + ('segoeuib.ttf' if b else 'segoeui.ttf')
    f = ImageFont.truetype(font_path, size * S)
    d.text((x * S, y * S), t, font=f, fill=c)

def pill(x, y, w, t, c=C_PRIMARY_LIGHT, fg=C_PRIMARY, sz=11, b=True, h=26):
    box(x, y, w, h, c, r=h // 2)
    font_path = 'C:/Windows/Fonts/' + ('segoeuib.ttf' if b else 'segoeui.ttf')
    f = ImageFont.truetype(font_path, sz * S)
    bbox = d.textbbox((0, 0), t, font=f)
    tw = (bbox[2] - bbox[0]) // S
    th = (bbox[3] - bbox[1]) // S
    tx = x + (w - tw) // 2
    ty = y + (h - th) // 2 - 1
    d.text((tx * S, ty * S), t, font=f, fill=fg)

def avatar(x, y, t, bg='#E2E8F0', fg=C_INK, sz=36):
    box(x, y, sz, sz, bg, r=sz // 2)
    font_path = 'C:/Windows/Fonts/segoeuib.ttf'
    f = ImageFont.truetype(font_path, int(sz * 0.38) * S)
    bbox = d.textbbox((0, 0), t, font=f)
    tw = (bbox[2] - bbox[0]) // S
    th = (bbox[3] - bbox[1]) // S
    tx = x + (sz - tw) // 2
    ty = y + (sz - th) // 2 - 1
    d.text((tx * S, ty * S), t, font=f, fill=fg)

# ==========================================
# 1. TOP BAR: FIGMA DESIGN SYSTEM & COLOR CODES
# ==========================================
box(25, 14, 1870, 92, C_WHITE, r=12, outline=C_BORDER)

# Left brand tag
text(45, 26, 'KITE SUPPORT  ·  AGENTIC RAG MULTI-CHANNEL PLATFORM', 15, C_DARK, b=True)
text(45, 50, 'BẢNG MÃ MÀU FIGMA (DESIGN TOKENS) & ĐẶC TẢ GIAO DIỆN HỆ THỐNG', 11, C_MUTED, b=True)
text(45, 70, 'Next.js 15  ·  Tailwind CSS  ·  shadcn/ui  ·  FastAPI + pgvector  ·  Gemini Flash', 11, C_PRIMARY)

# Divider in top bar
box(515, 22, 1, 74, C_BORDER)

# Color Swatches List for Figma
swatches = [
    ('Primary Teal', '#147D69', 'CTA, Active'),
    ('Dark Forest', '#163A32', 'Sidebar, Nav'),
    ('Warm Canvas', '#F4F3EE', 'Nền hệ thống'),
    ('Card Surface', '#FFFFFF', 'Card, Khung chat'),
    ('AI Bubble', '#EAF4F1', 'Tin nhắn AI RAG'),
    ('Alert Amber', '#D97706', 'Handoff Cảnh báo'),
    ('SLA Urgent', '#E06D53', 'Khẩn cấp / SLA'),
    ('Success Green', '#10B981', 'Trực tuyến / Xong'),
    ('Border Line', '#E2E6E1', 'Đường viền thẻ'),
    ('Text Ink', '#1E293B', 'Chữ chính'),
    ('Text Muted', '#64748B', 'Chữ phụ, nhãn'),
]

start_x = 530
sw_w = 120
for i, (name, hex_code, role) in enumerate(swatches):
    sx = start_x + i * sw_w
    # Swatch circle with outline
    box(sx, 26, 22, 22, hex_code, r=11, outline='#CBD5E1' if hex_code in ['#FFFFFF', '#F4F3EE', '#EAF4F1'] else None)
    # Hex code
    text(sx + 28, 24, hex_code, 10, C_INK, b=True)
    # Swatch name
    text(sx + 28, 42, name, 9, C_PRIMARY if 'Teal' in name else C_DARK, b=True)
    # Role description
    text(sx + 28, 60, role, 8, C_MUTED)

# ==========================================
# 2. MAIN DESKTOP DASHBOARD CONTAINER
# ==========================================
D_X, D_Y, D_W, D_H = 25, 120, 1490, 1035
box(D_X, D_Y, D_W, D_H, C_WHITE, r=14, outline=C_BORDER)

# ------------------------------------------
# A. SIDEBAR (Width: 205)
# ------------------------------------------
S_W = 205
box(D_X, D_Y, S_W, D_H, C_DARK, r=14)
box(D_X + S_W - 14, D_Y, 14, D_H, C_DARK)

# Logo
box(D_X + 22, D_Y + 22, 34, 34, '#D6E8AD', r=10)
text(D_X + 32, D_Y + 23, 'k', 23, C_DARK, b=True)
text(D_X + 66, D_Y + 20, 'kite.ai', 24, C_WHITE, b=True)
text(D_X + 67, D_Y + 48, 'AGENTIC SUPPORT', 9, '#8FB8A6', b=True)

box(D_X + 20, D_Y + 74, S_W - 40, 1, '#234D43')

# Nav Menu items
navs = [
    ('Hộp thư đa kênh', True, '12', '#D6E8AD', C_DARK),
    ('Kho tri thức RAG', False, '5 Docs', '#265248', '#B8CEC2'),
    ('Tra cứu đơn hàng', False, None, None, None),
    ('Khách hàng', False, None, None, None),
    ('Báo cáo & SLA', False, '99%', '#265248', '#B8CEC2'),
    ('Cấu hình AI Agent', False, None, None, None),
]

ny = D_Y + 90
for title, active, badge, b_bg, b_fg in navs:
    if active:
        box(D_X + 14, ny - 2, S_W - 28, 38, C_DARK_HOVER, r=8)
        box(D_X + 14, ny + 5, 4, 24, '#D6E8AD', r=2)
        text(D_X + 28, ny + 7, title, 13, C_WHITE, b=True)
    else:
        text(D_X + 28, ny + 7, title, 13, '#B8CEC2')
    
    if badge:
        pill(D_X + S_W - 58, ny + 5, 40, badge, b_bg, b_fg, sz=9, h=22)
    ny += 48

# Connected channels section
box(D_X + 16, D_Y + 420, S_W - 32, 175, '#1B4239', r=10)
text(D_X + 28, D_Y + 434, 'KÊNH ĐANG KẾT NỐI (4)', 10, '#8FB8A6', b=True)

channels = [
    ('Website Widget', '● Trực tuyến', '#34D399'),
    ('Zalo OA Biz', '● Đã đồng bộ', '#60A5FA'),
    ('Facebook Fanpage', '● Đã kết nối', '#38BDF8'),
    ('Telegram Bot', '● Đã kết nối', '#A78BFA')
]
cy = D_Y + 460
for ch_name, st, st_col in channels:
    box(D_X + 28, cy + 5, 6, 6, st_col, r=3)
    text(D_X + 42, cy, ch_name, 11, '#E2EFE7', b=True)
    text(D_X + 42, cy + 15, st, 9, '#8FB8A6')
    cy += 36

# Agent profile bottom
box(D_X + 16, D_Y + D_H - 85, S_W - 32, 68, '#1B4239', r=10)
avatar(D_X + 26, D_Y + D_H - 72, 'MK', bg='#D6E8AD', fg=C_DARK, sz=40)
text(D_X + 74, D_Y + D_H - 70, 'Minh Khánh', 13, C_WHITE, b=True)
text(D_X + 74, D_Y + D_H - 52, 'Tư vấn viên Tier 2', 10, '#8FB8A6')
box(D_X + 74, D_Y + D_H - 35, 7, 7, '#34D399', r=4)
text(D_X + 86, D_Y + D_H - 38, 'Đang trực tuyến', 9, '#34D399')

# ------------------------------------------
# B. DASHBOARD TOP HEADER BAR
# ------------------------------------------
H_X = D_X + S_W
H_W = D_W - S_W
H_H = 68
box(H_X, D_Y, H_W, H_H, C_WHITE)
box(H_X, D_Y + H_H - 1, H_W, 1, C_BORDER)

text(H_X + 25, D_Y + 14, 'Hộp thư hội thoại tập trung (Unified Inbox)', 17, C_DARK, b=True)
text(H_X + 25, D_Y + 38, 'Định tuyến thông minh  ·  Agentic RAG tự động  ·  Human-in-the-loop Escalation', 11, C_MUTED)

# Stats badges on top
pill(H_X + 540, D_Y + 20, 115, '● 12 Đang mở', '#F1F5F9', C_INK, sz=11, h=28)
pill(H_X + 665, D_Y + 20, 145, '● 3 Chờ tiếp nhận', C_ALERT_BG, C_ALERT_TXT, sz=11, h=28)
pill(H_X + 820, D_Y + 20, 135, 'SLA TB: 1m 24s', '#ECFDF5', '#047857', sz=11, h=28)
pill(H_X + 965, D_Y + 20, 135, 'RAG: 98.4% chính xác', C_PRIMARY_LIGHT, C_PRIMARY, sz=11, h=28)

# Search Bar
box(H_X + H_W - 175, D_Y + 18, 155, 32, C_WHITE, r=6, outline=C_BORDER)
text(H_X + H_W - 162, D_Y + 25, 'Tìm kiếm... Ctrl K', 10, C_MUTED)

# ------------------------------------------
# C. TICKET QUEUE / INBOX COLUMN (Width: 320)
# ------------------------------------------
Q_X = H_X
Q_W = 320
Q_Y = D_Y + H_H
Q_H = D_H - H_H
box(Q_X, Q_Y, Q_W, Q_H, '#FAFAF8')
box(Q_X + Q_W - 1, Q_Y, 1, Q_H, C_BORDER)

# Queue Filter Tabs
text(Q_X + 20, Q_Y + 16, 'Danh sách hội thoại', 14, C_DARK, b=True)
pill(Q_X + 20, Q_Y + 44, 75, 'Tất cả (12)', C_PRIMARY, C_WHITE, sz=10, h=24)
pill(Q_X + 102, Q_Y + 44, 98, 'Cần Handoff (3)', C_ALERT_BG, C_ALERT_TXT, sz=10, h=24)
pill(Q_X + 208, Q_Y + 44, 75, 'Của tôi (5)', '#EDF0EB', C_MUTED, sz=10, h=24)

# Tickets
tickets = [
    {
        'active': True,
        'name': 'Lê Mai Anh',
        'channel': 'Website Chat',
        'time': '1p trước',
        'msg': 'Đơn hàng ORD-DEMO02 bị lỗi nguồn, mình muốn gặp nhân viên gấp...',
        'badge1': ('SLA: 5m (Gấp)', C_SLA_BG, C_SLA_TXT),
        'badge2': ('Yêu cầu Handoff', C_ALERT_BG, C_ALERT_TXT),
        'av': 'LA',
        'av_bg': '#FCE7DB',
    },
    {
        'active': False,
        'name': 'Hoàng Nam',
        'channel': 'Zalo OA Biz',
        'time': '4p trước',
        'msg': 'Kiểm tra giúp mình đơn hàng ORD-DEMO05 đã giao đến chưa?',
        'badge1': ('AI tra cứu đơn', C_PRIMARY_LIGHT, C_PRIMARY),
        'badge2': ('Chờ phản hồi', '#F1F5F9', C_MUTED),
        'av': 'HN',
        'av_bg': '#ECE4D9',
    },
    {
        'active': False,
        'name': 'Thảo Linh',
        'channel': 'Website Chat',
        'time': '8p trước',
        'msg': 'Chính sách đổi trả phụ kiện trong vòng mấy ngày vậy shop?',
        'badge1': ('RAG đã trả lời', C_PRIMARY_LIGHT, C_PRIMARY),
        'badge2': ('Đã giải quyết', C_SUCCESS_BG, '#15803D'),
        'av': 'TL',
        'av_bg': '#DDE8ED',
    },
    {
        'active': False,
        'name': 'Minh Trí',
        'channel': 'Telegram Bot',
        'time': '16p trước',
        'msg': 'Cảm ơn shop nhiều, mình nhận được đơn hàng rồi nhé!',
        'badge1': ('Hoàn thành', '#F1F5F9', C_MUTED),
        'badge2': None,
        'av': 'MT',
        'av_bg': '#EEE3D9',
    },
    {
        'active': False,
        'name': 'Quỳnh Hoa',
        'channel': 'Website Chat',
        'time': '25p trước',
        'msg': 'Shop có xuất hóa đơn VAT điện tử cho công ty được không?',
        'badge1': ('RAG tư vấn', C_PRIMARY_LIGHT, C_PRIMARY),
        'badge2': None,
        'av': 'QH',
        'av_bg': '#E8E3EF',
    },
    {
        'active': False,
        'name': 'Đức Huy',
        'channel': 'Facebook Messenger',
        'time': '42p trước',
        'msg': 'Tư vấn giúp mình mẫu tai nghe chống ồn mới nhất với ạ.',
        'badge1': ('Bot phản hồi', C_PRIMARY_LIGHT, C_PRIMARY),
        'badge2': None,
        'av': 'DH',
        'av_bg': '#E0E7FF',
    }
]

t_y = Q_Y + 80
for t in tickets:
    is_act = t['active']
    t_h = 118
    if is_act:
        box(Q_X + 10, t_y, Q_W - 20, t_h, '#F2F8F5', r=8, outline=C_PRIMARY, width=1)
        box(Q_X + 10, t_y + 8, 4, t_h - 16, C_PRIMARY, r=2)
    else:
        box(Q_X + 10, t_y, Q_W - 20, t_h, C_WHITE, r=8, outline=C_BORDER)
    
    avatar(Q_X + 22, t_y + 12, t['av'], bg=t['av_bg'], sz=36)
    text(Q_X + 66, t_y + 10, t['name'], 13, C_DARK, b=True)
    text(Q_X + 66, t_y + 28, t['channel'], 10, C_MUTED)
    text(Q_X + Q_W - 75, t_y + 10, t['time'], 10, C_MUTED)
    
    # snippet
    msg_prev = t['msg'][:42] + ('...' if len(t['msg']) > 42 else '')
    text(Q_X + 22, t_y + 54, msg_prev, 11, C_INK if is_act else C_MUTED)
    
    # badges
    bx = Q_X + 22
    if t['badge1']:
        b_txt, b_bg, b_fg = t['badge1']
        pill(bx, t_y + 80, 108, b_txt, b_bg, b_fg, sz=9, h=22)
        bx += 114
    if t['badge2']:
        b_txt, b_bg, b_fg = t['badge2']
        pill(bx, t_y + 80, 112, b_txt, b_bg, b_fg, sz=9, h=22)

    t_y += t_h + 10

# ------------------------------------------
# D. CHAT CONVERSATION AREA (Width: 605)
# ------------------------------------------
C_X = Q_X + Q_W
C_W = 605
C_Y = Q_Y
C_H = Q_H
box(C_X, C_Y, C_W, C_H, C_WHITE)
box(C_X + C_W - 1, C_Y, 1, C_H, C_BORDER)

# Chat Header
box(C_X, C_Y, C_W, 64, C_WHITE)
box(C_X, C_Y + 63, C_W, 1, C_BORDER)

avatar(C_X + 20, C_Y + 12, 'LA', bg='#FCE7DB', sz=40)
text(C_X + 70, C_Y + 14, 'Lê Mai Anh', 15, C_DARK, b=True)
text(C_X + 70, C_Y + 36, 'Website Chat Widget  ·  Mã ticket: #CV-1024', 10, C_MUTED)

# Action buttons on header (no overlap)
pill(C_X + 375, C_Y + 18, 120, 'Cần Human Handoff', C_ALERT_BG, C_ALERT_TXT, sz=10, h=28)
pill(C_X + 505, C_Y + 18, 85, 'Hoàn tất', C_DARK, C_WHITE, sz=10, h=28)

# Handoff Escalation Banner
box(C_X + 15, C_Y + 74, C_W - 30, 48, '#FFFBEB', r=8, outline='#FDE68A', width=1)
box(C_X + 15, C_Y + 74, 4, 48, '#D97706', r=2)
text(C_X + 30, C_Y + 82, '● AI HANDOFF ALERT: Phát hiện khách hàng bức xúc (Sentiment: 84% Bất mãn).', 11, '#92400E', b=True)
text(C_X + 30, C_Y + 100, 'AI đã tự động tạm dừng & chuyển giao toàn quyền hội thoại cho tư vấn viên Minh Khánh.', 10, '#B45309')

# Timestamp
text(C_X + C_W // 2 - 40, C_Y + 132, 'Hôm nay, 10:41 AM', 10, C_MUTED)

# --- Message 1: Khách hàng ---
m1_y = C_Y + 152
box(C_X + 20, m1_y, 450, 68, '#F1F5F9', r=12)
text(C_X + 36, m1_y + 12, 'Chào shop, mình nhận đơn ORD-DEMO02 sáng nay nhưng tai nghe', 12, C_INK)
text(C_X + 36, m1_y + 32, 'bị trầy xước và không lên nguồn. Shop xử lý gấp giúp mình với!', 12, C_INK)
text(C_X + 22, m1_y + 74, '10:41 · Lê Mai Anh (Khách hàng)', 9, C_MUTED)

# --- Message 2: Kite AI (Agentic RAG) ---
m2_y = C_Y + 242
box(C_X + 50, m2_y, 535, 238, C_AI_BUBBLE, r=12, outline='#C5E2D8')
# AI Badge header
box(C_X + 66, m2_y + 12, 18, 18, C_PRIMARY, r=4)
text(C_X + 71, m2_y + 13, 'k', 12, C_WHITE, b=True)
text(C_X + 90, m2_y + 13, 'Kite AI  ·  Agentic RAG Assistant', 11, C_PRIMARY, b=True)
pill(C_X + 440, m2_y + 10, 130, 'Gemini 1.5 Flash', '#D7ECE5', C_DARK, sz=9, h=20)

text(C_X + 66, m2_y + 38, 'Chào chị Mai Anh, em rất tiếc vì sự cố của đơn hàng ORD-DEMO02 ạ.', 12, C_INK)
text(C_X + 66, m2_y + 56, 'Em đã kiểm tra thông tin đơn và đối chiếu chính sách bảo hành của shop:', 12, C_INK)

# Subcard: Tool Calling
box(C_X + 66, m2_y + 80, 502, 54, C_WHITE, r=6, outline='#CDE1D9')
text(C_X + 78, m2_y + 87, '[TOOL CALL] orders.lookup(order_id="ORD-DEMO02")', 10, C_PRIMARY, b=True)
text(C_X + 78, m2_y + 107, 'Trạng thái: Đã giao 09:30 · Vận đơn: VN654321 · SP: Tai nghe ANC Pro', 10, C_DARK)

# Subcard: RAG Knowledge Citation
box(C_X + 66, m2_y + 140, 502, 50, C_WHITE, r=6, outline='#CDE1D9')
text(C_X + 78, m2_y + 146, '[RAG CITATION] Chinh_sach_doi_tra_2026.pdf (Trang 2, Mục 2.1)', 10, '#047857', b=True)
text(C_X + 78, m2_y + 166, '"Khách hàng được hỗ trợ 1 đổi 1 miễn phí trong 7 ngày nếu sản phẩm lỗi kỹ thuật."', 10, C_MUTED)

text(C_X + 66, m2_y + 200, 'Chị có thể gửi giúp em ảnh tình trạng sản phẩm để bên em hỗ trợ đổi mới ngay nhé!', 11, C_INK)
text(C_X + 50, m2_y + 244, '10:41 · Tự động phản hồi (RAG pipeline 1.2s)', 9, C_MUTED)

# --- Message 3: Khách hàng (Frustrated) ---
m3_y = C_Y + 504
box(C_X + 20, m3_y, 440, 48, '#F1F5F9', r=12)
text(C_X + 36, m3_y + 14, 'Mình muốn gặp nhân viên trực tiếp để giải quyết, không nói với bot!', 12, C_INK)
text(C_X + 22, m3_y + 54, '10:43 · Lê Mai Anh (Khách hàng)', 9, C_MUTED)

# --- System Escalation Line ---
s_y = C_Y + 574
box(C_X + 30, s_y + 8, C_W - 60, 1, '#CBD5E1')
pill(C_X + 110, s_y, 385, '● Minh Khánh đã tiếp nhận hội thoại · AI chuyển quyền tư vấn', '#F1F5F9', C_DARK, sz=10, h=22)

# --- Message 4: Nhân viên tư vấn (Minh Khánh) ---
m4_y = C_Y + 608
box(C_X + 80, m4_y, 505, 84, C_DARK, r=12)
text(C_X + 96, m4_y + 10, 'Minh Khánh  ·  Nhân viên hỗ trợ khách hàng', 11, '#D6E8AD', b=True)
text(C_X + 96, m4_y + 32, 'Dạ em chào chị Mai Anh! Em là Khánh, em đã đọc toàn bộ tóm tắt từ', 12, C_WHITE)
text(C_X + 96, m4_y + 52, 'trợ lý AI rồi ạ. Em sẽ tạo yêu cầu đổi mới ngay và freeship thu hồi cho chị nhé!', 12, C_WHITE)
text(C_X + 80, m4_y + 98, '10:44 · Nhân viên hỗ trợ', 9, C_MUTED)

# --- Chat Composer / Input Bar (Bottom) ---
comp_y = C_Y + C_H - 195
box(C_X + 15, comp_y, C_W - 30, 180, C_WHITE, r=10, outline=C_BORDER_DARK)

# Input Tabs
pill(C_X + 25, comp_y + 10, 130, 'Trả lời khách hàng', C_PRIMARY, C_WHITE, sz=10, h=26)
pill(C_X + 162, comp_y + 10, 140, 'Ghi chú nội bộ (Private)', '#EDF0EB', C_MUTED, sz=10, h=26)
box(C_X + 15, comp_y + 42, C_W - 30, 1, C_BORDER)

# Input text area placeholder
text(C_X + 30, comp_y + 56, 'Nhập nội dung phản hồi chị Mai Anh...', 12, '#94A3B8')
text(C_X + 30, comp_y + 78, '(Gõ / để gọi câu trả lời mẫu, tra cứu đơn hàng hoặc trích xuất tài liệu RAG)', 11, '#CBD5E1')

# Bottom toolbar of composer
box(C_X + 15, comp_y + 125, C_W - 30, 1, C_BORDER)
pill(C_X + 25, comp_y + 138, 90, 'Đính kèm tệp', '#F1F5F9', C_INK, sz=10, h=28)
pill(C_X + 122, comp_y + 138, 120, 'Câu trả lời mẫu', '#F1F5F9', C_INK, sz=10, h=28)
pill(C_X + 250, comp_y + 138, 115, 'Trích dẫn RAG', '#F1F5F9', C_INK, sz=10, h=28)

pill(C_X + C_W - 145, comp_y + 136, 115, 'Gửi tin nhắn →', C_PRIMARY, C_WHITE, sz=11, h=32)

# ------------------------------------------
# E. RIGHT PANEL: CUSTOMER CONTEXT & RAG (Width: 360)
# ------------------------------------------
R_X = C_X + C_W
R_W = D_W - S_W - Q_W - C_W
R_Y = Q_Y
R_H = Q_H
box(R_X, R_Y, R_W, R_H, '#FAFAF8')

ry = R_Y + 14

# Section 1: AI Handoff Summary Card
box(R_X + 12, ry, R_W - 24, 178, '#FFFBEB', r=10, outline='#FDE68A')
text(R_X + 24, ry + 12, 'TÓM TẮT CHUYỂN GIAO (AI HANDOFF)', 10, '#92400E', b=True)
pill(R_X + R_W - 120, ry + 8, 95, 'Human-in-the-loop', '#FEF3C7', '#B45309', sz=8, h=20)

box(R_X + 24, ry + 36, R_W - 48, 1, '#FDE68A')
summary_bullets = [
    ('• Cảm xúc khách:', 'Bức xúc cao (84% Frustrated)'),
    ('• Vấn đề chính:', 'Đơn ORD-DEMO02 lỗi nguồn, trầy xước'),
    ('• AI đã xử lý:', 'Đã tra cứu đơn & trích dẫn Đổi trả 7 ngày'),
    ('• Đề xuất xử lý:', 'Tạo đơn 1 đổi 1 ngay, freeship thu hồi'),
    ('• Cấp thẩm quyền:', 'Duyệt đổi mới không cần gửi kiểm định')
]
sy = ry + 46
for label, val in summary_bullets:
    text(R_X + 24, sy, label, 10, '#92400E', b=True)
    text(R_X + 125, sy, val, 10, C_INK)
    sy += 24

ry += 194

# Section 2: Thông tin khách hàng
box(R_X + 12, ry, R_W - 24, 185, C_WHITE, r=10, outline=C_BORDER)
text(R_X + 24, ry + 12, 'THÔNG TIN KHÁCH HÀNG', 10, C_MUTED, b=True)
avatar(R_X + 24, ry + 34, 'LA', bg='#FCE7DB', sz=44)
text(R_X + 78, ry + 34, 'Lê Mai Anh', 14, C_DARK, b=True)
pill(R_X + 78, ry + 56, 110, '[VIP] Khách thân thiết', '#FEF3C7', '#B45309', sz=9, h=20)

box(R_X + 24, ry + 88, R_W - 48, 1, C_BORDER)
cust_info = [
    ('Số điện thoại:', '0987.***.321'),
    ('Email:', 'maianh.le@gmail.com'),
    ('Kênh truy cập:', 'Website Chat (Chrome)'),
    ('Lịch sử mua hàng:', '4 đơn  ·  Tổng chi 6.850.000đ')
]
ci_y = ry + 98
for k, v in cust_info:
    text(R_X + 24, ci_y, k, 10, C_MUTED)
    text(R_X + 125, ci_y, v, 10, C_INK, b=('Tổng' in v))
    ci_y += 20

ry += 200

# Section 3: Đơn hàng liên quan (Tool Calling Data)
box(R_X + 12, ry, R_W - 24, 215, C_WHITE, r=10, outline=C_BORDER)
text(R_X + 24, ry + 12, 'ĐƠN HÀNG LIÊN QUAN (TOOL CALL)', 10, C_MUTED, b=True)
text(R_X + 24, ry + 32, 'ORD-DEMO02', 15, C_DARK, b=True)
pill(R_X + R_W - 120, ry + 30, 95, 'Đã giao hàng', C_SUCCESS_BG, '#15803D', sz=9, h=22)

box(R_X + 24, ry + 62, R_W - 48, 1, C_BORDER)
order_info = [
    ('Sản phẩm:', 'Tai nghe không dây ANC Pro (Đen)'),
    ('Giá trị:', '1.450.000 VNĐ (Đã thanh toán)'),
    ('Đơn vị vận chuyển:', 'ViettelPost  ·  Mã: VN654321'),
    ('Thời gian giao:', '09:30 AM  ·  12/09/2026'),
    ('Thời hạn đổi trả:', 'Còn 7 ngày (Hạn chót: 19/09)')
]
oi_y = ry + 72
for k, v in order_info:
    text(R_X + 24, oi_y, k, 10, C_MUTED)
    text(R_X + 125, oi_y, v, 10, C_INK, b=('Còn' in v or 'Giá trị' in v))
    oi_y += 20

pill(R_X + 24, ry + 176, 140, 'Tạo đơn đổi mới', C_PRIMARY, C_WHITE, sz=10, h=26)
pill(R_X + 172, ry + 176, 140, 'Tra cứu vận đơn →', '#F1F5F9', C_INK, sz=10, h=26)

ry += 230

# Section 4: Tài liệu RAG Knowledge Base đã trích xuất
box(R_X + 12, ry, R_W - 24, 150, C_WHITE, r=10, outline=C_BORDER)
text(R_X + 24, ry + 12, 'TÀI LIỆU RAG TRÍCH XUẤT (KNOWLEDGE BASE)', 10, C_MUTED, b=True)

box(R_X + 20, ry + 34, R_W - 40, 48, '#F8FAFC', r=6, outline='#E2E8F0')
text(R_X + 30, ry + 42, '[PDF] Chinh_sach_doi_tra_2026.pdf', 10, C_DARK, b=True)
pill(R_X + R_W - 110, ry + 38, 60, 'Khớp 94%', C_PRIMARY_LIGHT, C_PRIMARY, sz=8, h=18)
text(R_X + 30, ry + 60, 'Mục 2.1: Quy định bảo hành lỗi kỹ thuật 7 ngày', 9, C_MUTED)

box(R_X + 20, ry + 90, R_W - 40, 48, '#F8FAFC', r=6, outline='#E2E8F0')
text(R_X + 30, ry + 98, '[DOCX] So_tay_quy_trinh_CSKH_v3.docx', 10, C_DARK, b=True)
pill(R_X + R_W - 110, ry + 94, 60, 'Khớp 81%', '#FEF3C7', '#B45309', sz=8, h=18)
text(R_X + 30, ry + 116, 'Quy trình xử lý khiếu nại khách hàng khẩn cấp', 9, C_MUTED)

# ==========================================
# 3. MOBILE RESPONSIVE PREVIEW (Right Frame)
# ==========================================
M_X, M_Y, M_W, M_H = 1535, 120, 360, 1035

# Phone Outer Body (Titanium frame)
box(M_X, M_Y, M_W, M_H - 45, '#1E293B', r=32, outline='#0F172A', width=2)

# Phone Screen Container
SCR_X, SCR_Y, SCR_W, SCR_H = M_X + 10, M_Y + 10, M_W - 20, M_H - 65
box(SCR_X, SCR_Y, SCR_W, SCR_H, C_WHITE, r=24)

# Camera Notch Pill
box(SCR_X + SCR_W // 2 - 45, SCR_Y + 8, 90, 20, '#0F172A', r=10)

# Phone Status Bar
text(SCR_X + 20, SCR_Y + 12, '10:44', 10, C_INK, b=True)
text(SCR_X + SCR_W - 55, SCR_Y + 12, '5G  98%', 9, C_INK, b=True)

# Mobile App Header (Customer Web Widget)
box(SCR_X, SCR_Y + 36, SCR_W, 58, C_DARK)
avatar(SCR_X + 16, SCR_Y + 44, 'k', bg='#D6E8AD', fg=C_DARK, sz=36)
text(SCR_X + 60, SCR_Y + 44, 'Kite AI Support', 13, C_WHITE, b=True)
box(SCR_X + 60, SCR_Y + 66, 6, 6, '#34D399', r=3)
text(SCR_X + 72, SCR_Y + 63, 'Đang trực tuyến  ·  Phản hồi tức thì', 9, '#8FB8A6')
text(SCR_X + SCR_W - 32, SCR_Y + 52, 'X', 13, '#8FB8A6', b=True)

# Mobile Chat Content
m_y = SCR_Y + 106
text(SCR_X + SCR_W // 2 - 35, m_y, 'Hôm nay, 10:41', 9, C_MUTED)

# 1. Customer bubble
m_y += 22
box(SCR_X + 35, m_y, SCR_W - 50, 54, '#F1F5F9', r=10)
text(SCR_X + 45, m_y + 8, 'Đơn ORD-DEMO02 bị lỗi nguồn,', 11, C_INK)
text(SCR_X + 45, m_y + 28, 'shop xử lý gấp giúp mình với!', 11, C_INK)

# 2. Kite AI bubble
m_y += 66
box(SCR_X + 15, m_y, SCR_W - 40, 160, C_AI_BUBBLE, r=10, outline='#C5E2D8')
text(SCR_X + 25, m_y + 8, 'Kite AI  ·  Agentic RAG', 10, C_PRIMARY, b=True)
text(SCR_X + 25, m_y + 26, 'Em đã kiểm tra đơn ORD-DEMO02:', 10, C_INK)

# Mini tool card
box(SCR_X + 25, m_y + 46, SCR_W - 60, 44, C_WHITE, r=6, outline='#CDE1D9')
text(SCR_X + 32, m_y + 52, '[TOOL] Tra cứu đơn hàng', 9, C_PRIMARY, b=True)
text(SCR_X + 32, m_y + 70, 'Đã giao 09:30 · Vận đơn VN654321', 9, C_DARK)

# Mini RAG chip
pill(SCR_X + 25, m_y + 98, 175, '[RAG] Nguồn: CS đổi trả 7 ngày', C_WHITE, C_PRIMARY, sz=8, h=20)
text(SCR_X + 25, m_y + 126, 'Hỗ trợ 1 đổi 1 miễn phí trong 7 ngày.', 10, C_INK)

# 3. Customer Frustration
m_y += 172
box(SCR_X + 45, m_y, SCR_W - 60, 44, '#F1F5F9', r=10)
text(SCR_X + 55, m_y + 12, 'Mình muốn gặp nhân viên trực tiếp!', 11, C_INK)

# 4. Handoff notification
m_y += 56
box(SCR_X + 15, m_y, SCR_W - 30, 36, '#FFFBEB', r=6, outline='#FDE68A')
text(SCR_X + 24, m_y + 10, '● Chuyển quyền: Minh Khánh hỗ trợ bạn', 10, '#92400E', b=True)

# 5. Agent message
m_y += 48
box(SCR_X + 15, m_y, SCR_W - 40, 72, C_DARK, r=10)
text(SCR_X + 25, m_y + 8, 'Minh Khánh (Tư vấn viên):', 10, '#D6E8AD', b=True)
text(SCR_X + 25, m_y + 26, 'Chào chị Mai Anh, em đổi mới sản phẩm', 11, C_WHITE)
text(SCR_X + 25, m_y + 46, 'tận nơi cho chị ngay hôm nay nhé!', 11, C_WHITE)

# Mobile Bottom Input Bar
box(SCR_X, SCR_Y + SCR_H - 65, SCR_W, 65, C_WHITE)
box(SCR_X, SCR_Y + SCR_H - 65, SCR_W, 1, C_BORDER)
box(SCR_X + 14, SCR_Y + SCR_H - 52, SCR_W - 75, 40, '#F1F5F9', r=20)
text(SCR_X + 28, SCR_Y + SCR_H - 40, 'Nhập tin nhắn hỗ trợ...', 11, C_MUTED)
pill(SCR_X + SCR_W - 52, SCR_Y + SCR_H - 52, 40, '→', C_PRIMARY, C_WHITE, sz=13, h=40)

# Caption under phone (Clean pill outside phone)
pill(M_X + 20, M_Y + M_H - 35, M_W - 40, 'RESPONSIVE MOBILE CHAT WIDGET', C_DARK, '#D6E8AD', sz=10, h=30)

# Output image path
out_path = Path(__file__).with_name('ui-mockup-figma.png')
im.save(out_path, quality=95)
print(f'Successfully rendered: {out_path}')
