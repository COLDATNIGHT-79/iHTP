from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class PostCreate(BaseModel):
    image_url: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=180)
    reason: Optional[str] = Field(None, max_length=250)
    tags: List[str] = Field(default_factory=list, max_length=3)

class PostResponse(BaseModel):
    id: UUID
    image_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: datetime
    like_count: int
    status: str
    moderation_reason: Optional[str] = None

    class Config:
        from_attributes = True
