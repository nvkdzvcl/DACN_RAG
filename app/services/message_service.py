from uuid import uuid4
from contextlib import nullcontext
import logging
import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.support import Conversation, Message
from app.services.handoff_service import classify_message, queue_handoff
from app.services.order_service import ORDER_PATTERN, lookup_order
from app.services.tool_service import select_order_tool
from app.rag.answer_service import answer_question, sources_current
from app.rag.ollama import ProviderError
from app.rag.vector_store import document_lock

ORDER_REFERENCE = re.compile(r'(?<!\w)đơn(?: hàng)? (?:đó|này|ấy|vừa nêu|ở trên)(?!\w)')

def simple_reply(content: str) -> str | None:
    # ponytail: standalone phrases only; broaden after evaluated intent examples cover mixed policy questions.
    text = ' '.join(re.sub(r'[!?.,]+', ' ', unicodedata.normalize('NFC', content).casefold()).split())
    if text in {'chào', 'chào bạn', 'chào shop', 'xin chào', 'hi', 'hello', 'tôi cần hỗ trợ', 'xin chào tôi cần hỗ trợ'}:
        return 'Chào bạn! Mình là trợ lý AI hỗ trợ khách hàng. Bạn có thể hỏi về chính sách cửa hàng hoặc chọn Gặp nhân viên.'
    if text in {'bạn là ai', 'đây là ai', 'ai đang trả lời', 'bạn là bot hay người'}:
        return 'Mình là trợ lý AI hỗ trợ khách hàng. Mình trả lời chính sách dựa trên tài liệu cửa hàng; nếu cần người hỗ trợ, hãy chọn Gặp nhân viên.'
    return None


def process_message(db: Session, conversation: Conversation, content: str, external_message_id: str | None = None) -> dict:
    content = content.strip()
    if not content or len(content) > 4000:
        raise HTTPException(422, "Message must contain 1-4000 nonblank characters")
    conversation_id = conversation.id
    try:
        db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
        db.refresh(conversation)
        if conversation.status == "closed":
            raise HTTPException(409, "Conversation is closed")
        if external_message_id:
            previous = db.query(Message).filter_by(conversation_id=conversation_id, external_message_id=external_message_id).first()
            if previous:
                if previous.sender_type != "customer" or previous.content != content:
                    raise HTTPException(409, "Message ID was already used for different content")
                response = {"message_id": previous.id, "status": conversation.status, "duplicate": True}
                db.commit()
                return response
        message_id = str(uuid4())
        message = Message(id=message_id, conversation_id=conversation_id, sender_type="customer", content=content,
                          external_message_id=external_message_id)
        db.add(message)
        conversation.last_customer_message_id = message_id
        db.flush()
        sentiment, handoff = classify_message(content)
        order_result = rag = None
        answer = error = None
        should_generate = False
        order_id = selection = None
        order_context = {}
        history = []
        if conversation.status in {"open", "resolved"}:
            if conversation.status == "resolved":
                handoff = True
                conversation.assigned_agent_id = None
            if handoff:
                queue_handoff(db, conversation)
            else:
                recent = db.query(Message).filter(Message.conversation_id == conversation_id, Message.id != message_id,
                    Message.sender_type.in_(["customer", "ai"])).order_by(Message.created_at.desc(), Message.id.desc()).limit(4).all()
                history = [{"role": "user" if m.sender_type == "customer" else "assistant", "content": m.content[:500]} for m in reversed(recent)]
                candidates = list(dict.fromkeys(m.group().upper() for m in ORDER_PATTERN.finditer(content)))
                normalized = ' '.join(unicodedata.normalize('NFC', content).casefold().split())
                # ponytail: explicit Vietnamese references within four messages; broader coreference needs independent evaluation.
                # A malformed/new order token must never silently select an older order.
                if not candidates and ORDER_REFERENCE.search(normalized) and not re.search(r'(?ai:DH|ORD)[\w-]*', content):
                    candidates = list(dict.fromkeys(match.group().upper() for item in recent if item.sender_type == 'customer'
                        for match in ORDER_PATTERN.finditer(item.content)))
                    if candidates:
                        order_context = {'order_id_source': 'history'}
                if len(candidates) > 1:
                    answer = 'Bạn muốn tra cứu đơn nào? Vui lòng gửi một mã đơn trong mỗi tin nhắn.'
                    message.tool_trace = {'status': 'clarification', 'reason': 'multiple_order_ids', **order_context}
                elif candidates:
                    order_id = candidates[0]
                    message.tool_trace = {'status': 'pending', 'order_id': order_id, **order_context}
                else:
                    answer = simple_reply(content)
                    should_generate = answer is None
        # Persist inbound first. Ollama must never hold the conversation write lock.
        db.commit()
        if order_id:
            try:
                selection = select_order_tool(content, order_id)
                should_generate = selection is None
            except ProviderError as exc:
                error = str(exc)
        if should_generate:
            try:
                rag = answer_question(content, history=history, db=db)
                answer = rag["answer"]
            except ProviderError as exc:
                error = str(exc)
            finally:
                db.rollback()
        ai_message_id = None
        # Recheck after generation and serialize with document deletion/reindex.
        with document_lock if answer else nullcontext():
            db.execute(update(Conversation).where(Conversation.id == conversation_id).values(status=Conversation.status))
            db.refresh(conversation)
            current = conversation.status == "open" and conversation.last_customer_message_id == message_id
            if order_id:
                trace = {**order_context, 'order_id': order_id, 'tool': selection['name'] if selection else None,
                         'status': 'skipped' if not current else 'provider_error' if error else 'rag' if selection is None else 'executed'}
                if current and selection:
                    if selection['name'] == 'lookup_order':
                        try:
                            order_result = lookup_order(db, order_id, conversation.customer_id, conversation_id)
                        except SQLAlchemyError as exc:
                            logging.getLogger(__name__).exception('Order lookup failed for message %s', message_id)
                            raise HTTPException(503, 'Không thể tra cứu đơn lúc này. Tin nhắn đã được lưu.') from exc
                        trace['outcome'] = 'found' if order_result['found'] else 'not_found_or_not_owned'
                        if order_result['found']:
                            answer = f"Đơn hàng {order_result['order_id']}: {order_result['status']}."
                            if order_result['tracking_code']:
                                answer += f" Mã vận đơn: {order_result['tracking_code']}."
                    if selection['name'] == 'handoff' or not order_result['found']:
                        queue_handoff(db, conversation)
                db.get(Message, message_id).tool_trace = trace
            valid_sources = not rag or not rag.get("grounded") or sources_current(db, rag.get("reviewed_sources", rag["citations"]))
            if answer and current and valid_sources:
                ai_message_id = str(uuid4())
                db.add(Message(id=ai_message_id, conversation_id=conversation_id, sender_type="ai", content=answer,
                               citations=rag["citations"] if rag else [], reply_to_id=message_id))
            else:
                rag = None
                if not current:
                    order_result = None
                    error = None
            status = conversation.status
            db.commit()
        return {"message_id": message_id, "ai_message_id": ai_message_id, "status": status, "sentiment": sentiment,
                "needs_handoff": status in {"handoff_requested", "assigned"}, "order_lookup": order_result,
                "rag": rag, "ai_error": error}
    except Exception:
        db.rollback()
        raise
