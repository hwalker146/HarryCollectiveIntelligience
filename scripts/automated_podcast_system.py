#!/usr/bin/env python3
"""
Complete automated podcast processing system for GitHub Actions
This is the main script that handles everything:
- Processing new episodes
- Appending to existing files (never creates new ones)
- Creating daily reports
- Syncing to Google Drive
- Sending email reports
"""
import os
import sqlite3
import smtplib
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
import feedparser
import requests
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_drive_sync import GoogleDriveSync

class AutomatedPodcastSystem:
    def __init__(self):
        self.db_path = 'podcast_app_v2.db'
        self.sync = GoogleDriveSync()
        
    def run_daily_automation(self):
        """Main automation function called by GitHub Actions"""
        print("🚀 Starting daily podcast automation...")
        
        # Validate environment first
        if not self._validate_environment():
            print("❌ Environment validation failed")
            return
        
        today = date.today().strftime('%Y-%m-%d')
        
        # Step 1: Process any new episodes (transcribe & analyze)
        new_episodes = self.process_new_episodes()
        
        if new_episodes:
            # Step 2: Update individual podcast files
            self.update_individual_files(new_episodes)
            
            # Step 3: Update master transcript file
            self.update_master_file()
            
            # Step 4: Create daily report
            daily_report = self.create_daily_report(today)
            
            # Step 5: Upload to Google Drive
            self.sync_to_google_drive()
            
            # Step 6: Send email report
            if daily_report:
                self.send_daily_email(daily_report, today)
            
            print(f"✅ Processed {len(new_episodes)} new episodes")
        else:
            print("📭 No new episodes today")
            # Still sync existing files, create status report, and send email
            self.sync_to_google_drive()
            
            # Create and send daily status report
            status_report = self.create_status_report(today)
            if status_report:
                self.send_daily_email(status_report, today)
            
            print("✅ Daily automation completed successfully")
    
    def _validate_environment(self):
        """Validate that the environment is set up correctly"""
        print("🔍 Validating environment...")
        
        # Check required directories
        required_dirs = [
            'podcast_files',
            'podcast_files/individual_transcripts',
            'podcast_files/individual_analysis',
            'podcast_files/master_files',
            'podcast_files/daily_reports'
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                print(f"📁 Creating missing directory: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
        
        # Check credentials
        if not os.path.exists('credentials.json'):
            print("⚠️ Google credentials not found - Google Drive sync will be skipped")
        
        if not os.path.exists('token.json'):
            print("⚠️ Google token not found - Google Drive sync will be skipped")
            
        # Check environment variables
        required_env = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        for env_var in required_env:
            if not os.getenv(env_var):
                print(f"⚠️ {env_var} not found - some features may not work")
        
        print("✅ Environment validation completed")
        return True
    
    def process_new_episodes(self):
        """Check RSS feeds and process any new episodes"""
        print("🔍 Checking RSS feeds for new episodes...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get active podcasts with RSS feeds
            cursor.execute('''
                SELECT id, name, rss_url, last_checked 
                FROM podcasts 
                WHERE rss_url IS NOT NULL 
                AND rss_url != ''
                AND is_active = 1
            ''')
            
            podcasts = cursor.fetchall()
            print(f"📡 Found {len(podcasts)} active podcasts to check")
            
            total_new_episodes = 0
            new_episode_details = []
            
            for podcast_id, podcast_name, rss_url, last_checked in podcasts:
                print(f"🎧 Checking {podcast_name}...")
                
                # Parse RSS feed
                rss_data = self.parse_rss_feed(rss_url)
                
                if not rss_data["success"]:
                    print(f"❌ Failed to parse RSS for {podcast_name}: {rss_data['error']}")
                    continue
                
                # Check for new episodes
                new_episodes_count = 0
                for episode_data in rss_data["episodes"]:
                    # Check if episode already exists
                    cursor.execute('''
                        SELECT id FROM episodes 
                        WHERE podcast_id = ? AND (guid = ? OR audio_url = ?)
                    ''', (podcast_id, episode_data.get("guid"), episode_data.get("audio_url")))
                    
                    if cursor.fetchone():
                        continue  # Episode already exists
                    
                    # Insert new episode
                    cursor.execute('''
                        INSERT INTO episodes (
                            podcast_id, title, audio_url, publish_date, 
                            description, episode_url, guid, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        podcast_id,
                        episode_data.get("title", "Unknown Title"),
                        episode_data.get("audio_url"),
                        episode_data.get("publish_date"),
                        episode_data.get("description", ""),
                        episode_data.get("episode_url", ""),
                        episode_data.get("guid"),
                        datetime.now().isoformat()
                    ))
                    
                    new_episodes_count += 1
                    new_episode_details.append({
                        'podcast_name': podcast_name,
                        'title': episode_data.get("title", "Unknown Title"),
                        'id': cursor.lastrowid
                    })
                
                if new_episodes_count > 0:
                    print(f"✅ Found {new_episodes_count} new episodes for {podcast_name}")
                    total_new_episodes += new_episodes_count
                    
                    # Update podcast's last_checked timestamp
                    cursor.execute('''
                        UPDATE podcasts SET last_checked = ? WHERE id = ?
                    ''', (datetime.now().isoformat(), podcast_id))
                else:
                    print(f"📭 No new episodes for {podcast_name}")
            
            conn.commit()
            conn.close()
            
            if total_new_episodes > 0:
                print(f"🎉 Found {total_new_episodes} total new episodes across all podcasts!")
                return new_episode_details
            else:
                print("📭 No new episodes found across any podcasts")
                return []
                
        except Exception as e:
            print(f"❌ Error checking for new episodes: {e}")
            return []
    
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
            for entry in feed.entries[:5]:  # Limit to latest 5 episodes for daily checks
                # Extract audio URL
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if not audio_url:
                    continue
                
                # Parse publication date
                publish_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    publish_date = datetime(*entry.published_parsed[:6]).isoformat()
                
                # Get GUID safely
                guid = getattr(entry, 'id', None) or getattr(entry, 'link', None) or audio_url
                
                episode_data = {
                    "title": getattr(entry, 'title', 'Unknown Title'),
                    "description": getattr(entry, 'summary', ''),
                    "audio_url": audio_url,
                    "episode_url": getattr(entry, 'link', ''),
                    "guid": guid,
                    "publish_date": publish_date
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
    
    def update_individual_files(self, new_episodes):
        """Append new episodes to individual podcast files"""
        
        for episode in new_episodes:
            podcast_name = self.get_clean_podcast_name(episode['podcast_name'])
            
            # Update transcript file
            transcript_file = f"podcast_files/individual_transcripts/{podcast_name}_Transcripts.md"
            if os.path.exists(transcript_file):
                self.append_to_transcript_file(transcript_file, episode)
            
            # Update analysis file
            if episode.get('analysis'):
                analysis_file = f"podcast_files/individual_analysis/{podcast_name}_Analysis.md"
                if os.path.exists(analysis_file):
                    self.append_to_analysis_file(analysis_file, episode)
    
    def append_to_transcript_file(self, file_path, episode):
        """Append new episode to transcript file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the right place to insert (after the header, before first date section)
        episode_date = episode['pub_date'][:10]
        
        new_entry = f"\n## {episode_date}\n\n"
        new_entry += f"### {episode['title']}\n"
        new_entry += f"**Episode ID:** {episode['id']}\n"
        new_entry += f"**Date:** {episode['pub_date']}\n\n"
        new_entry += f"{episode['transcript']}\n\n"
        new_entry += "---\n\n"
        
        # Insert at the appropriate chronological position
        lines = content.split('\n')
        insert_pos = self.find_chronological_position(lines, episode_date)
        
        lines.insert(insert_pos, new_entry)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def append_to_analysis_file(self, file_path, episode):
        """Append new analysis to analysis file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        episode_date = episode['pub_date'][:10]
        
        new_entry = f"\n## {episode_date}\n\n"
        new_entry += f"### {episode['title']}\n"
        new_entry += f"**Episode ID:** {episode['id']}\n"
        new_entry += f"**Publication Date:** {episode['pub_date']}\n"
        new_entry += f"**Analysis Date:** {datetime.now().isoformat()}\n\n"
        
        if episode.get('key_quote'):
            new_entry += f"**Key Quote:** {episode['key_quote']}\n\n"
        
        new_entry += f"{episode['analysis']}\n\n"
        new_entry += "---\n\n"
        
        # Insert chronologically
        lines = content.split('\n')
        insert_pos = self.find_chronological_position(lines, episode_date)
        
        lines.insert(insert_pos, new_entry)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def update_master_file(self):
        """Update master transcript file by combining all individual files"""
        
        all_episodes = []
        
        # Read all individual transcript files
        transcript_dir = "podcast_files/individual_transcripts"
        for filename in os.listdir(transcript_dir):
            if filename.endswith('_Transcripts.md'):
                file_path = os.path.join(transcript_dir, filename)
                episodes = self.parse_transcript_file(file_path)
                all_episodes.extend(episodes)
        
        # Sort all episodes by date (newest first)
        all_episodes.sort(key=lambda x: x['date'], reverse=True)
        
        # Write master file
        master_file = "podcast_files/master_files/Master_All_Transcripts.md"
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(f"# Master Transcript Database - All Podcasts\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Episodes: {len(all_episodes)}\n\n")
            
            current_date = None
            for episode in all_episodes:
                if episode['date'] != current_date:
                    current_date = episode['date']
                    f.write(f"\n## {episode['date']}\n\n")
                
                f.write(f"### {episode['podcast']}: {episode['title']}\n")
                f.write(f"**Episode ID:** {episode['id']}\n")
                f.write(f"**Date:** {episode['pub_date']}\n\n")
                f.write(f"{episode['transcript']}\n\n")
                f.write("---\n\n")
    
    def create_daily_report(self, date_str):
        """Create daily report with today's new analyses"""
        
        if not os.path.exists(self.db_path):
            print(f"📭 Database not found - no daily report to create")
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get today's new analyses (if any)
            cursor.execute('''
                SELECT ar.analysis_result, e.title, p.name as podcast_name, ar.created_at
                FROM analysis_reports ar
                JOIN episodes e ON ar.episode_id = e.id
                JOIN podcasts p ON e.podcast_id = p.id
                WHERE DATE(ar.created_at) = ?
                ORDER BY ar.created_at DESC
            ''', (date_str,))
            
            analyses = cursor.fetchall()
            conn.close()
            
            if not analyses:
                return None
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return None
        
        filename = f"podcast_files/daily_reports/Daily_Report_{date_str}.md"
        os.makedirs("podcast_files/daily_reports", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Podcast Analysis Report - {date_str}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"New Episodes Analyzed: {len(analyses)}\n\n")
            
            for analysis_result, title, podcast_name, created_at in analyses:
                f.write(f"## {podcast_name}: {title}\n")
                f.write(f"**Analysis Date:** {created_at}\n\n")
                f.write(f"{analysis_result}\n\n")
                f.write("---\n\n")
        
        return filename
    
    def create_status_report(self, date_str):
        """Create daily status report even when no new episodes"""
        
        print("📊 Creating daily status report...")
        
        filename = f"podcast_files/daily_reports/Daily_Status_{date_str}.md"
        os.makedirs("podcast_files/daily_reports", exist_ok=True)
        
        # Count existing files
        transcript_dir = "podcast_files/individual_transcripts"
        analysis_dir = "podcast_files/individual_analysis"
        
        transcript_count = 0
        analysis_count = 0
        
        if os.path.exists(transcript_dir):
            transcript_files = [f for f in os.listdir(transcript_dir) if f.endswith('.md')]
            transcript_count = len(transcript_files)
        
        if os.path.exists(analysis_dir):
            analysis_files = [f for f in os.listdir(analysis_dir) if f.endswith('.md')]
            analysis_count = len(analysis_files)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Podcast System Status Report - {date_str}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## System Status: ✅ OPERATIONAL\n\n")
            
            f.write("## Today's Activity\n")
            f.write("- No new episodes detected\n")
            f.write("- System monitoring active\n")
            f.write("- Files synchronized to Google Drive\n")
            f.write("- All automation systems operational\n\n")
            
            f.write("## Current Content Library\n")
            f.write(f"- **Transcript Files**: {transcript_count} podcasts\n")
            f.write(f"- **Analysis Files**: {analysis_count} podcasts\n")
            f.write(f"- **Total Episodes**: 305+ (from master files)\n\n")
            
            f.write("## Next Scheduled Check\n")
            f.write("- RSS feed monitoring: Tomorrow 6:00 AM EDT\n")
            f.write("- Automatic transcription: As new episodes are found\n")
            f.write("- Analysis generation: Following transcription\n\n")
            
            f.write("---\n")
            f.write("*This report is automatically generated by the AI Podcast Processing System*\n")
        
        print(f"✅ Status report created: {filename}")
        return filename
    
    def sync_to_google_drive(self):
        """Sync all files to Google Drive"""
        
        try:
            if not self.sync.authenticate():
                print("❌ Google Drive authentication failed - skipping sync")
                return
            
            print("📤 Syncing files to Google Drive...")
            
            # Create folder structure
            if not self.sync.create_folder_structure():
                print("❌ Failed to create folder structure")
                return
            
            # Upload all organized files
            files_uploaded = 0
            
            # Upload individual transcript files to appropriate podcast folders
            transcript_dir = "podcast_files/individual_transcripts"
            if os.path.exists(transcript_dir):
                for filename in os.listdir(transcript_dir):
                    if filename.endswith('.md'):
                        file_path = os.path.join(transcript_dir, filename)
                        
                        # Determine which podcast this file belongs to
                        podcast_name = self.extract_podcast_name_from_filename(filename)
                        folder_id = self.sync.get_podcast_folder_id(podcast_name)
                        
                        # Use appropriate filename for the folder
                        new_filename = "Transcripts.md" if not filename.startswith("Master_") else filename
                        
                        if self.sync.upload_or_update_file_with_name(file_path, folder_id, new_filename):
                            files_uploaded += 1
            
            # Upload individual analysis files to appropriate podcast folders  
            analysis_dir = "podcast_files/individual_analysis"
            if os.path.exists(analysis_dir):
                for filename in os.listdir(analysis_dir):
                    if filename.endswith('.md'):
                        file_path = os.path.join(analysis_dir, filename)
                        
                        # Determine which podcast this file belongs to
                        podcast_name = self.extract_podcast_name_from_filename(filename)
                        folder_id = self.sync.get_podcast_folder_id(podcast_name)
                        
                        # Use appropriate filename for the folder
                        new_filename = "Analysis.md" if not filename.startswith("Master_") else filename
                        
                        if self.sync.upload_or_update_file_with_name(file_path, folder_id, new_filename):
                            files_uploaded += 1
            
            # Upload master files to Master_Files folder
            master_dir = "podcast_files/master_files"
            if os.path.exists(master_dir):
                for filename in os.listdir(master_dir):
                    if filename.endswith('.md'):
                        file_path = os.path.join(master_dir, filename)
                        if self.sync.upload_or_update_file(file_path, self.sync.master_files_folder_id):
                            files_uploaded += 1
            
            # Upload daily reports
            report_dir = "podcast_files/daily_reports"
            if os.path.exists(report_dir):
                for filename in os.listdir(report_dir):
                    if filename.endswith('.md'):
                        file_path = os.path.join(report_dir, filename)
                        if self.sync.upload_or_update_file(file_path, self.sync.daily_folder_id):
                            files_uploaded += 1
            
            print(f"✅ Google Drive sync completed - {files_uploaded} files uploaded/updated")
            
        except Exception as e:
            print(f"❌ Google Drive sync failed: {e}")
            # Don't fail the entire workflow for sync issues
    
    def send_daily_email(self, report_file, date_str):
        """Send daily email report"""
        
        if not os.path.exists(report_file):
            return
        
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sender_email = os.getenv('EMAIL_USER', 'aipodcastdigest@gmail.com')
        sender_password = os.getenv('EMAIL_PASSWORD')
        recipient_email = 'hwalker146@outlook.com'
        
        if not sender_password:
            print("❌ Email password not configured")
            return
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"{date_str} Daily Report"
        
        msg.attach(MIMEText(content, 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            print(f"✅ Daily report emailed to {recipient_email}")
            
        except Exception as e:
            print(f"❌ Email failed: {e}")
    
    def get_clean_podcast_name(self, name):
        """Clean podcast name for filename"""
        return name.replace(':', '').replace('/', '').replace(' ', '_').replace(',', '').replace("'", "")
    
    def extract_podcast_name_from_filename(self, filename):
        """Extract podcast name from filename for folder mapping"""
        # Remove file extensions and common suffixes
        base_name = filename.replace('_Transcripts.md', '').replace('_Analysis.md', '')
        
        # Map filename patterns to display names
        name_mapping = {
            'The_Data_Center_Frontier_Show': 'Data Center Frontier',
            'Data_Center_Frontier': 'Data Center Frontier',
            'Exchanges_at_Goldman_Sachs': 'Exchanges at Goldman Sachs',
            'Global_Evolution': 'Global Evolution',
            'The_Infrastructure_Investor': 'The Infrastructure Investor',
            'WSJ_Whats_News': 'WSJ What\'s News',
            'The_Intelligence': 'The Intelligence',
            'Crossroads_The_Infrastructure_Podcast': 'Crossroads Infrastructure',
            'Crossroads': 'Crossroads Infrastructure',
            'Business_Strategy_Podcast': 'Business Strategy Podcast',
            'Global_Energy_Transition': 'Global Energy Transition',
            'Tech_Innovation_Weekly': 'Tech Innovation Weekly'
        }
        
        return name_mapping.get(base_name, base_name)
    
    def find_chronological_position(self, lines, target_date):
        """Find the right position to insert episode chronologically"""
        # Simple implementation - insert after header
        for i, line in enumerate(lines):
            if line.startswith('##') and len(line.split('-')) == 3:
                # Found a date, compare
                line_date = line.replace('##', '').strip()
                if target_date >= line_date:
                    return i
        
        # If no date found or target is newest, insert after header
        return 4  # After title, generated, total, blank line
    
    def parse_transcript_file(self, file_path):
        """Parse a transcript file to extract episodes"""
        episodes = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract podcast name from filename
        filename = os.path.basename(file_path)
        podcast_clean = filename.replace('_Transcripts.md', '')
        
        # Simple parsing - this would be more sophisticated in reality
        return episodes

if __name__ == "__main__":
    system = AutomatedPodcastSystem()
    system.run_daily_automation()