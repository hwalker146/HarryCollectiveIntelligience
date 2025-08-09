"""
Knowledge base service for personal learning organization
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import KnowledgeBaseEntry, PodcastCategory, AnalysisReport, Episode, Podcast
from app.schemas import KnowledgeBaseEntryUpdate, CategoryCreate


class KnowledgeBaseService:
    def get_user_entries(
        self, 
        db: Session, 
        user_id: int, 
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[KnowledgeBaseEntry]:
        """Get user's knowledge base entries"""
        query = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.user_id == user_id)
        
        if category:
            query = query.filter(KnowledgeBaseEntry.podcast_category == category)
        
        return query.order_by(KnowledgeBaseEntry.created_at.desc()).offset(skip).limit(limit).all()
    
    def search_entries(self, db: Session, user_id: int, search_query: str) -> List[KnowledgeBaseEntry]:
        """Search user's knowledge base entries"""
        search_term = f"%{search_query}%"
        
        return db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.user_id == user_id,
            or_(
                KnowledgeBaseEntry.entry_title.contains(search_term),
                KnowledgeBaseEntry.key_insights.contains(search_term),
                KnowledgeBaseEntry.personal_notes.contains(search_term),
                KnowledgeBaseEntry.tags.contains(search_term)
            )
        ).order_by(KnowledgeBaseEntry.updated_at.desc()).all()
    
    def update_entry(
        self, 
        db: Session, 
        entry_id: int, 
        entry_data: KnowledgeBaseEntryUpdate
    ) -> Optional[KnowledgeBaseEntry]:
        """Update knowledge base entry"""
        entry = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.id == entry_id).first()
        if not entry:
            return None
        
        if entry_data.podcast_category is not None:
            entry.podcast_category = entry_data.podcast_category
        if entry_data.entry_title is not None:
            entry.entry_title = entry_data.entry_title
        if entry_data.key_insights is not None:
            entry.key_insights = entry_data.key_insights
        if entry_data.personal_notes is not None:
            entry.personal_notes = entry_data.personal_notes
        if entry_data.tags is not None:
            entry.tags = entry_data.tags
        if entry_data.is_favorited is not None:
            entry.is_favorited = entry_data.is_favorited
        
        db.commit()
        db.refresh(entry)
        
        return entry
    
    def toggle_favorite(self, db: Session, entry_id: int, user_id: int) -> bool:
        """Toggle favorite status of knowledge base entry"""
        entry = db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.id == entry_id,
            KnowledgeBaseEntry.user_id == user_id
        ).first()
        
        if not entry:
            return False
        
        entry.is_favorited = not entry.is_favorited
        db.commit()
        
        return True
    
    def get_user_categories(self, db: Session, user_id: int) -> List[PodcastCategory]:
        """Get user's custom categories"""
        return db.query(PodcastCategory).filter(
            PodcastCategory.user_id == user_id
        ).order_by(PodcastCategory.category_name).all()
    
    def create_category(
        self, 
        db: Session, 
        user_id: int, 
        category_data: CategoryCreate
    ) -> PodcastCategory:
        """Create new category"""
        category = PodcastCategory(
            user_id=user_id,
            category_name=category_data.category_name,
            color_code=category_data.color_code,
            description=category_data.description
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category
    
    def update_category(
        self, 
        db: Session, 
        category_id: int, 
        user_id: int, 
        category_data: CategoryCreate
    ) -> Optional[PodcastCategory]:
        """Update category"""
        category = db.query(PodcastCategory).filter(
            PodcastCategory.id == category_id,
            PodcastCategory.user_id == user_id
        ).first()
        
        if not category:
            return None
        
        category.category_name = category_data.category_name
        category.color_code = category_data.color_code
        category.description = category_data.description
        
        db.commit()
        db.refresh(category)
        
        return category
    
    def get_timeline_view(self, db: Session, user_id: int, days: int = 30) -> List[dict]:
        """Get chronological timeline view of knowledge base entries"""
        entries = db.query(KnowledgeBaseEntry).join(AnalysisReport).join(Episode).join(Podcast).filter(
            KnowledgeBaseEntry.user_id == user_id
        ).order_by(KnowledgeBaseEntry.created_at.desc()).limit(days * 5).all()  # Rough estimate
        
        timeline = []
        for entry in entries:
            timeline_item = {
                "id": entry.id,
                "date": entry.created_at.date(),
                "title": entry.entry_title,
                "podcast_name": entry.analysis_report.episode.podcast.name,
                "category": entry.podcast_category,
                "key_quote": entry.analysis_report.key_quote,
                "is_favorited": entry.is_favorited,
                "reading_time": entry.analysis_report.reading_time_minutes
            }
            timeline.append(timeline_item)
        
        return timeline
    
    def get_favorites(self, db: Session, user_id: int) -> List[KnowledgeBaseEntry]:
        """Get user's favorited entries"""
        return db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.user_id == user_id,
            KnowledgeBaseEntry.is_favorited == True
        ).order_by(KnowledgeBaseEntry.updated_at.desc()).all()
    
    def get_category_stats(self, db: Session, user_id: int) -> dict:
        """Get statistics by category"""
        entries = db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.user_id == user_id).all()
        
        stats = {}
        for entry in entries:
            category = entry.podcast_category or "Uncategorized"
            if category not in stats:
                stats[category] = {"count": 0, "favorited": 0}
            
            stats[category]["count"] += 1
            if entry.is_favorited:
                stats[category]["favorited"] += 1
        
        return stats