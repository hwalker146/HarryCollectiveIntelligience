"""
Knowledge base models for personal learning organization
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_report_id = Column(Integer, ForeignKey("analysis_reports.id"), unique=True, nullable=False)
    podcast_category = Column(String, nullable=True)  # User-defined category
    entry_title = Column(String, nullable=True)
    key_insights = Column(Text, nullable=True)
    personal_notes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)  # Comma-separated tags
    is_favorited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="knowledge_base_entries")
    analysis_report = relationship("AnalysisReport", back_populates="knowledge_base_entry")

    def __repr__(self):
        return f"<KnowledgeBaseEntry(id={self.id}, user_id={self.user_id}, title='{self.entry_title}')>"


class PodcastCategory(Base):
    __tablename__ = "podcast_categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_name = Column(String, nullable=False)
    color_code = Column(String, nullable=True)  # Hex color for UI
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="podcast_categories")

    def __repr__(self):
        return f"<PodcastCategory(id={self.id}, user_id={self.user_id}, name='{self.category_name}')>"