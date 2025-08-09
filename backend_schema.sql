-- Simplified Database Schema for Backend-Only Podcast Analysis System
-- Focus: RSS Processing, Transcription, AI Analysis, Email Digests, Knowledge Base

-- Users table - simplified for backend use
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    digest_schedule TEXT DEFAULT '08:00',  -- Daily digest time (HH:MM format)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Podcasts table - core podcast information
CREATE TABLE IF NOT EXISTS podcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rss_url TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User podcast subscriptions with custom prompts
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    podcast_id INTEGER NOT NULL,
    custom_prompt TEXT,  -- Custom analysis prompt for this podcast
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(id) ON DELETE CASCADE,
    UNIQUE(user_id, podcast_id)
);

-- Episodes table - stores episode metadata and transcripts
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    podcast_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    audio_url TEXT,
    transcript TEXT,  -- Full transcript stored here
    pub_date TIMESTAMP,
    duration INTEGER,  -- Duration in seconds
    processed_at TIMESTAMP,  -- When transcription/analysis was completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(id) ON DELETE CASCADE
);

-- Analysis reports - AI-generated analysis for each user
CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    analysis_result TEXT NOT NULL,  -- Claude AI analysis
    key_topics TEXT,  -- Comma-separated topics for categorization
    reading_time_minutes INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Knowledge base entries - organized by date and topic
CREATE TABLE IF NOT EXISTS knowledge_base_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_report_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,  -- Date for organization (YYYY-MM-DD)
    topic_category TEXT NOT NULL,  -- News topic (politics, tech, business, etc.)
    entry_title TEXT NOT NULL,
    key_insights TEXT NOT NULL,
    tags TEXT,  -- Comma-separated tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_report_id) REFERENCES analysis_reports(id) ON DELETE CASCADE
);

-- Email digest log - track sent digests
CREATE TABLE IF NOT EXISTS email_digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    digest_date DATE NOT NULL,
    digest_type TEXT DEFAULT 'daily',  -- daily, ad_hoc, bulk_analysis
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Processing queue - track background tasks
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,  -- rss_check, transcribe, analyze, email
    podcast_id INTEGER,
    episode_id INTEGER,
    user_id INTEGER,
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(id) ON DELETE CASCADE,
    FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_episodes_podcast_date ON episodes(podcast_id, pub_date);
CREATE INDEX IF NOT EXISTS idx_analysis_user_date ON analysis_reports(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_date_topic ON knowledge_base_entries(user_id, entry_date, topic_category);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON user_subscriptions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_processing_status ON processing_queue(status, created_at);