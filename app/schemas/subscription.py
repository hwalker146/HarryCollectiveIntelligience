"""
Subscription schemas for API validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SubscriptionBase(BaseModel):
    podcast_id: int
    custom_prompt: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    custom_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True