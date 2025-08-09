"""
Analysis schemas for API validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AnalysisBase(BaseModel):
    episode_id: int
    prompt_used: str
    analysis_result: str
    key_quote: Optional[str] = None
    reading_time_minutes: Optional[int] = None


class AnalysisCreate(AnalysisBase):
    pass


class AnalysisResponse(AnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    processing_time_seconds: Optional[float] = None

    class Config:
        from_attributes = True