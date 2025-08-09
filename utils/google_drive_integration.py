#!/usr/bin/env python3
"""
Google Drive Integration for Podcast Processor v2
Automatically uploads transcripts and analysis to Google Drive
"""
import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveSync:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.folder_id = None
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Google Drive credentials file not found: {self.credentials_file}")
                    print("Please download credentials.json from Google Cloud Console")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                
        self.service = build('drive', 'v3', credentials=creds)
        return True
    
    def create_folder_structure(self):
        """Create folder structure in Google Drive"""
        if not self.service:
            return False
            
        # Create main podcast folder
        main_folder = self.create_folder("Podcast Transcripts & Analysis")
        if not main_folder:
            return False
            
        self.folder_id = main_folder['id']
        
        # Create subfolders
        self.create_folder("Raw Transcripts", parent_id=self.folder_id)
        self.create_folder("Daily Analysis", parent_id=self.folder_id)
        self.create_folder("Master Files", parent_id=self.folder_id)
        
        return True
    
    def create_folder(self, name, parent_id=None):
        """Create a folder in Google Drive"""
        try:
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
                
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            print(f"✅ Created folder: {name}")
            return folder
            
        except Exception as e:
            print(f"❌ Error creating folder {name}: {e}")
            return None
    
    def upload_file(self, file_path, folder_name="Raw Transcripts"):
        """Upload a file to Google Drive"""
        if not self.service or not os.path.exists(file_path):
            return None
            
        try:
            # Get folder ID for the specified folder
            target_folder_id = self.get_folder_id(folder_name)
            if not target_folder_id:
                target_folder_id = self.folder_id  # Default to main folder
            
            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [target_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            print(f"✅ Uploaded {file_name} to Google Drive")
            return file.get('id')
            
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return None
    
    def get_folder_id(self, folder_name):
        """Get folder ID by name"""
        try:
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
            
        except Exception as e:
            print(f"❌ Error finding folder {folder_name}: {e}")
            return None
    
    def upload_daily_transcripts(self, transcript_dir="data/transcripts"):
        """Upload new transcripts from today"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_path = os.path.join(transcript_dir, today)
        
        if not os.path.exists(today_path):
            print(f"📁 No transcripts found for {today}")
            return []
        
        uploaded_files = []
        for filename in os.listdir(today_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(today_path, filename)
                file_id = self.upload_file(file_path, "Raw Transcripts")
                if file_id:
                    uploaded_files.append(filename)
        
        return uploaded_files
    
    def upload_master_file(self, file_path):
        """Upload master transcript/analysis file"""
        return self.upload_file(file_path, "Master Files")
    
    def upload_daily_analysis(self, file_path):
        """Upload daily analysis file"""
        return self.upload_file(file_path, "Daily Analysis")

def setup_google_drive():
    """Setup Google Drive integration"""
    print("🔧 Setting up Google Drive integration...")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing")
    print("3. Enable Google Drive API")
    print("4. Create credentials (Desktop application)")
    print("5. Download credentials.json to this directory")
    print("6. Run this script again to authenticate")

if __name__ == "__main__":
    # Test the Google Drive integration
    drive_sync = GoogleDriveSync()
    
    if drive_sync.authenticate():
        print("✅ Google Drive authentication successful")
        
        if drive_sync.create_folder_structure():
            print("✅ Folder structure created")
            
            # Test upload
            uploaded = drive_sync.upload_daily_transcripts()
            if uploaded:
                print(f"✅ Uploaded {len(uploaded)} files")
            else:
                print("📝 No new files to upload")
        else:
            print("❌ Failed to create folder structure")
    else:
        print("❌ Google Drive authentication failed")
        setup_google_drive()