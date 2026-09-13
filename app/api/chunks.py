from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import DocumentChunk, KnowledgeDocument

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.get("/{document_id}/chunks")
def list_chunks(document_id: str, db: Session = Depends(get_db)):
    if db.get(KnowledgeDocument, document_id) is None:
        raise HTTPException(404, "Document not found")
    chunks = db.query(DocumentChunk).filter_by(document_id=document_id).order_by(DocumentChunk.chunk_index).all()
    return {"document_id": document_id, "count": len(chunks), "chunks": [{"chunk_id": c.id, "index": c.chunk_index, "source": c.source, "content": c.content, "page": c.page, "location": c.location} for c in chunks]}


@router.get("/{document_id}/chunks/{chunk_id}")
def get_chunk(document_id: str, chunk_id: str, index_version: str | None = None, db: Session = Depends(get_db)):
    document = db.get(KnowledgeDocument, document_id)
    if not document or (index_version and document.index_version != index_version):
        raise HTTPException(409, "Nguồn đã thay đổi. Trích dẫn lưu trong lịch sử thuộc phiên bản cũ.")
    chunk = db.query(DocumentChunk).filter_by(document_id=document_id, id=chunk_id).first()
    if chunk is None:
        raise HTTPException(404, "Nguồn đã bị xóa hoặc thay đổi.")
    return {"chunk_id": chunk.id, "source": chunk.source, "content": chunk.content, "page": chunk.page, "location": chunk.location}
