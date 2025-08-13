#!/usr/bin/env python3
"""
Run REAL analysis on newly detected episodes
This script will:
1. Download audio files from URLs
2. Transcribe using OpenAI Whisper
3. Analyze using your specific prompts (Infrastructure PE / Goldman Sachs)
4. Update all files and Google Drive
5. Send email report
"""
import os
import sys
import sqlite3
import openai
from datetime import datetime, timedelta
from pathlib import Path
import requests
import tempfile

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add paths for imports
sys.path.append('scripts')
sys.path.append('.')

from automated_podcast_system import AutomatedPodcastSystem

class RealAnalysisProcessor:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.system = AutomatedPodcastSystem()
        
        # Your analysis prompts
        self.infrastructure_prompt = """# Infrastructure Podcast Deep Analysis for Private Equity Investment

Please provide a comprehensive analysis of this infrastructure podcast transcript. This analysis is for private equity investors evaluating opportunities in the infrastructure sector.

## Executive Summary
Provide a detailed 3-4 paragraph overview covering the key investment themes and market opportunities discussed, the guest's primary investment thesis and strategic outlook, the significant deals, companies, or market developments mentioned, the regulatory or policy changes impacting the sector, and the most compelling insights for private equity investors

## Guest Profile & Credentials
- **Name & Title:** [Guest's full name and current role]
- **Company:** [Company name and brief description]
- **Background:** Key experience and credentials relevant to infrastructure investing
- **Track Record:** Notable deals, funds, or investments mentioned

## Investment Strategy & Market Insights

### Deal Sourcing & Evaluation
- How does the guest's firm identify investment opportunities?
- What criteria do they use for deal selection?
- Which sectors or geographies are they focusing on?
- What deal sizes or structures do they prefer?

### Market Analysis
- Current market conditions and trends discussed
- Sector-specific opportunities and challenges
- Regulatory environment and policy impacts
- Competitive dynamics and market consolidation trends
- Risk factors and mitigation strategies

## Specific Investment Opportunities & Deals
List any concrete investments, deals, or opportunities mentioned:
- Company names and transaction details
- Investment sizes and structures
- Returns achieved or expected
- Lessons learned from specific investments

## Financial Analysis & Returns
- Return expectations and metrics discussed
- Portfolio performance data mentioned
- Valuation methodologies or multiples referenced
- Capital deployment schedules
- Exit strategies and timing

## Key Quotes & Insights
Extract 5-7 most impactful quotes that capture:
- Unique investment insights or contrarian views
- Specific market predictions or forecasts
- Strategic wisdom or lessons learned
- Notable frameworks or principles
- Actionable investment advice

**Quote 1:** "[Full quote]" - Context and significance
**Quote 2:** "[Full quote]" - Context and significance  
**Quote 3:** "[Full quote]" - Context and significance
**Quote 4:** "[Full quote]" - Context and significance
**Quote 5:** "[Full quote]" - Context and significance

## Investment Committee Discussion Points
Based on this episode, prepare 7-10 targeted questions for investment committee:
1. [Specific question about opportunity mentioned]
2. [Question about market trends or assumptions]
3. [Challenge to thesis or risk consideration]
4. [Operational or strategic consideration]
5. [Regulatory or policy question]
6. [Competitive dynamics inquiry]
7. [Exit planning consideration]

**Analysis Instructions:**
- only write in paragraphs and full sentences. No bullet points or lists
- Be extremely specific with numbers, dates, company names, and deal details
- Distinguish clearly between facts and opinions/predictions  
- Focus on actionable intelligence for private equity decision-making"""

        self.goldman_prompt = """# Goldman Sachs Exchanges Deep Market Analysis

Analyze this Goldman Sachs podcast transcript for institutional investment insights and market intelligence.

## Episode Overview
**Topic:** [Main subject matter]
**Market Context:** [Current market environment and timing]
**Key Participants:** [Host and guest details]

## Executive Summary  
Provide detailed analysis covering:
- Primary market themes and investment implications
- Key data points and market forecasts presented
- Strategic insights for institutional investors
- Risk factors and market dynamics discussed

## Market Analysis & Investment Thesis

### Primary Arguments Presented
For each major argument, provide:
- **Core Thesis:** [Detailed explanation]
- **Supporting Evidence:** [Data, trends, examples cited]
- **Market Implications:** [How this affects investment decisions]
- **Confidence Level:** [How certain are the predictions]
- **Timeline:** [When effects are expected]

### Quantitative Data & Forecasts
List all specific numbers, percentages, forecasts mentioned:
- Market size estimates
- Growth projections  
- Valuation metrics
- Performance data
- Economic indicators
- Sector-specific metrics

## Sector & Asset Class Analysis
Break down insights by relevant sectors:
- **Equities:** [Specific insights about stock markets]
- **Fixed Income:** [Bond market analysis]
- **Alternatives:** [Private markets, real estate, etc.]
- **Commodities:** [Commodity market insights]
- **Currency/FX:** [Foreign exchange considerations]

## Risk Assessment
- **Key Risks Identified:** [Specific risks discussed]
- **Probability Assessment:** [Likelihood of risks materializing]
- **Mitigation Strategies:** [How to hedge or prepare]
- **Tail Risks:** [Low probability, high impact scenarios]

## Trading & Investment Strategies
- **Recommended Positions:** [Specific investment recommendations]
- **Asset Allocation Insights:** [Portfolio construction advice]
- **Timing Considerations:** [Entry/exit points discussed]
- **Hedging Strategies:** [Risk management approaches]

## Notable Quotes & Market Calls
Extract 5-7 most significant quotes focusing on:
- Specific market predictions
- Investment recommendations  
- Risk warnings
- Contrarian viewpoints
- Strategic insights

**Quote 1:** "[Full quote]" - Market significance and implications
**Quote 2:** "[Full quote]" - Market significance and implications
**Quote 3:** "[Full quote]" - Market significance and implications

**Analysis Instructions:**
- Prioritize quantitative data and specific market calls
- Note confidence levels and timeframes for predictions
- Distinguish between short-term tactics and long-term strategy
- Highlight any proprietary Goldman Sachs research or data
- Focus on actionable market intelligence"""

    def download_audio(self, audio_url, episode_id):
        """Download audio file"""
        try:
            print(f"📥 Downloading audio for episode {episode_id}...")
            
            headers = {
                'User-Agent': 'Podcast Analysis Application v2/2.0.0'
            }
            
            response = requests.get(audio_url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_path = temp_file.name
            
            print(f"✅ Audio downloaded: {temp_path}")
            return temp_path
            
        except Exception as e:
            print(f"❌ Audio download failed: {e}")
            return None

    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using OpenAI Whisper"""
        try:
            print(f"🎤 Transcribing audio...")
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                print(f"❌ Audio file too large: {file_size / (1024*1024):.1f}MB")
                return None
            
            print(f"📁 File size: {file_size / (1024*1024):.1f}MB")
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            print(f"✅ Transcription complete: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None

    def analyze_transcript(self, transcript, title, podcast_name, podcast_id):
        """Analyze transcript using your prompts"""
        try:
            print(f"🧠 Analyzing transcript...")
            
            # Choose prompt based on podcast
            if 'goldman sachs' in podcast_name.lower() or 'exchanges' in podcast_name.lower():
                system_prompt = self.goldman_prompt
                print("📊 Using Goldman Sachs analysis prompt")
            else:
                system_prompt = self.infrastructure_prompt
                print("🏗️ Using Infrastructure PE analysis prompt")
            
            user_prompt = f"""Podcast: {podcast_name}
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using full GPT-4 for best quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            # Extract key quote
            key_quote = ""
            lines = analysis.split('\n')
            for line in lines:
                if 'Quote 1:' in line or ('quote' in line.lower() and len(line) > 50):
                    key_quote = line[:400]
                    break
            
            print(f"✅ Analysis complete: {len(analysis)} characters")
            return analysis, key_quote
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None, None

    def process_episode(self, episode_id, title, audio_url, publish_date, podcast_name, podcast_id):
        """Process single episode completely"""
        print(f"\n🎧 PROCESSING: {title}")
        print(f"   📡 Podcast: {podcast_name}")
        print(f"   🔗 Audio URL: {audio_url}")
        
        # Step 1: Download audio
        audio_path = self.download_audio(audio_url, episode_id)
        if not audio_path:
            return None
        
        try:
            # Step 2: Transcribe
            transcript = self.transcribe_audio(audio_path)
            if not transcript:
                return None
            
            # Step 3: Analyze
            analysis, key_quote = self.analyze_transcript(transcript, title, podcast_name, podcast_id)
            if not analysis:
                return None
            
            # Step 4: Save to database
            conn = sqlite3.connect(self.system.db_path)
            cursor = conn.cursor()
            
            # Update episode with transcript
            cursor.execute("""
                UPDATE episodes 
                SET transcript = ?, transcript_status = 'completed'
                WHERE id = ?
            """, (transcript, episode_id))
            
            # Create analysis report
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 1, analysis, key_quote or "", max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Episode {episode_id} fully processed and saved")
            
            return {
                'id': episode_id,
                'title': title,
                'podcast_name': podcast_name,
                'publish_date': publish_date,
                'transcript': transcript,
                'analysis': analysis,
                'key_quote': key_quote
            }
            
        finally:
            # Clean up audio file
            try:
                os.unlink(audio_path)
            except:
                pass

def run_real_analysis():
    """Run complete analysis pipeline"""
    print("🚀 Starting REAL episode analysis with transcription...")
    
    processor = RealAnalysisProcessor()
    
    # Get new episodes from last 24 hours
    conn = sqlite3.connect(processor.system.db_path)
    cursor = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    cursor.execute('''
        SELECT e.id, e.title, e.audio_url, e.publish_date, p.name as podcast_name, p.id as podcast_id
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.created_at >= ?
        AND (e.transcript IS NULL OR e.transcript = '')
        AND e.audio_url IS NOT NULL
        ORDER BY e.created_at DESC
        LIMIT 5
    ''', (yesterday,))
    
    episodes = cursor.fetchall()
    conn.close()
    
    print(f"📊 Found {len(episodes)} episodes to process")
    
    if not episodes:
        print("📭 No new episodes need processing")
        return
    
    processed_episodes = []
    
    for episode_id, title, audio_url, publish_date, podcast_name, podcast_id in episodes:
        try:
            result = processor.process_episode(episode_id, title, audio_url, publish_date, podcast_name, podcast_id)
            if result:
                processed_episodes.append(result)
        except Exception as e:
            print(f"❌ Failed to process episode {episode_id}: {e}")
    
    if processed_episodes:
        print(f"\n✅ Successfully processed {len(processed_episodes)} episodes")
        
        # Update files and sync
        print("\n📝 Updating transcript and analysis files...")
        processor.system.update_individual_files(processed_episodes)
        processor.system.update_master_file()
        
        print("\n📤 Syncing to Google Drive...")
        processor.system.sync_to_google_drive()
        
        # Create and send report
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = processor.system.create_analysis_report(today, processed_episodes)
        
        if report_file:
            print(f"\n📧 Sending email report...")
            processor.system.send_daily_email(report_file, today)
        
        print(f"\n🎉 REAL ANALYSIS COMPLETE!")
        print(f"   ✅ Episodes processed: {len(processed_episodes)}")
        for ep in processed_episodes:
            print(f"      • {ep['podcast_name']}: {ep['title']}")
    
    else:
        print("❌ No episodes were successfully processed")

if __name__ == "__main__":
    run_real_analysis()