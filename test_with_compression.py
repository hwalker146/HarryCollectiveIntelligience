#!/usr/bin/env python3
"""
Test transcription pipeline with audio compression
"""
import os
import sqlite3
import tempfile
import subprocess
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

def compress_audio(input_path, output_path, target_size_mb=20):
    """Compress audio file to fit Whisper limits"""
    try:
        # Get input duration
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', input_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        import json
        probe_data = json.loads(probe_result.stdout)
        duration = float(probe_data['format']['duration'])
        
        # Calculate target bitrate
        target_size_bytes = target_size_mb * 1024 * 1024
        target_bitrate = int((target_size_bytes * 8) / duration) - 1000  # Leave some margin
        target_bitrate = max(target_bitrate, 32000)  # Minimum 32kbps
        
        # Compress audio
        compress_cmd = [
            'ffmpeg', '-i', input_path, '-y',
            '-acodec', 'mp3',
            '-ab', f'{target_bitrate}',
            '-ar', '16000',  # 16kHz sample rate is fine for speech
            '-ac', '1',      # Mono
            output_path
        ]
        
        subprocess.run(compress_cmd, capture_output=True, check=True)
        
        compressed_size = os.path.getsize(output_path)
        print(f"✅ Compressed: {compressed_size / (1024*1024):.1f}MB (bitrate: {target_bitrate}bps)")
        
        return True
        
    except Exception as e:
        print(f"❌ Compression failed: {e}")
        return False

def test_pipeline_with_compression():
    """Test pipeline with audio compression"""
    
    # Get one recent episode
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
    print(f"🧪 Testing with compression: {title}")
    
    try:
        # Download audio
        print("📥 Downloading audio...")
        headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
        response = requests.get(audio_url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            original_path = temp_file.name
        
        original_size = os.path.getsize(original_path)
        print(f"📁 Original: {original_size / (1024*1024):.1f}MB")
        
        # Compress if needed
        if original_size > 25 * 1024 * 1024:
            print("🗜️ Compressing audio...")
            compressed_path = original_path.replace('.mp3', '_compressed.mp3')
            
            if compress_audio(original_path, compressed_path):
                audio_path = compressed_path
            else:
                print("❌ Compression failed")
                return False
        else:
            audio_path = original_path
        
        # Transcribe
        print("🎤 Transcribing...")
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        print(f"✅ Transcribed: {len(transcript)} characters")
        print(f"📄 Sample: {transcript[:150]}...")
        
        # Clean up
        os.unlink(original_path)
        if audio_path != original_path:
            os.unlink(audio_path)
        
        # Save transcript
        cursor.execute("""
            UPDATE episodes 
            SET transcript = ?, transcribed = 1
            WHERE id = ?
        """, (transcript, episode_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ PIPELINE WITH COMPRESSION SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    test_pipeline_with_compression()