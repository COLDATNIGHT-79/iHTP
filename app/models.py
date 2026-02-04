from sqlalchemy import Column, String, Integer, ARRAY, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content Fields
    image_data = Column(Text, nullable=True)  # Base64 encoded image
    title = Column(String(50), nullable=False)
    description = Column(String(180), nullable=True)
    reason = Column(String(250), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    nationality = Column(String(5), nullable=True)
    
    # Legacy fields (kept for compatibility)
    image_url = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    author_hash = Column(String, nullable=False)
    like_count = Column(Integer, default=0)
    
    # Moderation
    status = Column(String(20), default="active")
    moderation_reason = Column(String, nullable=True)

class Like(Base):
    __tablename__ = "likes"

    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    client_hash = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
