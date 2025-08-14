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
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any

class EnhancedPodcastSystem:
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

if __name__ == "__main__":
    import sys
    
    system = EnhancedPodcastSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        system.status_check()
    else:
        system.run_daily_automation()