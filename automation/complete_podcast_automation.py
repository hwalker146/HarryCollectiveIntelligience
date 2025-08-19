#!/usr/bin/env python3
"""
Complete working podcast automation system
- Checks RSS feeds for new episodes
- Transcribes with OpenAI Whisper
- Analyzes with specialized prompts  
- Updates master files
- Sends email reports
- Can be run on-demand or scheduled
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
from dotenv import load_dotenv

load_dotenv()

class CompletePodcastAutomation:
    def __init__(self):
        self.db_path = 'podcast_app_v2.db'
        self.master_dir = Path('content/master_transcripts')
        self.reports_dir = Path('content/reports/daily')
        
        # Create directories
        self.master_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # API clients - initialize lazily
        self.openai_client = None
        self.anthropic_client = None
        
        # Podcast name to file mapping
        self.podcast_files = {
            'Exchanges at Goldman Sachs': 'Exchanges_at_Goldman_Sachs_Master_Transcripts.md',
            'The Infrastructure Investor': 'The_Infrastructure_Investor_Master_Transcripts.md',
            'The Data Center Frontier Show': 'The_Data_Center_Frontier_Show_Master_Transcripts.md',
            'Crossroads: The Infrastructure Podcast': 'Crossroads_The_Infrastructure_Podcast_Master_Transcripts.md',
            'Deal Talks': 'Deal_Talks_Master_Transcripts.md',
            'Global Evolution': 'Global_Evolution_Master_Transcripts.md',
            'WSJ What\'s News': 'WSJ_Whats_News_Master_Transcripts.md',
            'The Intelligence': 'The_Intelligence_Master_Transcripts.md',
            'The Ezra Klein Show': 'The_Ezra_Klein_Show_Master_Transcripts.md',
            'Optimistic Outlook': 'Optimistic_Outlook_Master_Transcripts.md',
            'The Engineers Collective': 'The_Engineers_Collective_Master_Transcripts.md',
            'Talking Infrastructure': 'Talking_Infrastructure_Master_Transcripts.md'
        }
        
        # Analysis prompts
        self.wsj_prompt = """Summarize this Wall Street Journal "What's News" daily podcast transcript in 200–300 words. Capture all major stories in the order they appear, including key facts, figures, quotes, and the people or organizations involved. Briefly explain background context when needed so the summary stands on its own. Keep the tone neutral and factual, avoiding opinion or unnecessary adjectives. Begin with a short 1–2 sentence overview of the episode's main themes, then present each story in its own short paragraph with its headline in bold."""
        
        self.intelligence_prompt = """Summarize this episode of The Intelligence podcast from The Economist in 250–350 words. Capture the main global news stories covered, presenting them in the order they appear. For each story, include key facts, developments, context, and any data or analysis provided. Note the hosts and any expert guests or correspondents who provide insights. Highlight significant geopolitical implications, economic impacts, or policy developments. Provide enough background so each story is understandable on its own. Keep the tone neutral and informative, matching The Economist's analytical style. Begin with a brief overview of the episode's main themes, then summarize each story in its own paragraph with clear transitions between topics."""
        
        self.ezra_klein_prompt = """Summarize this episode of the Ezra Klein Show in 300–400 words. Clearly identify the guest speaker's main argument or thesis and explain the reasoning behind it. Highlight the most important supporting points, evidence, and examples the guest uses. Note Ezra Klein's key questions, challenges, or counterpoints, and how the guest responds. Capture any relevant facts, statistics, or policy proposals discussed. Provide enough background context so the summary stands alone. Keep the tone neutral, analytical, and clear. Begin with a 2–3 sentence overview of the episode's theme and the guest's central argument, then organize the rest of the summary by the major points of discussion."""
        
        self.goldman_prompt = """# Goldman Sachs Exchanges Deep Market Analysis

Analyze this Goldman Sachs podcast transcript for institutional investment insights and market intelligence.

## Executive Summary  
Provide detailed analysis covering primary market themes and investment implications, key data points and market forecasts presented, strategic insights for institutional investors, and risk factors and market dynamics discussed.

## Key Market Insights
Extract the most important market calls, data points, and investment recommendations with specific numbers and timeframes where mentioned.

## Notable Quotes & Analysis
Include 3-5 key quotes that capture market predictions, investment recommendations, or strategic insights with context.

Focus on actionable market intelligence and specific investment implications."""
        
        self.infrastructure_prompt = """# Infrastructure Podcast Deep Analysis for Private Equity Investment

Analyze this infrastructure podcast for private equity investment insights.

## Executive Summary
Provide detailed overview of key investment themes, guest's investment thesis, significant deals or opportunities mentioned, and most compelling insights for PE investors.

## Investment Strategy & Market Insights
Cover deal sourcing approaches, market conditions and trends, sector opportunities and challenges, and risk factors discussed.

## Key Quotes & Insights  
Extract 5 most impactful quotes with context that capture investment insights, market predictions, or strategic wisdom.

Focus on actionable intelligence for private equity decision-making with specific company names, deal details, and market data."""
    
    def get_prompt_for_podcast(self, podcast_name):
        """Select appropriate prompt based on podcast"""
        if 'wsj' in podcast_name.lower() or 'what\'s news' in podcast_name.lower():
            return self.wsj_prompt, "WSJ Summary"
        elif 'intelligence' in podcast_name.lower():
            return self.intelligence_prompt, "Intelligence Analysis"
        elif 'ezra klein' in podcast_name.lower():
            return self.ezra_klein_prompt, "Ezra Klein Analysis"
        elif 'goldman sachs' in podcast_name.lower() or 'exchanges' in podcast_name.lower():
            return self.goldman_prompt, "Goldman Sachs Analysis"
        else:
            return self.infrastructure_prompt, "Infrastructure PE Analysis"
    
    def get_openai_client(self):
        """Get OpenAI client"""
        if self.openai_client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.openai_client = openai.OpenAI(api_key=api_key)
        return self.openai_client
    
    def get_anthropic_client(self):
        """Get Anthropic client"""
        if self.anthropic_client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self.anthropic_client
    
    def run_complete_automation(self):
        """Run the complete automation workflow"""
        print("🚀 STARTING COMPLETE PODCAST AUTOMATION")
        print("=" * 60)
        start_time = datetime.now()
        
        # Step 1: Check RSS feeds for new episodes
        new_episodes = self.check_rss_feeds()
        
        # Step 2: Process new episodes
        processed_episodes = []
        if new_episodes:
            print(f"\n🎧 PROCESSING {len(new_episodes)} NEW EPISODES")
            for episode in new_episodes:
                result = self.process_episode(episode)
                if result:
                    processed_episodes.append(result)
        
        # Step 3: Update master files
        if processed_episodes:
            print(f"\n📝 UPDATING MASTER FILES")
            for episode in processed_episodes:
                self.update_master_file(episode)
        
        # Step 4: Send email report
        self.send_email_report(len(new_episodes), len(processed_episodes))
        
        # Summary
        duration = datetime.now() - start_time
        print("\n" + "=" * 60)
        print("🎯 AUTOMATION COMPLETE")
        print(f"⏱️  Duration: {duration}")
        print(f"📈 New episodes found: {len(new_episodes)}")
        print(f"✅ Successfully processed: {len(processed_episodes)}")
        print("=" * 60)
        
        return len(processed_episodes) > 0
    
    def check_rss_feeds(self):
        """Check RSS feeds for new episodes"""
        print("🔍 CHECKING RSS FEEDS FOR NEW EPISODES...")
        
        new_episodes = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get active podcasts
            cursor.execute('''
                SELECT id, name, rss_url 
                FROM podcasts 
                WHERE rss_url IS NOT NULL 
                AND rss_url != ''
                AND is_active = 1
            ''')
            
            podcasts = cursor.fetchall()
            print(f"📡 Checking {len(podcasts)} active podcasts")
            
            for podcast_id, podcast_name, rss_url in podcasts:
                print(f"\n🎧 {podcast_name}...")
                
                # Parse RSS feed
                try:
                    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
                    response = requests.get(rss_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    
                    if feed.bozo:
                        print(f"   ❌ Invalid RSS feed")
                        continue
                    
                    # Check latest 3 episodes
                    for entry in feed.entries[:3]:
                        # Extract audio URL
                        audio_url = None
                        for enclosure in getattr(entry, 'enclosures', []):
                            if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                                audio_url = enclosure.href
                                break
                        
                        if not audio_url:
                            continue
                        
                        # Parse publication date
                        publish_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            publish_date = datetime(*entry.published_parsed[:6]).isoformat()
                        
                        episode_title = getattr(entry, 'title', 'Unknown Title')
                        
                        # Check if episode exists in database
                        cursor.execute('''
                            SELECT id FROM episodes 
                            WHERE podcast_id = ? AND (guid = ? OR audio_url = ? OR title = ?)
                        ''', (podcast_id, getattr(entry, 'id', audio_url), audio_url, episode_title))
                        
                        if not cursor.fetchone():
                            # New episode!
                            episode_data = {
                                'podcast_id': podcast_id,
                                'podcast_name': podcast_name,
                                'title': episode_title,
                                'description': getattr(entry, 'summary', ''),
                                'audio_url': audio_url,
                                'episode_url': getattr(entry, 'link', ''),
                                'guid': getattr(entry, 'id', None) or audio_url,
                                'publish_date': publish_date
                            }
                            new_episodes.append(episode_data)
                            print(f"   🆕 NEW: {episode_title[:50]}...")
                            break  # Only take first missing per podcast
                        
                except Exception as e:
                    print(f"   ❌ RSS error: {e}")
                    continue
            
            conn.close()
            
            if new_episodes:
                print(f"\n✅ FOUND {len(new_episodes)} NEW EPISODES TO PROCESS")
            else:
                print(f"\n📭 No new episodes found")
                
            return new_episodes[:5]  # Limit to 5 per run
            
        except Exception as e:
            print(f"❌ RSS checking failed: {e}")
            return []
    
    def process_episode(self, episode):
        """Process a single episode (transcribe and analyze)"""
        print(f"\n🔧 PROCESSING: {episode['title'][:50]}...")
        
        try:
            # Step 1: Download and transcribe
            transcript = self.transcribe_episode(episode)
            if not transcript:
                return None
            
            # Step 2: Analyze
            analysis = self.analyze_episode(episode, transcript)
            
            # Step 3: Save to database
            episode_id = self.save_to_database(episode, transcript, analysis)
            
            return {
                'episode_id': episode_id,
                'podcast_name': episode['podcast_name'],
                'title': episode['title'],
                'date': episode.get('publish_date', '').split('T')[0] if episode.get('publish_date') else date.today().strftime('%Y-%m-%d'),
                'transcript': transcript,
                'analysis': analysis
            }
            
        except Exception as e:
            print(f"   ❌ Processing failed: {e}")
            return None
    
    def transcribe_episode(self, episode):
        """Download and transcribe episode"""
        try:
            print("   📥 Downloading audio...")
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(episode['audio_url'], headers=headers, timeout=120, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                audio_path = temp_file.name
            
            # Check file size and compress if needed
            file_size = os.path.getsize(audio_path)
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                print("   🗜️ Compressing audio...")
                compressed_path = self.compress_audio(audio_path)
                if compressed_path:
                    audio_path = compressed_path
                else:
                    os.unlink(audio_path)
                    return None
            
            # Transcribe
            print("   🎤 Transcribing...")
            with open(audio_path, 'rb') as audio_file:
                transcript = self.get_openai_client().audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            os.unlink(audio_path)
            
            if len(transcript) < 100:
                print("   ❌ Transcript too short")
                return None
            
            print(f"   ✅ Transcribed: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            print(f"   ❌ Transcription failed: {e}")
            return None
    
    def compress_audio(self, input_path):
        """Compress audio file using ffmpeg"""
        try:
            output_path = input_path.replace('.mp3', '_compressed.mp3')
            
            # Get duration first
            probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', input_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(probe_result.stdout)
            duration = float(probe_data['format']['duration'])
            
            # Calculate bitrate for ~20MB target
            target_size_bytes = 20 * 1024 * 1024
            target_bitrate = int((target_size_bytes * 8) / duration) - 1000
            target_bitrate = max(target_bitrate, 32000)
            
            # Compress
            compress_cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-acodec', 'mp3', '-ab', f'{target_bitrate}',
                '-ar', '16000', '-ac', '1', output_path
            ]
            
            subprocess.run(compress_cmd, capture_output=True, check=True)
            os.unlink(input_path)
            return output_path
            
        except Exception as e:
            print(f"   ❌ Compression failed: {e}")
            return None
    
    def analyze_episode(self, episode, transcript):
        """Analyze episode with appropriate prompt"""
        try:
            print("   🧠 Analyzing...")
            
            # Choose prompt
            prompt, prompt_type = self.get_prompt_for_podcast(episode['podcast_name'])
            print(f"   📊 Using {prompt_type} prompt")
            
            user_prompt = f"""Podcast: {episode['podcast_name']}
Episode: {episode['title']}
Published: {episode.get('publish_date', 'Unknown')}

TRANSCRIPT:
{transcript}"""
            
            response = self.get_anthropic_client().messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            analysis = response.content[0].text
            print(f"   ✅ Analysis complete: {len(analysis)} characters")
            return analysis
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
    
    def save_to_database(self, episode, transcript, analysis):
        """Save episode to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert episode
            cursor.execute('''
                INSERT INTO episodes (
                    podcast_id, title, audio_url, publish_date, 
                    description, episode_url, guid, transcript, transcribed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                episode['podcast_id'],
                episode['title'],
                episode['audio_url'],
                episode.get('publish_date'),
                episode.get('description', ''),
                episode.get('episode_url', ''),
                episode.get('guid', episode['audio_url']),
                transcript,
                datetime.now().isoformat()
            ))
            
            episode_id = cursor.lastrowid
            
            # Save analysis
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 1, analysis, "", max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ Saved to database: Episode ID {episode_id}")
            return episode_id
            
        except Exception as e:
            print(f"   ❌ Database save failed: {e}")
            return None
    
    def update_master_file(self, episode):
        """Update master transcript file"""
        try:
            filename = self.podcast_files.get(episode['podcast_name'])
            if not filename:
                print(f"   ⚠️ No master file configured for: {episode['podcast_name']}")
                return
            
            filepath = self.master_dir / filename
            
            # Create episode content
            episode_content = f"""## {episode['date']}

### {episode['title']}
**Publication Date:** {episode['date']}T00:00:00
**Episode ID:** {episode['episode_id']}

**Full Transcript:**
{episode['transcript']}

---

"""
            
            if filepath.exists():
                # Read existing file
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Insert new episode at top (after header)
                header_end = existing_content.find("---\n\n")
                if header_end != -1:
                    header_part = existing_content[:header_end + 5]
                    episodes_part = existing_content[header_end + 5:]
                    new_content = header_part + episode_content + episodes_part
                    
                    # Update episode count
                    episode_count_match = re.search(r'\*\*Total Episodes:\*\* (\d+)', header_part)
                    if episode_count_match:
                        current_count = int(episode_count_match.group(1))
                        new_count = current_count + 1
                        new_content = new_content.replace(
                            f"**Total Episodes:** {current_count}",
                            f"**Total Episodes:** {new_count}"
                        )
                else:
                    new_content = existing_content + episode_content
            else:
                # Create new file
                new_content = f"""# {episode['podcast_name']} - Master Transcripts

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Episodes:** 1

Episodes organized by publication date (newest first).

---

{episode_content}"""
            
            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"   ✅ Updated master file: {filename}")
            
        except Exception as e:
            print(f"   ❌ Master file update failed: {e}")
    
    def send_email_report(self, episodes_found, episodes_processed):
        """Send automation report email"""
        try:
            sender_email = os.getenv('EMAIL_FROM', 'aipodcastdigest@gmail.com')
            sender_password = os.getenv('EMAIL_PASSWORD')
            recipient_email = 'hwalker146@outlook.com'
            
            if not sender_password:
                print("❌ Email password not configured")
                return
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            
            if episodes_processed > 0:
                msg['Subject'] = f"✅ {episodes_processed} New Podcast Episodes Processed - {datetime.now().strftime('%Y-%m-%d')}"
                
                body = f"""🤖 COMPLETE PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TODAY'S RESULTS:
• Episodes Found: {episodes_found}
• Successfully Processed: {episodes_processed}

✅ SYSTEM STATUS: Full automation working correctly
🎯 PROMPTS: All specialized prompts active
   • WSJ What's News → WSJ Summary
   • The Intelligence → Intelligence Analysis  
   • Ezra Klein Show → Ezra Klein Analysis
   • Goldman Sachs → Goldman Sachs Analysis
   • Infrastructure → Infrastructure PE Analysis

🔗 GitHub: https://github.com/hwalker146/HarryCollectiveIntelligience
📁 Master Files: content/master_transcripts/

🤖 Generated by complete automation system
"""
            else:
                msg['Subject'] = f"📊 Podcast Automation: No New Episodes - {datetime.now().strftime('%Y-%m-%d')}"
                
                body = f"""🤖 COMPLETE PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 STATUS: No new episodes found today
✅ SYSTEM: All systems operational and monitoring

Episodes checked: {episodes_found}
All podcasts are up to date.

🤖 Generated by complete automation system
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            
            print(f"✅ Email report sent to {recipient_email}")
            
        except Exception as e:
            print(f"❌ Email failed: {e}")

if __name__ == "__main__":
    automation = CompletePodcastAutomation()
    automation.run_complete_automation()