import re
import unicodedata

COMPLAINT_TERMS = ("khiếu nại", "bức xúc", "tệ", "lừa đảo", "hoàn tiền", "gặp nhân viên", "người thật")
COMPLAINT_PATTERN = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, COMPLAINT_TERMS)) + r')(?!\w)')
NEUTRAL_CONTEXT_PATTERN = re.compile(
    r'(?<!\w)tiền tệ(?!\w)|'
    r'(?:^|[.!?;,] )(?:(?:tôi|mình|em) )?(?:không|chưa) (?:cần|muốn) '
    r'(?:gặp nhân viên|(?:gặp |nói chuyện với )?người thật)(?!\w)|'
    r'(?<!\w)(?:điều kiện|chính sách|quy định|quy trình|thủ tục) hoàn tiền'
    r'(?=\s*\?| (?:theo (?:chính sách|quy định)(?: cửa hàng)? |của (?:cửa hàng|shop) )?'
    r'(?:là gì|như thế nào|thế nào|ra sao)(?!\w))')

def classify_message(content: str) -> tuple[str, bool]:
    # Normalize matching only; stored messages and handoff excerpts keep the original text.
    normalized = ' '.join(unicodedata.normalize('NFC', content).casefold().split())
    # ponytail: mask only clear local phrases; free-form negation needs separately evaluated intent detection.
    # Keep other complaints/requests in the same message eligible for immediate handoff.
    normalized = NEUTRAL_CONTEXT_PATTERN.sub(' ', normalized)
    if COMPLAINT_PATTERN.search(normalized):
        return "negative", True
    return "neutral", False


def queue_handoff(db, conversation):
    from uuid import uuid4
    from app.models.support import Message, Ticket

    # Caller holds the conversation write lock.
    notify = conversation.channel == 'telegram' and conversation.status != 'handoff_requested'
    conversation.status, conversation.priority = 'handoff_requested', 'high'
    ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation.id, Ticket.status.in_(['open', 'assigned'])).first()
    if ticket is None:
        recent = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at.desc(), Message.id.desc()).limit(8).all()
        summary = '\n'.join(f'{item.sender_type}: {item.content[:400]}' for item in reversed(recent))
        db.add(Ticket(id=str(uuid4()), conversation_id=conversation.id, priority='high', summary=summary))
    # Commit the notice with the transition so an interrupted worker cannot lose it.
    if notify:
        db.add(Message(id=str(uuid4()), conversation_id=conversation.id, sender_type='system',
                       content='Đã chuyển yêu cầu cho nhân viên. Bạn có thể để lại thêm thông tin.'))
