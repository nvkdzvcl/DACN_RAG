from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.answer import AnswerRequest
from app.db.session import get_db
from app.rag.vector_store import vector_store

router = APIRouter(prefix="/api/v1", tags=["rag"])

@router.post("/rag/search")
def search(payload: AnswerRequest, db: Session = Depends(get_db)):
    return {"query": payload.query, "results": vector_store.search(payload.query, payload.top_k, db)}
