from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.rag.vector_store import vector_store

router = APIRouter(prefix="/api/v1", tags=["rag"])

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

@router.post("/rag/search")
def search(payload: SearchRequest):
    return {"query": payload.query, "results": vector_store.search(payload.query, payload.top_k)}
