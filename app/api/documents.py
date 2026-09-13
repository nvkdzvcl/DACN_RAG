from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.db.session import get_db
from app.models.support import KnowledgeDocument
from app.rag.ollama import ProviderError, call, chat_model, embedding_model
from app.services.document_service import (MAX_FILE_SIZE, delete_document, document_info,
    document_mutation, index_document, knowledge_root, save_document)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    return {"documents": [document_info(db, d) for d in db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()]}


@router.get("/runtime")
def runtime_status():
    try:
        models = [m["name"] for m in call("/api/tags").get("models", [])]
        return {"ready": chat_model() in models and embedding_model() in models,
                "chat_model": chat_model(), "embedding_model": embedding_model(), "installed_models": models}
    except ProviderError as exc:
        return {"ready": False, "chat_model": chat_model(), "embedding_model": embedding_model(), "error": str(exc)}


@router.post("/upload", status_code=201, dependencies=[Depends(require_admin)])
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        return save_document(db, file.filename or "document", file.file.read(MAX_FILE_SIZE + 1), knowledge_root())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        file.file.close()


@router.post("/{document_id}/reindex", dependencies=[Depends(require_admin)])
def reindex(document_id: str, db: Session = Depends(get_db)):
    with document_mutation():
        record = db.get(KnowledgeDocument, document_id)
        if record is None:
            raise HTTPException(404, "Document not found")
        if record.status == "deleting":
            raise HTTPException(409, "Tài liệu đang xóa. Hãy hoàn tất thao tác xóa.")
        return index_document(db, record)


@router.delete("/{document_id}", dependencies=[Depends(require_admin)])
def remove(document_id: str, db: Session = Depends(get_db)):
    with document_mutation():
        record = db.get(KnowledgeDocument, document_id)
        if record is None:
            raise HTTPException(404, "Document not found")
        delete_document(db, record)
    return {"deleted": document_id}
