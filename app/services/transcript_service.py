"""
Transcript service for audio transcription with smart reuse
"""
import os
import time
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
import requests
import openai
from sqlalchemy.orm import Session

from app.models import Episode, Transcript
from app.core.config import settings


class TranscriptService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.audio_storage_path = Path(settings.audio_storage_path)
        self.audio_storage_path.mkdir(parents=True, exist_ok=True)
    
    def get_transcript_by_episode_id(self, db: Session, episode_id: int) -> Optional[Transcript]:
        """Get transcript for episode"""
        return db.query(Transcript).filter(Transcript.episode_id == episode_id).first()
    
    def check_existing_transcript(self, db: Session, audio_url: str) -> Optional[Transcript]:
        """Check if transcript already exists for this audio URL (smart reuse)"""
        # Find episode with same audio URL that has a transcript
        episode_with_transcript = db.query(Episode).join(Transcript).filter(
            Episode.audio_url == audio_url,
            Episode.transcript_status == "completed"
        ).first()
        
        if episode_with_transcript:
            return episode_with_transcript.transcript
        
        return None
    
    def download_audio_file(self, audio_url: str, episode_id: int) -> Optional[str]:
        """Download audio file for transcription"""
        try:
            # Create episode-specific directory
            episode_dir = self.audio_storage_path / f"episode_{episode_id}"
            episode_dir.mkdir(exist_ok=True)
            
            # Download audio file
            headers = {
                'User-Agent': 'Podcast Analysis Application v2/2.0.0'
            }
            
            response = requests.get(audio_url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'audio/mpeg' in content_type or 'audio/mp3' in content_type:
                extension = '.mp3'
            elif 'audio/wav' in content_type:
                extension = '.wav'
            elif 'audio/mp4' in content_type or 'audio/m4a' in content_type:
                extension = '.m4a'
            else:
                extension = '.mp3'  # Default
            
            audio_file_path = episode_dir / f"audio{extension}"
            
            # Save audio file
            with open(audio_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return str(audio_file_path)
            
        except Exception as e:
            print(f"Failed to download audio: {str(e)}")
            return None
    
    def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file using OpenAI Whisper"""
        start_time = time.time()
        
        try:
            # Check file size (Whisper has 25MB limit)
            file_size = os.path.getsize(audio_file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB
                return {
                    "success": False,
                    "error": "Audio file too large for transcription (>25MB)",
                    "processing_time": time.time() - start_time
                }
            
            # Transcribe using OpenAI Whisper
            with open(audio_file_path, 'rb') as audio_file:
                transcript_response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            transcript_text = transcript_response
            processing_time = time.time() - start_time
            word_count = len(transcript_text.split())
            
            return {
                "success": True,
                "transcript_text": transcript_text,
                "word_count": word_count,
                "processing_time": processing_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def create_transcript(
        self, 
        db: Session, 
        episode_id: int, 
        transcript_text: str, 
        word_count: int, 
        processing_time: float
    ) -> Transcript:
        """Create transcript record"""
        transcript = Transcript(
            episode_id=episode_id,
            transcript_text=transcript_text,
            transcription_service="whisper-1",
            word_count=word_count,
            processing_time_seconds=processing_time
        )
        
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        return transcript
    
    def transcribe_episode(self, db: Session, episode_id: int) -> Dict[str, Any]:
        """
        Transcribe episode with smart reuse logic
        """
        # Get episode
        episode = db.query(Episode).filter(Episode.id == episode_id).first()
        if not episode:
            return {"success": False, "error": "Episode not found"}
        
        # Check if transcript already exists for this episode
        existing_transcript = self.get_transcript_by_episode_id(db, episode_id)
        if existing_transcript:
            return {
                "success": True, 
                "message": "Transcript already exists",
                "transcript_id": existing_transcript.id,
                "reused": False
            }
        
        # Check for existing transcript with same audio URL (smart reuse)
        reusable_transcript = self.check_existing_transcript(db, episode.audio_url)
        if reusable_transcript:
            # Create new transcript record for this episode (referencing same content)
            new_transcript = Transcript(
                episode_id=episode_id,
                transcript_text=reusable_transcript.transcript_text,
                transcription_service=reusable_transcript.transcription_service,
                word_count=reusable_transcript.word_count,
                processing_time_seconds=0  # No processing time for reused transcript
            )
            
            db.add(new_transcript)
            
            # Update episode status
            episode.transcript_status = "completed"
            
            db.commit()
            db.refresh(new_transcript)
            
            return {
                "success": True,
                "message": "Transcript reused from existing episode",
                "transcript_id": new_transcript.id,
                "reused": True
            }
        
        # Mark episode as processing
        episode.transcript_status = "processing"
        db.commit()
        
        try:
            # Download audio file
            audio_file_path = self.download_audio_file(episode.audio_url, episode_id)
            if not audio_file_path:
                episode.transcript_status = "failed"
                db.commit()
                return {"success": False, "error": "Failed to download audio file"}
            
            # Transcribe audio
            transcription_result = self.transcribe_audio_file(audio_file_path)
            
            if not transcription_result["success"]:
                episode.transcript_status = "failed"
                db.commit()
                return transcription_result
            
            # Create transcript record
            transcript = self.create_transcript(
                db=db,
                episode_id=episode_id,
                transcript_text=transcription_result["transcript_text"],
                word_count=transcription_result["word_count"],
                processing_time=transcription_result["processing_time"]
            )
            
            # Update episode status
            episode.transcript_status = "completed"
            episode.audio_file_path = audio_file_path
            db.commit()
            
            # Clean up audio file (optional)
            try:
                os.remove(audio_file_path)
            except:
                pass
            
            return {
                "success": True,
                "message": "Transcription completed successfully",
                "transcript_id": transcript.id,
                "word_count": transcript.word_count,
                "processing_time": transcript.processing_time_seconds,
                "reused": False
            }
            
        except Exception as e:
            episode.transcript_status = "failed"
            db.commit()
            return {"success": False, "error": str(e)}
    
    def get_transcription_stats(self, db: Session) -> Dict[str, Any]:
        """Get transcription statistics"""
        total_transcripts = db.query(Transcript).count()
        
        total_episodes = db.query(Episode).count()
        
        pending_episodes = db.query(Episode).filter(
            Episode.transcript_status == "pending"
        ).count()
        
        processing_episodes = db.query(Episode).filter(
            Episode.transcript_status == "processing"
        ).count()
        
        failed_episodes = db.query(Episode).filter(
            Episode.transcript_status == "failed"
        ).count()
        
        # Calculate total words and processing time
        transcript_stats = db.query(
            db.func.sum(Transcript.word_count).label('total_words'),
            db.func.sum(Transcript.processing_time_seconds).label('total_processing_time')
        ).first()
        
        return {
            "total_episodes": total_episodes,
            "total_transcripts": total_transcripts,
            "transcription_rate": (total_transcripts / total_episodes * 100) if total_episodes > 0 else 0,
            "pending_transcription": pending_episodes,
            "currently_processing": processing_episodes,
            "failed_transcription": failed_episodes,
            "total_words_transcribed": transcript_stats.total_words or 0,
            "total_processing_time_minutes": (transcript_stats.total_processing_time or 0) / 60
        }