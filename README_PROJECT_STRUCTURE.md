# Podcast Analysis System - Project Structure

Organized by workstream for clarity and maintainability.

## 📁 Directory Structure

```
podcast_app_v2/
├── 🔄 automation/              # Daily automation workstream
│   ├── unified_podcast_automation.py ⭐ Main daily automation  
│   ├── archive/                # Archived automation versions
│   └── README.md
│
├── 📥 podcast_management/      # New podcast & bulk processing
│   ├── add_new_podcasts.py    ⭐ Add new podcasts
│   ├── process_remaining_podcasts.py ⭐ Bulk historical processing  
│   ├── process_single_podcast.py ⭐ Single podcast processing
│   └── README.md
│
├── 🔧 utilities/              # Maintenance & utilities
│   ├── identify_missing_episodes.py ⭐ Gap analysis
│   ├── sync_gdrive_to_database.py ⭐ Database sync
│   ├── google_drive_sync.py   # Google Drive integration
│   ├── create_complete_master_files.py # Master file generation
│   ├── test_automation.py     # Testing utilities
│   └── README.md
│
├── 🌐 web_app/               # Web interface
│   ├── main.py              ⭐ FastAPI application
│   ├── auth.py              # Authentication  
│   ├── celery_app.py        # Background tasks
│   └── README.md
│
├── 📄 content/              # Generated content
│   ├── master_transcripts/  # Master transcript files
│   ├── transcripts/        # Individual transcripts
│   ├── analysis/          # Episode analyses
│   └── reports/           # Daily reports
│
├── 🏗️ app/                 # Core application modules
├── 🗄️ data/                # Audio files and temp data
└── ⚙️ .github/workflows/    # GitHub Actions automation
```

## 🔄 Core Workstreams

### 1. **Daily Automation** → `automation/`
- **Purpose:** Monitor RSS feeds, auto-transcribe new episodes, analyze, email reports
- **Main file:** `unified_podcast_automation.py`
- **Schedule:** Runs daily at 10 AM UTC via GitHub Actions
- **Prompts:** Specialized analysis prompts for different podcast types

### 2. **New Podcast Management** → `podcast_management/`  
- **Purpose:** Add new podcasts and process historical episodes
- **Key files:** `add_new_podcasts.py`, `process_remaining_podcasts.py`
- **Use cases:** Expanding podcast collection, backfilling episodes

### 3. **Maintenance & Utilities** → `utilities/`
- **Purpose:** Gap analysis, database management, system maintenance  
- **Key files:** `identify_missing_episodes.py`, `sync_gdrive_to_database.py`
- **Use cases:** Finding missing episodes, data sync, debugging

### 4. **Web Interface** → `web_app/`
- **Purpose:** Dashboard for monitoring and manual management
- **Key files:** `main.py`, `auth.py`, `celery_app.py` 
- **Features:** Browse episodes, view analyses, system admin

## 🚀 Quick Start

### Daily Operations
```bash
# Check system status
python automation/unified_podcast_automation.py --status

# Run automation manually  
python automation/unified_podcast_automation.py
```

### Adding New Podcasts
```bash
# 1. Edit podcast details in the file
# 2. Run to add podcast
python podcast_management/add_new_podcasts.py

# 3. Process historical episodes
python podcast_management/process_remaining_podcasts.py
```

### Maintenance
```bash
# Find missing episodes
python utilities/identify_missing_episodes.py

# Check for gaps or issues
python utilities/test_automation.py
```

### Web Interface
```bash
# Start web server
python web_app/main.py

# Access dashboard at: http://localhost:8000
```

## 📊 Current System Status

**Active Podcasts:** 12 podcasts with specialized analysis prompts
**Automation:** GitHub Actions daily processing at 10 AM UTC  
**Prompts:** Infrastructure PE, Goldman Sachs, WSJ, Intelligence, Ezra Klein
**Storage:** GitHub-based with master transcript files
**Notifications:** Email reports with processing results

## 🔧 Configuration

- **API Keys:** Set in GitHub Secrets and `.env` file
- **Email:** Uses Gmail SMTP with app password
- **Database:** SQLite (`podcast_app_v2.db`)
- **Master Files:** Located in `content/master_transcripts/`