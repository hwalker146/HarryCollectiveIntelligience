"""
Episode service for episode management
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Episode, Podcast


class EpisodeService:
    def get_episode_by_id(self, db: Session, episode_id: int) -> Optional[Episode]:
        """Get episode by ID"""
        return db.query(Episode).filter(Episode.id == episode_id).first()
    
    def get_episodes_by_podcast(
        self, 
        db: Session, 
        podcast_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Episode]:
        """Get episodes for a specific podcast"""
        return db.query(Episode).filter(
            Episode.podcast_id == podcast_id
        ).order_by(Episode.published_date.desc()).offset(skip).limit(limit).all()
    
    def get_recent_episodes(
        self, 
        db: Session, 
        days: int = 7, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Episode]:
        """Get recent episodes across all podcasts"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return db.query(Episode).filter(
            Episode.published_date >= cutoff_date
        ).order_by(Episode.published_date.desc()).offset(skip).limit(limit).all()
    
    def get_episodes_pending_transcription(self, db: Session, limit: int = 50) -> List[Episode]:
        """Get episodes that need transcription"""
        return db.query(Episode).filter(
            Episode.transcript_status == "pending"
        ).order_by(Episode.published_date.desc()).limit(limit).all()
    
    def get_episodes_with_transcripts(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Episode]:
        """Get episodes that have completed transcripts"""
        return db.query(Episode).filter(
            Episode.transcript_status == "completed"
        ).order_by(Episode.published_date.desc()).offset(skip).limit(limit).all()
    
    def update_transcript_status(
        self, 
        db: Session, 
        episode_id: int, 
        status: str
    ) -> bool:
        """Update episode transcript status"""
        episode = self.get_episode_by_id(db, episode_id)
        if not episode:
            return False
        
        episode.transcript_status = status
        db.commit()
        
        return True
    
    def get_episode_with_podcast(self, db: Session, episode_id: int) -> Optional[dict]:
        """Get episode with podcast information"""
        result = db.query(Episode, Podcast).join(Podcast).filter(
            Episode.id == episode_id
        ).first()
        
        if not result:
            return None
        
        episode, podcast = result
        
        return {
            "episode": episode,
            "podcast": podcast
        }