from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import DocumentChunk

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.get("/{document_id}/chunks")
def list_chunks(document_id: str, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter_by(document_id=document_id).order_by(DocumentChunk.chunk_index).all()
    return {"document_id": document_id, "count": len(chunks), "chunks": [{"chunk_id": c.id, "index": c.chunk_index, "source": c.source, "content": c.content} for c in chunks]}
