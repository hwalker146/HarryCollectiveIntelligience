"""
Pydantic schemas for request/response validation
"""
from .user import UserCreate, UserResponse, UserUpdate
from .podcast import PodcastCreate, PodcastResponse, PodcastUpdate
from .episode import EpisodeResponse
from .subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from .analysis import AnalysisResponse, AnalysisCreate
from .knowledge_base import KnowledgeBaseEntryResponse, KnowledgeBaseEntryUpdate, CategoryResponse, CategoryCreate

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "PodcastCreate", "PodcastResponse", "PodcastUpdate", 
    "EpisodeResponse",
    "SubscriptionCreate", "SubscriptionResponse", "SubscriptionUpdate",
    "AnalysisResponse", "AnalysisCreate",
    "KnowledgeBaseEntryResponse", "KnowledgeBaseEntryUpdate",
    "CategoryResponse", "CategoryCreate",
]