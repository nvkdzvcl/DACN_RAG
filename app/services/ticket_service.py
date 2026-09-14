from datetime import datetime, timezone

from app.models.support import Ticket
from app.services.sla_service import ticket_slas


def complete_tickets(db, conversation_id, status, user_id=None, note=None):
    # Caller holds the conversation write lock; freeze SLA in the same transaction.
    slas = ticket_slas(db, [conversation_id])
    tickets = db.query(Ticket).filter(Ticket.conversation_id == conversation_id, Ticket.status.in_(['open', 'assigned'])).all()
    completed_at = datetime.now(timezone.utc)
    for ticket in tickets:
        replied_at = slas[ticket.id]['responded_at']
        ticket.first_response_at = datetime.fromisoformat(replied_at) if replied_at else None
        ticket.status, ticket.completed_at = status, completed_at
        ticket.completed_by_id, ticket.completion_note = user_id, note
    return tickets
