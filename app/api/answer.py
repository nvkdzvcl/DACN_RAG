from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.rag.answer_service import answer_question

router = APIRouter(prefix="/api/v1", tags=["rag"])

class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

@router.post("/rag/answer")
def answer(payload: AnswerRequest):
    return {"query": payload.query, **answer_question(payload.query, payload.top_k)}
