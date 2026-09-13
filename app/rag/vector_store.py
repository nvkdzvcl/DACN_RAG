"""Persistent Qdrant local store; only indexed SQL documents are searchable."""
import hashlib
import os
from threading import RLock
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.db.session import SessionLocal
from app.models.support import KnowledgeDocument
from app.rag.ollama import ProviderError, embed, embedding_model

# ponytail: one API worker with embedded Qdrant; use Qdrant server for multiple workers.
document_lock = RLock()


class VectorStore:
    def __init__(self, path=None):
        self.path = path
        self.client = None
        self.lock = RLock()

    def _client(self):
        if self.client is None:
            self.client = QdrantClient(path=self.path or os.getenv("QDRANT_PATH", "data/vectors"))
        return self.client

    @staticmethod
    def collection():
        return "knowledge_" + hashlib.sha256(embedding_model().encode()).hexdigest()[:16]

    def upsert(self, chunks, vectors):
        with self.lock:
            client = self._client()
            collection = self.collection()
            if not client.collection_exists(collection):
                client.create_collection(collection, vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE))
            client.upsert(collection, points=[models.PointStruct(id=str(uuid5(NAMESPACE_URL, c["chunk_id"])), vector=v, payload=c)
                                               for c, v in zip(chunks, vectors, strict=True)])

    def delete(self, document_id):
        with self.lock:
            client = self._client()
            for collection in client.get_collections().collections:
                client.delete(collection.name, models.FilterSelector(filter=models.Filter(must=[
                    models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))])))

    def search(self, query, top_k=5, db=None):
        if not query.strip():
            raise ValueError("Query must not be blank")
        if db is None:
            with SessionLocal() as session:
                return self.search(query, top_k, session)
        ready = db.query(KnowledgeDocument).filter_by(status="indexed", embedding_model=embedding_model()).all()
        versions = [d.index_version for d in ready if d.index_version]
        db.commit()  # No SQL transaction during embedding/network work.
        if not versions:
            return []
        vector = embed(["task: search result | query: " + query])[0]
        try:
            with self.lock:
                client = self._client()
                if not client.collection_exists(self.collection()):
                    raise ProviderError("Kho vector chưa có dữ liệu. Hãy lập chỉ mục lại tài liệu.")
                hits = client.query_points(self.collection(), query=vector, limit=top_k,
                    query_filter=models.Filter(must=[models.FieldCondition(key="index_version", match=models.MatchAny(any=versions))])).points
                results = [{**hit.payload, "score": round(hit.score, 6)} for hit in hits]
            with document_lock:
                current_versions = {v for (v,) in db.query(KnowledgeDocument.index_version).filter_by(status="indexed", embedding_model=embedding_model()).all()}
                db.commit()
            return [r for r in results if r["index_version"] in current_versions]
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Không đọc được kho vector. Kiểm tra đường dẫn và lập chỉ mục lại.") from exc

    def close(self):
        with self.lock:
            if self.client is not None:
                self.client.close()
                self.client = None


vector_store = VectorStore()
