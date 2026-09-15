COMPLAINT_TERMS = ("khiếu nại", "bức xúc", "tệ", "lừa đảo", "hoàn tiền", "gặp nhân viên", "người thật")

def classify_message(content: str) -> tuple[str, bool]:
    normalized = content.casefold()
    matched = [term for term in COMPLAINT_TERMS if term in normalized]
    if matched:
        return "negative", True
    return "neutral", False


def queue_handoff(db, conversation):
    from uuid import uuid4
    from app.models.support import Message, Ticket

    # Caller holds the conversation write lock.
    conversation.status, conversation.priority = 'handoff_requested', 'high'
    ticket = db.query(Ticket).filter(Ticket.conversation_id == conversation.id, Ticket.status.in_(['open', 'assigned'])).first()
    if ticket is None:
        recent = db.query(Message).filter_by(conversation_id=conversation.id).order_by(Message.created_at.desc(), Message.id.desc()).limit(8).all()
        summary = '\n'.join(f'{item.sender_type}: {item.content[:400]}' for item in reversed(recent))
        db.add(Ticket(id=str(uuid4()), conversation_id=conversation.id, priority='high', summary=summary))
