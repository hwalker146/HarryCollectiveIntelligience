#!/usr/bin/env python3
"""
Enhanced Daily Automation Script for Podcast Processor v2
Complete daily workflow:
1. Check for new episodes
2. Transcribe new episodes
3. Add to master transcript file
4. Run analysis on new episodes
5. Add analysis to master analysis file
6. Upload to Google Drive
7. Send daily email with new analysis
"""
import os
import sys
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_parallel_processor import EnhancedParallelProcessor
from google_drive_integration import GoogleDriveSync
from email_service import EmailService

class EnhancedDailyAutomation:
    def __init__(self):
        self.processor = EnhancedParallelProcessor(max_workers=6)
        self.drive_sync = GoogleDriveSync()
        self.email_service = EmailService()
        self.target_podcasts = [3, 6, 7, 8]  # Infrastructure Investor, Crossroads, Deal Talks, Goldman Sachs
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def step1_check_new_episodes(self, days=1):
        """Step 1: Check for new episodes in the last N days"""
        print(f"🔍 Step 1: Checking for episodes from last {days} days...")
        
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT e.id, p.name, e.title, e.pub_date
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE e.podcast_id IN (3, 6, 7, 8)
            AND e.pub_date >= ?
            ORDER BY e.pub_date DESC
        """, (cutoff_date,))
        
        new_episodes = cursor.fetchall()
        conn.close()
        
        print(f"📅 Found {len(new_episodes)} new episodes:")
        for episode_id, podcast_name, title, pub_date in new_episodes:
            print(f"   {pub_date}: {podcast_name} - {title[:60]}...")
        
        return [ep[0] for ep in new_episodes]
    
    def step2_transcribe_new_episodes(self):
        """Step 2: Transcribe any episodes without transcripts"""
        print("🎧 Step 2: Transcribing episodes without transcripts...")
        
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title FROM episodes
            WHERE podcast_id IN (3, 6, 7, 8)
            AND (transcript IS NULL OR transcript = '')
            ORDER BY pub_date DESC
            LIMIT 20
        """)
        
        missing_episodes = cursor.fetchall()
        conn.close()
        
        if missing_episodes:
            print(f"📝 Processing {len(missing_episodes)} episodes...")
            episode_ids = [ep[0] for ep in missing_episodes]
            results = self.processor.parallel_transcribe_episodes(episode_ids)
            
            print(f"✅ Successfully transcribed: {len(results['success'])}")
            if results['failed']:
                print(f"❌ Failed to transcribe: {len(results['failed'])}")
            
            return results
        else:
            print("✅ All episodes already transcribed")
            return {"success": [], "failed": []}
    
    def step3_update_master_transcript_file(self):
        """Step 3: Update master transcript file with all episodes"""
        print("📄 Step 3: Updating master transcript file...")
        
        # Run the transcript document creator
        subprocess.run([sys.executable, "create_transcript_document.py"])
        
        # Find the latest transcript file
        transcript_files = list(Path(".").glob("complete_podcast_transcripts_*.md"))
        if transcript_files:
            latest_file = max(transcript_files, key=os.path.getctime)
            print(f"✅ Updated master transcript file: {latest_file}")
            return str(latest_file)
        
        return None
    
    def step4_analyze_new_episodes(self):
        """Step 4: Run analysis on episodes that need it"""
        print("🧠 Step 4: Running analysis on new episodes...")
        
        # Check for episodes with transcripts but no analysis
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM episodes
            WHERE podcast_id IN (3, 6, 7, 8)
            AND transcript IS NOT NULL 
            AND transcript != ''
            AND id NOT IN (SELECT episode_id FROM analysis WHERE episode_id IS NOT NULL)
        """)
        
        unanalyzed_count = cursor.fetchone()[0]
        conn.close()
        
        if unanalyzed_count > 0:
            print(f"📊 Found {unanalyzed_count} episodes needing analysis")
            subprocess.run([sys.executable, "fixed_analysis_processor.py"])
            return True
        else:
            print("✅ All episodes already analyzed")
            return False
    
    def step5_update_master_analysis_file(self):
        """Step 5: Update master analysis file"""
        print("📈 Step 5: Creating updated master analysis file...")
        
        report_path = self.processor.create_unified_report()
        if report_path:
            print(f"✅ Updated master analysis file: {report_path}")
            return report_path
        
        return None
    
    def step6_upload_to_google_drive(self, transcript_file, analysis_file):
        """Step 6: Upload files to Google Drive"""
        print("☁️ Step 6: Uploading to Google Drive...")
        
        if not self.drive_sync.authenticate():
            print("❌ Google Drive authentication failed - skipping upload")
            return False
        
        success = True
        
        # Upload daily transcripts
        uploaded_transcripts = self.drive_sync.upload_daily_transcripts()
        if uploaded_transcripts:
            print(f"📤 Uploaded {len(uploaded_transcripts)} new transcripts")
        
        # Upload master files
        if transcript_file:
            if self.drive_sync.upload_master_file(transcript_file):
                print("📤 Uploaded master transcript file")
            else:
                success = False
        
        if analysis_file:
            if self.drive_sync.upload_master_file(analysis_file):
                print("📤 Uploaded master analysis file")
            else:
                success = False
        
        return success
    
    def step7_send_daily_email(self, new_episodes_count=0):
        """Step 7: Send daily email with new analysis"""
        print("📧 Step 7: Preparing daily email...")
        
        # Get today's new analysis
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        # Get analysis from today
        cursor.execute("""
            SELECT a.analysis, e.title, p.name, e.pub_date
            FROM analysis a
            JOIN episodes e ON a.episode_id = e.id
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE DATE(a.created_at) = DATE('now')
            AND e.podcast_id IN (3, 6, 7, 8)
            ORDER BY e.pub_date DESC
        """, ())
        
        today_analysis = cursor.fetchall()
        conn.close()
        
        if not today_analysis and new_episodes_count == 0:
            print("📝 No new analysis today - sending status update")
            self.send_status_email()
            return True
        
        # Create email content
        email_content = self.create_daily_email_content(today_analysis)
        
        # Send email
        recipient = os.getenv("DAILY_EMAIL_RECIPIENT", "harris.m.walker@gmail.com")
        subject = f"Daily Podcast Analysis - {self.today}"
        
        success = self.email_service.send_html_email(
            to_email=recipient,
            subject=subject,
            html_content=email_content
        )
        
        if success:
            print(f"✅ Daily email sent to {recipient}")
        else:
            print("❌ Failed to send daily email")
        
        return success
    
    def create_daily_email_content(self, analysis_data):
        """Create HTML email content for daily digest"""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .episode {{ margin-bottom: 30px; padding: 15px; border-left: 4px solid #3498db; background-color: #f8f9fa; }}
                .episode-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
                .podcast-name {{ color: #7f8c8d; font-size: 14px; margin-bottom: 10px; }}
                .analysis {{ margin-top: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎧 Daily Podcast Analysis</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="content">
                <h2>📊 Today's Analysis ({len(analysis_data)} episodes)</h2>
        """
        
        if analysis_data:
            for analysis, title, podcast_name, pub_date in analysis_data:
                html_content += f"""
                <div class="episode">
                    <div class="episode-title">{title}</div>
                    <div class="podcast-name">{podcast_name} • {pub_date}</div>
                    <div class="analysis">{analysis[:500]}...</div>
                </div>
                """
        else:
            html_content += "<p>No new analysis generated today.</p>"
        
        html_content += f"""
            </div>
            
            <div class="footer">
                Generated by Podcast Analysis System v2<br>
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_status_email(self):
        """Send status email when no new content"""
        recipient = os.getenv("DAILY_EMAIL_RECIPIENT", "harris.m.walker@gmail.com")
        subject = f"Podcast Analysis Status - {self.today}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                <h2>🎧 Podcast Analysis Status</h2>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div style="padding: 20px;">
                <p>✅ Daily automation completed successfully</p>
                <p>📝 No new episodes or analysis today</p>
                <p>🔄 System is monitoring for new content</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_service.send_html_email(recipient, subject, html_content)
    
    def run_complete_workflow(self):
        """Run the complete daily workflow"""
        print("🚀 Starting Enhanced Daily Podcast Automation")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Check for new episodes
            new_episode_ids = self.step1_check_new_episodes()
            
            # Step 2: Transcribe new episodes
            transcription_results = self.step2_transcribe_new_episodes()
            
            # Step 3: Update master transcript file
            master_transcript_file = self.step3_update_master_transcript_file()
            
            # Step 4: Analyze new episodes
            analysis_performed = self.step4_analyze_new_episodes()
            
            # Step 5: Update master analysis file
            master_analysis_file = self.step5_update_master_analysis_file()
            
            # Step 6: Upload to Google Drive
            drive_success = self.step6_upload_to_google_drive(
                master_transcript_file, master_analysis_file
            )
            
            # Step 7: Send daily email
            email_success = self.step7_send_daily_email(len(new_episode_ids))
            
            # Summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("=" * 60)
            print("🎯 DAILY AUTOMATION SUMMARY")
            print(f"⏱️  Duration: {duration}")
            print(f"📅 New Episodes: {len(new_episode_ids)}")
            print(f"🎧 Transcriptions: {len(transcription_results['success'])} success, {len(transcription_results['failed'])} failed")
            print(f"🧠 Analysis: {'✅ Performed' if analysis_performed else '✅ Up to date'}")
            print(f"☁️  Google Drive: {'✅ Success' if drive_success else '❌ Failed'}")
            print(f"📧 Email: {'✅ Sent' if email_success else '❌ Failed'}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False

if __name__ == "__main__":
    automation = EnhancedDailyAutomation()
    success = automation.run_complete_workflow()
    
    if success:
        print("✅ Daily automation completed successfully")
        sys.exit(0)
    else:
        print("❌ Daily automation failed")
        sys.exit(1)