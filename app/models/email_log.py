"""
Email log model for tracking email delivery
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_type = Column(String, nullable=False)  # signup/weekly_report/error
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False)  # sent/failed
    subject = Column(String, nullable=True)
    content_preview = Column(Text, nullable=True)  # First 200 chars of content
    
    # Relationships
    user = relationship("User", back_populates="email_logs")

    def __repr__(self):
        return f"<EmailLog(id={self.id}, user_id={self.user_id}, type='{self.email_type}', status='{self.status}')>"