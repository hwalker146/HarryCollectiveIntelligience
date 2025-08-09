"""
User model for multi-user support
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="user")
    analysis_reports = relationship("AnalysisReport", back_populates="user")
    knowledge_base_entries = relationship("KnowledgeBaseEntry", back_populates="user")
    podcast_categories = relationship("PodcastCategory", back_populates="user")
    email_logs = relationship("EmailLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"