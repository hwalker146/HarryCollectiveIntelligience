"""
Main API routes for Podcast Analysis Application v2
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User, Podcast, Episode, AnalysisReport, UserSubscription, KnowledgeBaseEntry
from app.schemas import (
    UserCreate, UserResponse, 
    PodcastResponse, PodcastCreate,
    EpisodeResponse,
    SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate,
    AnalysisResponse,
    KnowledgeBaseEntryResponse, KnowledgeBaseEntryUpdate, CategoryResponse, CategoryCreate
)
from app.services import UserService, PodcastService, AnalysisService, KnowledgeBaseService

router = APIRouter()

# User routes
@router.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    user_service = UserService()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        is_active=True,
        email_verified=False  # Will be verified via email
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/auth/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token"""
    # TODO: Implement email verification logic
    return {"message": "Email verified successfully"}


# Podcast routes
@router.get("/podcasts", response_model=List[PodcastResponse])
async def get_podcasts(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get available podcasts"""
    query = db.query(Podcast).filter(Podcast.is_active == True)
    
    if search:
        query = query.filter(Podcast.name.contains(search))
    
    podcasts = query.offset(skip).limit(limit).all()
    return podcasts


@router.get("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(podcast_id: int, db: Session = Depends(get_db)):
    """Get specific podcast details"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    return podcast


@router.post("/podcasts", response_model=PodcastResponse)
async def create_podcast(podcast_data: PodcastCreate, db: Session = Depends(get_db)):
    """Create new podcast (admin only)"""
    # TODO: Add admin authentication
    podcast = Podcast(
        name=podcast_data.name,
        rss_feed_url=str(podcast_data.rss_feed_url),
        description=podcast_data.description,
        is_active=True
    )
    
    db.add(podcast)
    db.commit()
    db.refresh(podcast)
    
    return podcast


# Subscription routes
@router.get("/users/{user_id}/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    """Get user's podcast subscriptions"""
    subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.is_active == True
    ).all()
    return subscriptions


@router.post("/users/{user_id}/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    user_id: int, 
    subscription_data: SubscriptionCreate, 
    db: Session = Depends(get_db)
):
    """Create new podcast subscription"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if podcast exists
    podcast = db.query(Podcast).filter(Podcast.id == subscription_data.podcast_id).first()
    if not podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    # Check if subscription already exists
    existing = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.podcast_id == subscription_data.podcast_id
    ).first()
    
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.custom_prompt = subscription_data.custom_prompt
            db.commit()
            return existing
        else:
            raise HTTPException(status_code=400, detail="Already subscribed to this podcast")
    
    # Create new subscription
    subscription = UserSubscription(
        user_id=user_id,
        podcast_id=subscription_data.podcast_id,
        custom_prompt=subscription_data.custom_prompt,
        is_active=True
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return subscription


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_data: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Update subscription settings"""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    if subscription_data.custom_prompt is not None:
        subscription.custom_prompt = subscription_data.custom_prompt
    
    if subscription_data.is_active is not None:
        subscription.is_active = subscription_data.is_active
    
    db.commit()
    db.refresh(subscription)
    
    return subscription


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Remove subscription"""
    subscription = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription.is_active = False
    db.commit()
    
    return {"message": "Subscription removed successfully"}


# Analysis routes
@router.get("/users/{user_id}/reports", response_model=List[AnalysisResponse])
async def get_user_reports(
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get user's analysis reports"""
    analysis_service = AnalysisService()
    reports = analysis_service.get_user_analysis_reports(db, user_id, skip, limit)
    return reports


@router.get("/reports/{report_id}", response_model=AnalysisResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get specific analysis report"""
    analysis_service = AnalysisService()
    report = analysis_service.get_analysis_report_by_id(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.put("/reports/{report_id}/notes")
async def update_report_notes(
    report_id: int,
    notes_data: dict,
    db: Session = Depends(get_db)
):
    """Update personal notes for analysis report"""
    analysis_service = AnalysisService()
    
    # Get the report to find user_id
    report = analysis_service.get_analysis_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    success = analysis_service.update_personal_notes(
        db, report_id, report.user_id, notes_data.get("notes", "")
    )
    
    if success:
        return {"message": "Notes updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update notes")


# Knowledge Base routes
@router.get("/users/{user_id}/knowledge-base", response_model=List[KnowledgeBaseEntryResponse])
async def get_knowledge_base(
    user_id: int,
    category: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get user's knowledge base entries"""
    knowledge_service = KnowledgeBaseService()
    return knowledge_service.get_user_entries(db, user_id, category, skip, limit)


@router.get("/users/{user_id}/knowledge-base/search", response_model=List[KnowledgeBaseEntryResponse])
async def search_knowledge_base(
    user_id: int,
    q: str = Query(..., description="Search query"),
    db: Session = Depends(get_db)
):
    """Search user's knowledge base"""
    knowledge_service = KnowledgeBaseService()
    return knowledge_service.search_entries(db, user_id, q)


@router.get("/users/{user_id}/knowledge-base/categories", response_model=List[CategoryResponse])
async def get_user_categories(user_id: int, db: Session = Depends(get_db)):
    """Get user's custom categories"""
    knowledge_service = KnowledgeBaseService()
    return knowledge_service.get_user_categories(db, user_id)


@router.post("/users/{user_id}/knowledge-base/categories", response_model=CategoryResponse)
async def create_category(
    user_id: int,
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
):
    """Create new category"""
    knowledge_service = KnowledgeBaseService()
    return knowledge_service.create_category(db, user_id, category_data)


@router.put("/knowledge-base/{entry_id}", response_model=KnowledgeBaseEntryResponse)
async def update_knowledge_base_entry(
    entry_id: int,
    entry_data: KnowledgeBaseEntryUpdate,
    db: Session = Depends(get_db)
):
    """Update knowledge base entry"""
    knowledge_service = KnowledgeBaseService()
    entry = knowledge_service.update_entry(db, entry_id, entry_data)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")
    
    return entry


# Admin routes
@router.get("/admin/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    # TODO: Add admin authentication
    
    stats = {
        "total_users": db.query(User).count(),
        "total_podcasts": db.query(Podcast).count(),
        "total_episodes": db.query(Episode).count(),
        "total_analysis_reports": db.query(AnalysisReport).count(),
        "active_subscriptions": db.query(UserSubscription).filter(UserSubscription.is_active == True).count(),
    }
    
    return stats