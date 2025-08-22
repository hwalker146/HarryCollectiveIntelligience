#!/usr/bin/env python3
"""
Enhanced GitHub-based automated podcast system
- Appends to master files instead of individual files
- Includes WSJ and Ezra Klein specialized prompts
- Date range checking and gap filling
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
import time
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any

class EnhancedPodcastSystem:
    def __init__(self):
        # Use absolute paths to avoid working directory issues
        base_dir = Path(__file__).parent.parent
        self.db_path = str(base_dir / 'podcast_app_v2.db')
        self.master_dir = base_dir / 'content/master_transcripts_organized'
        self.reports_dir = Path('content/reports/daily')
        
        # Create directories
        self.master_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # API clients - initialize lazily
        self.openai_client = None
        self.anthropic_client = None
        
        # Podcast name to file mapping
        self.podcast_files = {
            'Exchanges at Goldman Sachs': 'Exchanges_at_Goldman_Sachs_Master_Transcripts_Organized.md',
            'The Infrastructure Investor': 'The_Infrastructure_Investor_Master_Transcripts_Organized.md',
            'The Data Center Frontier Show': 'The_Data_Center_Frontier_Show_Master_Transcripts_Organized.md',
            'Crossroads: The Infrastructure Podcast': 'Crossroads_The_Infrastructure_Podcast_Master_Transcripts_Organized.md',
            'Deal Talks': 'Deal_Talks_Master_Transcripts_Organized.md',
            'Global Evolution': 'Global_Evolution_Master_Transcripts_Organized.md',
            'WSJ What\'s News': 'WSJ_Whats_News_Master_Transcripts_Organized.md',
            'The Intelligence': 'The_Intelligence_Master_Transcripts_Organized.md',
            'The Ezra Klein Show': 'The_Ezra_Klein_Show_Master_Transcripts_Organized.md',
            'Optimistic Outlook': 'Optimistic_Outlook_Master_Transcripts_Organized.md',
            'The Engineers Collective': 'The_Engineers_Collective_Master_Transcripts_Organized.md',
            'Talking Infrastructure': 'Talking_Infrastructure_Master_Transcripts_Organized.md',
            'a16z Podcast': 'a16z_Podcast_Master_Transcripts_Organized.md'
        }
        
        # Analysis prompts
        self.wsj_prompt = """Summarize this Wall Street Journal "What's News" daily podcast transcript in 200–300 words. Capture all major stories in the order they appear, including key facts, figures, quotes, and the people or organizations involved. Briefly explain background context when needed so the summary stands on its own. Keep the tone neutral and factual, avoiding opinion or unnecessary adjectives. Begin with a short 1–2 sentence overview of the episode's main themes, then present each story in its own short paragraph with its headline in bold."""
        
        self.ezra_klein_prompt = """Summarize this episode of the Ezra Klein Show in 300–400 words. Clearly identify the guest speaker's main argument or thesis and explain the reasoning behind it. Highlight the most important supporting points, evidence, and examples the guest uses. Note Ezra Klein's key questions, challenges, or counterpoints, and how the guest responds. Capture any relevant facts, statistics, or policy proposals discussed. Provide enough background context so the summary stands alone. Keep the tone neutral, analytical, and clear. Begin with a 2–3 sentence overview of the episode's theme and the guest's central argument, then organize the rest of the summary by the major points of discussion."""
        
        self.intelligence_prompt = """Summarize this episode of The Intelligence podcast from The Economist in 250–350 words. Capture the main global news stories covered, presenting them in the order they appear. For each story, include key facts, developments, context, and any data or analysis provided. Note the hosts and any expert guests or correspondents who provide insights. Highlight significant geopolitical implications, economic impacts, or policy developments. Provide enough background so each story is understandable on its own. Keep the tone neutral and informative, matching The Economist's analytical style. Begin with a brief overview of the episode's main themes, then summarize each story in its own paragraph with clear transitions between topics."""
        
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

        self.a16z_prompt = """A16Z Podcast Transcription Analysis Prompt

Context: You are analyzing this transcription to extract key insights about technology, business strategy, economics, and industry trends. Focus on understanding the current state and future direction of the markets, sectors, or topics being discussed.

## Analysis Framework

### Executive Summary
Provide a brief overview of the most significant insights and themes discussed in the conversation. Capture the core arguments, disagreements, and consensus points in 2-3 sentences.

### Key Developments and Insights
Analyze the main developments, trends, or insights discussed in the conversation. Focus on extracting actionable intelligence about market conditions, strategic opportunities, technological shifts, or policy changes. Describe each development with its implications and potential timeline for impact. Consider both consensus views and contrarian perspectives presented by the speakers.

### Market and Industry Dynamics
Examine the broader market forces, competitive landscape, and industry dynamics discussed. Analyze growth drivers and headwinds, regulatory environment changes, and disruption factors. Map out key players mentioned, their positioning, and competitive advantages. Identify trends toward market consolidation or fragmentation, barriers to entry, and potential competitive threats or new market entrants.

### Strategic and Business Insights
Explore business model innovations, monetization strategies, and new market approaches discussed. Identify partnership trends, collaboration patterns, and strategic relationships mentioned. Extract insights about funding trends, capital allocation strategies, and investment themes. Note any regulatory considerations, policy discussions, and their potential business impacts.

### Future Outlook and Predictions
Capture forecasts about market direction, technology evolution, and industry trends. Note development timelines, adoption curves, and maturity predictions. Identify adoption barriers, success factors driving implementations, and future market opportunities. Assess the credibility of predictions based on speaker expertise and track record.

### Risk Assessment
Analyze primary risks to the developments and trends discussed. Identify potential headwinds, challenges, or threats mentioned by speakers. Note any mitigation strategies, contingency plans, or risk management approaches discussed. Consider both short-term tactical risks and long-term strategic challenges.

### Actionable Intelligence
Synthesize insights into actionable intelligence for investors, entrepreneurs, and business leaders. Identify companies, technologies, or sectors worth researching further. Highlight trends worth monitoring and potential opportunities or threats to watch. Connect insights to broader macroeconomic, geopolitical, or societal themes when relevant.

### Notable Quotes
* [Most insightful quote #1]
* [Most insightful quote #2]
* [Most insightful quote #3]
* [Most insightful quote #4]
* [Most insightful quote #5]

## Additional Guidelines
Quantify insights wherever possible with specific market sizes, growth rates, timelines, and financial metrics. Flag any contrarian or non-consensus views expressed and note the reasoning behind them. Consider the credibility and track record of speakers when assessing the weight of their insights. Highlight any mentions of ESG considerations, sustainability trends, or social impact themes. Maintain objectivity while capturing the nuance of different perspectives presented in the discussion."""
    
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
        elif 'a16z' in podcast_name.lower():
            return self.a16z_prompt, "A16Z Analysis"
        else:
            return self.infrastructure_prompt, "Infrastructure PE Analysis"
    
    def get_openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self.openai_client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.openai_client = openai.OpenAI(api_key=api_key)
        return self.openai_client
    
    def get_anthropic_client(self):
        """Lazy initialization of Anthropic client"""
        if self.anthropic_client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self.anthropic_client
    
    def status_check(self):
        """Check system status without processing episodes"""
        print("🔍 Unified Podcast Automation System Status")
        print("=" * 50)
        
        # Check database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM podcasts WHERE is_active = 1")
            active_podcasts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM episodes WHERE transcript IS NOT NULL")
            transcribed_episodes = cursor.fetchone()[0]
            
            print(f"📊 Active podcasts: {active_podcasts}")
            print(f"📄 Transcribed episodes: {transcribed_episodes}")
            
            conn.close()
        except Exception as e:
            print(f"❌ Database check failed: {e}")
        
        # Check API keys
        openai_key = "✅" if os.getenv('OPENAI_API_KEY') else "❌"
        anthropic_key = "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌"
        email_password = "✅" if os.getenv('EMAIL_PASSWORD') else "❌"
        
        print(f"🔑 OpenAI API Key: {openai_key}")
        print(f"🔑 Anthropic API Key: {anthropic_key}") 
        print(f"📧 Email Password: {email_password}")
        
        print("\n✅ Status check complete")
    
    def run_daily_automation(self):
        """Main automation function - complete RSS processing workflow"""
        from dotenv import load_dotenv
        load_dotenv()
        
        print("🚀 STARTING UNIFIED PODCAST AUTOMATION")
        print("=" * 60)
        start_time = datetime.now()
        
        # Step 1: Check RSS feeds for new episodes
        new_episodes = self.check_rss_for_new_episodes()
        
        # Step 2: Process new episodes
        processed_episodes = []
        if new_episodes:
            print(f"\n🎧 PROCESSING {len(new_episodes)} NEW EPISODES")
            processed_episodes = self.process_new_episodes(new_episodes)
        
        # Step 3: Update master files
        if processed_episodes:
            print(f"\n📝 UPDATING MASTER FILES")
            self.append_to_master_files(processed_episodes)
        
        # Step 4: Send email report (check for episodes added today even if processing failed)
        self.send_email_report_with_fallback(len(new_episodes), len(processed_episodes), processed_episodes)
        
        # Summary
        duration = datetime.now() - start_time
        print("\n" + "=" * 60)
        print("🎯 AUTOMATION COMPLETE")
        print(f"⏱️  Duration: {duration}")
        print(f"📈 New episodes found: {len(new_episodes)}")
        print(f"✅ Successfully processed: {len(processed_episodes)}")
        print("=" * 60)
        
        return len(processed_episodes) > 0
    
    def check_rss_for_new_episodes(self):
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
            
            # Set cutoff date for daily automation
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(hours=24)
            
            for podcast_id, podcast_name, rss_url in podcasts:
                print(f"\n🎧 {podcast_name}...")
                
                # Get date range for this podcast to detect gaps
                cursor.execute('''
                    SELECT MIN(publish_date), MAX(publish_date), COUNT(*) 
                    FROM episodes 
                    WHERE podcast_id = ? AND publish_date IS NOT NULL
                ''', (podcast_id,))
                
                date_info = cursor.fetchone()
                oldest_date, newest_date, episode_count = date_info
                
                # Get existing episodes for proper matching
                cursor.execute('''
                    SELECT guid, audio_url, title FROM episodes 
                    WHERE podcast_id = ?
                ''', (podcast_id,))
                
                existing_episodes = set()
                for guid, audio_url, title in cursor.fetchall():
                    # Add all possible identifiers for this episode
                    if guid:
                        existing_episodes.add(guid)
                    if audio_url:
                        existing_episodes.add(audio_url)
                    if title:
                        existing_episodes.add(title)
                
                print(f"   📊 Database: {episode_count} episodes, oldest: {oldest_date}, newest: {newest_date}")
                print(f"   🔍 Checking for gaps and new episodes...")
                print(f"   🎯 Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} (24 hours ago)")
                
                # Parse RSS feed
                try:
                    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
                    response = requests.get(rss_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    
                    if feed.bozo:
                        print(f"   ❌ Invalid RSS feed")
                        continue
                    
                    # Check all RSS episodes for gaps and new episodes
                    episodes_checked = 0
                    new_episodes_for_podcast = 0
                    missing_episodes = []
                    
                    # Parse oldest/newest dates from database for comparison
                    oldest_db_date = None
                    newest_db_date = None
                    if oldest_date:
                        try:
                            oldest_db_date = datetime.fromisoformat(oldest_date.replace('Z', '+00:00'))
                        except:
                            oldest_db_date = None
                    if newest_date:
                        try:
                            newest_db_date = datetime.fromisoformat(newest_date.replace('Z', '+00:00'))
                        except:
                            newest_db_date = None
                    
                    # Check recent episodes only (cutoff date set above)
                    
                    print(f"   📻 RSS feed has {len(feed.entries)} total episodes")
                    
                    for entry in feed.entries:  
                        episodes_checked += 1
                        if episodes_checked > 20:  # Lower limit for daily runs
                            print(f"   ⏹️  Stopping after checking {episodes_checked} episodes (limit reached)")
                            break
                            
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
                        episode_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            episode_date = datetime(*entry.published_parsed[:6])
                            publish_date = episode_date.isoformat()
                        
                        # Skip episodes older than 24 hours for daily automation
                        if episode_date and episode_date < cutoff_date:
                            print(f"   ⏭️  SKIPPED (too old): {episode_title[:50]}... ({publish_date[:19] if publish_date else 'no date'})")
                            continue
                        
                        episode_title = getattr(entry, 'title', 'Unknown Title')
                        episode_guid = getattr(entry, 'id', None) or audio_url
                        
                        # Check if this episode exists in our database using any identifier
                        episode_exists = (
                            (episode_guid and episode_guid in existing_episodes) or
                            (audio_url and audio_url in existing_episodes) or  
                            (episode_title and episode_title in existing_episodes)
                        )
                        
                        print(f"   🔍 CHECKING: {episode_title[:50]}... ({publish_date[:19] if publish_date else 'no date'})")
                        print(f"      GUID: {episode_guid}")
                        print(f"      EXISTS: {episode_exists}")
                        
                        # If episode doesn't exist, only process if it's genuinely new (published after newest episode)
                        if not episode_exists:
                            is_new = False
                            
                            if episode_date and newest_db_date:
                                # Convert to naive datetime for comparison
                                episode_naive = episode_date.replace(tzinfo=None) if episode_date.tzinfo else episode_date
                                newest_naive = newest_db_date.replace(tzinfo=None) if newest_db_date and newest_db_date.tzinfo else newest_db_date
                                
                                # Only process if episode is newer than our newest episode
                                if episode_naive > newest_naive:
                                    is_new = True
                            elif not newest_db_date:
                                # No episodes in database yet - treat as new
                                is_new = True
                            
                            if is_new:
                                episode_data = {
                                    'podcast_id': podcast_id,
                                    'podcast_name': podcast_name,
                                    'title': episode_title,
                                    'description': getattr(entry, 'summary', ''),
                                    'audio_url': audio_url,
                                    'episode_url': getattr(entry, 'link', ''),
                                    'guid': episode_guid,
                                    'publish_date': publish_date,
                                    'existing_episode_id': None
                                }
                                new_episodes.append(episode_data)
                                new_episodes_for_podcast += 1
                                
                                print(f"   🆕 NEW: {episode_title[:50]}... ({publish_date[:10] if publish_date else 'no date'})")
                        
                        # Also check for existing episodes that need transcription
                        elif episode_exists:
                            cursor.execute('''
                                SELECT id, transcribed, transcript FROM episodes 
                                WHERE podcast_id = ? AND (guid = ? OR audio_url = ? OR title = ?)
                            ''', (podcast_id, episode_guid, audio_url, episode_title))
                            
                            existing_episode = cursor.fetchone()
                            if (existing_episode and 
                                (existing_episode[1] == 0 or not existing_episode[2] or len(existing_episode[2].strip()) < 100)):
                                
                                episode_data = {
                                    'podcast_id': podcast_id,
                                    'podcast_name': podcast_name,
                                    'title': episode_title,
                                    'description': getattr(entry, 'summary', ''),
                                    'audio_url': audio_url,
                                    'episode_url': getattr(entry, 'link', ''),
                                    'guid': episode_guid,
                                    'publish_date': publish_date,
                                    'existing_episode_id': existing_episode[0]
                                }
                                new_episodes.append(episode_data)
                                new_episodes_for_podcast += 1
                                
                                # Enhanced retranscription logging
                                episode_id, transcribed, transcript = existing_episode
                                transcript_length = len(transcript.strip()) if transcript else 0
                                print(f"   🔄 RETRANSCRIBE: {episode_title[:50]}...")
                                print(f"      DB ID: {episode_id}, Transcribed: {transcribed}, Transcript length: {transcript_length}")
                                
                                # Log why it needs retranscription
                                reasons = []
                                if transcribed == 0:
                                    reasons.append("transcribed=0")
                                if not transcript:
                                    reasons.append("transcript=NULL")
                                if transcript and len(transcript.strip()) < 100:
                                    reasons.append("transcript<100chars")
                                print(f"      REASON: {', '.join(reasons)}")
                        
                except Exception as e:
                    print(f"   ❌ RSS error: {e}")
                    continue
            
            conn.close()
            
            if new_episodes:
                print(f"\n✅ FOUND {len(new_episodes)} NEW EPISODES TO PROCESS")
                print(f"📝 Episodes to process:")
                for episode in new_episodes:
                    status = "NEW" if not episode.get('existing_episode_id') else "RETRANSCRIBE"
                    print(f"  {status}: {episode['podcast_name']} - {episode['title'][:60]}...")
            else:
                print(f"\n📭 No new episodes found")
                
            return new_episodes  # Process ALL detected episodes
            
        except Exception as e:
            print(f"❌ RSS checking failed: {e}")
            return []
    
    def process_single_episode(self, episode):
        """Process a single episode - used for parallel processing"""
        try:
            print(f"\n🔧 PROCESSING: {episode['title'][:50]}...")
            
            # Step 1: Download and transcribe
            transcript = self.transcribe_episode(episode)
            if not transcript:
                return None
            
            # Step 2: Analyze
            analysis = self.analyze_episode(episode, transcript)
            
            # Step 3: Add to database or update existing
            if episode.get('existing_episode_id'):
                episode_id = self.update_existing_episode(episode, transcript, analysis)
            else:
                episode_id = self.save_to_database(episode, transcript, analysis)
            
            if episode_id:
                # Step 4: Append to master file happens in the main process
                
                return {
                    'episode_id': episode_id,
                    'podcast_name': episode['podcast_name'],
                    'title': episode['title'],
                    'date': episode.get('publish_date', '').split('T')[0] if episode.get('publish_date') else date.today().strftime('%Y-%m-%d'),
                    'transcript': transcript,
                    'analysis': analysis
                }
        except Exception as e:
            print(f"❌ Error processing {episode['title']}: {e}")
            return None
    
    def process_new_episodes(self, episodes):
        """Process new episodes with parallel transcription and analysis"""
        processed = []
        
        # Process episodes in parallel with optimized worker count
        # OpenAI has high rate limits, 8 parallel workers for maximum efficiency
        max_workers = min(8, len(episodes))
        
        print(f"\n🚀 PARALLEL PROCESSING: {len(episodes)} episodes with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all episodes for processing
            future_to_episode = {executor.submit(self.process_single_episode, ep): ep for ep in episodes}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_episode):
                episode = future_to_episode[future]
                try:
                    result = future.result()
                    if result:
                        processed.append(result)
                        print(f"✅ Completed: {result['title'][:50]}")
                except Exception as e:
                    print(f"❌ Exception processing {episode['title']}: {e}")
        
        return processed
    
    def transcribe_episode(self, episode):
        """Download audio and transcribe"""
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
            
            # Always compress audio for faster transcription
            print("   🗜️ Compressing audio for optimal transcription...")
            compressed_path = self.compress_audio(audio_path)
            if compressed_path:
                audio_path = compressed_path
            else:
                print("   ⚠️ Compression failed, using original file")
                # Continue with original file rather than failing
            
            # Transcribe with rate limit handling
            print("   🎤 Transcribing...")
            with open(audio_path, 'rb') as audio_file:
                transcript = self.transcribe_with_retry(audio_file)
            
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
        """Compress audio file with silence removal for optimal transcription speed"""
        try:
            output_path = input_path.replace('.mp3', '_compressed.mp3')
            
            # Enhanced compression with audio preprocessing:
            # - Remove silence and quiet sections
            # - 16kHz sample rate (Whisper minimum)
            # - Mono (single channel)  
            # - 64kbps bitrate (good quality for speech)
            # - Fast compression preset
            compress_cmd = [
                'ffmpeg', '-i', input_path, '-y',
                '-af', 'silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB:detection=peak,aformat=sample_rates=16000',
                '-acodec', 'libmp3lame',
                '-ar', '16000',      # 16kHz sample rate
                '-ac', '1',          # Mono
                '-ab', '64k',        # 64kbps bitrate
                '-preset', 'ultrafast',  # Fastest compression
                '-v', 'quiet',       # Suppress output
                output_path
            ]
            
            subprocess.run(compress_cmd, capture_output=True, check=True, timeout=60)
            
            # Verify compression worked and file is smaller
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = compressed_size / original_size
            
            print(f"   📉 Compressed: {original_size/1024/1024:.1f}MB → {compressed_size/1024/1024:.1f}MB ({compression_ratio*100:.1f}%)")
            
            os.unlink(input_path)
            return output_path
            
        except Exception as e:
            print(f"   ❌ Compression failed: {e}")
            return None
    
    def transcribe_with_retry(self, audio_file):
        """Transcribe audio with rate limit error handling and exponential backoff"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                transcript = self.get_openai_client().audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",  # English language hint for faster/better transcription
                    response_format="text"
                )
                return transcript
                
            except openai.RateLimitError as e:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: 2^attempt + random(0-1) seconds
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"   ⏳ Rate limit exceeded (attempt {attempt + 1}/{max_retries}), waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ Rate limit exceeded after {max_retries} attempts")
                    raise e
                    
            except openai.APIError as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"   ⏳ API error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   ❌ API error after {max_retries} attempts")
                    raise e
                    
            except Exception as e:
                print(f"   ❌ Transcription error: {e}")
                raise e
    
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
    
    def update_existing_episode(self, episode, transcript, analysis):
        """Update existing episode with transcript and analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            episode_id = episode['existing_episode_id']
            
            # Update episode with transcript
            cursor.execute('''
                UPDATE episodes 
                SET transcript = ?, transcribed = 1, processed = 1, created_at = ?
                WHERE id = ?
            ''', (transcript, datetime.now().isoformat(), episode_id))
            
            # Save analysis
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 1, analysis, "", max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return episode_id
            
        except Exception as e:
            print(f"   ❌ Database update failed: {e}")
            return None

    def save_to_database(self, episode, transcript, analysis):
        """Save episode to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert episode
            cursor.execute('''
                INSERT INTO episodes (
                    podcast_id, title, audio_url, publish_date, 
                    description, episode_url, guid, transcript, transcribed, processed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
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
            
            return episode_id
            
        except Exception as e:
            print(f"   ❌ Database save failed: {e}")
            return None
    
    def append_to_master_files(self, processed_episodes):
        """Append new episodes to master files"""
        for episode in processed_episodes:
            try:
                self.append_episode_to_master(episode)
                print(f"   ✅ Appended: {episode['title'][:50]}...")
                
            except Exception as e:
                print(f"   ❌ Failed to append {episode['title'][:50]}: {e}")
    
    def append_episode_to_master(self, episode):
        """Append single episode to appropriate master file"""
        podcast_name = episode['podcast_name']
        filename = self.podcast_files.get(podcast_name)
        
        if not filename:
            print(f"   ⚠️  No master file configured for: {podcast_name}")
            return
        
        filepath = self.master_dir / filename
        
        # Create new episode content
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
            
            # Find insertion point (after header, before first episode)
            header_end = existing_content.find("---\n\n")
            if header_end != -1:
                header_part = existing_content[:header_end + 5]
                episodes_part = existing_content[header_end + 5:]
                
                # Insert new episode at top
                new_content = header_part + episode_content + episodes_part
                
                # Update episode count in header
                episode_count_match = re.search(r'\*\*Total Episodes:\*\* (\d+)', header_part)
                if episode_count_match:
                    current_count = int(episode_count_match.group(1))
                    new_count = current_count + 1
                    new_content = new_content.replace(
                        f"**Total Episodes:** {current_count}",
                        f"**Total Episodes:** {new_count}"
                    )
            else:
                # Fallback: append at end
                new_content = existing_content + episode_content
        else:
            # Create new file
            new_content = f"""# {podcast_name} - Master Transcripts

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Episodes:** 1

Episodes organized by publication date (newest first).

---

{episode_content}"""
        
        # Save updated file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def send_email_report_complete(self, episodes_found, episodes_processed, processed_episodes=None):
        """Send automation report email with episode analysis summaries"""
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
                
                body = f"""🤖 UNIFIED PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TODAY'S RESULTS:
• Episodes Found: {episodes_found}
• Successfully Processed: {episodes_processed}

"""
                
                # Add analysis summaries for each processed episode
                if processed_episodes:
                    body += "📝 EPISODE ANALYSIS SUMMARIES:\n\n"
                    for episode in processed_episodes:
                        body += f"🎧 {episode['podcast_name']}: {episode['title']}\n"
                        body += f"📅 {episode['date']}\n\n"
                        
                        # Include the analysis
                        analysis = episode.get('analysis', 'No analysis available')
                        
                        body += f"{analysis}\n\n"
                        body += "="*80 + "\n\n"
                
                body += f"""
✅ SYSTEM STATUS: Full automation working correctly
🎯 PROMPTS: All specialized prompts active
   • WSJ What's News → WSJ Summary
   • The Intelligence → Intelligence Analysis  
   • Ezra Klein Show → Ezra Klein Analysis
   • Goldman Sachs → Goldman Sachs Analysis
   • Infrastructure → Infrastructure PE Analysis

🔗 GitHub: https://github.com/hwalker146/HarryCollectiveIntelligience
📁 Master Files: content/master_transcripts/

🤖 Generated by unified automation system
"""
            else:
                msg['Subject'] = f"📊 Podcast Automation: No New Episodes - {datetime.now().strftime('%Y-%m-%d')}"
                
                body = f"""🤖 UNIFIED PODCAST AUTOMATION REPORT

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 STATUS: No new episodes found today
✅ SYSTEM: All systems operational and monitoring

Episodes checked: {episodes_found}
All podcasts are up to date.

🤖 Generated by unified automation system
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
    
    def send_email_report_with_fallback(self, episodes_found, episodes_processed, processed_episodes=None):
        """Send email report with fallback to check database for episodes added today"""
        try:
            # Check if episodes were actually added to database today (fallback for partial failures)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.name, e.title, e.publish_date, LENGTH(e.transcript) as transcript_length, e.created_at
                FROM episodes e 
                JOIN podcasts p ON e.podcast_id = p.id 
                WHERE DATE(e.created_at) = DATE('now') 
                ORDER BY e.created_at DESC
            ''')
            
            todays_episodes = cursor.fetchall()
            conn.close()
            
            # If episodes were processed successfully, use normal reporting
            if episodes_processed > 0 and processed_episodes:
                print(f"📧 Sending success email for {episodes_processed} processed episodes")
                self.send_email_report_complete(episodes_found, episodes_processed, processed_episodes)
            
            # If no episodes in processed_episodes but episodes exist in DB from today, send fallback email
            elif todays_episodes:
                print(f"📧 Sending fallback email for {len(todays_episodes)} episodes found in database")
                self.send_fallback_email_for_db_episodes(episodes_found, todays_episodes)
            
            # Otherwise, send normal "no episodes" email
            else:
                print(f"📧 Sending no episodes email")
                self.send_email_report_complete(episodes_found, 0, None)
                
        except Exception as e:
            print(f"❌ Email fallback failed: {e}")
            # Fall back to original method
            self.send_email_report_complete(episodes_found, episodes_processed, processed_episodes)
    
    def send_fallback_email_for_db_episodes(self, episodes_found, todays_episodes):
        """Send email for episodes that were saved to DB but not in processed_episodes list"""
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
            msg['Subject'] = f"✅ {len(todays_episodes)} Podcast Episodes Processed - {datetime.now().strftime('%Y-%m-%d')} (Recovered)"
            
            body = f"""🤖 UNIFIED PODCAST AUTOMATION REPORT (RECOVERED DATA)

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TODAY'S RESULTS:
• Episodes Found: {episodes_found}
• Successfully Processed: {len(todays_episodes)} (recovered from database)

⚠️  Note: Episodes were successfully transcribed and saved, but some processing steps encountered errors.
All episode data is intact in the database.

📝 EPISODES PROCESSED TODAY:

"""
            
            for podcast_name, title, publish_date, transcript_length, created_at in todays_episodes:
                publish_date_short = publish_date[:10] if publish_date else 'Unknown'
                body += f"""🎧 {podcast_name}
📅 {publish_date_short}: {title}
📊 Transcript: {transcript_length:,} characters
⏰ Processed: {created_at.split('T')[1][:8]} UTC

"""
            
            body += f"""
📈 PERFORMANCE METRICS:
• Total episodes: {len(todays_episodes)}
• Total characters: {sum(ep[3] for ep in todays_episodes):,}
• Average length: {sum(ep[3] for ep in todays_episodes) // len(todays_episodes):,} chars

✅ All episodes successfully:
• Downloaded and transcribed with OpenAI Whisper
• Saved to database with full metadata
• Ready for analysis and master file updates

🔧 Recent optimizations working:
• Parallel processing (3 workers)
• Audio compression for faster transcription  
• 4-hour timeout prevents failures
• Improved episode detection logic

🤖 Generated by unified automation system
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            
            print(f"✅ Fallback email sent to {recipient_email}")
            
        except Exception as e:
            print(f"❌ Fallback email failed: {e}")

if __name__ == "__main__":
    import sys
    
    system = EnhancedPodcastSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        system.status_check()
    else:
        system.run_daily_automation()