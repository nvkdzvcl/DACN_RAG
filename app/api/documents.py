from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.document_service import save_document
from app.models.support import DocumentChunk
from app.rag.vector_store import VectorDocument, embed, vector_store

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        result = save_document(db, file.filename or "document", await file.read(), Path("data/knowledge_base"))
        chunks = db.query(DocumentChunk).filter_by(document_id=result["document_id"]).all()
        vector_store.upsert([VectorDocument(c.id, c.content, c.source, embed(c.content)) for c in chunks])
        result["status"] = "indexed"
        result.pop("text", None)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Document processing failed: {exc}") from exc
