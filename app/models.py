from sqlalchemy import Column, String, Integer, ARRAY, DateTime, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from .database import Base

class ModerationStatus(str, enum.Enum):
    active = "active"
    blocked = "blocked"

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content Fields (Updated for iHateThisPerson)
    image_url = Column(String, nullable=True)  # Public image URL
    title = Column(String(50), nullable=False)  # Person's name (max 50)
    description = Column(String(180), nullable=True)  # Description (max 180)
    reason = Column(String(250), nullable=True)  # Reason for hate (max 250)
    tags = Column(ARRAY(String), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author_hash = Column(String, nullable=False)
    like_count = Column(Integer, default=0)
    
    # Moderation
    status = Column(Enum(ModerationStatus), default=ModerationStatus.active)
    moderation_reason = Column(String, nullable=True)

class Like(Base):
    __tablename__ = "likes"

    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    client_hash = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
