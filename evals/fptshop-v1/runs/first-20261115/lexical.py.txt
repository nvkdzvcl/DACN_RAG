"""Lexical retrieval (BM25) and rank fusion, used by the retrieval benchmark (app.evaluate_retrieval).

Not wired into production search: on the pooled eval corpora every fusion weight lowered Recall@5
(docs/RAG_RETRIEVAL.md). Kept so the experiment can be rerun on a larger or real knowledge base.

Vietnamese is tokenized by syllable without a word segmenter: unigrams plus adjacent-syllable bigrams
approximate compound words. Diacritics are removed so customers typing without accents ("ship qua My")
still match. Pure Python; the index is rebuilt only when the set of indexed document versions changes.
"""
import math
import os
import re
import unicodedata
from collections import Counter
from threading import Lock

RRF_K = 60


def fold(text):
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn").casefold()


def tokens(text):
    words = re.findall(r"\w+", fold(text))
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


class BM25:
    def __init__(self, documents, k1=1.2, b=0.75):
        self.k1, self.b = k1, b
        self.terms = [Counter(tokens(text)) for text in documents]
        self.lengths = [sum(counts.values()) for counts in self.terms]
        self.average = sum(self.lengths) / len(self.lengths) if self.lengths else 0
        frequency = Counter(term for counts in self.terms for term in counts)
        total = len(self.terms)
        self.idf = {term: math.log(1 + (total - n + 0.5) / (n + 0.5)) for term, n in frequency.items()}

    def scores(self, query):
        query_terms = set(tokens(query)) & self.idf.keys()
        results = []
        for counts, length in zip(self.terms, self.lengths):
            score = 0.0
            for term in query_terms & counts.keys():
                tf = counts[term]
                score += self.idf[term] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.average))
            results.append(score)
        return results


class LexicalIndex:
    """BM25 over chunk payloads, cached per set of indexed versions."""

    def __init__(self):
        self.key = None
        self.chunks = []
        self.bm25 = None
        self.lock = Lock()

    def search(self, query, limit, key, load_chunks):
        with self.lock:
            if key != self.key:
                self.chunks = load_chunks()
                self.bm25 = BM25([f"{chunk['source']} {chunk['content']}" for chunk in self.chunks])
                self.key = key
            chunks, bm25 = self.chunks, self.bm25
        scored = [(score, index) for index, score in enumerate(bm25.scores(query)) if score > 0]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [(chunks[index], score) for score, index in scored[:limit]]


def lexical_weight():
    return float(os.getenv("RAG_LEXICAL_WEIGHT", "1.0"))


def fuse(dense, lexical, top_k, weight=None):
    """Weighted reciprocal rank fusion of two ranked chunk lists; returns chunks annotated with lexical rank/score."""
    weight = lexical_weight() if weight is None else weight
    best = lexical[0][1] if lexical else 0
    merged = {chunk["chunk_id"]: dict(chunk) for chunk in dense}
    fused = Counter()
    for rank, chunk in enumerate(dense, 1):
        fused[chunk["chunk_id"]] += 1 / (RRF_K + rank)
    for rank, (chunk, score) in enumerate(lexical, 1):
        item = merged.setdefault(chunk["chunk_id"], dict(chunk))
        item["lexical_rank"], item["lexical_score"] = rank, round(score / best, 6)
        fused[chunk["chunk_id"]] += weight / (RRF_K + rank)
    scored = [chunk_id for chunk_id in merged if "score" in merged[chunk_id]]
    scored.sort(key=lambda chunk_id: (-fused[chunk_id], -merged[chunk_id]["score"], chunk_id))
    return [merged[chunk_id] for chunk_id in scored[:top_k]]
