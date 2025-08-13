#!/usr/bin/env python3
"""
Working analysis processor that handles full transcripts and uses OpenAI instead of Anthropic
"""
import os
import sqlite3
import openai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_with_openai():
    """Run analysis on all transcribed episodes using OpenAI"""
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Detailed infrastructure analysis prompt
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

    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get episodes that need analysis - focusing on recent ones first
    cursor.execute("""
        SELECT e.id, e.title, e.transcript, p.id as podcast_id, p.name as podcast_name
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.podcast_id IN (3, 6, 7, 8, 10) 
        AND e.transcript IS NOT NULL AND e.transcript != ''
        AND LENGTH(e.transcript) > 1000
        AND e.id NOT IN (SELECT episode_id FROM analysis_reports WHERE episode_id IS NOT NULL)
        ORDER BY e.publish_date DESC
        LIMIT 20
    """)
    
    episodes_to_analyze = cursor.fetchall()
    print(f"🧠 Found {len(episodes_to_analyze)} episodes needing analysis")
    
    successful = 0
    failed = 0
    
    for episode_id, title, transcript, podcast_id, podcast_name in episodes_to_analyze:
        try:
            print(f"🧠 Analyzing: {title[:60]}... (Length: {len(transcript)} chars)")
            
            # Choose prompt based on podcast
            if podcast_id == 8:  # Goldman Sachs
                system_prompt = goldman_prompt
            else:  # Infrastructure podcasts  
                system_prompt = infrastructure_prompt
            
            user_prompt = f"""Podcast: {podcast_name}
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
            
            # Analyze with GPT-4 - it can handle much longer contexts
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for speed, can upgrade to gpt-4o for better quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            # Extract key quote
            lines = analysis.split('\n')
            key_quote = ""
            for line in lines:
                if 'Quote 1:' in line or 'quote' in line.lower():
                    key_quote = line[:500]
                    break
            
            # Save analysis
            cursor.execute("""
                INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (episode_id, 2, analysis, key_quote, max(1, len(analysis.split()) // 200), datetime.now()))
            
            conn.commit()
            successful += 1
            print(f"✅ Episode {episode_id} analyzed successfully")
            
        except Exception as e:
            failed += 1
            print(f"❌ Episode {episode_id} analysis failed: {str(e)}")
    
    conn.close()
    
    print(f"\n🎉 ANALYSIS BATCH COMPLETE:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    return successful, failed

if __name__ == "__main__":
    analyze_with_openai()