"""
Enhanced analysis service with key quote extraction and reading time calculation
"""
import re
import time
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from anthropic import Anthropic

from app.models import AnalysisReport, Episode, Transcript, User, KnowledgeBaseEntry
from app.core.config import settings


class AnalysisService:
    def __init__(self):
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        
    def extract_key_quote_and_reading_time(self, analysis_text: str) -> Tuple[Optional[str], int]:
        """
        Extract key quote from analysis and calculate reading time
        """
        # Calculate reading time (average 200 words per minute)
        word_count = len(analysis_text.split())
        reading_time = max(1, round(word_count / 200))
        
        # Try to extract a key quote from the analysis
        # Look for quotes in quotation marks
        quote_patterns = [
            r'"([^"]{50,200})"',  # Double quotes, 50-200 chars
            r"'([^']{50,200})'",  # Smart quotes
            r"'([^']{50,200})'",  # Single quotes
        ]
        
        key_quote = None
        for pattern in quote_patterns:
            matches = re.findall(pattern, analysis_text)
            if matches:
                # Take the longest quote
                key_quote = max(matches, key=len)
                break
        
        # If no quoted text found, extract the first compelling sentence
        if not key_quote:
            sentences = re.split(r'[.!?]+', analysis_text)
            for sentence in sentences:
                sentence = sentence.strip()
                # Look for sentences with key phrases
                if (len(sentence) > 50 and len(sentence) < 200 and 
                    any(phrase in sentence.lower() for phrase in 
                        ['key insight', 'important', 'significant', 'reveals', 'shows', 'demonstrates'])):
                    key_quote = sentence
                    break
        
        return key_quote, reading_time
    
    def generate_enhanced_analysis(
        self, 
        transcript: str, 
        prompt: str, 
        episode_title: str, 
        podcast_name: str
    ) -> Dict[str, Any]:
        """
        Generate analysis with enhanced features using Claude
        """
        start_time = time.time()
        
        # Enhanced prompt that includes key quote extraction
        enhanced_prompt = f"""
{prompt}

IMPORTANT: Your analysis should be comprehensive and insightful. As part of your response, please:
1. Include at least one compelling, quotable insight that captures the essence of the episode
2. Write in a clear, digestible style suitable for a knowledge base
3. Focus on actionable insights and key takeaways

Episode: {episode_title}
Podcast: {podcast_name}

Transcript:
{transcript}
"""
        
        try:
            # Call Claude API
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user", 
                        "content": enhanced_prompt
                    }
                ]
            )
            
            analysis_result = message.content[0].text
            processing_time = time.time() - start_time
            
            # Extract key quote and calculate reading time
            key_quote, reading_time = self.extract_key_quote_and_reading_time(analysis_result)
            
            return {
                "analysis_result": analysis_result,
                "key_quote": key_quote,
                "reading_time_minutes": reading_time,
                "processing_time_seconds": processing_time,
                "success": True
            }
            
        except Exception as e:
            return {
                "analysis_result": f"Analysis failed: {str(e)}",
                "key_quote": None,
                "reading_time_minutes": 1,
                "processing_time_seconds": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    def create_analysis_report(
        self,
        db: Session,
        user_id: int,
        episode_id: int,
        prompt: str,
        transcript_text: str,
        episode_title: str,
        podcast_name: str
    ) -> AnalysisReport:
        """
        Create a new analysis report with enhanced features
        """
        # Generate enhanced analysis
        result = self.generate_enhanced_analysis(
            transcript=transcript_text,
            prompt=prompt,
            episode_title=episode_title,
            podcast_name=podcast_name
        )
        
        # Create analysis report
        analysis_report = AnalysisReport(
            user_id=user_id,
            episode_id=episode_id,
            prompt_used=prompt,
            analysis_result=result["analysis_result"],
            key_quote=result["key_quote"],
            reading_time_minutes=result["reading_time_minutes"],
            processing_time_seconds=result["processing_time_seconds"]
        )
        
        db.add(analysis_report)
        db.commit()
        db.refresh(analysis_report)
        
        # Automatically create knowledge base entry
        self._create_knowledge_base_entry(db, analysis_report)
        
        return analysis_report
    
    def _create_knowledge_base_entry(self, db: Session, analysis_report: AnalysisReport):
        """
        Automatically create knowledge base entry from analysis report
        """
        # Get episode and podcast info
        episode = db.query(Episode).filter(Episode.id == analysis_report.episode_id).first()
        if not episode:
            return
        
        # Create knowledge base entry
        kb_entry = KnowledgeBaseEntry(
            user_id=analysis_report.user_id,
            analysis_report_id=analysis_report.id,
            podcast_category=None,  # User can categorize later
            entry_title=episode.title,
            key_insights=analysis_report.analysis_result[:500] + "..." if len(analysis_report.analysis_result) > 500 else analysis_report.analysis_result,
            personal_notes=None,  # User can add later
            tags=None,  # User can add later
            is_favorited=False
        )
        
        db.add(kb_entry)
        db.commit()
    
    def get_user_analysis_reports(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ):
        """
        Get analysis reports for a user
        """
        return db.query(AnalysisReport).filter(
            AnalysisReport.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_analysis_report_by_id(self, db: Session, report_id: int) -> Optional[AnalysisReport]:
        """
        Get specific analysis report by ID
        """
        return db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
    
    def update_personal_notes(
        self, 
        db: Session, 
        report_id: int, 
        user_id: int, 
        notes: str
    ) -> bool:
        """
        Update personal notes for an analysis report via knowledge base entry
        """
        # Find the knowledge base entry for this analysis report
        kb_entry = db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.analysis_report_id == report_id,
            KnowledgeBaseEntry.user_id == user_id
        ).first()
        
        if kb_entry:
            kb_entry.personal_notes = notes
            db.commit()
            return True
        
        return False