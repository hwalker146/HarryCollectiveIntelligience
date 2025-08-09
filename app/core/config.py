"""
Configuration settings for Podcast Analysis Application v2
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "Podcast Analysis Application v2"
    debug: bool = False
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/podcast_app_v2")
    sqlite_url: str = os.getenv("SQLITE_URL", "sqlite:///./podcast_app_v2.db")
    
    # V1 Migration - preserve existing database
    v1_database_path: str = os.getenv("V1_DATABASE_PATH", "../data/podcast_processor.db")
    v1_transcripts_path: str = os.getenv("V1_TRANSCRIPTS_PATH", "../data/transcripts")
    
    # Redis for Celery
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # External APIs
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Email settings
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@podcastapp.com")
    
    # Application limits
    max_transcript_length: int = int(os.getenv("MAX_TRANSCRIPT_LENGTH", "50000"))
    max_subscriptions_per_user: int = int(os.getenv("MAX_SUBSCRIPTIONS_PER_USER", "10"))
    
    # Audio processing
    audio_storage_path: str = os.getenv("AUDIO_STORAGE_PATH", "./data/audio")
    transcripts_storage_path: str = os.getenv("TRANSCRIPTS_STORAGE_PATH", "./data/transcripts")
    
    # JWT settings
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class DevelopmentSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///./podcast_app_v2_dev.db"
    model_config = {"env_file": ".env", "extra": "ignore"}


class ProductionSettings(Settings):
    debug: bool = False
    # Use PostgreSQL in production
    database_url: Optional[str] = None
    model_config = {"env_file": ".env", "extra": "ignore"}


class TestingSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///:memory:"
    model_config = {"env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


settings = get_settings()