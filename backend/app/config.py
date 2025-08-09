from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # Database settings
    database_url: str = "postgresql://testmanager_user:testmanager_password@localhost:5432/testmanager_db"
    
    # App settings
    app_name: str = "AI Test Manager API"
    debug: bool = True
    
    # Security settings
    secret_key: str = secrets.token_urlsafe(32)  # Generate secure key by default
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7  # New setting for refresh token expiration
    
    class Config:
        env_file = ".env"
        env_prefix = "TESTMANAGER_"  # Environment variables should be prefixed with TESTMANAGER_


settings = Settings()