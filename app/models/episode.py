"""
Episode model - enhanced from v1
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    title = Column(String, nullable=False)
    audio_url = Column(String, nullable=False)
    published_date = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Transcript processing status
    transcript_status = Column(String, default="pending")  # pending/processing/completed/failed
    
    # Migration fields from v1
    episode_url = Column(String, nullable=True)
    guid = Column(String, unique=True, nullable=False)
    audio_file_path = Column(String, nullable=True)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="episodes")
    transcript = relationship("Transcript", back_populates="episode", uselist=False)
    analysis_reports = relationship("AnalysisReport", back_populates="episode")

    def __repr__(self):
        return f"<Episode(id={self.id}, title='{self.title[:50]}...')>"