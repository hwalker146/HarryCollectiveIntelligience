# Web Application

FastAPI-based web interface for podcast management and monitoring.

## Files

### `main.py` ⭐
**Main FastAPI application**

**What it provides:**
1. Web dashboard for podcast monitoring
2. Episode management interface  
3. User authentication system
4. API endpoints for podcast data

**Usage:**
```bash
# Start web server
python web_app/main.py

# Access at: http://localhost:8000
```

### `auth.py` ⭐
**Authentication system**

**What it does:**
1. User login/registration
2. Session management
3. Access control for web interface

### `celery_app.py` ⭐  
**Background task processing**

**What it does:**
1. Handles long-running tasks (transcription, analysis)
2. Queue management for episode processing
3. Background job coordination

**Usage:**
```bash
# Start Celery worker
celery -A web_app.celery_app worker --loglevel=info
```

## Web Interface Features

- **Dashboard:** Overview of podcast processing status
- **Episodes:** Browse and search transcribed episodes  
- **Analysis:** View AI-generated episode analyses
- **Admin:** Manage podcasts and system settings
- **API:** RESTful endpoints for programmatic access