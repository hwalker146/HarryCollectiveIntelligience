#!/usr/bin/env python3
"""
Process last 20 episodes of a16z podcast
"""
import os
import sqlite3
import feedparser
import requests
import tempfile
import openai
import anthropic
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    return openai.OpenAI(api_key=api_key)

def get_anthropic_client():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    return anthropic.Anthropic(api_key=api_key)

def compress_audio_if_needed(audio_path):
    """Compress audio if over 25MB"""
    import subprocess
    import json
    
    file_size = os.path.getsize(audio_path)
    if file_size <= 25 * 1024 * 1024:
        return audio_path
    
    print(f"   🗜️ Compressing audio ({file_size/1024/1024:.1f}MB)...")
    
    try:
        output_path = audio_path.replace('.mp3', '_compressed.mp3')
        
        # Get duration first
        probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(probe_result.stdout)
        duration = float(probe_data['format']['duration'])
        
        # Calculate bitrate for ~20MB target
        target_size_bytes = 20 * 1024 * 1024
        target_bitrate = int((target_size_bytes * 8) / duration) - 1000
        target_bitrate = max(target_bitrate, 32000)
        
        # Compress
        compress_cmd = [
            'ffmpeg', '-i', audio_path, '-y',
            '-acodec', 'mp3', '-ab', f'{target_bitrate}',
            '-ar', '16000', '-ac', '1', output_path
        ]
        
        subprocess.run(compress_cmd, capture_output=True, check=True)
        os.unlink(audio_path)
        
        new_size = os.path.getsize(output_path)
        print(f"   ✅ Compressed to {new_size/1024/1024:.1f}MB")
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Compression failed: {e}")
        return None

def transcribe_episode(audio_url, title):
    """Download and transcribe episode"""
    try:
        print(f"   📥 Downloading: {title[:50]}...")
        headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
        response = requests.get(audio_url, headers=headers, timeout=120, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            audio_path = temp_file.name
        
        # Check file size
        audio_path = compress_audio_if_needed(audio_path)
        if not audio_path:
            return None
        
        # Transcribe
        print(f"   🎤 Transcribing...")
        with open(audio_path, 'rb') as audio_file:
            transcript = get_openai_client().audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        os.unlink(audio_path)
        
        if len(transcript) < 100:
            print(f"   ❌ Transcript too short")
            return None
        
        print(f"   ✅ Transcribed: {len(transcript)} characters")
        return transcript
        
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        return None

def analyze_episode(title, transcript):
    """Analyze episode with a16z prompt"""
    a16z_prompt = """A16Z Podcast Transcription Analysis Prompt

Context: You are analyzing this transcription with a focus on AI developments, technology trends, and business insights. Extract key learnings that would be valuable for understanding the current state and future direction of AI and technology markets.

## Primary Analysis Framework

### AI & Technology Insights
* AI Development Trends: Highlight discussions about model architectures, capabilities, limitations, and breakthrough developments
* Application Areas: Note specific use cases, industry applications, and real-world implementations discussed
* Technical Challenges: Identify mentioned bottlenecks, unsolved problems, or areas needing innovation
* Market Opportunities: Extract specific market sizing data, growth projections, and emerging segments

### Competitive Landscape Analysis
* Key Players: Map out mentioned companies, their positioning, and competitive advantages
* Market Consolidation: Identify trends toward consolidation or fragmentation
* Barriers to Entry: Note capital requirements, technical moats, or regulatory barriers
* Competitive Threats: Highlight potential disruptors or new market entrants

### Technology Evolution & Adoption
* Development Timelines: Note predictions about technology maturity and adoption curves
* Adoption Barriers: Extract challenges preventing widespread adoption
* Success Factors: Identify what's driving successful implementations
* Future Predictions: Capture forecasts about technology direction and market evolution

### Business & Strategic Insights
* Business Model Innovation: Note new monetization strategies or market approaches
* Partnership Trends: Identify collaboration patterns or strategic relationships
* Investment Themes: Extract insights about funding trends and capital allocation
* Regulatory Considerations: Highlight policy discussions and regulatory impacts

## Output Structure

### Executive Summary 
Brief overview of the most significant AI and technology insights (2-3 sentences)

### Key AI Developments
* Development 1: [Description, implications, timeline]
* Development 2: [Description, implications, timeline]
* Development 3: [Description, implications, timeline]

### Market Dynamics
* Growth drivers and headwinds
* Regulatory environment changes
* Technology disruption factors

### Actionable Intelligence
* Companies or technologies to research further
* Trends worth monitoring
* Potential opportunities or threats

### Risk Assessment
* Primary risks to discussed developments
* Mitigation strategies mentioned

### Notable Quotes
* 3-5 most insightful quotes relevant to AI and technology trends

## Additional Instructions
* Quantify wherever possible (market sizes, growth rates, timelines)
* Flag any contrarian or non-consensus views expressed
* Note the credibility and track record of speakers when assessing insights
* Highlight any mentions of ESG considerations or sustainability trends
* Connect insights to broader macroeconomic or geopolitical themes when relevant"""

    try:
        print(f"   🧠 Analyzing...")
        
        user_prompt = f"""Podcast: a16z Podcast
Episode: {title}

TRANSCRIPT:
{transcript}"""
        
        response = get_anthropic_client().messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=a16z_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        analysis = response.content[0].text
        print(f"   ✅ Analysis complete: {len(analysis)} characters")
        return analysis
        
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return f"Analysis failed: {str(e)}"

def save_to_database(podcast_id, episode_data, transcript, analysis):
    """Save episode to database"""
    try:
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        # Insert episode
        cursor.execute('''
            INSERT INTO episodes (
                podcast_id, title, audio_url, publish_date, 
                episode_url, guid, transcript, transcribed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        ''', (
            podcast_id,
            episode_data['title'],
            episode_data['audio_url'],
            episode_data.get('publish_date'),
            episode_data.get('episode_url', ''),
            episode_data.get('guid', episode_data['audio_url']),
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

def update_master_file(episode_data, transcript):
    """Update a16z master transcript file"""
    try:
        master_dir = Path('content/master_transcripts')
        master_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = master_dir / 'a16z_Podcast_Master_Transcripts.md'
        
        # Parse date
        pub_date = episode_data.get('publish_date', '').split('T')[0] if episode_data.get('publish_date') else datetime.now().strftime('%Y-%m-%d')
        
        # Create episode content
        episode_content = f"""## {pub_date}

### {episode_data['title']}
**Publication Date:** {pub_date}T00:00:00
**Episode ID:** {episode_data['episode_id']}

**Full Transcript:**
{transcript}

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
                import re
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
            new_content = f"""# a16z Podcast - Master Transcripts

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Episodes:** 1

Episodes organized by publication date (newest first).

---

{episode_content}"""
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"   ✅ Updated master file")
        
    except Exception as e:
        print(f"   ❌ Master file update failed: {e}")

def main():
    print("🚀 PROCESSING A16Z PODCAST - LAST 20 EPISODES")
    print("=" * 60)
    
    # Get podcast ID
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM podcasts WHERE name = 'a16z Podcast'")
    result = cursor.fetchone()
    if not result:
        print("❌ a16z Podcast not found in database")
        return
    
    podcast_id = result[0]
    conn.close()
    
    # Parse RSS feed
    print("📡 Fetching RSS feed...")
    try:
        headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
        response = requests.get('https://feeds.simplecast.com/JGE3yC0V', headers=headers, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if feed.bozo:
            print("❌ Invalid RSS feed")
            return
        
        print(f"✅ Found {len(feed.entries)} episodes in feed")
        
        # Process last 5 episodes (test run)
        episodes_to_process = feed.entries[:5]
        processed_count = 0
        
        for i, entry in enumerate(episodes_to_process, 1):
            print(f"\n🎧 EPISODE {i}/5: {getattr(entry, 'title', 'Unknown')[:50]}...")
            
            # Extract audio URL
            audio_url = None
            for enclosure in getattr(entry, 'enclosures', []):
                if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                    audio_url = enclosure.href
                    break
            
            if not audio_url:
                print("   ❌ No audio URL found")
                continue
            
            # Parse publication date
            publish_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                publish_date = datetime(*entry.published_parsed[:6]).isoformat()
            
            episode_data = {
                'title': getattr(entry, 'title', 'Unknown Title'),
                'audio_url': audio_url,
                'episode_url': getattr(entry, 'link', ''),
                'guid': getattr(entry, 'id', None) or audio_url,
                'publish_date': publish_date
            }
            
            # Check if episode already exists
            conn = sqlite3.connect('podcast_app_v2.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM episodes 
                WHERE podcast_id = ? AND (guid = ? OR audio_url = ? OR title = ?)
            ''', (podcast_id, episode_data['guid'], audio_url, episode_data['title']))
            
            if cursor.fetchone():
                print("   ⏭️  Episode already exists, skipping")
                conn.close()
                continue
            
            conn.close()
            
            # Process episode
            transcript = transcribe_episode(audio_url, episode_data['title'])
            if not transcript:
                continue
            
            analysis = analyze_episode(episode_data['title'], transcript)
            
            episode_id = save_to_database(podcast_id, episode_data, transcript, analysis)
            if not episode_id:
                continue
            
            episode_data['episode_id'] = episode_id
            update_master_file(episode_data, transcript)
            
            processed_count += 1
            print(f"   ✅ Successfully processed episode {processed_count}")
        
        print(f"\n🎯 PROCESSING COMPLETE: {processed_count}/5 episodes processed")
        
    except Exception as e:
        print(f"❌ RSS processing failed: {e}")

if __name__ == "__main__":
    main()