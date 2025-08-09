"""
Podcast service for RSS monitoring and episode management
"""
import feedparser
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Podcast, Episode
from app.schemas import PodcastCreate, PodcastUpdate


class PodcastService:
    def create_podcast(self, db: Session, podcast_data: PodcastCreate) -> Podcast:
        """Create a new podcast"""
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
    
    def get_podcast_by_id(self, db: Session, podcast_id: int) -> Optional[Podcast]:
        """Get podcast by ID"""
        return db.query(Podcast).filter(Podcast.id == podcast_id).first()
    
    def get_active_podcasts(self, db: Session) -> List[Podcast]:
        """Get all active podcasts"""
        return db.query(Podcast).filter(Podcast.is_active == True).all()
    
    def search_podcasts(self, db: Session, search_query: str) -> List[Podcast]:
        """Search podcasts by name"""
        return db.query(Podcast).filter(
            Podcast.name.contains(search_query),
            Podcast.is_active == True
        ).all()
    
    def update_podcast(
        self, 
        db: Session, 
        podcast_id: int, 
        podcast_data: PodcastUpdate
    ) -> Optional[Podcast]:
        """Update podcast information"""
        podcast = self.get_podcast_by_id(db, podcast_id)
        if not podcast:
            return None
        
        if podcast_data.name is not None:
            podcast.name = podcast_data.name
        if podcast_data.rss_feed_url is not None:
            podcast.rss_feed_url = str(podcast_data.rss_feed_url)
        if podcast_data.description is not None:
            podcast.description = podcast_data.description
        if podcast_data.is_active is not None:
            podcast.is_active = podcast_data.is_active
        
        db.commit()
        db.refresh(podcast)
        
        return podcast
    
    def parse_rss_feed(self, rss_url: str) -> Dict[str, Any]:
        """Parse RSS feed and return episode data"""
        try:
            # Set user agent to avoid blocking
            headers = {
                'User-Agent': 'Podcast Analysis Application v2/2.0.0 (podcast-app@example.com)'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                return {"success": False, "error": "Invalid RSS feed format"}
            
            episodes = []
            for entry in feed.entries[:10]:  # Limit to latest 10 episodes
                # Extract audio URL
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if not audio_url:
                    continue
                
                # Parse publication date
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])
                
                episode_data = {
                    "title": getattr(entry, 'title', 'Unknown Title'),
                    "description": getattr(entry, 'summary', ''),
                    "audio_url": audio_url,
                    "episode_url": getattr(entry, 'link', ''),
                    "guid": getattr(entry, 'id', entry.link),
                    "published_date": published_date
                }
                
                episodes.append(episode_data)
            
            return {
                "success": True,
                "episodes": episodes,
                "feed_title": getattr(feed.feed, 'title', 'Unknown Podcast'),
                "feed_description": getattr(feed.feed, 'description', '')
            }
            
        except requests.RequestException as e:
            return {"success": False, "error": f"Failed to fetch RSS feed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse RSS feed: {str(e)}"}
    
    def update_podcast_episodes(self, db: Session, podcast: Podcast) -> Dict[str, Any]:
        """Update episodes for a podcast from RSS feed"""
        rss_data = self.parse_rss_feed(podcast.rss_feed_url)
        
        if not rss_data["success"]:
            return rss_data
        
        new_episodes = 0
        for episode_data in rss_data["episodes"]:
            # Check if episode already exists
            existing = db.query(Episode).filter(
                Episode.podcast_id == podcast.id,
                Episode.guid == episode_data["guid"]
            ).first()
            
            if existing:
                continue
            
            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=episode_data["title"],
                audio_url=episode_data["audio_url"],
                published_date=episode_data["published_date"],
                description=episode_data["description"],
                episode_url=episode_data["episode_url"],
                guid=episode_data["guid"],
                transcript_status="pending"
            )
            
            db.add(episode)
            new_episodes += 1
        
        # Update last checked timestamp
        podcast.last_checked = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "new_episodes": new_episodes,
            "total_episodes": len(rss_data["episodes"])
        }
    
    def update_all_podcast_feeds(self, db: Session) -> Dict[str, Any]:
        """Update all active podcast feeds"""
        podcasts = self.get_active_podcasts(db)
        
        results = {
            "success": True,
            "updated_podcasts": 0,
            "total_new_episodes": 0,
            "errors": []
        }
        
        for podcast in podcasts:
            try:
                result = self.update_podcast_episodes(db, podcast)
                if result["success"]:
                    results["updated_podcasts"] += 1
                    results["total_new_episodes"] += result["new_episodes"]
                else:
                    results["errors"].append(f"Failed to update {podcast.name}: {result['error']}")
            except Exception as e:
                results["errors"].append(f"Error updating {podcast.name}: {str(e)}")
        
        return results
    
    def get_podcast_stats(self, db: Session, podcast_id: int) -> Dict[str, Any]:
        """Get statistics for a podcast"""
        podcast = self.get_podcast_by_id(db, podcast_id)
        if not podcast:
            return {"error": "Podcast not found"}
        
        total_episodes = db.query(Episode).filter(Episode.podcast_id == podcast_id).count()
        
        transcribed_episodes = db.query(Episode).filter(
            Episode.podcast_id == podcast_id,
            Episode.transcript_status == "completed"
        ).count()
        
        return {
            "podcast_name": podcast.name,
            "total_episodes": total_episodes,
            "transcribed_episodes": transcribed_episodes,
            "transcription_rate": (transcribed_episodes / total_episodes * 100) if total_episodes > 0 else 0,
            "last_checked": podcast.last_checked,
            "is_active": podcast.is_active
        }