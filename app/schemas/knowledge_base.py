"""
Knowledge base schemas for API validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class KnowledgeBaseEntryBase(BaseModel):
    podcast_category: Optional[str] = None
    entry_title: Optional[str] = None
    key_insights: Optional[str] = None
    personal_notes: Optional[str] = None
    tags: Optional[str] = None
    is_favorited: Optional[bool] = False


class KnowledgeBaseEntryUpdate(KnowledgeBaseEntryBase):
    pass


class KnowledgeBaseEntryResponse(KnowledgeBaseEntryBase):
    id: int
    user_id: int
    analysis_report_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    category_name: str
    color_code: Optional[str] = None
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True