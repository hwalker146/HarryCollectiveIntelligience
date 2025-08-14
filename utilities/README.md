# Utilities & Maintenance

Tools for database management, gap analysis, and system maintenance.

## Files

### `identify_missing_episodes.py` ⭐
**Find missing episodes and gaps**

**What it does:**
1. Compares RSS feeds against database
2. Shows most recent transcribed episode per podcast
3. Lists all missing episodes for review
4. Helps identify processing gaps

**Usage:**
```bash
python utilities/identify_missing_episodes.py
```

### `sync_gdrive_to_database.py` ⭐
**Sync Google Drive content to database**

**What it does:**
1. Matches episodes using title, date, and audio URL
2. Syncs transcript content from Google Drive
3. Updates database with external content

**Usage:**
```bash
python utilities/sync_gdrive_to_database.py
```

### `google_drive_sync.py`
**Google Drive integration**

**What it does:**
1. Syncs master files to Google Drive
2. Handles authentication and uploads
3. Provides backup and sharing capabilities

**Usage:**
```bash
python utilities/google_drive_sync.py
```

### `create_complete_master_files.py`
**Generate comprehensive master files**

**What it does:**
1. Creates master files with ALL historical data
2. Consolidates transcripts and analyses
3. One-time file generation utility

**Usage:**
```bash
python utilities/create_complete_master_files.py
```

### `test_automation.py`
**Testing and debugging**

**What it does:**
1. Tests automation system components
2. Debugging utilities
3. Development testing

**Usage:**
```bash
python utilities/test_automation.py
```