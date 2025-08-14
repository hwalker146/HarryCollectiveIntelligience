#!/usr/bin/env python3
"""
Enhanced GitHub-based automated podcast system with Google Drive sync
- Appends to master files instead of individual files
- Includes WSJ and Ezra Klein specialized prompts
- Date range checking and gap filling
- Syncs all files to Google Drive for backup and sharing
"""
import os
import sqlite3
import smtplib
import feedparser
import requests
import tempfile
import subprocess
import json
import openai
import anthropic
import re
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any

# Import existing enhanced automation
from enhanced_automation import EnhancedPodcastSystem

# Import Google Drive sync
try:
    from google_drive_sync import GoogleDriveSync
    GDRIVE_AVAILABLE = True
except ImportError:
    print("⚠️  Google Drive sync not available - continuing without it")
    GDRIVE_AVAILABLE = False

class EnhancedPodcastSystemWithGDrive(EnhancedPodcastSystem):
    def __init__(self):
        super().__init__()
        
        # Initialize Google Drive sync
        self.gdrive_sync = None
        if GDRIVE_AVAILABLE:
            try:
                self.gdrive_sync = GoogleDriveSync()
                print("📁 Google Drive sync initialized")
            except Exception as e:
                print(f"⚠️  Google Drive sync initialization failed: {e}")
    
    def run_daily_automation(self):
        """Main automation function with Google Drive sync"""
        print("🚀 Starting enhanced podcast automation with Google Drive sync...")
        
        today = date.today().strftime('%Y-%m-%d')
        
        # Step 1: Check RSS feeds for new episodes
        new_episodes = self.check_rss_for_new_episodes()
        
        if new_episodes:
            print(f"🎉 Found {len(new_episodes)} new episodes")
            
            # Step 2: Process new episodes (transcribe & analyze)
            processed_episodes = self.process_new_episodes(new_episodes)
            
            # Step 3: Append to master files
            self.append_to_master_files(processed_episodes)
            
            # Step 4: Create daily report
            report_path = self.create_daily_report(today, processed_episodes)
            
            # Step 5: Sync to Google Drive
            self.sync_to_google_drive(processed_episodes)
            
            # Step 6: Send email
            self.send_email_report(report_path, today, processed_episodes)
            
            print(f"✅ Processed {len(processed_episodes)} episodes")
        else:
            print("📭 No new episodes found")
            
            # Still create and send status report
            status_report = self.create_status_report(today)
            self.send_email_report(status_report, today, [])
        
        print("🎉 Daily automation complete!")
    
    def sync_to_google_drive(self, processed_episodes):
        """Sync updated master files and daily reports to Google Drive"""
        if not self.gdrive_sync:
            print("⚠️  Google Drive sync not available - skipping")
            return
        
        try:
            print("📁 Syncing to Google Drive...")
            
            # Authenticate with Google Drive
            if not self.gdrive_sync.authenticate():
                print("❌ Google Drive authentication failed")
                return
            
            # Create folder structure if needed
            if not hasattr(self.gdrive_sync, 'podcast_folder_id') or not self.gdrive_sync.podcast_folder_id:
                if not self.gdrive_sync.create_folder_structure():
                    print("❌ Failed to create Google Drive folder structure")
                    return
            
            # Sync master transcript files
            synced_count = 0
            
            # Get list of all master files
            master_files = list(self.master_dir.glob("*.md"))
            
            for master_file in master_files:
                try:
                    # Upload to Master Files folder
                    result = self.gdrive_sync.upload_or_update_file(
                        str(master_file),
                        self.gdrive_sync.master_files_folder_id,
                        f"Master podcast file - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    if result:
                        synced_count += 1
                        print(f"   ✅ Synced: {master_file.name}")
                except Exception as e:
                    print(f"   ❌ Failed to sync {master_file.name}: {e}")
            
            # Sync daily reports
            report_files = list(self.reports_dir.glob("*.md"))
            for report_file in report_files[-7:]:  # Only sync last 7 days
                try:
                    result = self.gdrive_sync.upload_or_update_file(
                        str(report_file),
                        self.gdrive_sync.daily_folder_id,
                        f"Daily podcast report - {report_file.stem}"
                    )
                    if result:
                        synced_count += 1
                        print(f"   ✅ Synced: {report_file.name}")
                except Exception as e:
                    print(f"   ❌ Failed to sync {report_file.name}: {e}")
            
            print(f"📁 Google Drive sync complete: {synced_count} files synced")
            
            # Provide folder URL
            folder_url = self.gdrive_sync.get_drive_folder_url()
            if folder_url:
                print(f"🔗 Access files: {folder_url}")
            
        except Exception as e:
            print(f"❌ Google Drive sync failed: {e}")
    
    def create_daily_report(self, date_str, processed_episodes):
        """Create daily report with Google Drive link"""
        filename = f"Daily_Report_{date_str}.md"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Daily Podcast Analysis Report - {date_str}\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"New Episodes Processed: {len(processed_episodes)}\\n\\n")
            
            # Add Google Drive link if available
            if self.gdrive_sync and hasattr(self.gdrive_sync, 'podcast_folder_id'):
                folder_url = self.gdrive_sync.get_drive_folder_url()
                if folder_url:
                    f.write(f"📁 **Google Drive Folder:** {folder_url}\\n\\n")
            
            if processed_episodes:
                f.write("## 🎯 Today's New Episodes\\n\\n")
                
                for episode in processed_episodes:
                    f.write(f"### {episode['podcast_name']}: {episode['title']}\\n")
                    f.write(f"**Episode ID:** {episode['episode_id']}\\n")
                    f.write(f"**Date:** {episode['date']}\\n")
                    f.write(f"**Master File:** {self.podcast_files.get(episode['podcast_name'], 'N/A')}\\n\\n")
                    
                    # Show analysis preview
                    analysis_preview = episode['analysis'][:500] + "..." if len(episode['analysis']) > 500 else episode['analysis']
                    f.write(f"**Analysis:**\\n{analysis_preview}\\n\\n")
                    f.write("---\\n\\n")
            else:
                f.write("## 📭 No New Episodes Today\\n\\n")
                f.write("All podcasts are up to date. System monitoring active.\\n\\n")
            
            f.write("---\\n")
            f.write("*Generated by Enhanced GitHub-Based Podcast Automation System with Google Drive Sync*\\n")
        
        return filepath

if __name__ == "__main__":
    system = EnhancedPodcastSystemWithGDrive()
    system.run_daily_automation()