"""
Transcript model - centralized transcript storage
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), unique=True, nullable=False)
    transcript_text = Column(Text, nullable=False)
    transcription_service = Column(String, default="whisper-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    word_count = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    episode = relationship("Episode", back_populates="transcript")

    def __repr__(self):
        return f"<Transcript(id={self.id}, episode_id={self.episode_id}, words={self.word_count})>"