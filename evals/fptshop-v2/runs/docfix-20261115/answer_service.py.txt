"""Grounded RAG answering: rewrite -> retrieve -> select sentences -> verify -> recheck sources.

The model never writes answer text. It only picks source/sentence IDs; the backend copies those
sentences verbatim (app.rag.evidence). Decisions such as "ask the customer for a missing condition"
or "sources conflict" are made by the model from the retrieved sources, not by per-question rules.
Regex remains only for input safety and structural source checks (app.rag.safety).

Each model call lives here so tests can patch app.rag.answer_service.chat in one place.
"""
import json
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.db.session import SessionLocal
from app.models.support import KnowledgeDocument
from app.rag.evidence import (Evidence, SentenceChoice, allowed_ids, assemble_evidence, build_candidates,
                              sentence_choice_schema, source_sentences)
from app.rag.ollama import chat
from app.rag.prompts import REVIEW_PROMPT, REWRITE_PROMPT, SELECTION_PROMPT
from app.rag.safety import (clean_history, has_instruction, opposing_policy, required_contact_number,
                            unresolved_notices)
from app.rag.vector_store import document_lock, vector_store

__all__ = ["ABSTENTION", "CLARIFICATION", "CONFLICT", "Evidence", "answer_question", "opposing_policy",
           "source_sentences", "sources_current", "unresolved_notices"]

ABSTENTION = "Tôi chưa tìm thấy đủ thông tin trong tài liệu để trả lời. Bạn có thể cung cấp thêm chi tiết hoặc yêu cầu gặp nhân viên."
CLARIFICATION = "Bạn đang hỏi về vấn đề nào và trong trường hợp cụ thể nào? Vui lòng nêu rõ để tôi tra đúng chính sách."
# 0.30 was tried: more weak sources made the selector answer ambiguous questions (docs/RAG_RETRIEVAL.md).
DEFAULT_MIN_SCORE = "0.35"
CONFLICT = "Tài liệu có quy định mâu thuẫn cho cùng trường hợp. Tôi chưa thể xác nhận quy định áp dụng; bạn vui lòng yêu cầu nhân viên kiểm tra."


class StandaloneQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=400)


class SourceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reason: str = Field(default="", max_length=500)
    decision: Literal["answer", "ask_customer", "sources_disagree", "not_in_sources"] = "answer"
    # ponytail: three excerpts fit the 4000-character message limit; add packing for longer answers.
    citations: list[SentenceChoice] = Field(max_length=3)


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supported: bool
    answer: str = Field(max_length=4000)
    citations: list[Evidence] = Field(max_length=5)


class AnswerReview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reason: str = Field(min_length=1, max_length=1500)
    question_resolved: bool
    sources_consistent: bool
    claims_supported: bool
    needs_clarification: bool
    repair_citations: list[SentenceChoice] = Field(max_length=3)

    @property
    def accepted(self):
        return self.question_resolved and self.sources_consistent and self.claims_supported and not self.needs_clarification


def min_score():
    return float(os.getenv("RAG_MIN_SCORE", DEFAULT_MIN_SCORE))


def ask_model(system, payload, schema, model):
    """One structured model call; returns the validated object or None when the provider ignores the schema."""
    response = chat([{"role": "system", "content": system},
                     {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], schema)
    try:
        return model.model_validate_json(response)
    except ValidationError:
        return None


def standalone_question(query, history):
    """Resolve a follow-up into a self-contained question; one model call only when the customer has history."""
    user_turns = [m["content"] for m in history if m["role"] == "user"]
    if not user_turns:
        return query
    fallback = "\n".join([*(turn[:240] for turn in user_turns), query])
    result = ask_model(REWRITE_PROMPT, {"HISTORY": history, "CÂU HỎI CUỐI": query},
                       StandaloneQuestion.model_json_schema(), StandaloneQuestion)
    rewritten = " ".join(result.question.split()) if result else ""
    # An unchanged or instruction-carrying rewrite is discarded; the raw customer turns are still safe retrieval input.
    if not rewritten or rewritten.casefold() == " ".join(query.split()).casefold() or has_instruction(rewritten):
        return fallback
    return rewritten


def select_evidence(question, history, choices, choice_schema):
    schema = SourceSelection.model_json_schema()
    schema["required"] = ["reason", "decision", "citations"]
    schema["$defs"]["SentenceChoice"] = choice_schema
    return ask_model(SELECTION_PROMPT, {"HISTORY": history, "SOURCES": choices, "QUESTION": question}, schema, SourceSelection)


def review_answer(question, history, sources, answer, choice_schema):
    # ponytail: same-model review reduces errors, not a proof; add independent human evaluation before acceptance.
    schema = AnswerReview.model_json_schema()
    schema["$defs"]["SentenceChoice"] = choice_schema
    payload = {"QUESTION": question, "HISTORY": history, "CANDIDATE": answer.model_dump(), "SOURCES": sources}
    return ask_model(REVIEW_PROMPT, payload, schema, AnswerReview)


def sources_current(db, sources):
    for source in sources:
        document = db.get(KnowledgeDocument, source.get("document_id"), populate_existing=True)
        if not document or document.status != "indexed" or document.index_version != source.get("index_version"):
            return False
    return True


def answer_question(query, top_k=5, history=None, db=None):
    if db is None:
        with SessionLocal() as session:
            return answer_question(query, top_k, history, session)
    history = clean_history(history)
    # History resolves follow-up subjects; it is never evidence for policy facts.
    question = standalone_question(query, history)
    results = vector_store.search(question, top_k, db)
    useful = [r for r in results if r["score"] >= min_score()][:5]
    fallback = {"answer": ABSTENTION, "grounded": False, "citations": [], "results": results}
    clarify = fallback | {"answer": CLARIFICATION, "needs_clarification": True}
    conflict = fallback | {"answer": CONFLICT}
    required_number = required_contact_number(question)
    if not useful or (required_number and not any(required_number.search(r["content"]) for r in useful)):
        return fallback
    sources, choices, sentences = build_candidates(useful)
    if not any(choice["sentences"] for choice in choices):
        return fallback
    choice_schema = sentence_choice_schema(choices)
    selection = select_evidence(question, history, choices, choice_schema)
    if selection is None:
        return fallback
    if selection.decision == "ask_customer":
        return clarify
    if selection.decision == "sources_disagree":
        return conflict
    selected = selection.citations if selection.decision == "answer" else []
    for attempt in range(2):
        assembled = assemble_evidence(selected, useful, sentences, choices) if selected else None
        if not assembled or not assembled[0]:
            return fallback
        evidence, citations = assembled
        answer = GroundedAnswer(supported=True, answer="\n\n".join(item.quote for item in evidence), citations=evidence)
        if required_number and not required_number.search(answer.answer):
            return fallback
        if any(unresolved_notices(item.quote) for item in evidence) or opposing_policy(evidence, [s["text"] for s in sources]):
            return conflict
        review = review_answer(question, history, sources, answer, choice_schema)
        if review is None:
            return fallback
        if not review.sources_consistent:
            return fallback if review.needs_clarification else conflict
        if review.needs_clarification and not review.question_resolved:
            return clarify
        if review.accepted:
            break
        # One repair: the reviewer may point at better sentences, which are then reviewed again.
        if attempt or any(identity not in allowed_ids(choices) for identity in
                          ((c.source_id, c.sentence_id) for c in review.repair_citations)):
            return fallback
        selected = review.repair_citations
    reviewed_sources = [{k: source[k] for k in ("document_id", "index_version")} for source in useful]
    with document_lock:
        valid = sources_current(db, reviewed_sources)
        db.commit()
    if not valid:
        return fallback | {"results": []}
    return {"answer": answer.answer.strip(), "grounded": True, "citations": citations, "results": results,
            "reviewed_sources": reviewed_sources}
