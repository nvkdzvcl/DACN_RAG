from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models.support import Conversation, Message, Ticket

# ponytail: fixed 24/7 demo policy; persist policy/deadline per ticket before configurable SLAs.
RESPONSE_MINUTES = {'urgent': 5, 'high': 15, 'normal': 60, 'low': 240}


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def ticket_slas(db, conversation_ids, now=None):
    now = utc(now or datetime.now(timezone.utc))
    first_reply = select(func.min(Message.created_at)).where(
        Message.conversation_id == Ticket.conversation_id,
        Message.sender_type == 'agent', Message.agent_id.is_not(None),
        Message.created_at >= Ticket.created_at,
    ).correlate(Ticket).scalar_subquery()
    rows = db.query(Ticket, first_reply, Conversation.status).join(
        Conversation, Conversation.id == Ticket.conversation_id
    ).filter(Ticket.conversation_id.in_(conversation_ids)).order_by(Ticket.created_at.desc(), Ticket.id).all()
    result = {}
    for ticket, replied_at, conversation_status in rows:
        if ticket.status in {'closed', 'resolved'}:
            replied_at = ticket.first_response_at
        target = RESPONSE_MINUTES.get(ticket.priority, RESPONSE_MINUTES['normal'])
        due_at = utc(ticket.created_at) + timedelta(minutes=target)
        replied_at = utc(replied_at) if replied_at else None
        if replied_at:
            status = 'met' if replied_at <= due_at else 'breached'
        elif ticket.status in {'closed', 'resolved'} or conversation_status in {'closed', 'resolved'}:
            status = 'cancelled'
        else:
            status = 'overdue' if now > due_at else 'on_track'
        result[ticket.id] = {'ticket_id': ticket.id, 'conversation_id': ticket.conversation_id,
                             'target_minutes': target, 'due_at': due_at.isoformat(),
                             'responded_at': replied_at.isoformat() if replied_at else None, 'status': status}
    return result


def conversation_sla(items):
    pending = [item for item in items if item['status'] in {'on_track', 'overdue'}]
    return min(pending, key=lambda item: item['due_at']) if pending else next(iter(items), None)
