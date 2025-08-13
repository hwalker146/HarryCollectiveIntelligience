#!/usr/bin/env python3
"""
Actually transcribe one new episode to test the real pipeline
"""
import os
import tempfile
import sqlite3
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

def transcribe_episode(episode_id, audio_url):
    """Download and transcribe a single episode"""
    
    print(f"🎧 Transcribing episode {episode_id}")
    print(f"📡 Audio URL: {audio_url}")
    
    # Download audio
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
            return None
        
        # Transcribe with Whisper
        print("🎤 Transcribing with Whisper...")
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with open(temp_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        print(f"✅ Transcribed: {len(transcript)} characters")
        
        # Clean up
        os.unlink(temp_path)
        
        return transcript
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None

def test_transcription():
    """Test transcribing one new episode"""
    
    # Get a new episode
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, audio_url 
        FROM episodes 
        WHERE created_at >= '2025-08-12' 
        AND audio_url IS NOT NULL 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ No new episodes found")
        return
    
    episode_id, title, audio_url = result
    print(f"🎯 Testing transcription on: {title}")
    
    # Transcribe
    transcript = transcribe_episode(episode_id, audio_url)
    
    if transcript:
        # Update database
        cursor.execute("""
            UPDATE episodes 
            SET transcript = ?, transcribed = 1
            WHERE id = ?
        """, (transcript, episode_id))
        
        conn.commit()
        print(f"✅ Transcript saved to database")
        print(f"📊 First 200 chars: {transcript[:200]}...")
    
    conn.close()

if __name__ == "__main__":
    test_transcription()