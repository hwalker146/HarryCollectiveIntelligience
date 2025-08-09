"""
Google Drive Logger for RSS Intelligence System
Saves daily reports to Google Drive as markdown files
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Google Drive API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False
    logging.warning("Google API client not installed. Google Drive logging will be disabled.")

logger = logging.getLogger(__name__)

class GDriveLogger:
    """Logs daily reports to Google Drive"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, config):
        self.config = config
        self.drive_service = None
        self.folder_id = config.gdrive_settings.get('folder_id')
        self.folder_name = config.gdrive_settings.get('folder_name', 'RSS Intelligence Reports')
        self.credentials_file = config.gdrive_settings.get('credentials_file', 'credentials.json')
        self.token_file = config.gdrive_settings.get('token_file', 'token.json')
        
        if GDRIVE_AVAILABLE:
            try:
                self.drive_service = self._authenticate()
                if self.drive_service and not self.folder_id:
                    self.folder_id = self._ensure_folder_exists()
            except Exception as e:
                logger.warning(f"Google Drive authentication failed: {e}")
                self.drive_service = None
        else:
            logger.warning("Google Drive API not available - reports will be saved locally only")
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Google Drive credentials file not found: {self.credentials_file}")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)
    
    def _ensure_folder_exists(self) -> str:
        """Ensure the reports folder exists in Google Drive"""
        try:
            # Search for existing folder
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                logger.info(f"Using existing Google Drive folder: {self.folder_name} (ID: {folder_id})")
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': self.folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created new Google Drive folder: {self.folder_name} (ID: {folder_id})")
            return folder_id
            
        except Exception as e:
            logger.error(f"Failed to create/find Google Drive folder: {e}")
            return None
    
    async def save_daily_log(self, report: Dict[str, Any], articles: List) -> bool:
        """Save daily report to Google Drive"""
        if not GDRIVE_AVAILABLE or not self.drive_service:
            # Fallback to local storage
            return self._save_local_log(report, articles)
        
        try:
            # Generate markdown content
            from report_generator import ReportGenerator
            report_gen = ReportGenerator(self.config)
            markdown_content = report_gen.generate_markdown_report(report)
            
            # Create filename with date
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"Intelligence_Report_{date_str}.md"
            
            # Save to temporary file
            temp_file = Path(f"temp_{filename}")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            media = MediaFileUpload(
                str(temp_file),
                mimetype='text/markdown',
                resumable=True
            )
            
            # Check if file already exists for today
            existing_file_id = self._find_existing_file(filename)
            
            if existing_file_id:
                # Update existing file
                file = self.drive_service.files().update(
                    fileId=existing_file_id,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                logger.info(f"✅ Updated Google Drive report: {filename}")
            else:
                # Create new file
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                logger.info(f"✅ Created Google Drive report: {filename}")
            
            # Clean up temp file
            temp_file.unlink(missing_ok=True)
            
            # Also save locally as backup
            local_success = self._save_local_log(report, articles)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Google Drive: {e}")
            # Fallback to local storage
            return self._save_local_log(report, articles)
    
    def _find_existing_file(self, filename: str) -> str:
        """Find existing file with same name in the folder"""
        try:
            query = f"name='{filename}'"
            if self.folder_id:
                query += f" and parents in '{self.folder_id}'"
            query += " and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            items = results.get('files', [])
            return items[0]['id'] if items else None
            
        except Exception as e:
            logger.warning(f"Failed to check for existing file: {e}")
            return None
    
    def _save_local_log(self, report: Dict[str, Any], articles: List) -> bool:
        """Save report locally as fallback"""
        try:
            # Create local reports directory
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Generate markdown content
            from report_generator import ReportGenerator
            report_gen = ReportGenerator(self.config)
            markdown_content = report_gen.generate_markdown_report(report)
            
            # Save markdown file
            date_str = datetime.now().strftime('%Y-%m-%d')
            md_filename = reports_dir / f"Intelligence_Report_{date_str}.md"
            
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Save JSON data for potential reprocessing
            json_filename = reports_dir / f"Intelligence_Data_{date_str}.json"
            report_data = {
                'report': report,
                'articles': [article.to_dict() for article in articles]
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"✅ Saved local reports: {md_filename}, {json_filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save local log: {e}")
            return False
    
    def get_drive_folder_url(self) -> str:
        """Get the URL to the Google Drive folder"""
        if self.folder_id:
            return f"https://drive.google.com/drive/folders/{self.folder_id}"
        return "Google Drive folder not configured"
    
    def test_connection(self) -> bool:
        """Test Google Drive connection"""
        if not GDRIVE_AVAILABLE:
            logger.info("Google Drive API not available")
            return False
        
        if not self.drive_service:
            logger.info("Google Drive not authenticated")
            return False
        
        try:
            # Try to access the folder
            if self.folder_id:
                folder = self.drive_service.files().get(fileId=self.folder_id).execute()
                logger.info(f"✅ Google Drive connection successful: {folder.get('name')}")
                return True
            else:
                logger.info("Google Drive folder not configured")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google Drive connection failed: {e}")
            return False