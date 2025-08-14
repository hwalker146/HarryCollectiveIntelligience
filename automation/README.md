# Daily Automation

Handles the core daily podcast processing workflow.

## Active Files

### `unified_podcast_automation.py` ⭐
**Main daily automation system** - Runs via GitHub Actions every day at 10 AM UTC

**What it does:**
1. Checks RSS feeds for new episodes  
2. Compares against database to find unprocessed episodes
3. Downloads and transcribes new episodes (OpenAI Whisper)
4. Analyzes episodes with specialized prompts (Anthropic Claude)
5. Appends to master transcript files
6. Sends email report

**Specialized prompts:**
- WSJ What's News → WSJ Summary prompt
- The Intelligence → Intelligence Analysis prompt  
- Ezra Klein Show → Ezra Klein Analysis prompt
- Goldman Sachs → Goldman Sachs Analysis prompt
- Infrastructure podcasts → Infrastructure PE Analysis prompt

**Usage:**
```bash
# Run manually
python automation/unified_podcast_automation.py

# Check system status  
python automation/unified_podcast_automation.py --status
```

## Archive

### `improved_daily_automation.py`
Previous version of daily automation - kept for reference

### `enhanced_automation_with_gdrive.py` 
Version with Google Drive integration - archived as system moved to GitHub-only