from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.order_service import lookup_order

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

class OrderLookupRequest(BaseModel):
    order_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)

@router.post("/lookup")
def lookup(payload: OrderLookupRequest, db: Session = Depends(get_db)):
    return lookup_order(db, payload.order_id, payload.customer_id)
