import re
import unicodedata

# Strong terms always hand off. Topic terms also name policies customers ask about, so they hand off only
# when the message is a demand or concerns the customer's own case, not an information question.
STRONG_TERMS = ("bức xúc", "tệ", "lừa đảo", "gặp nhân viên", "người thật")
TOPIC_TERMS = ("khiếu nại", "hoàn tiền")
COMPLAINT_TERMS = TOPIC_TERMS + STRONG_TERMS
STRONG_PATTERN = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, STRONG_TERMS)) + r')(?!\w)')
TOPIC_PATTERN = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, TOPIC_TERMS)) + r')(?!\w)')
QUESTION_PATTERN = re.compile(
    r'\?|(?<!\w)(?:bao lâu|mấy ngày|mấy giờ|bao nhiêu|thế nào|ra sao|ở đâu|số nào|khi nào|là gì|có được|được không)(?!\w)')
OWN_CASE_PATTERN = re.compile(
    r'(?<!\w)(?:(?:tôi|mình|em|anh|chị)(?: \S+){0,2}? (?:muốn|cần|yêu cầu|đòi|xin)(?: được)? (?:hoàn tiền|khiếu nại)|'
    r'(?:hoàn|trả)(?: \S+){0,3}? cho (?:tôi|mình|em)|'
    r'chưa (?:được |nhận được |thấy )?(?:hoàn|nhận|trả)|'
    r'ngay(?! (?:khi|sau|lúc|từ)))(?!\w)')
NEUTRAL_CONTEXT_PATTERN = re.compile(
    r'(?<!\w)tiền tệ(?!\w)|'
    r'(?:^|[.!?;,] )(?:(?:hiện tại|bây giờ|lúc này) )?(?:(?:tôi|mình|em) )?(?:không|chưa) (?:cần|muốn) '
    r'(?:gặp nhân viên|(?:gặp |nói chuyện với )?người thật)(?!\w)|'
    r'(?:^|[.!?;,] )(?:(?:tôi|mình|em) )?chỉ (?:hỏi|muốn biết)(?: về)? '
    r'(?:điều kiện|chính sách|quy định|quy trình|thủ tục) hoàn tiền'
    r'(?: của (?:cửa hàng|shop))?(?: thôi)?(?=\s*(?:[.!?;,]|$))|'
    r'(?<!\w)(?:điều kiện|chính sách|quy định|quy trình|thủ tục) hoàn tiền'
    r'(?=\s*\?| (?:theo (?:chính sách|quy định)(?: cửa hàng)? |của (?:cửa hàng|shop) )?'
    r'(?:là gì|như thế nào|thế nào|ra sao)(?!\w))')

def classify_message(content: str) -> tuple[str, bool]:
    # Normalize matching only; stored messages and handoff excerpts keep the original text.
    normalized = ' '.join(unicodedata.normalize('NFC', content).casefold().split())
    # ponytail: mask only clear local phrases; free-form negation needs separately evaluated intent detection.
    # Keep other complaints/requests in the same message eligible for immediate handoff.
    normalized = NEUTRAL_CONTEXT_PATTERN.sub(' ', normalized)
    if STRONG_PATTERN.search(normalized):
        return "negative", True
    if TOPIC_PATTERN.search(normalized):
        # A policy question about refunds or complaints goes to RAG; the customer can still choose staff.
        if QUESTION_PATTERN.search(normalized) and not OWN_CASE_PATTERN.search(normalized):
            return "neutral", False
        return "negative", True
    return "neutral", False


# Staff read the summary as-is in the inbox, so senders are named in Vietnamese.
SUMMARY_SENDERS = {'customer': 'Khách', 'ai': 'AI'}


def refresh_handoff_summary(db, conversation):
    from app.models.support import Message, Ticket

    ticket = db.query(Ticket).filter(
        Ticket.conversation_id == conversation.id,
        Ticket.status.in_(['open', 'assigned']),
    ).order_by(Ticket.created_at.desc(), Ticket.id.desc()).first()
    if ticket is None:
        return
    recent = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_type.in_(['customer', 'ai']),
    ).order_by(Message.created_at.desc(), Message.id.desc()).limit(8).all()
    ticket.summary = '\n'.join(f'{SUMMARY_SENDERS[item.sender_type]}: {item.content[:400]}' for item in reversed(recent))

def queue_handoff(db, conversation):
    from uuid import uuid4
    from app.models.support import Message, Ticket

    # Caller holds the conversation write lock.
    notify = conversation.channel == 'telegram' and conversation.status != 'handoff_requested'
    conversation.status, conversation.priority = 'handoff_requested', 'high'
    ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation.id, Ticket.status.in_(['open', 'assigned'])).first()
    if ticket is None:
        db.add(Ticket(id=str(uuid4()), conversation_id=conversation.id, priority='high'))
        db.flush()
    refresh_handoff_summary(db, conversation)
    # Commit the notice with the transition so an interrupted worker cannot lose it.
    if notify:
        db.add(Message(id=str(uuid4()), conversation_id=conversation.id, sender_type='system',
                       content='Đã chuyển yêu cầu cho nhân viên. Bạn có thể để lại thêm thông tin.'))
