#!/usr/bin/env python3
"""
Enhanced parallel processor with automatic audio compression for Whisper API
Handles files >25MB by compressing them first
"""
import os
import sys
import concurrent.futures
import time
import sqlite3
import json
import subprocess
from datetime import datetime
from typing import List, Dict
import openai
import anthropic
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EnhancedParallelProcessor:
    def __init__(self, db_path: str = "podcast_app_v2.db", max_workers: int = 8):
        self.db_path = db_path
        self.max_workers = max_workers
        self.transcription_workers = min(max_workers, 8)
        self.analysis_workers = min(max_workers // 2, 4)
        
        # Initialize API clients
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        print(f"🚀 Enhanced processor initialized:")
        print(f"   Transcription workers: {self.transcription_workers}")
        print(f"   Analysis workers: {self.analysis_workers}")
        print(f"   Audio compression: ENABLED")
    
    def get_db_connection(self):
        return sqlite3.connect(self.db_path)
    
    def compress_audio(self, input_path: str, output_path: str, target_size_mb: int = 20) -> bool:
        """Compress audio file to fit within Whisper limits using ffmpeg"""
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            
            # Get input file size and duration
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', '-show_streams', input_path
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            probe_data = json.loads(probe_result.stdout)
            
            duration = float(probe_data['format']['duration'])
            input_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            
            if input_size_mb <= target_size_mb:
                return False  # No compression needed
            
            # Calculate target bitrate (with 10% safety margin)
            target_bitrate = int((target_size_mb * 8 * 1024) / (duration * 1.1))  # kbps
            target_bitrate = max(target_bitrate, 32)  # Minimum 32kbps for speech
            
            print(f"   Compressing {input_size_mb:.1f}MB → target {target_size_mb}MB (bitrate: {target_bitrate}kbps)")
            
            # Compress audio
            compress_cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-ac', '1',  # Mono
                '-ar', '22050',  # Lower sample rate for speech
                '-b:a', f'{target_bitrate}k',
                '-f', 'mp3',
                output_path
            ]
            
            subprocess.run(compress_cmd, capture_output=True, check=True)
            
            compressed_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   ✅ Compressed to {compressed_size_mb:.1f}MB")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Compression failed: {e}")
            return False
        except FileNotFoundError:
            print(f"   ❌ ffmpeg not found. Install with: brew install ffmpeg")
            return False
    
    def download_and_prepare_audio(self, audio_url: str, episode_id: int) -> str:
        """Download and compress audio file if needed"""
        audio_dir = Path("data/audio") / f"episode_{episode_id}"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        original_path = audio_dir / "audio.mp3"
        compressed_path = audio_dir / "compressed_audio.mp3"
        
        # Use existing files if available
        if compressed_path.exists():
            size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
            if size_mb <= 25:
                return str(compressed_path)
        
        if original_path.exists():
            size_mb = os.path.getsize(original_path) / (1024 * 1024)
            if size_mb <= 25:
                return str(original_path)
        
        # Download if needed
        if not original_path.exists():
            try:
                print(f"   📥 Downloading audio for episode {episode_id}")
                response = requests.get(audio_url, stream=True)
                response.raise_for_status()
                
                with open(original_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            except Exception as e:
                print(f"   ❌ Download failed: {e}")
                return None
        
        # Check size and compress if needed
        size_mb = os.path.getsize(original_path) / (1024 * 1024)
        
        if size_mb > 25:
            print(f"   🗜️ File too large ({size_mb:.1f}MB), compressing...")
            if self.compress_audio(str(original_path), str(compressed_path), target_size_mb=20):
                return str(compressed_path)
            else:
                print(f"   ❌ Compression failed, skipping episode {episode_id}")
                return None
        
        return str(original_path)
    
    def transcribe_episode(self, episode_id: int) -> bool:
        """Transcribe a single episode with automatic compression"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get episode info
            cursor.execute("SELECT audio_url, title FROM episodes WHERE id = ?", (episode_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            audio_url, title = result
            print(f"🎧 Transcribing: {title[:60]}...")
            
            # Check if already transcribed
            cursor.execute("SELECT transcript FROM episodes WHERE id = ? AND transcript IS NOT NULL AND transcript != ''", (episode_id,))
            if cursor.fetchone():
                conn.close()
                print(f"   ✅ Already transcribed")
                return True
            
            # Download and prepare audio
            audio_path = self.download_and_prepare_audio(audio_url, episode_id)
            if not audio_path:
                conn.close()
                return False
            
            # Final size check
            size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            if size_mb > 25:
                print(f"   ❌ File still too large ({size_mb:.1f}MB), skipping")
                conn.close()
                return False
            
            # Transcribe with OpenAI Whisper
            print(f"   🤖 Sending to Whisper API ({size_mb:.1f}MB)")
            with open(audio_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # Save transcript
            cursor.execute(
                "UPDATE episodes SET transcript = ? WHERE id = ?",
                (transcript, episode_id)
            )
            conn.commit()
            conn.close()
            
            print(f"   ✅ Transcription complete ({len(transcript)} chars)")
            return True
            
        except Exception as e:
            print(f"   ❌ Transcription failed for episode {episode_id}: {e}")
            return False
    
    def analyze_episode(self, episode_id: int) -> bool:
        """Analyze a single episode using custom prompts"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get episode and podcast info
            cursor.execute("""
                SELECT e.transcript, e.title, p.id, p.name, us.custom_prompt
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.id
                LEFT JOIN user_subscriptions us ON p.id = us.podcast_id AND us.user_id = 2
                WHERE e.id = ? AND e.transcript IS NOT NULL AND e.transcript != ''
            """, (episode_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            transcript, title, podcast_id, podcast_name, custom_prompt = result
            print(f"🧠 Analyzing: {title[:60]}...")
            
            # Check if already analyzed
            cursor.execute("SELECT id FROM analysis_reports WHERE episode_id = ?", (episode_id,))
            if cursor.fetchone():
                conn.close()
                print(f"   ✅ Already analyzed")
                return True
            
            # Use custom prompt or default
            if custom_prompt:
                prompt = f"{custom_prompt}\n\nPodcast: {podcast_name}\nEpisode: {title}\n\nTranscript:\n{transcript[:15000]}"  # Limit transcript length
            else:
                prompt = f"Please analyze this podcast episode:\n\nPodcast: {podcast_name}\nEpisode: {title}\n\nTranscript:\n{transcript[:15000]}"
            
            # Analyze with Claude
            print(f"   🤖 Sending to Claude API")
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = response.content[0].text
            
            # Extract key quote (simple extraction)
            lines = analysis.split('\n')
            key_quote = ""
            for line in lines:
                if 'quote' in line.lower() and len(line) > 50:
                    key_quote = line[:500]
                    break
            
            # Save analysis
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 2, analysis, key_quote, max(1, len(analysis.split()) // 200), datetime.now()))
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ Analysis complete ({len(analysis)} chars)")
            return True
            
        except Exception as e:
            print(f"   ❌ Analysis failed for episode {episode_id}: {e}")
            return False
    
    def parallel_transcribe_episodes(self, episode_ids: List[int]) -> Dict:
        """Transcribe multiple episodes in parallel with compression"""
        print(f"🎧 Starting parallel transcription of {len(episode_ids)} episodes")
        print(f"   Using {self.transcription_workers} workers with auto-compression")
        start_time = time.time()
        
        results = {"success": [], "failed": [], "total_time": 0}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.transcription_workers) as executor:
            future_to_episode = {
                executor.submit(self.transcribe_episode, episode_id): episode_id 
                for episode_id in episode_ids
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_episode):
                episode_id = future_to_episode[future]
                completed += 1
                
                try:
                    success = future.result()
                    if success:
                        results["success"].append(episode_id)
                        print(f"✅ ({completed}/{len(episode_ids)}) Episode {episode_id} transcribed")
                    else:
                        results["failed"].append(episode_id)
                        print(f"❌ ({completed}/{len(episode_ids)}) Episode {episode_id} failed")
                except Exception as e:
                    results["failed"].append(episode_id)
                    print(f"❌ ({completed}/{len(episode_ids)}) Episode {episode_id} exception: {str(e)}")
        
        results["total_time"] = time.time() - start_time
        
        print(f"\n🎧 Transcription phase complete:")
        print(f"   ✅ Success: {len(results['success'])}")
        print(f"   ❌ Failed: {len(results['failed'])}")
        print(f"   ⏱️ Time: {results['total_time']:.1f} seconds")
        print(f"   📈 Rate: {len(results['success']) / (results['total_time'] / 3600):.1f} episodes/hour")
        
        return results
    
    def parallel_analyze_episodes(self, episode_ids: List[int]) -> Dict:
        """Analyze multiple episodes in parallel"""
        print(f"\n🧠 Starting parallel analysis of {len(episode_ids)} episodes")
        print(f"   Using {self.analysis_workers} workers with custom prompts")
        start_time = time.time()
        
        results = {"success": [], "failed": [], "total_time": 0}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.analysis_workers) as executor:
            future_to_episode = {
                executor.submit(self.analyze_episode, episode_id): episode_id 
                for episode_id in episode_ids
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_episode):
                episode_id = future_to_episode[future]
                completed += 1
                
                try:
                    success = future.result()
                    if success:
                        results["success"].append(episode_id)
                        print(f"✅ ({completed}/{len(episode_ids)}) Episode {episode_id} analyzed")
                    else:
                        results["failed"].append(episode_id)
                        print(f"❌ ({completed}/{len(episode_ids)}) Episode {episode_id} failed")
                except Exception as e:
                    results["failed"].append(episode_id)
                    print(f"❌ ({completed}/{len(episode_ids)}) Episode {episode_id} exception: {str(e)}")
                
                time.sleep(0.1)  # Rate limiting for Claude API
        
        results["total_time"] = time.time() - start_time
        
        print(f"\n🧠 Analysis phase complete:")
        print(f"   ✅ Success: {len(results['success'])}")
        print(f"   ❌ Failed: {len(results['failed'])}")
        print(f"   ⏱️ Time: {results['total_time']:.1f} seconds")
        print(f"   📈 Rate: {len(results['success']) / (results['total_time'] / 3600):.1f} episodes/hour")
        
        return results
    
    def setup_custom_prompts(self):
        """Setup custom prompts for each podcast type"""
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

        goldman_prompt = """# Goldman Sachs Exchanges Podcast Analysis Prompt

Please analyze this Goldman Sachs Exchanges podcast transcription and provide a focused investment-oriented summary using the following structure:

## Episode Overview
**Topic & Focus:** What was the main subject of this episode? Provide a comprehensive paragraph describing the central theme, market sector, or economic issue discussed, including the key questions the episode aimed to address and the primary market context or catalyst that prompted the discussion.

## Executive Summary
Provide a comprehensive paragraph covering the key market themes, investment implications, and strategic insights discussed. Include the primary arguments made, any significant market predictions or outlooks, and the most compelling takeaways for investors.

## Guest Profile
- **Name & Title:** [Guest's current role and company]
- **Expertise Area:** [Primary area of focus or specialization]

## Main Arguments & Investment Thesis
### Primary Arguments Presented:
- **Argument 1:** [Key point with supporting reasoning]
- **Argument 2:** [Key point with supporting reasoning]
- **Argument 3:** [Key point with supporting reasoning]

### Supporting Evidence & Statistics:
- List 5-8 detailed statistics, data points, or quantitative insights mentioned
- Include specific numbers, percentages, timeframes, and market metrics
- Note the source or context for each statistic when provided

## Market Themes & Trends
### Current Market Dynamics:
- Key trends shaping the discussed sector/market
- Cyclical vs. structural changes identified
- Geographic or demographic factors influencing markets

### Investment Implications:
- Asset classes or sectors expected to benefit/suffer
- Risk factors and potential market dislocations
- Timing considerations for investment decisions

## Investment Committee Discussion Points
Based on this episode's content, prepare 4-5 targeted questions for investment discussions:
- Questions about specific market segments or themes covered
- Inquiries about timing and market cycle positioning
- Risk assessment questions related to topics discussed
- Strategic allocation considerations raised by the analysis

## Key Takeaways & Action Items
### Strategic Insights:
- Most important investment lessons from the discussion
- Market positioning recommendations or considerations
- Portfolio construction implications

### Notable Market Calls:
- Specific predictions or forecasts made
- Timeline expectations for market developments
- Confidence level expressed in various predictions

## Notable Quotes
Extract the 3 most insightful quotes that capture:
- Unique market insights or investment wisdom
- Memorable frameworks or analytical approaches
- Key predictions or contrarian viewpoints

**Quote 1:** [Full quote with context]
**Quote 2:** [Full quote with context]
**Quote 3:** [Full quote with context]

---

**Analysis Instructions:**
- Focus on actionable market intelligence and investment insights
- Emphasize quantitative data and specific market calls
- Distinguish between short-term trading ideas and long-term strategic themes
- Note the guest's confidence level in various predictions or recommendations
- Highlight any unique analytical frameworks or methodologies discussed"""

        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Infrastructure podcasts
        infrastructure_podcast_ids = [3, 6, 7]  # Infrastructure Investor, Crossroads, Deal Talks
        for podcast_id in infrastructure_podcast_ids:
            cursor.execute("""
                UPDATE user_subscriptions 
                SET custom_prompt = ? 
                WHERE user_id = 2 AND podcast_id = ?
            """, (infrastructure_prompt, podcast_id))
        
        # Goldman Sachs
        cursor.execute("""
            UPDATE user_subscriptions 
            SET custom_prompt = ? 
            WHERE user_id = 2 AND podcast_id = 8
        """, (goldman_prompt,))
        
        # Global Evolution - use infrastructure prompt (energy/commodities focused)
        cursor.execute("""
            UPDATE user_subscriptions 
            SET custom_prompt = ? 
            WHERE user_id = 2 AND podcast_id = 14
        """, (infrastructure_prompt,))
        
        # Data Center Frontier - use infrastructure prompt (data center infrastructure focused)
        cursor.execute("""
            UPDATE user_subscriptions 
            SET custom_prompt = ? 
            WHERE user_id = 2 AND podcast_id = 15
        """, (infrastructure_prompt,))
        
        conn.commit()
        conn.close()
        print("✅ Custom prompts configured")
    
    def get_target_episodes(self) -> List[int]:
        """Get all target episode IDs"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        all_episodes = []
        
        # Infrastructure podcasts - all episodes
        for podcast_id in [3, 6, 7]:
            cursor.execute("""
                SELECT id FROM episodes 
                WHERE podcast_id = ? 
                ORDER BY pub_date DESC, created_at DESC
            """, (podcast_id,))
            episodes = [row[0] for row in cursor.fetchall()]
            all_episodes.extend(episodes)
        
        # Goldman Sachs - last 50 episodes
        cursor.execute("""
            SELECT id FROM episodes 
            WHERE podcast_id = 8 
            ORDER BY pub_date DESC, created_at DESC
            LIMIT 50
        """)
        episodes = [row[0] for row in cursor.fetchall()]
        all_episodes.extend(episodes)
        
        # Global Evolution - all episodes
        cursor.execute("""
            SELECT id FROM episodes 
            WHERE podcast_id = 14 
            ORDER BY pub_date DESC, created_at DESC
        """)
        episodes = [row[0] for row in cursor.fetchall()]
        all_episodes.extend(episodes)
        
        # Data Center Frontier - all episodes
        cursor.execute("""
            SELECT id FROM episodes 
            WHERE podcast_id = 15 
            ORDER BY pub_date DESC, created_at DESC
        """)
        episodes = [row[0] for row in cursor.fetchall()]
        all_episodes.extend(episodes)
        
        conn.close()
        return all_episodes
    
    def create_unified_report(self) -> str:
        """Create unified analysis report organized by date and podcast"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get all analysis reports with episode and podcast info
        cursor.execute("""
            SELECT 
                ar.analysis_result,
                ar.key_quote,
                ar.created_at,
                e.title as episode_title,
                e.pub_date,
                p.name as podcast_name
            FROM analysis_reports ar
            JOIN episodes e ON ar.episode_id = e.id
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE p.id IN (3, 6, 7, 8, 14, 15) AND ar.user_id = 2
            ORDER BY e.pub_date DESC, p.name
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # Create unified report
        report = f"""# Infrastructure & Finance Podcast Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Episodes Analyzed: {len(results)}

---

"""
        
        current_date = None
        for result in results:
            analysis, quote, created_at, episode_title, pub_date, podcast_name = result
            
            # Group by publication date
            if pub_date != current_date:
                current_date = pub_date
                report += f"\n## {pub_date}\n\n"
            
            report += f"### {podcast_name}: {episode_title}\n\n"
            report += f"**Analysis Date:** {created_at}\n\n"
            
            if quote:
                report += f"**Key Quote:** {quote}\n\n"
            
            report += f"{analysis}\n\n"
            report += "---\n\n"
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"unified_infrastructure_analysis_{timestamp}.md"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Unified report saved: {filepath}")
        return filepath
    
    def run_full_processing(self):
        """Execute complete processing pipeline with compression"""
        print("🚀 Starting Enhanced Parallel Processing with Audio Compression")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Setup prompts
        print("\n📝 Step 1: Setting up custom prompts...")
        self.setup_custom_prompts()
        
        # Get target episodes
        print("\n📊 Step 2: Getting target episodes...")
        target_episodes = self.get_target_episodes()
        print(f"   Target episodes: {len(target_episodes)}")
        
        # Process episodes
        print(f"\n🎧 Step 3: Processing {len(target_episodes)} episodes...")
        
        # Transcription with compression
        transcription_results = self.parallel_transcribe_episodes(target_episodes)
        
        # Analysis (only successful transcriptions)
        if transcription_results["success"]:
            analysis_results = self.parallel_analyze_episodes(transcription_results["success"])
        else:
            analysis_results = {"success": [], "failed": []}
        
        # Create unified report
        print(f"\n📄 Step 4: Creating unified analysis report...")
        report_path = self.create_unified_report()
        
        # Create summary
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds() / 60
        
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_time_minutes": total_time,
            "target_episodes": len(target_episodes),
            "transcribed": len(transcription_results["success"]),
            "analyzed": len(analysis_results["success"]),
            "failed_transcription": len(transcription_results["failed"]),
            "failed_analysis": len(analysis_results["failed"]),
            "report_file": report_path
        }
        
        print(f"\n🎉 ENHANCED PROCESSING COMPLETE!")
        print(f"   Total time: {total_time:.1f} minutes")
        print(f"   Episodes transcribed: {len(transcription_results['success'])}/{len(target_episodes)} ({len(transcription_results['success'])/len(target_episodes)*100:.1f}%)")
        print(f"   Episodes analyzed: {len(analysis_results['success'])}/{len(target_episodes)} ({len(analysis_results['success'])/len(target_episodes)*100:.1f}%)")
        print(f"   Report file: {report_path}")
        
        # Save summary
        summary_file = f"enhanced_processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   Summary saved: {summary_file}")
        
        return summary, report_path

def main():
    processor = EnhancedParallelProcessor()
    processor.run_full_processing()

if __name__ == "__main__":
    main()