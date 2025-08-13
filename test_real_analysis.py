#!/usr/bin/env python3
"""
Test analysis with real prompts on real transcript
"""
import os
import sqlite3
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_real_analysis():
    """Test analysis on the real transcript we just created"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get the Goldman Sachs episode we just transcribed
    cursor.execute("""
        SELECT e.id, e.title, e.transcript, p.name
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.id = 5062
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ Episode not found")
        return False
    
    episode_id, title, transcript, podcast_name = result
    
    print(f"🧠 Testing REAL analysis on: {title}")
    print(f"📊 Transcript length: {len(transcript)} characters")
    print(f"📡 Podcast: {podcast_name}")
    
    # Your actual Goldman Sachs prompt
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
**Quote 4:** "[Full quote]" - Market significance and implications
**Quote 5:** "[Full quote]" - Market significance and implications

**Analysis Instructions:**
- Prioritize quantitative data and specific market calls
- Note confidence levels and timeframes for predictions
- Distinguish between short-term tactics and long-term strategy
- Highlight any proprietary Goldman Sachs research or data
- Focus on actionable market intelligence"""

    user_prompt = f"""Podcast: {podcast_name}
Episode: {title}

FULL TRANSCRIPT:
{transcript}"""
    
    print("🤖 Running analysis with GPT-4...")
    
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
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
        
        # Extract key quotes
        lines = analysis.split('\n')
        quotes_found = 0
        for line in lines:
            if 'Quote' in line and ':' in line and len(line) > 50:
                quotes_found += 1
                print(f"💬 Found quote {quotes_found}: {line[:100]}...")
        
        print(f"📊 Key quotes extracted: {quotes_found}")
        
        # Show first part of analysis
        print(f"\n📄 Analysis preview:")
        print(analysis[:500] + "...")
        
        # Delete old analysis and save new one
        cursor.execute("DELETE FROM analysis_reports WHERE episode_id = ?", (episode_id,))
        
        # Extract first key quote
        key_quote = ""
        for line in lines:
            if 'Quote 1:' in line and len(line) > 20:
                key_quote = line[:400]
                break
        
        cursor.execute("""
            INSERT INTO analysis_reports (episode_id, user_id, analysis_result, key_quote, reading_time_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (episode_id, 1, analysis, key_quote, max(1, len(analysis.split()) // 200), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ REAL ANALYSIS SUCCESSFUL - saved to database")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    success = test_real_analysis()
    if success:
        print("\n🎉 ANALYSIS PIPELINE IS WORKING WITH REAL PROMPTS!")
    else:
        print("\n💥 ANALYSIS PIPELINE NEEDS FIXING!")