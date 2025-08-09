"""
Migration script from v1 SQLite to v2 PostgreSQL/SQLite
Preserves all existing data while adding new features
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models import User, Podcast, Episode, Transcript, AnalysisReport, UserSubscription
from app.core.database import SessionLocal, create_tables
from app.core.config import settings


class V1ToV2Migration:
    def __init__(self, v1_db_path: str, v1_transcripts_path: str):
        self.v1_db_path = v1_db_path
        self.v1_transcripts_path = v1_transcripts_path
        self.migration_user_id = None
        
    def connect_v1_db(self):
        """Connect to v1 SQLite database"""
        if not os.path.exists(self.v1_db_path):
            raise FileNotFoundError(f"V1 database not found at {self.v1_db_path}")
        
        conn = sqlite3.connect(self.v1_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_migration_user(self, db: Session):
        """Create a default user for migrating v1 data"""
        # Check if migration user already exists
        user = db.query(User).filter(User.email == settings.smtp_username).first()
        if user:
            self.migration_user_id = user.id
            print(f"Using existing user: {user.email}")
            return user
        
        # Create new migration user
        user = User(
            email=settings.smtp_username or "migration@podcastapp.com",
            name="Migration User",
            is_active=True,
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        self.migration_user_id = user.id
        print(f"Created migration user: {user.email}")
        return user
    
    def migrate_podcasts(self, v1_conn, db: Session):
        """Migrate podcasts from v1 to v2"""
        print("Migrating podcasts...")
        
        cursor = v1_conn.cursor()
        cursor.execute("SELECT * FROM podcasts")
        v1_podcasts = cursor.fetchall()
        
        migrated_count = 0
        for v1_podcast in v1_podcasts:
            # Check if podcast already exists
            existing = db.query(Podcast).filter(Podcast.id == v1_podcast['id']).first()
            if existing:
                print(f"Podcast {v1_podcast['name']} already exists, skipping")
                continue
            
            podcast = Podcast(
                id=v1_podcast['id'],
                name=v1_podcast['name'],
                rss_feed_url=v1_podcast['rss_url'],
                description=None,  # v1 didn't have description
                is_active=bool(v1_podcast['is_active']),
                last_checked=datetime.fromisoformat(v1_podcast['last_checked']) if v1_podcast['last_checked'] else None,
                created_at=datetime.fromisoformat(v1_podcast['created_at']) if v1_podcast['created_at'] else datetime.now()
            )
            
            db.add(podcast)
            migrated_count += 1
        
        db.commit()
        print(f"Migrated {migrated_count} podcasts")
    
    def migrate_episodes(self, v1_conn, db: Session):
        """Migrate episodes from v1 to v2"""
        print("Migrating episodes...")
        
        cursor = v1_conn.cursor()
        cursor.execute("SELECT * FROM episodes")
        v1_episodes = cursor.fetchall()
        
        migrated_count = 0
        for v1_episode in v1_episodes:
            # Check if episode already exists
            existing = db.query(Episode).filter(Episode.id == v1_episode['id']).first()
            if existing:
                continue
            
            # Determine transcript status
            transcript_status = "pending"
            if v1_episode['transcribed']:
                transcript_status = "completed"
            
            episode = Episode(
                id=v1_episode['id'],
                podcast_id=v1_episode['podcast_id'],
                title=v1_episode['title'],
                audio_url=v1_episode['audio_url'],
                published_date=datetime.fromisoformat(v1_episode['publish_date']) if v1_episode['publish_date'] else None,
                duration=None,  # v1 didn't track duration
                description=v1_episode['description'],
                created_at=datetime.fromisoformat(v1_episode['created_at']) if v1_episode['created_at'] else datetime.now(),
                transcript_status=transcript_status,
                episode_url=v1_episode['episode_url'],
                guid=v1_episode['guid'],
                audio_file_path=v1_episode['audio_file_path']
            )
            
            db.add(episode)
            migrated_count += 1
        
        db.commit()
        print(f"Migrated {migrated_count} episodes")
    
    def migrate_transcripts(self, v1_conn, db: Session):
        """Migrate transcripts from v1 embedded text to v2 separate table"""
        print("Migrating transcripts...")
        
        cursor = v1_conn.cursor()
        cursor.execute("""
            SELECT id, transcript, transcribed 
            FROM episodes 
            WHERE transcript IS NOT NULL AND transcript != '' AND transcribed = 1
        """)
        v1_transcripts = cursor.fetchall()
        
        migrated_count = 0
        for v1_transcript in v1_transcripts:
            # Check if transcript already exists
            existing = db.query(Transcript).filter(Transcript.episode_id == v1_transcript['id']).first()
            if existing:
                continue
            
            word_count = len(v1_transcript['transcript'].split()) if v1_transcript['transcript'] else 0
            
            transcript = Transcript(
                episode_id=v1_transcript['id'],
                transcript_text=v1_transcript['transcript'],
                transcription_service="whisper-1",
                created_at=datetime.now(),  # We don't have original creation time
                word_count=word_count,
                processing_time_seconds=None  # Not tracked in v1
            )
            
            db.add(transcript)
            migrated_count += 1
        
        db.commit()
        print(f"Migrated {migrated_count} transcripts")
    
    def migrate_analysis_reports(self, v1_conn, db: Session):
        """Migrate processed summaries to analysis reports"""
        print("Migrating analysis reports...")
        
        cursor = v1_conn.cursor()
        cursor.execute("""
            SELECT e.id, e.processed_summary, p.custom_prompt, p.prompt_style
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE e.processed_summary IS NOT NULL AND e.processed_summary != ''
        """)
        v1_analyses = cursor.fetchall()
        
        migrated_count = 0
        for v1_analysis in v1_analyses:
            # Check if analysis already exists
            existing = db.query(AnalysisReport).filter(
                AnalysisReport.user_id == self.migration_user_id,
                AnalysisReport.episode_id == v1_analysis['id']
            ).first()
            if existing:
                continue
            
            # Create prompt based on v1 data
            prompt_used = v1_analysis['custom_prompt'] or f"Style: {v1_analysis['prompt_style']}"
            
            # Calculate reading time (rough estimate: 200 words per minute)
            word_count = len(v1_analysis['processed_summary'].split())
            reading_time = max(1, round(word_count / 200))
            
            analysis = AnalysisReport(
                user_id=self.migration_user_id,
                episode_id=v1_analysis['id'],
                prompt_used=prompt_used,
                analysis_result=v1_analysis['processed_summary'],
                key_quote=None,  # Will be extracted later
                reading_time_minutes=reading_time,
                created_at=datetime.now(),
                processing_time_seconds=None
            )
            
            db.add(analysis)
            migrated_count += 1
        
        db.commit()
        print(f"Migrated {migrated_count} analysis reports")
    
    def create_default_subscriptions(self, v1_conn, db: Session):
        """Create subscriptions for migration user to all active podcasts"""
        print("Creating default subscriptions...")
        
        # Get all active podcasts
        podcasts = db.query(Podcast).filter(Podcast.is_active == True).all()
        
        subscribed_count = 0
        for podcast in podcasts:
            # Check if subscription already exists
            existing = db.query(UserSubscription).filter(
                UserSubscription.user_id == self.migration_user_id,
                UserSubscription.podcast_id == podcast.id
            ).first()
            if existing:
                continue
            
            # Get custom prompt from v1
            v1_conn_cursor = v1_conn.cursor()
            v1_conn_cursor.execute("SELECT custom_prompt FROM podcasts WHERE id = ?", (podcast.id,))
            v1_podcast = v1_conn_cursor.fetchone()
            
            subscription = UserSubscription(
                user_id=self.migration_user_id,
                podcast_id=podcast.id,
                custom_prompt=v1_podcast['custom_prompt'] if v1_podcast else None,
                is_active=True
            )
            
            db.add(subscription)
            subscribed_count += 1
        
        db.commit()
        print(f"Created {subscribed_count} default subscriptions")
    
    def copy_transcript_files(self):
        """Copy transcript files from v1 to v2 location"""
        print("Copying transcript files...")
        
        if not os.path.exists(self.v1_transcripts_path):
            print(f"V1 transcripts path not found: {self.v1_transcripts_path}")
            return
        
        v2_transcripts_path = Path(settings.transcripts_storage_path)
        v2_transcripts_path.mkdir(parents=True, exist_ok=True)
        
        # Copy daily transcript folders
        v1_path = Path(self.v1_transcripts_path)
        copied_count = 0
        
        for daily_folder in v1_path.iterdir():
            if daily_folder.is_dir():
                v2_daily_folder = v2_transcripts_path / daily_folder.name
                if not v2_daily_folder.exists():
                    shutil.copytree(daily_folder, v2_daily_folder)
                    copied_count += len(list(v2_daily_folder.glob("*.txt")))
        
        print(f"Copied {copied_count} transcript files")
    
    def run_migration(self):
        """Run complete migration from v1 to v2"""
        print("Starting v1 to v2 migration...")
        print(f"V1 Database: {self.v1_db_path}")
        print(f"V1 Transcripts: {self.v1_transcripts_path}")
        
        # Create v2 database tables
        create_tables()
        
        # Connect to databases
        v1_conn = self.connect_v1_db()
        db = SessionLocal()
        
        try:
            # Create migration user
            self.create_migration_user(db)
            
            # Run migrations
            self.migrate_podcasts(v1_conn, db)
            self.migrate_episodes(v1_conn, db)
            self.migrate_transcripts(v1_conn, db)
            self.migrate_analysis_reports(v1_conn, db)
            self.create_default_subscriptions(v1_conn, db)
            
            # Copy files
            self.copy_transcript_files()
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.rollback()
            raise
        finally:
            v1_conn.close()
            db.close()


def main():
    """Run migration script"""
    v1_db_path = os.path.abspath(settings.v1_database_path)
    v1_transcripts_path = os.path.abspath(settings.v1_transcripts_path)
    
    print("Podcast Analysis Application - V1 to V2 Migration")
    print("=" * 60)
    
    migration = V1ToV2Migration(v1_db_path, v1_transcripts_path)
    migration.run_migration()


if __name__ == "__main__":
    main()