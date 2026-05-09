from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


def utcnow():
    """Helper tránh deprecated datetime.utcnow()"""
    return datetime.now(timezone.utc)


class Message(BaseModel):
    role: str          # "user" hoặc "model"
    content: str
    timestamp: datetime = Field(default_factory=utcnow)


class Conversation(BaseModel):
    user_id: int
    username: Optional[str] = None
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
