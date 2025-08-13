#!/usr/bin/env python3
"""
Test the complete audio download and transcription pipeline
"""
import os
import sqlite3
import tempfile
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

def test_single_episode_pipeline():
    """Test complete pipeline on one recent episode"""
    
    # Get one recent episode that needs transcription
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.title, e.audio_url, p.name
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.audio_url IS NOT NULL
        AND (e.transcript IS NULL OR LENGTH(e.transcript) < 1000)
        AND p.name = 'Exchanges at Goldman Sachs'
        ORDER BY e.publish_date DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ No test episode found")
        return False
    
    episode_id, title, audio_url, podcast_name = result
    print(f"🧪 Testing pipeline on: {title}")
    print(f"📡 Podcast: {podcast_name}")
    print(f"🔗 Audio URL: {audio_url}")
    
    try:
        # Step 1: Download audio
        print("\n📥 Step 1: Downloading audio...")
        headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
        
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
            os.unlink(temp_path)
            return False
        
        # Step 2: Transcribe with Whisper
        print("\n🎤 Step 2: Transcribing with Whisper...")
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with open(temp_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        print(f"✅ Transcribed: {len(transcript)} characters")
        print(f"📄 Sample: {transcript[:200]}...")
        
        # Clean up audio file
        os.unlink(temp_path)
        
        # Step 3: Test analysis
        print("\n🧠 Step 3: Testing analysis with Goldman Sachs prompt...")
        
        goldman_prompt = """# Goldman Sachs Exchanges Deep Market Analysis

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

## Key Quotes & Insights
Extract 3-5 most impactful quotes that capture:
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
- Focus on actionable market intelligence"""

        user_prompt = f"""Podcast: {podcast_name}
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": goldman_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        analysis = response.choices[0].message.content
        print(f"✅ Analysis complete: {len(analysis)} characters")
        print(f"📄 Sample: {analysis[:300]}...")
        
        # Extract key quote
        key_quote = ""
        lines = analysis.split('\n')
        for line in lines:
            if 'Quote 1:' in line and len(line) > 20:
                key_quote = line[:400]
                break
        
        if key_quote:
            print(f"💬 Key quote found: {key_quote[:100]}...")
        else:
            print("⚠️ No key quote extracted")
        
        # Step 4: Save to database
        print("\n💾 Step 4: Saving to database...")
        
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
        """, (episode_id, 1, analysis, key_quote, max(1, len(analysis.split()) // 200), "2025-08-13"))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Pipeline test SUCCESSFUL for episode {episode_id}")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test FAILED: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    success = test_single_episode_pipeline()
    if success:
        print("\n🎉 TRANSCRIPTION PIPELINE IS WORKING!")
    else:
        print("\n💥 TRANSCRIPTION PIPELINE NEEDS FIXING!")