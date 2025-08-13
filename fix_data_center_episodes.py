#!/usr/bin/env python3
"""
Properly transcribe and analyze the Data Center Frontier episodes
"""
import os
import tempfile
import sqlite3
import requests
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def transcribe_and_analyze_episode(episode_id, title, audio_url):
    """Download, transcribe, and analyze a single episode"""
    
    print(f"\n🎧 PROCESSING: {title}")
    print(f"📡 Audio URL: {audio_url}")
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Step 1: Download audio
    print("📥 Downloading audio...")
    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
    
    try:
        response = requests.get(audio_url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_path = temp_file.name
        
        file_size = os.path.getsize(temp_path)
        print(f"✅ Downloaded: {file_size / (1024*1024):.1f}MB")
        
        if file_size > 25 * 1024 * 1024:
            print("❌ File too large for Whisper (>25MB)")
            return False
        
        # Step 2: Transcribe
        print("🎤 Transcribing with Whisper...")
        with open(temp_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        print(f"✅ Transcribed: {len(transcript)} characters")
        
        # Step 3: Analyze with Infrastructure PE prompt
        print("🧠 Analyzing with Infrastructure PE prompt...")
        
        infrastructure_prompt = """# Infrastructure Podcast Deep Analysis for Private Equity Investment

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

        user_prompt = f"""Podcast: The Data Center Frontier Show
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": infrastructure_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        analysis = response.choices[0].message.content
        print(f"✅ Analysis complete: {len(analysis)} characters")
        
        # Extract key quote
        lines = analysis.split('\n')
        key_quote = ""
        for line in lines:
            if 'Quote 1:' in line and len(line) > 20:
                key_quote = line[:400]
                break
        
        # Step 4: Save to database
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        # Update transcript
        cursor.execute("""
            UPDATE episodes 
            SET transcript = ?, transcribed = 1
            WHERE id = ?
        """, (transcript, episode_id))
        
        # Delete old placeholder analysis
        cursor.execute("DELETE FROM analysis_reports WHERE episode_id = ?", (episode_id,))
        
        # Save real analysis
        cursor.execute("""
            INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (episode_id, 1, analysis, key_quote, max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Episode {episode_id} FULLY processed and saved")
        
        # Clean up
        os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False

def fix_data_center_episodes():
    """Fix the Data Center Frontier episodes with real transcription and analysis"""
    
    print("🚀 FIXING Data Center Frontier episodes with REAL transcription and analysis...")
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.title, e.audio_url
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE p.name = 'The Data Center Frontier Show'
        AND e.created_at >= '2025-08-12'
        ORDER BY e.publish_date DESC
        LIMIT 3
    """)
    
    episodes = cursor.fetchall()
    conn.close()
    
    print(f"📊 Found {len(episodes)} Data Center Frontier episodes to fix")
    
    successful = 0
    
    for episode_id, title, audio_url in episodes:
        if transcribe_and_analyze_episode(episode_id, title, audio_url):
            successful += 1
    
    print(f"\n🎉 FIXED {successful}/{len(episodes)} Data Center Frontier episodes")
    print("   ✅ Real transcripts from Whisper")
    print("   ✅ Real analysis with Infrastructure PE prompt")
    print("   ✅ Saved to database")

if __name__ == "__main__":
    fix_data_center_episodes()