"""
Analysis report model with enhanced features
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    prompt_used = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    key_quote = Column(Text, nullable=True)  # NEW: AI-extracted key quote
    reading_time_minutes = Column(Integer, nullable=True)  # NEW: Estimated reading time
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analysis_reports")
    episode = relationship("Episode", back_populates="analysis_reports")
    knowledge_base_entry = relationship("KnowledgeBaseEntry", back_populates="analysis_report", uselist=False)

    def __repr__(self):
        return f"<AnalysisReport(id={self.id}, user_id={self.user_id}, episode_id={self.episode_id})>"