from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Channel(str, Enum):
    website = "website"
    telegram = "telegram"


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    channel: Channel = Channel.website
    external_message_id: str | None = None


class ConversationCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    channel: Channel = Channel.website


class ConversationResponse(BaseModel):
    conversation_id: str
    status: str
    priority: str
    created_at: datetime
