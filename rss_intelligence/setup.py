#!/usr/bin/env python3
"""
Setup script for RSS Intelligence System
Handles initial configuration and testing
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

def create_directory_structure():
    """Create necessary directories"""
    directories = ['config', 'reports', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def copy_env_file():
    """Copy .env.example to .env if it doesn't exist"""
    if not Path('.env').exists():
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your credentials")
        else:
            print("❌ .env.example not found")
    else:
        print("✅ .env file already exists")

def validate_configuration():
    """Validate the configuration"""
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Check required environment variables
    required_vars = {
        'EMAIL_FROM': 'Email sender address',
        'EMAIL_PASSWORD': 'Email app password',
        'AI_PROVIDER': 'AI provider (claude or openai)'
    }
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            errors.append(f"Missing {var}: {description}")
    
    # Check AI API keys
    ai_provider = os.getenv('AI_PROVIDER', '').lower()
    if ai_provider == 'claude' and not os.getenv('ANTHROPIC_API_KEY'):
        errors.append("Missing ANTHROPIC_API_KEY for Claude")
    elif ai_provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        errors.append("Missing OPENAI_API_KEY for OpenAI")
    elif ai_provider not in ['claude', 'openai']:
        errors.append("AI_PROVIDER must be 'claude' or 'openai'")
    
    # Check optional Google Drive
    if not os.getenv('GDRIVE_FOLDER_ID'):
        warnings.append("Google Drive not configured - reports will be saved locally only")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    if warnings:
        print("⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("✅ Configuration validated")
    return True

async def test_system():
    """Test all system components"""
    print("\n🧪 Testing system components...")
    
    try:
        # Import main components
        from config_manager import ConfigManager
        from email_sender import EmailSender
        from gdrive_logger import GDriveLogger
        
        # Test configuration loading
        print("Testing configuration loading...")
        config = ConfigManager()
        print(f"✅ Loaded {len(config.rss_feeds)} RSS feeds")
        
        # Test email
        print("Testing email configuration...")
        email_sender = EmailSender(config)
        email_test = await email_sender.send_test_email()
        if email_test:
            print("✅ Email test successful")
        else:
            print("❌ Email test failed")
        
        # Test Google Drive (if configured)
        print("Testing Google Drive...")
        gdrive_logger = GDriveLogger(config)
        if gdrive_logger.test_connection():
            print("✅ Google Drive connected")
            print(f"📁 Folder: {gdrive_logger.get_drive_folder_url()}")
        else:
            print("⚠️  Google Drive not available (will use local storage)")
        
        print("\n🎉 System test complete!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def create_sample_cron_job():
    """Create sample cron job file"""
    current_dir = os.getcwd()
    
    cron_content = f"""# RSS Intelligence System - Daily Analysis
# Runs every day at 6:00 AM
0 6 * * * cd '{current_dir}' && python3 main.py >> logs/rss_intelligence.log 2>&1

# Alternative times:
# 0 8 * * * cd '{current_dir}' && python3 main.py >> logs/rss_intelligence.log 2>&1  # 8 AM
# 0 10 * * * cd '{current_dir}' && python3 main.py >> logs/rss_intelligence.log 2>&1  # 10 AM

# To install this cron job, run:
# crontab cron_job.txt

# To view current cron jobs:
# crontab -l

# To remove all cron jobs:
# crontab -r
"""
    
    with open('cron_job.txt', 'w') as f:
        f.write(cron_content)
    
    print("✅ Created sample cron job file: cron_job.txt")

def main():
    """Main setup function"""
    print("🚀 RSS Intelligence System Setup")
    print("=" * 40)
    
    # Create directories
    create_directory_structure()
    
    # Setup environment file
    copy_env_file()
    
    # Create sample cron job
    create_sample_cron_job()
    
    print("\n" + "=" * 40)
    print("📋 NEXT STEPS:")
    print("1. Edit .env file with your credentials")
    print("2. Run: python3 setup.py --test")
    print("3. Install cron job: crontab cron_job.txt")
    print("4. Check logs: tail -f logs/rss_intelligence.log")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run tests
        if validate_configuration():
            asyncio.run(test_system())
    elif len(sys.argv) > 1 and sys.argv[1] == "--validate":
        # Just validate configuration
        validate_configuration()
    else:
        # Run setup
        main()