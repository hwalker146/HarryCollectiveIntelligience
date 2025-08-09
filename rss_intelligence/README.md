# RSS Intelligence System

A production-ready daily RSS feed analysis and reporting system that automatically:

1. **Monitors RSS Feeds** - Pulls articles from dozens of news sources
2. **Extracts Content** - Gets full article text from each URL  
3. **AI Analysis** - Uses Claude/ChatGPT to analyze each article
4. **Generates Reports** - Creates structured daily intelligence briefings
5. **Email Delivery** - Sends daily reports to your email
6. **Cloud Storage** - Saves reports to Google Drive with full history

## ✨ Features

- **🔄 Fully Automated** - Runs daily via cron job
- **🧠 AI-Powered** - Claude 3.5 Sonnet or GPT-4o analysis
- **📧 Email Reports** - Professional daily briefings
- **☁️ Cloud Storage** - Google Drive integration
- **⚙️ Configurable** - Easy to add/remove feeds and customize prompts
- **🛡️ Robust** - Error handling, rate limiting, duplicate detection
- **📊 Structured** - Reports grouped by source with key insights

## 📋 RSS Feeds Monitored

**Financial & Business News:**
- NYT Business, Economy, Technology
- Wall Street Journal (Markets, Business, Technology)
- The Economist (Business, Regional coverage)

**Infrastructure & Development:**
- Infrastructure USA, Renew Canada
- Infrastructurist, New Civil Engineer
- Roads Online Australia

**Data Center & Tech:**
- Data Center News Asia
- Data Center Post

*Total: 22 RSS feeds monitored*

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the system
cd rss_intelligence

# Install Python dependencies
pip install -r requirements.txt

# Run setup
python3 setup.py
```

### 2. Configuration

Edit `.env` file with your credentials:

```bash
# Email (Gmail recommended)
EMAIL_FROM=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=hwalker146@outlook.com

# AI Provider (choose one)
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your_claude_key_here

# Or use OpenAI
# AI_PROVIDER=openai
# OPENAI_API_KEY=your_openai_key_here

# Google Drive (optional)
GDRIVE_FOLDER_ID=your_folder_id
```

### 3. Test System

```bash
# Validate configuration and test all components
python3 setup.py --test
```

### 4. Deploy

```bash
# Install daily cron job (6 AM)
crontab cron_job.txt

# Manual run
python3 main.py

# Check logs
tail -f logs/rss_intelligence.log
```

## 📊 Sample Daily Report

```
📊 DAILY INTELLIGENCE BRIEFING
Monday, December 09, 2024

Analyzed 15 articles from 8 sources. Most active sources: 
NYT Business (4), WSJ Markets (3), Economist Business (2).

🔥 KEY INSIGHTS:
1. **Investment Focus**: Mentioned in 8 articles. Major infrastructure 
   funding announcements indicate increased government spending.
2. **Technology Trends**: AI and automation themes across 6 articles.
3. **Market Signals**: Energy transition investments accelerating.

📑 ARTICLES BY SOURCE:
══════════════════════════════════════════════════

📰 NYT BUSINESS (4 articles)
────────────────────────────────────────────────
📄 Infrastructure Investment Surges in Q4
   🕒 2024-12-09 08:30
   🔗 https://nytimes.com/...
   📊 ANALYSIS: This article reveals significant infrastructure 
       investment opportunities as government spending increases...

[Additional articles...]
```

## ⚙️ System Architecture

```
RSS Intelligence System
├── main.py              # Main orchestrator
├── config_manager.py    # Configuration management
├── feed_processor.py    # RSS parsing & article processing
├── article_extractor.py # Web scraping & content cleaning
├── ai_analyzer.py       # Claude/OpenAI integration
├── report_generator.py  # Report compilation
├── email_sender.py      # Email delivery
├── gdrive_logger.py     # Google Drive storage
└── setup.py            # Installation & testing
```

## 🔧 Configuration Files

- **`config/rss_feeds.json`** - Add/remove RSS feeds
- **`config/analysis_prompt.txt`** - Customize AI analysis prompt
- **`.env`** - API keys and credentials

### Adding RSS Feeds

Edit `config/rss_feeds.json`:

```json
{
  "Financial Times": "https://ft.com/rss",
  "Your New Source": "https://example.com/feed"
}
```

### Customizing Analysis Prompt

Edit `config/analysis_prompt.txt`:

```text
You are a financial analyst. Focus on:
1. Investment implications
2. Market trends  
3. Risk factors

Article: {article_content}
```

## 📈 Deployment Options

### Local Machine (macOS/Linux)

```bash
# Install cron job
crontab cron_job.txt

# Verify installation
crontab -l
```

### Cloud Hosting

**Render.com:**
```bash
# Create render.yaml
services:
  - type: cron
    name: rss-intelligence
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python3 main.py
    schedule: "0 6 * * *"
```

**Google Cloud Platform:**
```bash
# Deploy as Cloud Function with Cloud Scheduler
gcloud functions deploy rss-intelligence \
  --runtime python39 \
  --trigger-http \
  --entry-point main
```

**Replit:**
```bash
# Create .replit file
[deployment]
run = "python3 main.py"

# Set up Replit cron job in dashboard
```

## 📊 Monitoring & Maintenance

### Check System Status

```bash
# View recent logs
tail -20 logs/rss_intelligence.log

# Test configuration
python3 setup.py --validate

# Test email
python3 -c "
from email_sender import EmailSender
from config_manager import ConfigManager
import asyncio

async def test():
    config = ConfigManager()
    sender = EmailSender(config)
    await sender.send_test_email()

asyncio.run(test())
"
```

### Troubleshooting

**No articles found:**
- Check RSS feed URLs are accessible
- Verify network connectivity
- Review `processed_articles.json` for duplicates

**AI analysis failing:**
- Check API key validity
- Verify API credits/usage limits
- Review article content length

**Email not sending:**
- Confirm Gmail app password setup
- Check SMTP settings
- Verify email credentials

**Google Drive issues:**
- Ensure `credentials.json` is present
- Check Google Drive API permissions
- Verify folder permissions

## 🔒 Security & Best Practices

- **API Keys**: Store in `.env`, never commit to version control
- **Email**: Use Gmail app passwords, not regular passwords
- **Rate Limiting**: Built-in delays prevent API abuse
- **Error Handling**: Graceful fallbacks for all external services
- **Logging**: Comprehensive logs for debugging

## 📞 Support & Maintenance

**Daily Operations:**
- System runs automatically at 6 AM
- Email reports sent to configured address
- Reports archived in Google Drive
- Logs rotated automatically

**Weekly Review:**
- Check `logs/rss_intelligence.log` for errors
- Review email deliverability
- Monitor RSS feed health

**Monthly Maintenance:**
- Update RSS feed list as needed
- Review and tune analysis prompt
- Check API usage and costs
- Update Python dependencies

## 🎯 Sample Output Files

The system generates:

1. **Daily Email Report** - Structured briefing with key insights
2. **Google Drive Markdown** - Complete report with full articles  
3. **Local JSON Backup** - Raw data for reprocessing
4. **Processing Logs** - Detailed system activity

All reports are dated and archived for historical analysis.

---

🤖 **RSS Intelligence System** - Automated daily news analysis and reporting