from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.rag.answer_service import answer_question

router = APIRouter(prefix="/api/v1", tags=["rag"])

class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Query must not be blank")
        return value.strip()

@router.post("/rag/answer")
def answer(payload: AnswerRequest, db: Session = Depends(get_db)):
    return {"query": payload.query, **answer_question(payload.query, payload.top_k, db=db)}
