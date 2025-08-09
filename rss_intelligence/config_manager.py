"""
Configuration Manager for RSS Intelligence System
Handles loading and managing all configuration settings
"""
import os
import json
import yaml
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    """Manages all configuration for the RSS Intelligence System"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Load all configuration
        self.rss_feeds = self._load_rss_feeds()
        self.analysis_prompt = self._load_analysis_prompt()
        self.email_settings = self._load_email_settings()
        self.ai_settings = self._load_ai_settings()
        self.gdrive_settings = self._load_gdrive_settings()
        
        # Validate configuration
        self._validate_config()
    
    def _load_rss_feeds(self) -> Dict[str, str]:
        """Load RSS feed URLs from config file"""
        feeds_file = self.config_dir / "rss_feeds.json"
        
        if not feeds_file.exists():
            # Create default feeds file with provided list
            default_feeds = {
                "NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
                "NYT Energy and Environment": "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml",
                "NYT Economy": "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
                "NYT Technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
                "Infrastructure USA": "https://infrastructureusa.org/feed",
                "Renew Canada": "https://renewcanada.net/feed",
                "Infrastructurist": "https://infrastructurist.com/feed",
                "New Civil Engineer": "https://newcivilengineer.com/feed",
                "Roads Online Australia": "https://roadsonline.com.au/feed",
                "Economist Business": "https://www.economist.com/business/rss.xml",
                "Economist Britain": "https://www.economist.com/britain/rss.xml",
                "Economist Europe": "https://www.economist.com/europe/rss.xml",
                "Economist Asia": "https://www.economist.com/asia/rss.xml",
                "Economist Middle East Africa": "https://www.economist.com/middle-east-and-africa/rss.xml",
                "Economist Americas": "https://www.economist.com/the-americas/rss.xml",
                "Economist China": "https://www.economist.com/china/rss.xml",
                "Data Center News Asia": "https://datacenternews.asia/feed",
                "Data Center Post": "https://datacenterpost.com/feed",
                "WSJ Markets": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
                "WSJ Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
                "WSJ Technology": "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
            }
            
            with open(feeds_file, 'w') as f:
                json.dump(default_feeds, f, indent=2)
        
        with open(feeds_file, 'r') as f:
            return json.load(f)
    
    def _load_analysis_prompt(self) -> str:
        """Load AI analysis prompt from config file"""
        prompt_file = self.config_dir / "analysis_prompt.txt"
        
        if not prompt_file.exists():
            # Create default analysis prompt
            default_prompt = """You are an expert financial and infrastructure analyst. 

Analyze the following article and provide a concise summary focusing on:

1. **Key Investment Insights**: What investment opportunities, risks, or market signals does this reveal?
2. **Infrastructure Implications**: How does this relate to infrastructure development, policy, or funding?
3. **Market Trends**: What broader economic or industry trends does this indicate?
4. **Action Items**: What should investors or industry professionals pay attention to?

Keep your analysis:
- Under 200 words
- Focused on actionable insights
- Professional and analytical in tone
- Highlighting the most important 2-3 takeaways

Article to analyze:
{article_content}"""
            
            with open(prompt_file, 'w') as f:
                f.write(default_prompt)
        
        with open(prompt_file, 'r') as f:
            return f.read().strip()
    
    def _load_email_settings(self) -> Dict:
        """Load email configuration"""
        return {
            'from_email': os.getenv('EMAIL_FROM'),
            'from_password': os.getenv('EMAIL_PASSWORD'),
            'to_email': os.getenv('EMAIL_TO', 'hwalker146@outlook.com'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587'))
        }
    
    def _load_ai_settings(self) -> Dict:
        """Load AI API configuration"""
        return {
            'provider': os.getenv('AI_PROVIDER', 'claude'),  # 'claude' or 'openai'
            'claude_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('AI_MODEL', 'claude-3-5-sonnet-20241022')  # or 'gpt-4o'
        }
    
    def _load_gdrive_settings(self) -> Dict:
        """Load Google Drive configuration"""
        return {
            'credentials_file': os.getenv('GDRIVE_CREDENTIALS', 'credentials.json'),
            'token_file': os.getenv('GDRIVE_TOKEN', 'token.json'),
            'folder_id': os.getenv('GDRIVE_FOLDER_ID'),
            'folder_name': os.getenv('GDRIVE_FOLDER_NAME', 'RSS Intelligence Reports')
        }
    
    def _validate_config(self):
        """Validate that all required configuration is present"""
        errors = []
        
        # Check email settings
        if not self.email_settings['from_email']:
            errors.append("EMAIL_FROM environment variable not set")
        if not self.email_settings['from_password']:
            errors.append("EMAIL_PASSWORD environment variable not set")
        
        # Check AI settings
        if self.ai_settings['provider'] == 'claude' and not self.ai_settings['claude_api_key']:
            errors.append("ANTHROPIC_API_KEY environment variable not set")
        if self.ai_settings['provider'] == 'openai' and not self.ai_settings['openai_api_key']:
            errors.append("OPENAI_API_KEY environment variable not set")
        
        # Check RSS feeds
        if not self.rss_feeds:
            errors.append("No RSS feeds configured")
        
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))
    
    def add_rss_feed(self, name: str, url: str):
        """Add a new RSS feed"""
        self.rss_feeds[name] = url
        feeds_file = self.config_dir / "rss_feeds.json"
        with open(feeds_file, 'w') as f:
            json.dump(self.rss_feeds, f, indent=2)
    
    def remove_rss_feed(self, name: str):
        """Remove an RSS feed"""
        if name in self.rss_feeds:
            del self.rss_feeds[name]
            feeds_file = self.config_dir / "rss_feeds.json"
            with open(feeds_file, 'w') as f:
                json.dump(self.rss_feeds, f, indent=2)
    
    def update_analysis_prompt(self, new_prompt: str):
        """Update the analysis prompt"""
        self.analysis_prompt = new_prompt
        prompt_file = self.config_dir / "analysis_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(new_prompt)
    
    def get_config_summary(self) -> str:
        """Get a summary of current configuration"""
        return f"""
RSS Intelligence System Configuration:
=====================================
RSS Feeds: {len(self.rss_feeds)} configured
AI Provider: {self.ai_settings['provider']}
AI Model: {self.ai_settings['model']}
Email: {self.email_settings['from_email']} → {self.email_settings['to_email']}
Google Drive: {'Configured' if self.gdrive_settings['folder_id'] else 'Not configured'}
"""