"""Turning retrieved chunks into selectable sentences and selected IDs back into verbatim evidence.

Pure functions: no model calls, no database. sentence_id=1 is the longest clean prefix of a chunk;
ids >= 2 are its individual sentences.
"""
import re

from pydantic import BaseModel, ConfigDict, Field

from app.rag.safety import ROLE_BLOCK, has_instruction

MAX_SOURCE_CHARS = 1200
CITATION_FIELDS = ("chunk_id", "document_id", "index_version", "source", "score", "page", "location")


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=1500)


class SentenceChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_id: int = Field(ge=1)
    sentence_id: int = Field(ge=1)


def split_sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def source_sentences(text):
    """Quotable form of each sentence: scoped paragraphs and anaphora keep the sentences before them."""
    parts = split_sentences(text)
    scoped = re.match(r"^(?:\*\*)?[^.!?:\n]{1,80}:(?:\*\*)?\s", text) is not None
    # ponytail: explicit paragraph scopes and anaphora only; broader coreference needs independently evaluated parsing.
    return [" ".join(parts[:index + 1]) if scoped or re.match(
        r"(?i)^(trường hợp (này|đó)|khi đó|sau đó|điều này|đây là|this (case|condition)|in (this|that) case)\b", part) or re.search(
        r"(?i)\b(không đủ|chưa đủ|not (?:enough|sufficient))\b", part)
        else part for index, part in enumerate(parts)]


def build_candidates(useful):
    """Returns (sources for review prompts, choices for the selector, raw sentence lists per source)."""
    sources = [{"source_id": i + 1, "text": r["content"][:MAX_SOURCE_CHARS]} for i, r in enumerate(useful)]
    sentences = [[source["text"], *split_sentences(source["text"])] for source in sources]
    choices = []
    for source_id, parts in enumerate(sentences, 1):
        blocked = [match.span() for match in ROLE_BLOCK.finditer(parts[0])]
        unsafe = set()
        offset = 0
        for sentence_id, part in enumerate(parts[1:], 2):
            start = parts[0].find(part, offset)
            offset = start + len(part)
            if has_instruction(part) or any(start < end and offset > begin for begin, end in blocked):
                unsafe.add(sentence_id)
        clean_prefix = []
        for sentence_id, part in enumerate(parts[1:], 2):
            if sentence_id in unsafe:
                break
            clean_prefix.append(part)
        parts[0] = " ".join(clean_prefix)
        choices.append({"source_id": source_id, "sentences": [{"sentence_id": sentence_id, "text": text}
                        for sentence_id, text in enumerate(parts, 1) if text and sentence_id not in unsafe]})
    for source, choice in zip(sources, choices):
        source["text"] = " ".join(f"[{part['sentence_id']}] {part['text']}" for part in choice["sentences"] if part["sentence_id"] != 1)
    return sources, choices, sentences


def allowed_ids(choices):
    return {(choice["source_id"], part["sentence_id"]) for choice in choices for part in choice["sentences"]}


def sentence_choice_schema(choices):
    # Bind sentence IDs to their source in Ollama's grammar; provider output is still validated afterwards.
    return {"oneOf": [
        {"type": "object", "additionalProperties": False, "required": ["source_id", "sentence_id"],
         "properties": {"source_id": {"type": "integer", "enum": [choice["source_id"]]},
                        "sentence_id": {"type": "integer", "enum": [part["sentence_id"] for part in choice["sentences"]]}}}
        for choice in choices if choice["sentences"]]}


def assemble_evidence(selected, useful, sentences, choices):
    """Copy selected sentences verbatim; returns (evidence, citation metadata) or None on any invalid ID."""
    if any(identity not in allowed_ids(choices) for identity in ((c.source_id, c.sentence_id) for c in selected)):
        return None
    evidence, citations, seen = [], [], set()
    for citation in selected:
        identity = (citation.source_id, citation.sentence_id)
        if identity in seen:
            continue
        seen.add(identity)
        source = useful[citation.source_id - 1]
        parts = sentences[citation.source_id - 1]
        quote = " ".join((parts[0] if citation.sentence_id == 1 else
                          source_sentences(source["content"][:MAX_SOURCE_CHARS])[citation.sentence_id - 2]).split())
        if not quote or has_instruction(quote):
            return None
        if any(item.source_id == citation.source_id and quote in item.quote for item in evidence):
            continue
        # A wider excerpt from the same source replaces the narrower ones it contains.
        retained = [(item, metadata) for item, metadata in zip(evidence, citations)
                    if not (item.source_id == citation.source_id and item.quote in quote)]
        evidence = [item for item, _ in retained]
        citations = [metadata for _, metadata in retained]
        evidence.append(Evidence(source_id=citation.source_id, quote=quote))
        citations.append({k: source[k] for k in CITATION_FIELDS} | {"quote": quote})
    return evidence, citations
