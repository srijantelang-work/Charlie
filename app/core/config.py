"""
Configuration settings for Charlie AI Assistant
"""

import os
from typing import List


class Settings:
    """Configuration settings"""
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Charlie AI Assistant"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    # Database - Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ocxrntrhleagdyiwsvct.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9jeHJudHJobGVhZ2R5aXdzdmN0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTgxNzIxMzcsImV4cCI6MjAxMzc0ODEzN30.QeQbDhBC83KjZRJjwIkDi8xxSVNaYlGDQOIwrp4zOVE")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Google Cloud Services
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./google-credentials.json")
    
    # Speech-to-Text
    STT_LANGUAGE_CODE: str = "en-US"
    STT_MODEL: str = "command_and_search"
    AUDIO_SAMPLE_RATE: int = 16000
    
    # Text-to-Speech
    TTS_VOICE_NAME: str = "en-US-Neural2-F"
    TTS_PITCH: float = 0.0
    TTS_SPEAKING_RATE: float = 1.0
    
    # Gemini Model
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_OUTPUT_TOKENS: int = 1024
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: float = 40
    
    # Audio Settings
    AUDIO_CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: str = "LINEAR16"
    
    # Task Execution Settings
    TASK_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_TASKS: int = 5
    TEMP_DIR: str = "/tmp/charlie_tasks"
    
    # Redis Configuration (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings() 