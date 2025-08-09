"""
Podcast model - enhanced from v1
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    rss_feed_url = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Migration fields from v1
    last_checked = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    episodes = relationship("Episode", back_populates="podcast")
    subscriptions = relationship("UserSubscription", back_populates="podcast")

    def __repr__(self):
        return f"<Podcast(id={self.id}, name='{self.name}')>"