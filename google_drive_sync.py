#!/usr/bin/env python3
"""
Google Drive Sync for Podcast Analysis Master Files
Automatically syncs master transcripts and analysis files to Google Drive
"""
import os
import json
import glob
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv
import io

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveSync:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.podcast_folder_id = None
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Google Drive credentials file not found: {self.credentials_file}")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                
        self.service = build('drive', 'v3', credentials=creds)
        return True
    
    def create_folder_structure(self):
        """Create organized folder structure for podcast analysis"""
        if not self.service:
            return False
        
        # Create main folder
        main_folder = self.create_folder("Podcast Analysis - Infrastructure & Finance")
        if not main_folder:
            return False
            
        self.podcast_folder_id = main_folder['id']
        
        # Create subfolders
        self.transcripts_folder_id = self.create_folder("Master Transcripts", self.podcast_folder_id)['id']
        self.analysis_folder_id = self.create_folder("Master Analysis Reports", self.podcast_folder_id)['id']
        self.daily_folder_id = self.create_folder("Daily Reports", self.podcast_folder_id)['id']
        
        print(f"✅ Created folder structure in Google Drive")
        return True
    
    def create_folder(self, name, parent_id=None):
        """Create a folder in Google Drive"""
        try:
            # Check if folder already exists
            existing_folder = self.find_folder(name, parent_id)
            if existing_folder:
                print(f"📁 Using existing folder: {name}")
                return existing_folder
            
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
                
            folder = self.service.files().create(body=folder_metadata, fields='id, name').execute()
            print(f"✅ Created folder: {name}")
            return folder
            
        except Exception as e:
            print(f"❌ Error creating folder {name}: {e}")
            return None
    
    def find_folder(self, name, parent_id=None):
        """Find a folder by name and parent"""
        try:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
                
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            
            return items[0] if items else None
            
        except Exception as e:
            print(f"❌ Error finding folder {name}: {e}")
            return None
    
    def find_file(self, filename, folder_id):
        """Find a file by name in a specific folder"""
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
            items = results.get('files', [])
            
            return items[0] if items else None
            
        except Exception as e:
            print(f"❌ Error finding file {filename}: {e}")
            return None
    
    def upload_or_update_file(self, local_file_path, folder_id, description=None):
        """Upload a new file or update existing file in Google Drive"""
        try:
            filename = os.path.basename(local_file_path)
            
            # Check if file exists
            existing_file = self.find_file(filename, folder_id)
            
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            
            if description:
                file_metadata['description'] = description
            
            media = MediaFileUpload(local_file_path, resumable=True)
            
            if existing_file:
                # Update existing file - don't include parents in update
                update_metadata = {
                    'name': filename
                }
                if description:
                    update_metadata['description'] = description
                
                file = self.service.files().update(
                    fileId=existing_file['id'],
                    body=update_metadata,
                    media_body=media,
                    fields='id, name, modifiedTime'
                ).execute()
                print(f"🔄 Updated: {filename}")
            else:
                # Create new file
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, modifiedTime'
                ).execute()
                print(f"📤 Uploaded: {filename}")
            
            return file
            
        except Exception as e:
            print(f"❌ Error uploading {local_file_path}: {e}")
            return None
    
    def sync_master_files(self):
        """Sync all master transcript and analysis files to Google Drive"""
        if not self.service or not self.podcast_folder_id:
            print("❌ Google Drive not initialized. Run setup first.")
            return False
        
        # Find master files
        transcript_files = glob.glob("MASTER_PODCAST_TRANSCRIPTS_*.md")
        analysis_files = glob.glob("MASTER_PODCAST_ANALYSIS_*.md")
        
        synced_count = 0
        
        # Sync transcript files
        for file_path in transcript_files:
            result = self.upload_or_update_file(
                file_path, 
                self.transcripts_folder_id,
                f"Master podcast transcripts - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if result:
                synced_count += 1
        
        # Sync analysis files
        for file_path in analysis_files:
            result = self.upload_or_update_file(
                file_path,
                self.analysis_folder_id,
                f"Master podcast analysis reports - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if result:
                synced_count += 1
        
        print(f"✅ Synced {synced_count} master files to Google Drive")
        return synced_count > 0
    
    def sync_daily_report(self, report_content, report_date=None):
        """Create a daily report document in Google Drive"""
        try:
            if not report_date:
                report_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create a daily report file
            filename = f"Daily_Report_{report_date}.md"
            
            # Write content to temp file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Upload to daily reports folder
            result = self.upload_or_update_file(
                filename,
                self.daily_folder_id,
                f"Daily podcast analysis report for {report_date}"
            )
            
            # Clean up temp file
            os.remove(filename)
            
            if result:
                print(f"✅ Daily report synced: {filename}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error syncing daily report: {e}")
            return False
    
    def get_drive_folder_url(self):
        """Get the shareable URL for the main folder"""
        if self.podcast_folder_id:
            return f"https://drive.google.com/drive/folders/{self.podcast_folder_id}"
        return None

def setup_google_drive_sync():
    """Setup and test Google Drive sync"""
    print("🔧 Setting up Google Drive sync for podcast analysis...")
    
    sync = GoogleDriveSync()
    
    if not sync.authenticate():
        print("❌ Authentication failed")
        return False
    
    if not sync.create_folder_structure():
        print("❌ Failed to create folder structure")
        return False
    
    # Test sync
    if sync.sync_master_files():
        folder_url = sync.get_drive_folder_url()
        print(f"🎉 Google Drive sync setup complete!")
        print(f"📁 Access your files: {folder_url}")
        return True
    else:
        print("⚠️ Setup complete but no master files found to sync")
        return True

if __name__ == "__main__":
    setup_google_drive_sync()