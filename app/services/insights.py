"""Answer-quality figures for staff, derived from stored messages (no extra tables).

An AI reply either quotes sources (``citations`` not empty), or is one of the fixed refusal texts
(not enough evidence, ask for clarification, conflicting sources). The customer question behind a
reply is its ``reply_to_id``.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.models.support import KnowledgeDocument, Message, Ticket
from app.rag.answer_service import ABSTENTION, CLARIFICATION, CONFLICT

REFUSALS = (ABSTENTION, CLARIFICATION, CONFLICT)
CITATION_WINDOW_DAYS = 7


def ai_replies(db, start, end):
    # ponytail: demo-sized windows are loaded into Python; aggregate in SQL before large deployments.
    return db.query(Message).filter(Message.sender_type == 'ai', Message.created_at >= start, Message.created_at <= end).all()


def cited(messages, key):
    """How many AI answers quoted each document (key='document_id') or chunk (key='chunk_id'); one per answer."""
    counts = Counter()
    for message in messages:
        counts.update({citation.get(key) for citation in message.citations or [] if citation.get(key)})
    return counts


def outcomes(db, messages, start, end):
    """AI answered with sources, AI could not answer, and conversations handed to staff in the window."""
    return {'answered': sum(1 for m in messages if m.citations),
            'not_answered': sum(1 for m in messages if m.content in REFUSALS),
            'handoffs': db.query(Ticket).filter(Ticket.created_at >= start, Ticket.created_at <= end).count()}


def unanswered_questions(db, messages, limit=5):
    """Customer questions the AI refused or asked to clarify, grouped by normalized text, most frequent first."""
    ids = [m.reply_to_id for m in messages if m.content in REFUSALS and m.reply_to_id]
    if not ids:
        return []
    groups = {}
    for question in db.query(Message).filter(Message.id.in_(ids)).all():
        key = ' '.join(question.content.casefold().split())
        entry = groups.setdefault(key, {'question': question.content.strip()[:200], 'count': 0, 'last_at': question.created_at})
        entry['count'] += 1
        if question.created_at > entry['last_at']:
            entry['last_at'], entry['question'] = question.created_at, question.content.strip()[:200]
    return sorted(groups.values(), key=lambda g: (-g['count'], -g['last_at'].timestamp()))[:limit]


def top_documents(db, messages, limit=5):
    from app.services.document_service import document_title
    counts = cited(messages, 'document_id')
    documents = {d.id: d for d in db.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(list(counts))).all()} if counts else {}
    rows = [{'document_id': doc_id, 'filename': documents[doc_id].filename, 'title': document_title(db, documents[doc_id]), 'count': count}
            for doc_id, count in counts.most_common() if doc_id in documents]
    return rows[:limit]


def recent_citations(db, key):
    """Citation counts over the last CITATION_WINDOW_DAYS days, for the knowledge base page."""
    end = datetime.now(timezone.utc)
    return cited(ai_replies(db, end - timedelta(days=CITATION_WINDOW_DAYS), end), key)
