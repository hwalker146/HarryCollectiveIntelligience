#!/usr/bin/env python3
"""
Process ALL missing episodes with real transcription and analysis
"""
import os
import sqlite3
import tempfile
import subprocess
import requests
import openai
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CompletePodcastProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Your actual prompts
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
**Quote 4:** "[Full quote]" - Market significance and implications
**Quote 5:** "[Full quote]" - Market significance and implications

**Analysis Instructions:**
- Prioritize quantitative data and specific market calls
- Note confidence levels and timeframes for predictions
- Distinguish between short-term tactics and long-term strategy
- Highlight any proprietary Goldman Sachs research or data
- Focus on actionable market intelligence"""

    def compress_audio(self, input_path, output_path, target_size_mb=20):
        """Compress audio file to fit Whisper limits"""
        try:
            # Get input duration
            probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', input_path]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(probe_result.stdout)
            duration = float(probe_data['format']['duration'])
            
            # Calculate target bitrate
            target_size_bytes = target_size_mb * 1024 * 1024
            target_bitrate = int((target_size_bytes * 8) / duration) - 1000
            target_bitrate = max(target_bitrate, 32000)
            
            # Compress audio
            compress_cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-acodec', 'mp3', '-ab', f'{target_bitrate}',
                '-ar', '16000', '-ac', '1', output_path
            ]
            
            subprocess.run(compress_cmd, capture_output=True, check=True)
            return True
            
        except Exception as e:
            print(f"   ❌ Compression failed: {e}")
            return False

    def process_episode(self, episode_id, title, audio_url, podcast_name, podcast_id):
        """Process complete episode: download, transcribe, analyze"""
        
        print(f"\n🎧 PROCESSING: {title}")
        print(f"   📡 Podcast: {podcast_name}")
        
        try:
            # Step 1: Download audio
            print("   📥 Downloading audio...")
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(audio_url, headers=headers, timeout=120, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                original_path = temp_file.name
            
            original_size = os.path.getsize(original_path)
            print(f"   📁 Downloaded: {original_size / (1024*1024):.1f}MB")
            
            # Step 2: Compress if needed
            if original_size > 25 * 1024 * 1024:
                print("   🗜️ Compressing audio...")
                compressed_path = original_path.replace('.mp3', '_compressed.mp3')
                
                if self.compress_audio(original_path, compressed_path):
                    audio_path = compressed_path
                    compressed_size = os.path.getsize(compressed_path)
                    print(f"   ✅ Compressed to: {compressed_size / (1024*1024):.1f}MB")
                else:
                    print("   ❌ Compression failed, skipping episode")
                    os.unlink(original_path)
                    return False
            else:
                audio_path = original_path
            
            # Step 3: Transcribe
            print("   🎤 Transcribing with Whisper...")
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            print(f"   ✅ Transcribed: {len(transcript)} characters")
            
            # Step 4: Analyze
            print("   🧠 Analyzing with appropriate prompt...")
            
            # Choose prompt based on podcast
            if 'goldman sachs' in podcast_name.lower() or 'exchanges' in podcast_name.lower():
                system_prompt = self.goldman_prompt
                prompt_type = "Goldman Sachs"
            else:
                system_prompt = self.infrastructure_prompt
                prompt_type = "Infrastructure PE"
            
            print(f"   📊 Using {prompt_type} analysis prompt")
            
            user_prompt = f"""Podcast: {podcast_name}
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            print(f"   ✅ Analysis complete: {len(analysis)} characters")
            
            # Extract key quote
            key_quote = ""
            lines = analysis.split('\n')
            for line in lines:
                if 'Quote 1:' in line and len(line) > 20:
                    key_quote = line[:400]
                    break
            
            # Step 5: Save to database
            print("   💾 Saving to database...")
            conn = sqlite3.connect('podcast_app_v2.db')
            cursor = conn.cursor()
            
            # Update transcript
            cursor.execute("""
                UPDATE episodes 
                SET transcript = ?, transcribed = 1
                WHERE id = ?
            """, (transcript, episode_id))
            
            # Delete old analysis if exists
            cursor.execute("DELETE FROM analysis_reports WHERE episode_id = ?", (episode_id,))
            
            # Save analysis
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 1, analysis, key_quote, max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            # Clean up
            os.unlink(original_path)
            if audio_path != original_path:
                os.unlink(audio_path)
            
            print(f"   ✅ Episode {episode_id} FULLY PROCESSED")
            return True
            
        except Exception as e:
            print(f"   ❌ Processing failed: {e}")
            return False

    def get_missing_episodes(self):
        """Get all episodes that need transcription and analysis"""
        
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        # Get episodes without real transcripts
        cursor.execute("""
            SELECT e.id, e.title, e.audio_url, p.name, p.id
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE e.audio_url IS NOT NULL
            AND (e.transcript IS NULL OR LENGTH(e.transcript) < 5000)
            AND p.id IN (2, 3, 4, 5, 6, 7, 8, 10)  -- Active podcasts
            ORDER BY e.publish_date DESC
            LIMIT 5  -- Test with 5 episodes first
        """)
        
        episodes = cursor.fetchall()
        conn.close()
        
        return episodes

    def process_all_missing(self):
        """Process all missing episodes"""
        
        print("🚀 PROCESSING ALL MISSING EPISODES...")
        
        episodes = self.get_missing_episodes()
        print(f"📊 Found {len(episodes)} episodes needing processing")
        
        if not episodes:
            print("✅ No episodes need processing")
            return
        
        successful = 0
        failed = 0
        
        for episode_id, title, audio_url, podcast_name, podcast_id in episodes:
            if self.process_episode(episode_id, title, audio_url, podcast_name, podcast_id):
                successful += 1
            else:
                failed += 1
            
            print(f"   📊 Progress: {successful + failed}/{len(episodes)} episodes processed")
        
        print(f"\n🎉 BATCH PROCESSING COMPLETE:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success rate: {(successful/(successful+failed)*100):.1f}%")

if __name__ == "__main__":
    processor = CompletePodcastProcessor()
    processor.process_all_missing()