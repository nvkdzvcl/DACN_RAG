import hashlib
import math
from dataclasses import dataclass


DIMENSION = 256


def embed(text: str) -> list[float]:
    values = [0.0] * DIMENSION
    for token in text.lower().split():
        index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % DIMENSION
        values[index] += 1.0
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


@dataclass
class VectorDocument:
    chunk_id: str
    content: str
    source: str
    vector: list[float]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.documents: dict[str, VectorDocument] = {}

    def upsert(self, documents: list[VectorDocument]) -> None:
        self.documents.update({document.chunk_id: document for document in documents})

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_vector = embed(query)
        ranked = sorted(self.documents.values(), key=lambda doc: cosine(query_vector, doc.vector), reverse=True)
        return [{"chunk_id": doc.chunk_id, "content": doc.content, "source": doc.source, "score": round(cosine(query_vector, doc.vector), 6)} for doc in ranked[:top_k]]


vector_store = InMemoryVectorStore()
