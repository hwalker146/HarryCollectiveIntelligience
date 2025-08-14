# Podcast Management

Scripts for adding new podcasts and processing historical episodes.

## Files

### `add_new_podcasts.py` ⭐
**Add new podcasts to the system**

**What it does:**
1. Adds new podcast metadata to database
2. Validates RSS feeds
3. Sets up master transcript files
4. Configures appropriate prompts

**Usage:**
```bash
# Edit the file to add your new podcast details, then run:
python podcast_management/add_new_podcasts.py
```

### `process_remaining_podcasts.py` ⭐
**Bulk process historical episodes**

**What it does:**
1. Processes multiple podcasts in batch
2. Date range filtering (e.g., episodes since Dec 2024)
3. Bulk transcription and analysis
4. Good for backfilling new podcasts

**Usage:**
```bash
# Process episodes from specified date range
python podcast_management/process_remaining_podcasts.py
```

### `process_single_podcast.py` ⭐  
**Process one podcast at a time**

**What it does:**
1. Processes all episodes from a single podcast
2. Avoids timeouts with large batches
3. Good for debugging or targeted processing

**Usage:**
```bash
# Process specific podcast
python podcast_management/process_single_podcast.py "Podcast Name Here"
```

## Workflow for Adding New Podcasts

1. **Add podcast:** Edit and run `add_new_podcasts.py`
2. **Process episodes:** Use `process_remaining_podcasts.py` for bulk or `process_single_podcast.py` for targeted processing
3. **Daily monitoring:** New episodes automatically handled by `automation/unified_podcast_automation.py`