# Automated Podcast Processing System

## Overview

The automated podcast processing system runs daily via GitHub Actions to:

1. **Smart Episode Detection**: Compare database vs RSS feeds to identify missing episodes
2. **Audio Transcription**: Download, compress, and transcribe audio using OpenAI Whisper
3. **AI Analysis**: Generate detailed analysis using custom prompts for Infrastructure PE vs Goldman Sachs content
4. **Database Sync**: Update local database with transcripts and analysis
5. **Google Drive Sync**: Sync all files to organized Google Drive structure
6. **Email Reports**: Send daily reports with new content and system status

## System Architecture

### Core Components

- **`scripts/automated_podcast_system.py`**: Main automation orchestrator
- **`identify_missing_episodes.py`**: Smart episode detection using AND logic matching
- **`sync_gdrive_to_database.py`**: Syncs Google Drive transcripts to database
- **`.github/workflows/daily_podcast_analysis.yml`**: GitHub Actions workflow
- **`google_drive_sync.py`**: Google Drive integration and file management

### Database Design

- **Episodes Table**: Stores episode metadata, transcripts, and processing status
- **Analysis Reports Table**: Stores AI-generated analysis with key quotes
- **Podcasts Table**: Active podcast configuration with RSS feeds

### Smart Episode Detection

The system uses sophisticated logic to identify missing episodes:

1. **Database State Check**: Find latest transcribed episode per podcast
2. **RSS Comparison**: Fetch recent episodes from RSS feeds  
3. **AND Logic Matching**: Match by title, date, and audio URL
4. **Gap Identification**: Find episodes that exist in RSS but missing from database or need transcripts

## GitHub Actions Workflow

### Schedule
- **Daily**: 6:00 AM EDT (10:00 UTC)
- **Manual**: Can be triggered via GitHub Actions UI

### Required Secrets

```yaml
OPENAI_API_KEY: OpenAI API key for Whisper and GPT-4
GOOGLE_CREDENTIALS_JSON: Google Drive API credentials
GOOGLE_TOKEN_JSON: Google Drive OAuth token
EMAIL_USER: Gmail address for reports
EMAIL_PASSWORD: Gmail app password
```

### Workflow Steps

1. **Environment Setup**: Install Python, ffmpeg, dependencies
2. **Credential Configuration**: Setup Google Drive and OpenAI access
3. **Episode Processing**: Run smart detection and processing pipeline
4. **File Operations**: Update database, sync to Google Drive
5. **Git Operations**: Commit and push changes to repository

## Google Drive Integration

### Folder Structure

```
Podcast Intelligence System/
├── 01_Active_Content/
│   ├── Individual_Podcasts/
│   │   ├── Exchanges at Goldman Sachs/
│   │   ├── Deal Talks/
│   │   ├── Global Evolution/
│   │   ├── The Infrastructure Investor/
│   │   ├── Crossroads Infrastructure/
│   │   └── Data Center Frontier/
│   ├── Master_Files/
│   └── Daily_Reports/
├── 02_Archive/
└── 03_System/
    ├── Database_Backups/
    └── Configuration_Files/
```

### File Synchronization

- **Individual Transcripts**: Episode transcripts by podcast
- **Individual Analysis**: AI analysis reports by podcast  
- **Master Files**: Consolidated files across all podcasts
- **Daily Reports**: Automated system status and new content reports

## AI Analysis System

### Prompt Selection

**Infrastructure Podcasts**: 
- Crossroads, Deal Talks, Infrastructure Investor, Data Center Frontier, Global Evolution
- Uses `infrastructure_prompt` focused on PE investment insights

**Goldman Sachs Podcasts**:
- Exchanges at Goldman Sachs
- Uses `goldman_prompt` focused on market intelligence

### Analysis Features

- **Executive Summaries**: 3-4 paragraph investment overviews
- **Key Quotes**: 5-7 most impactful quotes with context
- **Investment Insights**: Deal sourcing, market analysis, risk assessment
- **Financial Data**: Return expectations, valuations, portfolio performance
- **Market Intelligence**: Quantitative data, forecasts, sector analysis

## Processing Pipeline

### Episode Processing Flow

1. **Detection**: Smart RSS vs database comparison
2. **Audio Download**: Fetch audio files with proper headers
3. **Compression**: Reduce file size to meet Whisper 25MB limit using ffmpeg
4. **Transcription**: OpenAI Whisper API with error handling
5. **Analysis**: GPT-4 analysis with podcast-specific prompts
6. **Database Update**: Store transcripts and analysis with metadata
7. **File Updates**: Append to individual and master files
8. **Google Drive Sync**: Upload/update all organized files

### Error Handling

- **RSS Feed Failures**: Graceful fallback and continued processing
- **Audio Download Issues**: Retry logic and timeout handling
- **Transcription Errors**: Validation and fallback procedures
- **Analysis Failures**: Fallback content generation
- **Sync Problems**: Non-blocking Google Drive operations

## Current System Status

### Active Podcasts (6)
- **Crossroads: The Infrastructure Podcast** ✅ Up to date
- **Deal Talks** ⚠️ 19 episodes need transcription  
- **Exchanges at Goldman Sachs** ⚠️ 1 episode needs transcript
- **Global Evolution** ⚠️ 1 recent episode needs transcription
- **The Data Center Frontier Show** ✅ Up to date
- **The Infrastructure Investor** ⚠️ 1 episode needs transcription

### Processing Limits

- **Daily Limit**: 5 episodes per run to avoid timeouts
- **Per Podcast**: Maximum 3 episodes per podcast per run
- **File Size**: 25MB audio limit (auto-compression)
- **Runtime**: 60-minute GitHub Actions timeout

## Monitoring and Maintenance

### Daily Email Reports

Automated emails sent to `hwalker146@outlook.com` include:

- **New Episodes Processed**: Transcription and analysis summaries
- **System Status**: Database stats, sync status, error reports
- **Processing Statistics**: Success rates, file counts, performance metrics

### Logs and Debugging

- **GitHub Actions Logs**: Full processing logs in GitHub Actions UI
- **Error Artifacts**: Logs uploaded on failure for debugging
- **Database State**: Regular validation of episode counts and transcripts

### Manual Operations

- **Workflow Dispatch**: Manual trigger via GitHub Actions
- **Test Script**: `python test_automation.py` for local validation
- **Database Sync**: Manual Google Drive sync with `sync_gdrive_to_database.py`

## Future Enhancements

- **Parallel Processing**: Process multiple episodes simultaneously
- **Advanced Analytics**: Trend analysis across episodes and timeframes  
- **Smart Prioritization**: Priority scoring for episode processing order
- **Enhanced Monitoring**: Slack/Teams integration for real-time alerts
- **Content Classification**: Automatic tagging and categorization

---

*Last Updated: 2025-08-13*
*System Status: ✅ Operational*