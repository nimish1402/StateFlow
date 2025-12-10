"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./stateflow.db"
    
    # Logging
    log_level: str = "INFO"
    
    # API
    api_title: str = "StateFlow API"
    api_version: str = "0.1.0"
    api_description: str = "A minimal workflow engine for building agent workflows"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
