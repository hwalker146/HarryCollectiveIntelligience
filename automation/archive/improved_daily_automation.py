#!/usr/bin/env python3
"""
Improved Daily Automation Script
Guarantees analysis runs automatically on new episodes
"""
import os
import sys
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

load_dotenv()

def main():
    """Main automation function"""
    
    print(f"🤖 DAILY AUTOMATION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Check RSS feeds for new episodes
    print("\n📡 STEP 1: Checking RSS feeds for new episodes...")
    try:
        from daily_rss_checker import check_rss_feeds_for_new_episodes
        new_episode_ids = check_rss_feeds_for_new_episodes()
        
        if new_episode_ids:
            print(f"✅ Found {len(new_episode_ids)} new episodes")
        else:
            print("📧 No new episodes found")
    except Exception as e:
        print(f"❌ RSS check failed: {e}")
        new_episode_ids = []
    
    # Step 2: Process new episodes (transcribe + analyze)
    if new_episode_ids:
        print(f"\n🎧 STEP 2: Processing {len(new_episode_ids)} new episodes...")
        
        try:
            from enhanced_parallel_processor import EnhancedParallelProcessor
            processor = EnhancedParallelProcessor(max_workers=4)
            
            # Transcribe
            print("   📝 Transcribing episodes...")
            transcription_results = processor.parallel_transcribe_episodes(new_episode_ids)
            successful_transcripts = transcription_results.get("success", [])
            print(f"   ✅ Transcribed: {len(successful_transcripts)}/{len(new_episode_ids)}")
            
            # Analyze (AUTOMATIC - no prompting required)
            if successful_transcripts:
                print("   📊 Analyzing episodes (AUTOMATIC)...")
                analysis_results = processor.parallel_analyze_episodes(successful_transcripts)
                successful_analyses = analysis_results.get("success", [])
                print(f"   ✅ Analyzed: {len(successful_analyses)}/{len(successful_transcripts)}")
            else:
                successful_analyses = []
                
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            successful_transcripts = []
            successful_analyses = []
    else:
        successful_transcripts = []
        successful_analyses = []
    
    # Step 3: Update files (both markdown and perfect files if they exist)
    if new_episode_ids:
        print("\n📄 STEP 3: Updating master files...")
        try:
            # Try to update perfect files
            if os.path.exists('auto_update_perfect_files.py'):
                from auto_update_perfect_files import update_perfect_files_with_new_episodes
                update_perfect_files_with_new_episodes(new_episode_ids)
                print("   ✅ Updated perfect master files")
        except Exception as e:
            print(f"   ⚠️ Perfect files update failed: {e}")
        
        try:
            # Update regular files
            from daily_rss_checker import update_master_files
            from daily_email_processor import get_new_episodes_since_date
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            recent_episodes = get_new_episodes_since_date(yesterday)
            
            # Filter to today's episodes
            todays_episodes = [ep for ep in recent_episodes if ep[0] in new_episode_ids]
            
            if todays_episodes:
                update_master_files(todays_episodes)
                print("   ✅ Updated master files")
                
        except Exception as e:
            print(f"   ⚠️ Master files update failed: {e}")
    
    # Step 4: Send email report
    print("\n📧 STEP 4: Sending email report...")
    send_daily_email_report(new_episode_ids, successful_transcripts, successful_analyses)
    
    print("\n🎉 DAILY AUTOMATION COMPLETE!")
    print(f"   New Episodes: {len(new_episode_ids)}")
    print(f"   Transcribed: {len(successful_transcripts)}")
    print(f"   Analyzed: {len(successful_analyses)} (AUTOMATIC)")

def send_daily_email_report(new_episodes, transcripts, analyses):
    """Send daily email report"""
    try:
        email_from = os.getenv('EMAIL_FROM')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_from or not email_password:
            print("⚠️ Email credentials not set")
            return
        
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = "hwalker146@outlook.com"
        
        if new_episodes:
            msg['Subject'] = f"✅ Podcast Automation: {len(new_episodes)} New Episodes - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""🤖 DAILY PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TODAY'S RESULTS:
• New Episodes Found: {len(new_episodes)}
• Successfully Transcribed: {len(transcripts)}
• Successfully Analyzed: {len(analyses)} (AUTOMATIC ✅)

🔗 VIEW YOUR FILES:
📁 Main Folder: https://drive.google.com/drive/folders/1Zo8p26SksJCUTviH95w0JOoKdR1fHGzJ

✅ ANALYSIS RUNS AUTOMATICALLY - No manual prompting required!

🤖 Generated automatically by your podcast system
"""
        else:
            msg['Subject'] = f"📊 Podcast Automation: No New Episodes - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""🤖 DAILY PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TODAY'S STATUS: No new episodes found

✅ SYSTEM STATUS: All systems operational and monitoring

🔗 YOUR FILES: https://drive.google.com/drive/folders/1Zo8p26SksJCUTviH95w0JOoKdR1fHGzJ

🤖 Generated automatically by your podcast system
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_from, email_password)
        server.sendmail(email_from, "hwalker146@outlook.com", msg.as_string())
        server.quit()
        
        print("✅ Email report sent successfully")
        
    except Exception as e:
        print(f"❌ Email failed: {e}")

if __name__ == "__main__":
    main()
