from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.support import Conversation
from app.services.message_service import process_message

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
class ProcessRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

@router.post("/{conversation_id}/process")
def process(conversation_id: str, payload: ProcessRequest, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None: raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, **process_message(db, conversation, payload.content)}
