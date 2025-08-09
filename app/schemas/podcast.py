"""
Podcast schemas for API validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class PodcastBase(BaseModel):
    name: str
    rss_feed_url: HttpUrl
    description: Optional[str] = None


class PodcastCreate(PodcastBase):
    pass


class PodcastUpdate(BaseModel):
    name: Optional[str] = None
    rss_feed_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PodcastResponse(PodcastBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    last_checked: Optional[datetime] = None

    class Config:
        from_attributes = True