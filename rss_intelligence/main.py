#!/usr/bin/env python3
"""
RSS Intelligence System
Main entry point for the daily RSS feed analysis and reporting system
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys

from config_manager import ConfigManager
from feed_processor import FeedProcessor  
from report_generator import ReportGenerator
from email_sender import EmailSender
from gdrive_logger import GDriveLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_intelligence.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RSSIntelligenceSystem:
    """Main orchestrator for RSS intelligence system"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.feed_processor = FeedProcessor(self.config)
        self.report_generator = ReportGenerator(self.config)
        self.email_sender = EmailSender(self.config)
        self.gdrive_logger = GDriveLogger(self.config)
        
    async def run_daily_analysis(self):
        """Run the complete daily analysis pipeline"""
        logger.info("🤖 Starting RSS Intelligence Daily Analysis")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Process all RSS feeds
            logger.info("📡 Step 1: Processing RSS feeds...")
            articles = await self.feed_processor.process_all_feeds()
            logger.info(f"✅ Processed {len(articles)} articles from {len(self.config.rss_feeds)} feeds")
            
            if not articles:
                logger.info("📧 No new articles found - sending status email")
                await self._send_no_articles_email()
                return
            
            # Step 2: Analyze articles with AI
            logger.info("🧠 Step 2: Analyzing articles with AI...")
            analyzed_articles = await self.feed_processor.analyze_articles(articles)
            logger.info(f"✅ Analyzed {len(analyzed_articles)} articles")
            
            # Step 3: Generate daily report
            logger.info("📄 Step 3: Generating daily report...")
            report = await self.report_generator.generate_report(analyzed_articles)
            logger.info("✅ Daily report generated")
            
            # Step 4: Send email report
            logger.info("📧 Step 4: Sending email report...")
            await self.email_sender.send_daily_report(report, analyzed_articles)
            logger.info("✅ Email report sent")
            
            # Step 5: Log to Google Drive
            logger.info("☁️ Step 5: Logging to Google Drive...")
            await self.gdrive_logger.save_daily_log(report, analyzed_articles)
            logger.info("✅ Google Drive log saved")
            
            # Summary
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds() / 60
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 DAILY ANALYSIS COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"   Total time: {total_time:.1f} minutes")
            logger.info(f"   Articles processed: {len(articles)}")
            logger.info(f"   Articles analyzed: {len(analyzed_articles)}")
            logger.info(f"   Report generated: ✅")
            logger.info(f"   Email sent: ✅")
            logger.info(f"   Google Drive logged: ✅")
            
        except Exception as e:
            logger.error(f"❌ Daily analysis failed: {e}")
            await self._send_error_email(str(e))
            raise
    
    async def _send_no_articles_email(self):
        """Send email when no articles are found"""
        await self.email_sender.send_status_email("No new articles found today")
    
    async def _send_error_email(self, error_message):
        """Send email when system fails"""
        await self.email_sender.send_error_email(error_message)

async def main():
    """Main entry point"""
    system = RSSIntelligenceSystem()
    await system.run_daily_analysis()

if __name__ == "__main__":
    asyncio.run(main())