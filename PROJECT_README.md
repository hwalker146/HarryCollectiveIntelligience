# 🎙️ Automated Podcast Processing System

## Overview
This system automatically processes podcast episodes daily using GitHub Actions, transcribing with OpenAI Whisper, analyzing with Claude, and organizing everything into clean, structured files.

## 📁 File Structure

```
├── podcast_files/
│   ├── individual_transcripts/    # One file per podcast with all transcripts
│   ├── individual_analysis/       # One file per podcast with all analyses  
│   ├── master_files/              # Combined master files
│   └── daily_reports/             # Daily email reports
├── scripts/
│   ├── automated_podcast_system.py  # Main automation script
│   └── maintenance/               # Utility scripts
├── core/                          # Processing engines
├── .github/workflows/             # GitHub Actions automation
└── README.md
```

## 🚀 How It Works

### Daily Automation (6 AM EDT)
1. **GitHub Actions triggers** the daily workflow
2. **Checks for new episodes** across all subscribed podcasts
3. **Transcribes** new episodes using OpenAI Whisper
4. **Analyzes** episodes using Claude with custom prompts
5. **Appends** new content to existing organized files (never creates new files)
6. **Updates** master transcript file
7. **Creates** daily report with just that day's analysis
8. **Syncs** all files to Google Drive
9. **Emails** daily report to hwalker146@outlook.com

### File Organization

#### Individual Podcast Files
- **`{Podcast_Name}_Transcripts.md`**: All transcripts for one podcast, organized by date
- **`{Podcast_Name}_Analysis.md`**: All analyses for one podcast, organized by date

#### Master Files
- **`Master_All_Transcripts.md`**: All transcripts from all podcasts, chronological
- **`Master_All_Analysis.md`**: All analyses from all podcasts, chronological

#### Daily Reports
- **`Daily_Report_YYYY-MM-DD.md`**: Just that day's new analyses (gets emailed)

## 📊 Current Status

### Processed Content (As of restoration)
- **The Data Center Frontier Show**: 66 episodes transcribed
- **Crossroads Infrastructure**: 127 episodes transcribed  
- **Exchanges at Goldman Sachs**: 59 episodes transcribed
- **Infrastructure Investor**: 22 episodes transcribed
- **Global Evolution**: 21 episodes transcribed
- **Global Energy Transition**: 7 episodes transcribed
- **Tech Innovation Weekly**: 1 episode transcribed
- **Business Strategy Podcast**: 2 episodes transcribed
- **Total**: 305 episodes processed

## 🔧 Configuration

### GitHub Secrets (Already configured)
- `OPENAI_API_KEY`: OpenAI API for Whisper transcription
- `ANTHROPIC_API_KEY`: Anthropic Claude API for analysis
- `EMAIL_USER`: aipodcastdigest@gmail.com
- `EMAIL_PASSWORD`: Email app password
- `GOOGLE_CREDENTIALS_JSON`: Google Drive API credentials
- `GOOGLE_TOKEN_JSON`: Google Drive authentication token

### Workflow Schedule
- **Automatic**: Daily at 6:00 AM EDT (10:00 AM UTC)
- **Manual**: Can be triggered anytime from GitHub Actions tab

## 📝 Key Features

### Smart File Management
- **Never creates new files** - always appends to existing ones
- **Chronological organization** - newest episodes first
- **Clean structure** - easy to read and maintain
- **Consistent naming** - predictable file locations

### Email Reports
- **Daily digest** - only new episodes analyzed that day
- **Clean format** - each episode clearly separated
- **Automatic delivery** - no manual intervention needed

### Google Drive Sync
- **Automatic backup** - all files synced to cloud
- **Organization** - matches local file structure
- **Always current** - updated with each workflow run

## 🛠️ Maintenance

### Adding New Podcasts
1. Add podcast to database (via existing interface)
2. System automatically creates files on first episode processing

### Modifying Analysis Prompts
Edit the custom prompts in the core processors

### Viewing Logs
Check GitHub Actions tab for workflow execution logs

## 🔄 Future Updates

The system is designed for easy updates:
- **Modular scripts** - each component is separate
- **Version controlled** - all changes tracked in GitHub
- **Documented structure** - clear organization
- **Extensible design** - easy to add new features

## 📈 Monitoring

### Success Indicators
- ✅ Daily workflow completes successfully
- ✅ New episodes appear in appropriate files  
- ✅ Daily email arrives each morning (when there's new content)
- ✅ Google Drive files stay synchronized

### Troubleshooting
- Check GitHub Actions logs for specific errors
- Verify API keys haven't expired
- Ensure Google Drive authentication is valid

---

**Your podcast processing system runs completely automatically and maintains itself!** 🚀