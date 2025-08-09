"""
Episode schemas for API validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class EpisodeResponse(BaseModel):
    id: int
    podcast_id: int
    title: str
    audio_url: HttpUrl
    published_date: Optional[datetime] = None
    duration: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime
    transcript_status: str
    episode_url: Optional[str] = None
    guid: str

    class Config:
        from_attributes = True