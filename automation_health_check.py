#!/usr/bin/env python3
"""
Comprehensive automation health check
"""
import sqlite3
import os
from datetime import datetime, date

def automation_health_check():
    """Perform comprehensive health check of automation system"""
    print("🏥 AUTOMATION SYSTEM HEALTH CHECK")
    print("=" * 50)
    
    # 1. Database Health
    print("\n🗄️  DATABASE HEALTH:")
    db_path = 'podcast_app_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total episodes
    cursor.execute("SELECT COUNT(*) FROM episodes")
    total_episodes = cursor.fetchone()[0]
    print(f"   📊 Total episodes: {total_episodes}")
    
    # Episodes with transcripts
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE transcribed = 1 AND LENGTH(COALESCE(transcript, '')) > 100")
    transcribed_episodes = cursor.fetchone()[0]
    print(f"   ✅ Transcribed episodes: {transcribed_episodes}")
    
    # Episodes added today
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE DATE(created_at) = DATE('now')")
    todays_episodes = cursor.fetchone()[0]
    print(f"   📅 Episodes added today: {todays_episodes}")
    
    # Podcasts with episodes
    cursor.execute("""
        SELECT p.name, COUNT(e.id) as episode_count, MAX(e.publish_date) as latest
        FROM podcasts p 
        LEFT JOIN episodes e ON p.id = e.podcast_id 
        GROUP BY p.id, p.name 
        ORDER BY p.name
    """)
    podcasts = cursor.fetchall()
    
    print(f"\n📡 PODCAST STATUS ({len(podcasts)} podcasts):")
    for name, count, latest in podcasts:
        latest_short = latest[:10] if latest else 'None'
        status = "✅" if count > 0 else "⚪"
        print(f"   {status} {name}: {count} episodes (latest: {latest_short})")
    
    conn.close()
    
    # 2. API Keys
    print(f"\n🔑 API KEYS:")
    openai_key = "✅" if os.getenv('OPENAI_API_KEY') else "❌"
    anthropic_key = "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌"
    email_password = "✅" if os.getenv('EMAIL_PASSWORD') else "❌"
    
    print(f"   OpenAI API Key: {openai_key}")
    print(f"   Anthropic API Key: {anthropic_key}")
    print(f"   Email Password: {email_password}")
    
    # 3. File System
    print(f"\n📁 FILE SYSTEM:")
    master_dir = 'content/master_transcripts_organized'
    if os.path.exists(master_dir):
        master_files = [f for f in os.listdir(master_dir) if f.endswith('.md')]
        print(f"   ✅ Master transcript files: {len(master_files)}")
    else:
        print(f"   ❌ Master transcript directory missing")
    
    # 4. Recent Performance
    print(f"\n⚡ RECENT PERFORMANCE:")
    
    # Check if episodes detected correctly follow date logic
    from datetime import datetime, timedelta
    recent_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Episodes from last 7 days
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE created_at >= ?", (recent_date,))
    recent_episodes = cursor.fetchone()[0]
    print(f"   📈 Episodes added in last 7 days: {recent_episodes}")
    
    # Check for any episodes without transcripts (potential issues)
    cursor.execute("SELECT COUNT(*) FROM episodes WHERE transcribed = 0 OR LENGTH(COALESCE(transcript, '')) <= 100")
    incomplete_episodes = cursor.fetchone()[0]
    if incomplete_episodes == 0:
        print(f"   ✅ No incomplete episodes found")
    else:
        print(f"   ⚠️  {incomplete_episodes} episodes without transcripts")
    
    conn.close()
    
    # 5. Overall Health Score
    print(f"\n🎯 OVERALL HEALTH SCORE:")
    
    score = 0
    max_score = 7
    
    if total_episodes > 0: score += 1
    if transcribed_episodes == total_episodes: score += 1
    if openai_key == "✅": score += 1
    if anthropic_key == "✅": score += 1
    if email_password == "✅": score += 1
    if os.path.exists(master_dir): score += 1
    if incomplete_episodes == 0: score += 1
    
    percentage = (score / max_score) * 100
    
    if percentage >= 90:
        status = "🟢 EXCELLENT"
    elif percentage >= 70:
        status = "🟡 GOOD"
    elif percentage >= 50:
        status = "🟠 FAIR"
    else:
        status = "🔴 NEEDS ATTENTION"
    
    print(f"   {status} ({score}/{max_score}) - {percentage:.0f}%")
    
    # 6. Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    recommendations = []
    
    if openai_key != "✅":
        recommendations.append("❌ Set OPENAI_API_KEY environment variable")
    if anthropic_key != "✅":
        recommendations.append("❌ Set ANTHROPIC_API_KEY environment variable")
    if email_password != "✅":
        recommendations.append("❌ Set EMAIL_PASSWORD environment variable")
    if incomplete_episodes > 0:
        recommendations.append(f"⚠️  Investigate {incomplete_episodes} episodes without transcripts")
    if not os.path.exists(master_dir):
        recommendations.append("❌ Create master_transcripts_organized directory")
    
    if not recommendations:
        recommendations.append("✅ All systems operational - no action needed")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print(f"\n" + "=" * 50)
    print(f"✅ HEALTH CHECK COMPLETE")
    print(f"📊 System Status: {status}")

if __name__ == "__main__":
    automation_health_check()